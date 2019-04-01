# Built-in modules #
import os, sqlite3

# Internal modules #
from plumbing.color     import Color
from plumbing.cache     import property_cached
from plumbing.common    import download_from_url, md5sum
from autopaths.file_path import FilePath

# Third party modules #
import pandas

################################################################################
class SQLiteDatabase(FilePath):
    """A wrapper for an SQLite3 database."""

    def __init__(self, path,
                       factory   = None,
                       text_fact = None,
                       isolation = None,
                       retrieve  = None,
                       known_md5 = None):
        """
        * The path of the database comes first.
        * The factory option enables you to change how results are returned.
        * The text_fact option enables you to change text factory (useful for BLOB).
        * The Isolation source can be `None` for autocommit mode or one of:
        'DEFERRED', 'IMMEDIATE' or 'EXCLUSIVE'.
        * The retrieve option is an URL at which the database will be downloaded
        if it was not found at the `path` given.
        * The md5 option is used to check the integrity of a database."""
        self.path      = path
        self.text_fact = text_fact
        self.factory   = factory
        self.isolation = isolation
        self.retrieve  = retrieve
        self.known_md5 = known_md5
        self.prepared  = False

    def __repr__(self):
        """Called when evaluating ``print(database)``."""
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
        new_cursor.execute('SELECT * from "%s";' % self.main_table)
        return new_cursor

    def __contains__(self, key):
        """Called when evaluating ``"P81239A" in database``."""
        command = 'SELECT EXISTS(SELECT 1 FROM "%s" WHERE id=="%s" LIMIT 1);'
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
        return self.get_entry(key)

    # ------------------------------ Properties ----------------------------- #
    @property_cached
    def connection(self):
        """To be used externally by the user."""
        return self.new_connection()

    @property_cached
    def own_connection(self):
        """To be used internally in this object."""
        return self.new_connection()

    @property_cached
    def cursor(self):
        """To be used externally by the user."""
        return self.connection.cursor()

    @property_cached
    def own_cursor(self):
        """To be used internally in this object."""
        return self.own_connection.cursor()

    @property
    def tables(self):
        """The complete list of SQL tables."""
        self.own_connection.row_factory = sqlite3.Row
        self.own_cursor.execute('SELECT name from sqlite_master where type="table";')
        result = [x[0].encode('ascii') for x in self.own_cursor.fetchall()]
        self.own_connection.row_factory = self.factory
        return result

    @property_cached
    def main_table(self):
        return 'data'

    @property
    def columns(self):
        """The list of columns available in every entry."""
        return self.get_columns_of_table(self.main_table)

    @property
    def first(self):
        """Just the first entry."""
        return self.get_first()

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
    def new_connection(self):
        """Make a new connection."""
        if not self.prepared: self.prepare()
        con = sqlite3.connect(self.path, isolation_level=self.isolation)
        con.row_factory = self.factory
        if self.text_fact: con.text_factory = self.text_fact
        return con

    def prepare(self):
        """Check that the file exists, optionally downloads it.
        Checks that the file is indeed an SQLite3 database.
        Optionally check the MD5."""
        if not os.path.exists(self.path):
            if self.retrieve:
                print("Downloading SQLite3 database...")
                download_from_url(self.retrieve, self.path, progress=True)
            else: raise Exception("The file '" + self.path + "' does not exist.")
        self.check_format()
        if self.known_md5: assert self.known_md5 == self.md5
        self.prepared = True

    def check_format(self):
        if self.count_bytes == 0: return
        with open(self.path, 'r') as f: header = f.read(15)
        if header != 'SQLite format 3':
            raise Exception("The file '" + self.path + "' is not an SQLite database.")

    def create(self, columns=None, type_map=None, overwrite=False):
        """Create a new database with a certain schema."""
        # Check already exists #
        if self.count_bytes > 0:
            if overwrite: self.remove()
            else: raise Exception("File exists already at '%s'" % self)
        # If we want it empty #
        if columns is None:
            self.touch()
        # Make the table #
        else:
            self.add_table(self.main_table, columns=columns, type_map=type_map)

    def add_table(self, name, columns, type_map=None, if_not_exists=False):
        """Add add a new table to the database.  For instance you could do this:
        self.add_table('data', {'id':'integer', 'source':'text', 'pubmed':'integer'})"""
        # Check types mapping #
        if type_map is None and isinstance(columns, dict): types = columns
        if type_map is None:                               types = {}
        # Safe or unsafe #
        if if_not_exists: query = 'CREATE TABLE IF NOT EXISTS "%s" (%s);'
        else:             query = 'CREATE table "%s" (%s);'
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
        self.own_cursor.execute('SELECT * from "%s" LIMIT 1;' % table)
        columns = [x[0] for x in self.own_cursor.description]
        self.cursor.fetchall()
        return columns

    def add(self, entries, table=None, columns=None, ignore=False):
        """Add entries to a table.
        The *entries* variable should be an iterable."""
        # Default table and columns #
        if table is None:   table   = self.main_table
        if columns is None: columns = self.get_columns_of_table(table)
        # Default columns #
        question_marks = ','.join('?' for c in columns)
        cols           = ','.join('"' + c + '"' for c in columns)
        ignore         = " OR IGNORE" if ignore else ""
        sql_command    = 'INSERT%s into "%s"(%s) VALUES (%s);'
        sql_command    = sql_command % (ignore, table, cols, question_marks)
        # Possible errors we want to catch #
        errors  = (sqlite3.OperationalError, sqlite3.ProgrammingError)
        errors += (sqlite3.IntegrityError, sqlite3.InterfaceError, ValueError)
        # Do it #
        try:
            new_cursor = self.own_connection.cursor()
            new_cursor.executemany(sql_command, entries)
        except errors as err:
            raise Exception(self.detailed_error(sql_command, columns, entries, err))
        except KeyboardInterrupt as err:
            print("You interrupted the data insertion.")
            print("Committing everything done up to this point.")
            self.own_connection.commit()
            raise err

    def detailed_error(self, sql_command, columns, entries, err):
        # The command #
        message1 = "\n\n The command \n <%s%s%s> \n on the database '%s' failed."
        params   = (Color.cyn, sql_command, Color.end, self)
        message1 = message1 % params
        # The bindings #
        message2 = "\n * %sThe bindings (%i) %s: %s \n * %sYou gave%s: %s"
        params   = (Color.b_ylw, len(columns), Color.end)
        params  += (columns, Color.b_ylw, Color.end, entries)
        message2 = message2 % params
        # The first element #
        message3 = "\n * %sExample element (%i)%s: %s \n"
        elem     = None
        if isinstance(entries, types.GeneratorType):
            try: elem = entries.next()
            except StopIteration: pass
        if isinstance(entries, (list, tuple)) and entries:
            elem = entries[0]
        params   =  (Color.b_ylw, len(elem) if elem else 0, Color.end, elem)
        message3 = message3 % params
        # The original error #
        message4 = "The original error was:\n %s%s%s \n" % (Color.u_red, err, Color.end)
        # Return #
        return message1 + message2 + message3 + message4

    def add_by_steps(self, entries_by_step, table=None, columns=None):
        """Add entries to the main table.
        The *entries* variable should be an iterable yielding iterables."""
        for entries in entries_by_step: self.add(entries, table=table, columns=columns)

    def count_entries(self, table=None):
        """How many rows in a table."""
        if table is None: table = self.main_table
        self.own_cursor.execute('SELECT COUNT(1) FROM "%s";' % table)
        return int(self.own_cursor.fetchone()[0])

    def index(self, column='id', table=None):
        if table is None: table = self.main_table
        index_name = table + '_index'
        try:
            command = 'CREATE INDEX if not exists "%s" on "%s" (%s);'
            command = command % (index_name, table, column)
            self.own_cursor.execute(command)
        except KeyboardInterrupt as err:
            print("You interrupted the creation of the index. Not committing.")
            raise err

    def get_first(self, table=None):
        """Just the first entry."""
        if table is None: table = self.main_table
        query = 'SELECT * FROM "%s" LIMIT 1;' % table
        return self.own_cursor.execute(query).fetchone()

    def get_last(self, table=None):
        """Just the last entry."""
        if table is None: table = self.main_table
        query = 'SELECT * FROM "%s" ORDER BY ROWID DESC LIMIT 1;' % table
        return self.own_cursor.execute(query).fetchone()

    def get_number(self, num, table=None):
        """Get a specific entry by its number."""
        if table is None: table = self.main_table
        self.own_cursor.execute('SELECT * from "%s" LIMIT 1 OFFSET %i;' % (self.main_table, num))
        return self.own_cursor.fetchone()

    def get(self, table, column, key): return self.get_entry(key, column, table)
    def get_entry(self, key, column=None, table=None):
        """Get a specific entry."""
        if table is None:  table  = self.main_table
        if column is None: column = "id"
        if isinstance(key, basestring): key = key.replace("'","''")
        query = 'SELECT * from "%s" where "%s"=="%s" LIMIT 1;'
        query = query % (table, column, key)
        self.own_cursor.execute(query)
        return self.own_cursor.fetchone()

    def vacuum(self):
        """Compact the database, remove old transactions."""
        self.own_cursor.execute("VACUUM")

    def close(self):
        self.cursor.close()
        self.connection.close()
        self.own_cursor.close()
        self.own_connection.close()

    def insert_df(self, table_name, df):
        """Create a table and populate it with data from a dataframe."""
        df.to_sql(table_name, con=self.own_connection)

    # ----------------------------- Unfinished ------------------------------ #
    def add_column(self, name, kind=None, table=None):
        """Add add a new column to a table."""
        pass

    def open(self):
        """Reopen a database that was closed, useful for debugging."""
        pass

    def uniquify(self, name, kind=None, table=None):
        """Remove entries that have duplicate values on a specific column."""
        query = 'DELETE from "data" WHERE rowid not in (select min(rowid) from data group by id);'
        pass

    def get_and_order(self, ids, column=None, table=None):
        """Get specific entries and order them in the same way."""
        command = """
        SELECT rowid, * from "data"
        WHERE rowid in (%s)
        ORDER BY CASE rowid
        %s
        END;
        """
        ordered = ','.join(map(str,ids))
        rowids  = '\n'.join("WHEN '%s' THEN %s" % (row,i) for i,row in enumerate(ids))
        command = command % (ordered, rowids)
        # This could have worked but sqlite3 was too old on the server
        # ORDER BY instr(',%s,', ',' || id || ',')

    # ---------------------------- Multidatabase ---------------------------- #
    def import_table(self, source, table_name):
        """Copy a table from another SQLite database to this one."""
        query = "SELECT * FROM `%s`" % table_name.lower()
        df = pandas.read_sql(query, source.connection)
        df.to_sql(table_name, con=self.own_connection)
