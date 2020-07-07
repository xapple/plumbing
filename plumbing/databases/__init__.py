# Built-in modules #
import os, sqlite3

# Internal modules #
from itertools import islice

# First party modules #
from plumbing.color import Color

################################################################################
def convert_to_sql(dest, keys, values, sql_field_types=None):
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
            print("You interrupted the creation of the database. Committing everything done up to this point.")
            connection.commit()
            cursor.close()
            raise err
        # Index #
        try:
            cursor.execute("CREATE INDEX if not exists 'data_index' on 'data' (id)")
        except KeyboardInterrupt as err:
            print("You interrupted the creation of the index. Committing everything done up to this point.")
            connection.commit()
            cursor.close()
            raise err
        # Close #
        connection.commit()
        cursor.close()
