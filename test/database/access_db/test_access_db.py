#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Typically you would run this file from a command line like this:

     ipython.exe -i -- /deploy/plumbing/tests/database/access_db/test_access_db.py
"""

# Built-in module #
import inspect, os

# Internal modules #
from plumbing.databases.access_database import AccessDatabase
from autopaths.file_path import FilePath

# Third party modules #
import pandas

# Constants #
file_name = inspect.getframeinfo(inspect.currentframe()).filename
this_dir  = os.path.dirname(os.path.abspath(file_name)) + '/'

# Never modify the original #
orig_db    = FilePath(this_dir + 'orig.mdb')
testing_db = FilePath(this_dir + 'testing.mdb')
orig_db.copy(testing_db)

# The database #
db = AccessDatabase(testing_db)

# Test #
print(db.tables)
print(db['tblClassifierSets'])

# Create df #
df = pandas.DataFrame({'A': ['A0', 'A1', 'A2', 'A3'],
                       'B': ['B0', 'B1', 'B2', 'B3'],
                       'C': ['C0', 'C1', 'C2', 'C3'],
                       'D': ['D0', 'D1', 'D2', 'D3']},
                       index=[0, 1, 2, 3])

# Insert table #
db.insert_df('dataframe', df)

# Close #
db.close()