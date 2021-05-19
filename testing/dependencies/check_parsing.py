#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licensed.
Contact at www.sinclair.bio

Script to test the parsing of a `setup.py`file.
"""

# Built-in modules #
import os

# Internal modules #
from plumbing.dependencies import check_setup_py

# Third party modules #

###############################################################################
path = os.path.expanduser("~/repos/pacmill/setup.py")
result = check_setup_py(path)
