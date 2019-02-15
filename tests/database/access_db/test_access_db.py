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

# Constants #
file_name = inspect.getframeinfo(inspect.currentframe()).filename
this_dir  = os.path.dirname(os.path.abspath(file_name)) + '/'

# The database #
db_path = FilePath(this_dir + 'project.mdb')
db = AccessDatabase(db_path)

# Test #
print db.conn_string
print db.tables
print db['tblClassifiers']
db.close()

# Drop tables #
#for table in db.tables:
#    try:
#        print table
#        db.drop_table(table)
#    except:
#        pass