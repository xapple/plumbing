# Built-in modules #
import sqlite3
from itertools import islice

# Internal modules #
from color import Color
from autopaths import FilePath
from cache import property_cached

################################################################################
def convert_to_sql(source, dest, keys, values, sql_field_types=None):
    if sql_field_types is None: sql_field_types = {}
    with sqlite3.connect(dest) as connection:
        # Prepare #
        cursor = connection.cursor()
        fields = ','.join(['"' + f + '"' + ' ' + sql_field_types.get(f, 'text') for f in keys])
        cursor.execute("CREATE table 'data' (%s)" % fields)
        question_marks = '(' + ','.join(['?' for x in keys]) + ')'
        sql_command = "INSERT into 'data' values " + question_marks
        # Main loop #
        try:
            cursor.executemany(sql_command, values)
        except (ValueError, sqlite3.OperationalError, sqlite3.ProgrammingError, sqlite3.InterfaceError) as err:
            first_elem = islice(values, 0, 1)
            message1 = "The command <%s%s%s> on the database '%s' failed with error:\n %s%s%s"
            message1 = message1 % (Color.cyn, sql_command, Color.end, dest, Color.u_red, err, Color.end)
            message2 = "\n * %sThe bindings (%i) %s: %s \n * %sYou gave%s: %s"
            message2 = message2 % (Color.b_ylw, len(keys), Color.end, keys, Color.b_ylw, Color.end, values)
            message3 = "\n * %sFirst element (%i)%s: %s \n"
            message3 = message3 % (Color.b_ylw, len(first_elem) if first_elem else 0, Color.end, first_elem)
            raise Exception(message1 + message2 + message3)
        except KeyboardInterrupt as err:
            print "You interrupted the creation of the database. Committing everything done up to this point."
            connection.commit()
            cursor.close()
            raise err
        # Index #
        try:
            cursor.execute("CREATE INDEX if not exists 'data_index' on 'data' (id)")
        except KeyboardInterrupt as err:
            print "You interrupted the creation of the index. Committing everything done up to this point."
            connection.commit()
            cursor.close()
            raise err
        # Close #
        connection.commit()
        cursor.close()

################################################################################
class Database(FilePath):

    def __init__(self, path, factory=None, isolation=None):
        self.path      = path
        self.factory   = factory
        self.isolation = isolation

    def __repr__(self):
        """Called when evaluating ``print seqs``."""
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
        """Called when evaluating ``for x in seqs: pass``."""
        new_cursor = self.own_connection.cursor()
        new_cursor.execute("SELECT * from '%s'" % self.main_table)
        return new_cursor

    def __contains__(self, key):
        """Called when evaluating ``"P81239A" in seqs``."""
        self.own_cursor.execute("SELECT EXISTS(SELECT 1 FROM '%s' WHERE id=='%s' LIMIT 1);" % (self.main_table, key))
        return bool(self.own_cursor.fetchone())

    def __len__(self):
        """Called when evaluating ``len(seqs)``."""
        self.own_cursor.execute("SELECT COUNT(1) FROM '%s';" % self.main_table)
        return int(self.own_cursor.fetchone())

    def __nonzero__(self):
        """Called when evaluating ``if seqs: pass``."""
        return True if len(self) != 0 else False

    def __getitem__(self, key):
        """Called when evaluating ``seqs[0] or seqs['P81239A']``."""
        if isinstance(key, int):
            self.own_cursor.execute("SELECT * from '%s' LIMIT 1 OFFSET %i;" % (self.main_table, key))
        else:
            key = key.replace("'","''")
            self.own_cursor.execute("SELECT * from '%s' where id=='%s' LIMIT 1;" % (self.main_table, key))
        return self.own_cursor.fetchone()

    #------------------------------- Properties ------------------------------#
    @property_cached
    def connection(self):
        """To be used externally by the user."""
        self.check_format()
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
        self.check_format()
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
    def fields(self):
        """The list of fields available for every entry."""
        return self.get_fields_of_table(self.main_table)

    @property
    def first(self):
        """Just the first entry"""
        return self[0]

    @property
    def last(self):
        """Just the last entry"""
        return self.own_cursor.execute("SELECT * FROM data ORDER BY ROWID DESC LIMIT 1;").fetchone()

    #-------------------------------- Methods --------------------------------#
    def check_format(self):
        if self.count_bytes == 0: return
        with open(self.path, 'r') as f: header = f.read(15)
        if header != 'SQLite format 3':
            raise Exception("The file '" + self.path + "' is not an SQLite database.")

    def get_fields_of_table(self, table):
        """Return the list of fields for a particular table
        by querying the SQL for the complete list of column names."""
        # Check the table exists #
        if not table in self.tables: return []
        # A PRAGMA statement will implicitly issue a commit, don't use #
        self.own_cursor.execute("SELECT * from '%s' LIMIT 1" % table)
        fields = [x[0] for x in self.own_cursor.description]
        self.cursor.fetchall()
        return fields

    def close(self):
        self.cursor.close()
        self.connection.close()
        self.own_cursor.close()
        self.own_connection.close()

    def create(self, fields, types=None, overwrite=False):
        """Create a new database with a certain schema. For instance you could do this:
        self.create({'id':'integer', 'source':'text', 'pubmed':'integer'})"""
        # Check already exists #
        if self.count_bytes > 0:
            if overwrite: self.remove()
            else: raise Exception("File exists already at '%s'" % self)
        # Check types #
        if types is None and isinstance(fields, dict): types=fields
        if types is None: types = {}
        # Do it #
        fields = ','.join(['"' + f + '"' + ' ' + types.get(f, 'text') for f in fields])
        self.own_cursor.execute("CREATE table '%s' (%s)" % (self.main_table, fields))

    def index(self, column='id'):
        try:
            command = "CREATE INDEX if not exists 'main_index' on '%s' (%s)"
            self.own_cursor.execute(command % (self.main_table, column))
        except KeyboardInterrupt as err:
            print "You interrupted the creation of the index. Not committing."
            raise err

    def add(self, entries):
        """Add entries to the main table.
        The *entries* variable should be an iterable."""
        question_marks = '(' + ','.join(['?' for x in self.fields]) + ')'
        sql_command = "INSERT into 'data' values " + question_marks
        try:
            self.own_cursor.executemany(sql_command, entries)
        except (ValueError, sqlite3.OperationalError, sqlite3.ProgrammingError, sqlite3.InterfaceError) as err:
            first_elem = islice(entries, 0, 1)
            message1 = "The command <%s%s%s> on the database '%s' failed with error:\n %s%s%s"
            message1 = message1 % (Color.cyn, sql_command, Color.end, self, Color.u_red, err, Color.end)
            message2 = "\n * %sThe bindings (%i) %s: %s \n * %sYou gave%s: %s"
            message2 = message2 % (Color.b_ylw, len(self.fields), Color.end, self.fields, Color.b_ylw, Color.end, entries)
            message3 = "\n * %sFirst element (%i)%s: %s \n"
            message3 = message3 % (Color.b_ylw, len(first_elem) if first_elem else 0, Color.end, first_elem)
            message4 = "\n The original error was: '%s'" % err
            raise Exception(message1 + message2 + message3 + message4)
        except KeyboardInterrupt as err:
            print "You interrupted the data insertion. Committing everything done up to this point."
            self.own_connection.commit()
            raise err

    def add_by_steps(self, entries_by_step):
        """Add entries to the main table.
        The *entries* variable should be an iterable yielding iterables."""
        for entries in entries_by_step: self.add(entries)
