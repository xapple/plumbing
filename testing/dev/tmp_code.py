#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licensed.
Contact at www.sinclair.bio

Development script to test some of the methods in `plumbing`
and try out different things. This script can safely be ignored
and is meant simply as a sandbox.

Typically you would run this file from a command line like this:

     ipython3 -i -- ~/deploy/plumbing/test/dev/tmp_code.py
"""

# Built-in modules #
import os

# Internal modules #
from plumbing.dependencies import check_setup_py

# Third party modules #

###############################################################################
path = os.path.expanduser("~/deploy/pacmill/setup.py")
check_setup_py(path)