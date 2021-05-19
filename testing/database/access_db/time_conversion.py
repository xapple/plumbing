#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
Typically you would run this file from a command line like this:

     ipython.exe -i -- /deploy/plumbing/tests/database/access_db/time_conversion.py

Or in the Ubuntu WSL:

    ipython -i -- ~/deploy/plumbing/tests/database/access_db/time_conversion.py
"""

# Built-in module #
import inspect, os

# Internal modules #
from plumbing.databases.access_database import AccessDatabase
from plumbing.timer import Timer

# First party modules #
from autopaths.file_path import FilePath

# Constants #
file_name = inspect.getframeinfo(inspect.currentframe()).filename
this_dir  = os.path.dirname(os.path.abspath(file_name)) + '/'

# Paths #
big_mdb_path = FilePath(this_dir + 'big.mdb')

# Create example db #
from cbm_explorer.continent import continent
original = continent.first.run_database
original.copy(big_mdb_path)

# The database #
big_mdb = AccessDatabase(big_mdb_path)

# Clean up #
big_sql = big_mdb.replace_extension('sqlite')
big_sql.remove()

# Convert #
#with Timer(): big_mdb.convert_to_sqlite(method="shell", progress=True)
#with Timer(): big_mdb.convert_to_sqlite(method="dataframe", progress=True)
#with Timer(): big_mdb.convert_to_sqlite(method="object", progress=True)