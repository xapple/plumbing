#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Typically you would run this file from a command line like this:

    ipython.exe -i -- /deploy/plumbing/tests/database/access_db/test_copy_table.py

Or in the Ubuntu WSL:

    ipython -i -- ~/deploy/plumbing/tests/database/access_db/test_copy_table.py
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
orig_path    = FilePath(this_dir + 'orig.mdb')
testing_path = FilePath(this_dir + 'testing.mdb')
orig_path.copy(testing_path)

# The source database #
source_db = AccessDatabase(testing_path)

# The destination database #
dest_path = FilePath(this_dir + 'copied_table.mdb')
dest_db   = AccessDatabase.create(dest_path)

# Copy a table #
dest_db.import_table(source_db, "tblClassifierSets")