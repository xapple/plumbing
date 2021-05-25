# Built-in modules #
import os, platform, base64, shutil, gzip
from io import StringIO

# Internal modules #
from plumbing.common import camel_to_snake
from plumbing.cache import property_cached
from plumbing.databases.sqlite_database import SQLiteDatabase

# First party modules #
from autopaths.file_path import FilePath
from autopaths.tmp_path  import new_temp_path

# Third party modules #
import pandas

################################################################################
class AccessDatabase(FilePath):
    """
    A wrapper for a Microsoft Access database via pyodbc.
    On Ubuntu 18 you would install the dependencies like this:

        $ sudo apt install python3-pip
        $ sudo apt install unixodbc-dev
        $ pip install --user pyodbc
    """

    # Enable this to change `ThisName` to `this_name` on all columns #
    convert_col_names_to_snake = False

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
        # Get current system #
        system = platform.system()
        # macOS #
        if system == "Darwin":
            string = "Driver={Microsoft Access Driver (*.mdb)};User Id='%s';DBQ=%s"
            return string % (self.username, self.path)
        # Linux #
        if os.name == "posix":
            string = "Driver={MDBTools};User Id='%s';DBQ=%s"
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
        if os.name == "posix":
            import pbs3
            mdb_tables  = pbs3.Command("mdb-tables")
            tables_list = mdb_tables('-1', self.path).split('\n')
            condition   = lambda t: t and not t.startswith('MSys')
            return [t.lower() for t in tables_list if condition(t)]
        # Default case #
        return [table[2].lower() for table in self.own_cursor.tables()
                if not table[2].startswith('MSys')]

    @property
    def real_tables(self):
        """The complete list of tables excluding views and query tables."""
        return [table for table in self.tables if self.test_table(table)]

    # ------------------------------- Methods ------------------------------- #
    def __getitem__(self, key):
        """Called when evaluating ``database[0] or database['P81239A']``."""
        return self.table_as_df(key)

    def __contains__(self, key):
        """Called when evaluating ``'students' in database``."""
        return key.lower() in self.tables

    def test_table(self, table_name):
        """Can the table be read from?"""
        import pyodbc
        try:
            query = "SELECT COUNT (*) FROM `%s`" % table_name.lower()
            self.own_cursor.execute(query)
            self.own_cursor.fetchone()
        except pyodbc.Error:
            return False
        return True

    def new_conn(self):
        """Make a new connection."""
        import pyodbc
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
        """
        Return a table as a dataframe.
        There is a library that can do this, but it has a bug.
        See https://github.com/jbn/pandas_access/issues/3

            import pandas_access
            return pandas_access.read_table(self.path, table_name)

        This is also a possibility https://github.com/gilesc/mdbread
        but it is not in PyPI.
        """
        # Check #
        self.table_must_exist(table_name)
        # If we are on unix use mdb-tools instead #
        if os.name == "posix": df = self.table_as_df_via_mdbtools(table_name)
        # Default case #
        else: df = self.table_as_df_via_query(table_name)
        # Optionally rename columns #
        if self.convert_col_names_to_snake: df = df.rename(columns=camel_to_snake)
        # Return #
        return df

    def table_as_df_via_query(self, table_name):
        """Use an SQL query to create the dataframe."""
        query = "SELECT * FROM `%s`" % table_name.lower()
        return pandas.read_sql(query, self.own_conn)

    def table_as_df_via_mdbtools(self, table_name, *args, **kwargs):
        """Use an mdbtools executable to create the dataframe."""
        import subprocess
        cmd = ['mdb-export', self.path, table_name]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        return pandas.read_csv(proc.stdout, *args, **kwargs)

    def insert_df(self, table_name, df):
        """Create a table and populate it with data from a dataframe."""
        df.to_sql(table_name, con=self.own_conn)

    def count_rows(self, table_name):
        """Return the number of entries in a table by counting them."""
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
    def convert_to_sqlite(self, destination=None, method="shell", progress=False):
        """Who wants to use Access when you can deal with SQLite databases instead?"""
        # Display progress bar #
        if progress:
            import tqdm
            progress = tqdm.tqdm
        else:
            progress = lambda x:x
        # Default path #
        if destination is None: destination = self.replace_extension('sqlite')
        # Delete if it exists #
        destination.remove()
        # Method with shell and a temp file #
        if method == 'shell':     return self.sqlite_by_shell(destination)
        # Method without a temp file #
        if method == 'object':    return self.sqlite_by_object(destination, progress)
        # Method with dataframe #
        if method == 'dataframe': return self.sqlite_by_df(destination, progress)

    def sqlite_by_shell(self, destination):
        """Method with shell and a temp file. This is hopefully fast."""
        script_path = new_temp_path()
        self.sqlite_dump_shell(script_path)
        from shell_command import shell_output
        shell_output('sqlite3 -bail -init "%s" "%s" .quit' % (script, destination))
        script.remove()

    def sqlite_by_object(self, destination, progress):
        """This is probably not very fast."""
        db = SQLiteDatabase(destination)
        db.create()
        for script in self.sqlite_dump_string(progress): db.cursor.executescript(script)
        db.close()

    def sqlite_by_df(self, destination, progress):
        """Is this fast?"""
        db = SQLiteDatabase(destination)
        db.create()
        for table in progress(self.real_tables): self[table].to_sql(table, con=db.connection)
        db.close()

    def sqlite_dump_shell(self, script_path):
        """Generate a text dump compatible with SQLite by using
        shell commands. Place this script at *script_path*."""
        # First the schema #
        from shell_command import shell_output
        shell_output('mdb-schema "%s" sqlite >> "%s"' % (self.path, script_path))
        # Start a transaction, speeds things up when importing #
        script_path.append("\n\n\nBEGIN TRANSACTION;\n")
        # Then export every table #
        for table in self.tables:
            command = 'mdb-export -I sqlite "%s" "%s" >> "%s"'
            shell_output(command % (self.path, table, script_path))
        # End the transaction
        script_path.append("\n\n\nEND TRANSACTION;\n")

    def sqlite_dump_string(self, progress):
        """Generate a text dump compatible with SQLite.
        By yielding every table one by one as a byte string."""
        # First the schema #
        import pbs3
        mdb_schema = pbs3.Command("mdb-schema")
        yield mdb_schema(self.path, "sqlite").encode('utf8')
        # Start a transaction, speeds things up when importing #
        yield "BEGIN TRANSACTION;\n"
        # Then export every table #
        mdb_export = pbs3.Command("mdb-export")
        for table in progress(self.tables):
            yield mdb_export('-I', 'sqlite', self.path, table).encode('utf8')
        # End the transaction
        yield "END TRANSACTION;\n"

    # --------------------------- Multi-database ---------------------------- #
    def import_table(self, source, table_name):
        """Copy a table from another Access database to this one.
        Requires that you have mdbtools command line executables installed
        in a Windows Subsystem for Linux environment."""
        # Run commands #
        import pbs3
        wsl = pbs3.Command("wsl.exe")
        table_schema   = wsl("-e", "mdb-schema", "-T", table_name, source.wsl_style, "access")
        table_contents = wsl("-e", "mdb-export", "-I", "access", source.wsl_style, table_name)
        # Filter #
        table_schema = ' '.join(l for l in table_schema.split('\n') if not l.startswith("--"))
        # Execute statements #
        self.cursor.execute(str(table_schema))
        self.cursor.execute(str(table_contents))

    # -------------------------------- Create ------------------------------- #
    @classmethod
    def create(cls, destination):
        """Create a new empty MDB at destination."""
        mdb_gz_b64 = """\
        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
        """
        pristine = StringIO()
        pristine.write(base64.b64decode(mdb_gz_b64))
        pristine.seek(0)
        pristine = gzip.GzipFile(fileobj=pristine, mode='rb')
        with open(destination, 'wb') as handle: shutil.copyfileobj(pristine, handle)
        return cls(destination)