#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Typically you would run this file from a command line like this:

     ipython.exe -i -- /deploy/plumbing/tests/database/access_db/test_conversion.py

Or in the Ubuntu WSL:

    ipython -i -- ~/deploy/plumbing/tests/database/access_db/test_conversion.py
"""

# Built-in module #
import inspect, os

# Internal modules #
from plumbing.databases.access_database import AccessDatabase
from autopaths.file_path import FilePath

# Third party modules #

# Constants #
file_name = inspect.getframeinfo(inspect.currentframe()).filename
this_dir  = os.path.dirname(os.path.abspath(file_name)) + '/'

# Never modify the original #
orig_db    = FilePath(this_dir + 'orig.mdb')
testing_db = FilePath(this_dir + 'testing.mdb')
orig_db.copy(testing_db)

# The database #
db = AccessDatabase(testing_db)

# Convert #
db.convert_to_sqlite()
