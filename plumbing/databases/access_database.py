# Built-in modules #
import os

# Internal modules #
from autopaths.file_path import FilePath
from plumbing.cache      import property_cached

# Third party modules #
import pyodbc, pandas

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

    # ------------------------------ Properties ----------------------------- #
    @property_cached
    def conn_string(self):
        if os.name == "posix":
            string = "Driver=MDBTools;User Id='%s';DBQ=%s"
            return string % (self.username, self.path)
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
        return [table[2] for table in self.own_cursor.tables() if not table[2].startswith('MSys')]

    # ------------------------------- Methods ------------------------------- #
    def __getitem__(self, key):
        """Called when evaluating ``database[0] or database['P81239A']``."""
        return self.table_as_df(key)

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
        if table_name not in self.tables:
            raise Exception("The table '%s' does not seem to exist." % table_name)

    def table_as_df(self, table_name):
        """Return a table as a dataframe."""
        self.table_must_exist(table_name)
        query = "SELECT * FROM `%s`" % table_name
        return pandas.read_sql(query, self.own_conn)

    def count_rows(self, table_name):
        """Return the number of entries in a table by reallying counting them."""
        self.table_must_exist(table_name)
        query = "SELECT COUNT (*) FROM `%s`" % table_name
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