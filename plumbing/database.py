# Built-in modules #
import sqlite3

# Internal modules #
from common import get_next_item
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
            first_elem = get_next_item(values)
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

    def __init__(self, path, factory=None):
        self.path = path
        self.factory = factory

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
        self.cursor.execute("SELECT * from '%s'" % self.main_table)
        return self.cursor

    def __contains__(self, key):
        """Called when evaluating ``"P81239A" in seqs``."""
        self._cursor.execute("SELECT EXISTS(SELECT 1 FROM '%s' WHERE id=='%s' LIMIT 1);" % (self.main_table, key))
        return bool(self._cursor.fetchone())

    def __len__(self):
        """Called when evaluating ``len(seqs)``."""
        self._cursor.execute("SELECT COUNT(1) FROM '%s';" % self.main_table)
        return int(self._cursor.fetchone())

    def __nonzero__(self):
        """Called when evaluating ``if seqs: pass``."""
        return True if len(self) != 0 else False

    def __getitem__(self, key):
        """Called when evaluating ``seqs[0] or seqs['P81239A']``."""
        if isinstance(key, int):
            self.cursor.execute("SELECT * from '%s' LIMIT 1 OFFSET %i;" % (self.main_table, key))
        else:
            key = key.replace("'","''")
            self.cursor.execute("SELECT * from '%s' where id=='%s' LIMIT 1;" % (self.main_table, key))
        return self.cursor.fetchone()

    @property
    def main_table(self):
        if not 'data' in self.tables:
            raise Exception("The file '" + self.path + "' does not contain any 'data' table.")
        return 'data'

    def check_format(self):
        with open(self.path, 'r') as f: header = f.read(15)
        if header != 'SQLite format 3':
            raise Exception("The file '" + self.path + "' is not an SQLite database.")

    @property_cached
    def connection(self):
        self.check_format()
        con = sqlite3.connect(self.path)
        con.row_factory = self.factory
        return con

    @property_cached
    def cursor(self):
        return self.connection.cursor()

    @property_cached
    def _connection(self):
        self.check_format()
        return sqlite3.connect(self.path)

    @property_cached
    def _cursor(self):
        return self._connection.cursor()

    @property
    def tables(self):
        """The complete list of SQL tables."""
        self.connection.row_factory = sqlite3.Row
        self._cursor.execute("select name from sqlite_master where type='table'")
        result = [x[0].encode('ascii') for x in self._cursor.fetchall()]
        self.connection.row_factory = self.factory
        return result

    @property
    def fields(self):
        """The list of fields available for every entry."""
        return self.get_fields_of_table(self.main_table)

    @property
    def first(self):
        """Just the first entry"""
        return self[0]

    def get_fields_of_table(self, table):
        """Return the list of fields for a particular table
        by querying the SQL for the complete list of column names."""
        # Check the table exists #
        if not table in self.tables: return []
        # A PRAGMA statement will implicitly issue a commit, don't use #
        self._cursor.execute("SELECT * from '%s' LIMIT 1" % table)
        fields = [x[0] for x in self._cursor.description]
        self.cursor.fetchall()
        return fields

    def close(self):
        self.cursor.close()
        self.connection.close()