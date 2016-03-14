# Built-in modules #
import os, sqlite3
from itertools import islice

# Internal modules #
from color     import Color
from autopaths import FilePath
from cache     import property_cached
from common    import download_from_url, md5sum

################################################################################
class Database(FilePath):

    def __init__(self, path, factory=None, isolation=None, retrieve=None, md5=None):
        """
        * The path of the database comes first.
        * The factory option enables you to change how results are returned.
        * The Isolation source can be `None` for autocommit mode or one of:
        'DEFERRED', 'IMMEDIATE' or 'EXCLUSIVE'.
        * The retrieve option is an URL at which the database will be downloaded
        if it was not found at the `path` given.
        * The md5 option is used to check the integrety of a database."""
        self.path      = path
        self.factory   = factory
        self.isolation = isolation
        self.retrieve  = retrieve
        self.md5       = md5

    def __repr__(self):
        """Called when evaluating ``print database``."""
        return '<%s object on "%s">' % (self.__class__.__name__, self.path)

    def __enter__(self):
        """Called when entering the 'with' statement."""
        return self

    def __exit__(self, errtype, value, traceback):
        """Called when exiting the 'with' statement.
        Enables us to close the database properly, even when
        exceptions are raised."""
        self.close()

    def __iter__(self):
        """Called when evaluating ``for x in database: pass``."""
        new_cursor = self.own_connection.cursor()
        new_cursor.execute("SELECT * from '%s'" % self.main_table)
        return new_cursor

    def __contains__(self, key):
        """Called when evaluating ``"P81239A" in database``."""
        command = "SELECT EXISTS(SELECT 1 FROM '%s' WHERE id=='%s' LIMIT 1);"
        self.own_cursor.execute(command % (self.main_table, key))
        return bool(self.own_cursor.fetchone()[0])

    def __len__(self):
        """Called when evaluating ``len(database)``."""
        return self.count_entries()

    def __nonzero__(self):
        """Called when evaluating ``if database: pass``."""
        return True if len(self) != 0 else False

    def __getitem__(self, key):
        """Called when evaluating ``database[0] or database['P81239A']``."""
        if isinstance(key, int):
            self.own_cursor.execute("SELECT * from '%s' LIMIT 1 OFFSET %i;" % (self.main_table, key))
        else:
            key = key.replace("'","''")
            self.own_cursor.execute("SELECT * from '%s' where id=='%s' LIMIT 1;" % (self.main_table, key))
        return self.own_cursor.fetchone()

    # ------------------------------ Properties ----------------------------- #
    @property_cached
    def connection(self):
        """To be used externally by the user."""
        self.prepare()
        con = sqlite3.connect(self.path, isolation_level=self.isolation)
        con.row_factory = self.factory
        return con

    @property_cached
    def cursor(self):
        """To be used externally by the user."""
        return self.connection.cursor()

    @property_cached
    def own_connection(self):
        """To be used internally in this object."""
        self.prepare()
        return sqlite3.connect(self.path, isolation_level=self.isolation)

    @property_cached
    def own_cursor(self):
        """To be used internally in this object."""
        return self.own_connection.cursor()

    @property
    def tables(self):
        """The complete list of SQL tables."""
        self.own_connection.row_factory = sqlite3.Row
        self.own_cursor.execute("select name from sqlite_master where type='table'")
        result = [x[0].encode('ascii') for x in self.own_cursor.fetchall()]
        self.own_connection.row_factory = self.factory
        return result

    @property_cached
    def main_table(self):
        if self.tables and not 'data' in self.tables:
            raise Exception("The file '" + self.path + "' does not contain any 'data' table.")
        return 'data'

    @property
    def columns(self):
        """The list of columns available in every entry."""
        return self.get_columns_of_table(self.main_table)

    @property
    def first(self):
        """Just the first entry."""
        return self[0]

    @property
    def last(self):
        """Just the last entry."""
        return self.get_last()

    @property
    def frame(self):
        """The main table as a blaze data structure. Not ready yet."""
        pass
        #return blaze.Data('sqlite:///%s::%s') % (self.path, self.main_table)

    # ------------------------------- Methods ------------------------------- #
    def prepare(self):
        """Check that the file exists, optionally downloads it.
        Checks that the file is indeed an SQLite3 database.
        Optionally check the MD5."""
        if not os.path.exists(self.path):
            if self.retrieve:
                print "Downloading SQLite3 database..."
                download_from_url(self.retrieve, self.path, progress=True)
            else: raise Exception("The file '" + self.path + "' does not exist.")
        self.check_format()
        if self.md5: assert self.md5 == md5sum(self.path)

    def check_format(self):
        if self.count_bytes == 0: return
        with open(self.path, 'r') as f: header = f.read(15)
        if header != 'SQLite format 3':
            raise Exception("The file '" + self.path + "' is not an SQLite database.")

    def create(self, columns, type_map=None, overwrite=False):
        """Create a new database with a certain schema."""
        # Check already exists #
        if self.count_bytes > 0:
            if overwrite: self.remove()
            else: raise Exception("File exists already at '%s'" % self)
        # Make the table #
        self.add_table(self.main_table, columns=columns, type_map=type_map)

    def add_table(self, name, columns, type_map=None, if_not_exists=False):
        """Add add a new table to the database.  For instance you could do this:
        self.add_table('data', {'id':'integer', 'source':'text', 'pubmed':'integer'})"""
        # Check types mapping #
        if type_map is None and isinstance(columns, dict): types = columns
        if type_map is None:                               types = {}
        # Safe or unsafe #
        if if_not_exists: query = "CREATE IF NOT EXISTS table '%s' (%s)"
        else:             query = "CREATE table '%s' (%s)"
        # Do it #
        cols = ','.join(['"' + c + '"' + ' ' + types.get(c, 'text') for c in columns])
        self.own_cursor.execute(query % (self.main_table, cols))

    def execute(self, *args, **kwargs):
        """Convenience shortcut."""
        return self.cursor.execute(*args, **kwargs)

    def get_columns_of_table(self, table=None):
        """Return the list of columns for a particular table
        by querying the SQL for the complete list of column names."""
        # Check the table exists #
        if table is None: table = self.main_table
        if not table in self.tables: return []
        # A PRAGMA statement will implicitly issue a commit, don't use #
        self.own_cursor.execute("SELECT * from '%s' LIMIT 1" % table)
        columns = [x[0] for x in self.own_cursor.description]
        self.cursor.fetchall()
        return columns

    def index(self, column='id', table=None):
        if table is None: table = self.main_table
        try:
            command = "CREATE INDEX if not exists 'main_index' on '%s' (%s)"
            self.own_cursor.execute(command % (self.main_table, column))
        except KeyboardInterrupt as err:
            print "You interrupted the creation of the index. Not committing."
            raise err

    def add(self, entries, table=None, columns=None):
        """Add entries to a table.
        The *entries* variable should be an iterable."""
        # Default table and columns #
        if table is None:   table   = self.main_table
        if columns is None: columns = self.columns
        # Default columns #
        fields         = ','.join('"' + c + '"' for c in columns)
        question_marks = ','.join('?' for c in columns)
        sql_command    = "INSERT into '%s' (%s) VALUES (%s)" % (table, fields, question_marks)
        try:
            self.own_cursor.executemany(sql_command, entries)
        except (ValueError, sqlite3.OperationalError, sqlite3.ProgrammingError, sqlite3.InterfaceError) as err:
            first_elem = islice(entries, 0, 1)
            message1 = "The command <%s%s%s> on the database '%s' failed with error:\n %s%s%s"
            params   =  (Color.cyn, sql_command, Color.end, self, Color.u_red, err, Color.end)
            message1 = message1 % params
            message2 = "\n * %sThe bindings (%i) %s: %s \n * %sYou gave%s: %s"
            params   =  (Color.b_ylw, len(self.columns), Color.end)
            params  +=  (self.columns, Color.b_ylw, Color.end, entries)
            message2 = message2 % params
            message3 = "\n * %sFirst element (%i)%s: %s \n"
            params   =  (Color.b_ylw, len(first_elem) if first_elem else 0, Color.end, first_elem)
            message3 = message3 % params
            message4 = "\n The original error was: '%s'" % err
            raise Exception(message1 + message2 + message3 + message4)
        except KeyboardInterrupt as err:
            print "You interrupted the data insertion. Committing everything done up to this point."
            self.own_connection.commit()
            raise err

    def add_by_steps(self, entries_by_step, table=None, columns=None):
        """Add entries to the main table.
        The *entries* variable should be an iterable yielding iterables."""
        for entries in entries_by_step: self.add(entries, table=table, columns=columns)

    def count_entries(self, table=None):
        """How many rows in a table."""
        if table is None: table = self.main_table
        self.own_cursor.execute("SELECT COUNT(1) FROM '%s';" % table)
        return int(self.own_cursor.fetchone()[0])

    def get_last(self, table=None):
        """Just the last entry."""
        if table is None: table = self.main_table
        query = "SELECT * FROM %s ORDER BY ROWID DESC LIMIT 1;" % table
        return self.own_cursor.execute(query).fetchone()

    def close(self):
        self.cursor.close()
        self.connection.close()
        self.own_cursor.close()
        self.own_connection.close()

    # ------------------------------- Extended ------------------------------- #
    def add_column(self, name, kind=None, table=None):
        """Add add a new column to a table."""
        pass