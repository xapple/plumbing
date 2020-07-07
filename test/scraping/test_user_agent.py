#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to test the functionality of the scraping module.

Written by Lucas Sinclair. MIT Licensed.

Call it like this:

    $ ipython3 -i ~/repos/plumbing/test/scraping/test_user_agent.py
"""

# Internal modules #

###############################################################################
url = "http://example.com/index.html"

#from plumbing.scraping import retrieve_from_url
#print(retrieve_from_url(url, user_agent=1))

from plumbing.scraping import download_from_url
print(download_from_url(url, '~/test/example.com/extra_level/'))