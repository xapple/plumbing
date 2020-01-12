#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to test the functionality of the scraping module.

Written by Lucas Sinclair. MIT Licensed.

Call it like this:

    $ ipython3 -i ~/repos/plumbing/tests/scraping/test_user_agent.py
"""

# Internal modules #
from plumbing.scraping import retrieve_from_url

###############################################################################
url = "http://example.com/index.html"
print(retrieve_from_url(url, user_agent=1))