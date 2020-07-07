#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to test the functionality of the scraping module.

Written by Lucas Sinclair. MIT Licensed.

Call it like this:

    $ ipython3 -i ~/repos/plumbing/test/scraping/test_user_agent.py
"""

# Internal modules #
from plumbing.scraping.browser import download_via_browser

# Constants #
url = "http://speedtest.tele2.net/1MB.zip"
destination = '~/test2/'

###############################################################################
download_via_browser(url, destination)

url = "http://example.com/"
