# Built-in modules #
import os, platform

# Internal modules #
from autopaths.file_path import FilePath
from plumbing.cache      import property_cached
from plumbing.tmpstuff    import new_temp_file
from plumbing.databases.sqlite_database import SQLiteDatabase

# Third party modules #
import pyodbc, pandas
if os.name == "posix": import sh
if os.name == "nt":    import pbs as sh
from shell_command import shell_output

################################################################################
class AccessDatabase(FilePath):
    """A wrapper for a Microsoft Access database via pyodbc.
    On Ubuntu 18 you would install like this:

        $ sudo apt install python3-pip
        $ sudo apt install unixodbc-dev
        $ pip install --user pyodbc
    """

    # ------------------------------ Constructor ---------------------------- #
    def __init__(self, path,
                       username = 'admin',
                       password = None):
        """
        * The path of the database comes first.
        * The username.
        * The password.
        """
        # Path attribute #
        super(AccessDatabase, self).__init__(path)
        # Attributes #
        self.username = username
        self.password = password
        # Check the database exists #
        self.must_exist()

    # ------------------------------ Properties ----------------------------- #
    @property_cached
    def conn_string(self):
        system = platform.system()
        # macOS #
        if system == "Darwin":
            string = "Driver={Microsoft Access Driver (*.mdb)};User Id='%s';DBQ=%s"
            return string % (self.username, self.path)
        # Linux #
        if os.name == "posix":
            string = "Driver=MDBTools;User Id='%s';DBQ=%s"
            return string % (self.username, self.path)
        # Windows #
        if os.name == "nt":
            string = "Driver={Microsoft Access Driver (*.mdb, *.accdb)};User Id='%s';DBQ=%s"
            return string % (self.username, self.path)
        else:
            raise Exception("Unrecognized platform.")

    @property_cached
    def conn(self):
        """To be used externally by the user."""
        return self.new_conn()

    @property_cached
    def own_conn(self):
        """To be used internally in this object."""
        return self.new_conn()

    @property_cached
    def cursor(self):
        """To be used externally by the user."""
        return self.conn.cursor()

    @property_cached
    def own_cursor(self):
        """To be used internally in this object."""
        return self.own_conn.cursor()

    @property
    def tables(self):
        """The complete list of tables."""
        # If we are on unix use mdbtools instead #
        mdb_tables = sh.Command("mdb-tables")
        return [t for t in mdb_tables('-1', self.path).split('\n') if t]
        # Default case #
        return [table[2].lower() for table in self.own_cursor.tables() if not table[2].startswith('MSys')]

    # ------------------------------- Methods ------------------------------- #
    def __getitem__(self, key):
        """Called when evaluating ``database[0] or database['P81239A']``."""
        return self.table_as_df(key)

    def __contains__(self, key):
        """Called when evaluating ``'students' in database``."""
        return key.lower() in self.tables

    def new_conn(self):
        """Make a new connection."""
        return pyodbc.connect(self.conn_string)

    def close(self):
        self.cursor.close()
        self.conn.close()
        self.own_cursor.close()
        self.own_conn.close()

    def table_must_exist(self, table_name):
        """Return a table as a dataframe."""
        if table_name.lower() not in self.tables:
            raise Exception("The table '%s' does not seem to exist." % table_name)

    def table_as_df(self, table_name):
        """Return a table as a dataframe."""
        self.table_must_exist(table_name)
        query = "SELECT * FROM `%s`" % table_name.lower()
        return pandas.read_sql(query, self.own_conn)

    def insert_df(self, table_name, df):
        """Create a table and populate it with data from a dataframe."""
        df.to_sql(table_name, con=self.own_conn)

    def count_rows(self, table_name):
        """Return the number of entries in a table by reallying counting them."""
        self.table_must_exist(table_name)
        query = "SELECT COUNT (*) FROM `%s`" % table_name.lower()
        self.own_cursor.execute(query)
        return int(self.own_cursor.fetchone()[0])

    def count_rows_fast(self, table_name):
        """Return the number of entries in a table by using the quick inaccurate method."""
        pass

    def tables_with_counts(self):
        """Return the number of entries in all table."""
        table_to_count = lambda t: self.count_rows(t)
        return zip(self.tables, map(table_to_count, self.tables))

    def drop_table(self, table_name):
        if table_name not in self.tables:
            raise Exception("The table '%s' does not seem to exist." % table_name)
        query = "DROP TABLE %s" % table_name
        self.own_conn.execute(query)

    # ------------------------------- Convert ------------------------------- #
    def sqlite_dump(self, script_path):
        """Generate a text dump compatible with SQLite."""
        # First the schema #
        shell_output('mdb-schema "%s" sqlite >> "%s"' % (self.path, script_path))
        # Start a transaction, speeds things up when importing #
        shell_output('echo "BEGIN;" >> %s' % self.path)
        shell_output('echo "" >> %s' % self.path)
        # Then export every table #
        for table in self.tables:
            command = 'mdb-export -I sqlite "%s" "%s" >> "%s"'
            shell_output(command % (self.path, table, script_path))
        # End the transaction
        shell_output('echo "COMMIT;" >> "%s"' % self.path)
        shell_output('echo "" >> "%s"' % self.path)

    def convert_to_sqlite(self, destination=None):
        """Who wants to use Access when you can deal with SQLite databases instead?"""
        # Default path #
        if destination is None: destination = self.replace_extension('sqlite')
        # Delete if it exists #
        destination.remove()
        # Put the script somewhere #
        script = new_temp_file()
        self.sqlite_dump(script)
        # New database #
        sqlite = sh.Command("sqlite3")
        sqlite('-bail', '-init', script, destination, '.quit')
        script.remove()
