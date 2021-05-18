#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licensed.
Contact at www.sinclair.bio
"""

# Built-in modules #
import os, shutil, time
import urllib.parse

# Internal modules #
from plumbing.scraping import handle_destination

# First party modules #
from autopaths import Path

###############################################################################
def make_driver():
    """
    Create a headless webdriver with selenium.

    Note: #TODO Change the download dir to a temp dir #
    Otherwise it will append (1) and (2) etc. to the filename before the
    extension e.g. 'data.zip (1).crdownload'
    """
    # Import #
    from selenium import webdriver
    # Paths #
    chrome_driver_path = shutil.which('chromedriver')
    # Start a service #
    service = webdriver.chrome.service.Service(chrome_driver_path)
    service.start()
    # Add options #
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options = options.to_capabilities()
    # Create the driver #
    driver = webdriver.Remote(service.service_url, options)
    # #TODO Change the download dir to a temp dir #
    dl_dir = Path(os.getcwd() + '/')
    # Return #
    return driver, dl_dir

###############################################################################
def download_via_browser(url,
                         destination = None,
                         uncompress  = True,
                         timeout     = 120):
    """
    Save the resource as a file on disk by running a full browser to avoid
    being blocked by the server.
    Note: While the file is downloading, it will have ".crdownload" appended
    to it.
    """
    # Choose the right option for destination #
    destination = handle_destination(url, destination)
    # Make a driver if we don't already have one #
    driver, download_dir = make_driver()
    # Get resource #
    driver.get(url)
    # This should remove the query part of the URL #
    predicted_name = url.split("/")[-1].split("?")[0]
    # But we need to convert things like %20 to a space #
    predicted_name = urllib.parse.unquote(predicted_name)
    # It should land in the downloads directory #
    result = download_dir + predicted_name
    # We have no way to know when it finishes #
    start_time = time.time()
    while True:
        time.sleep(0.5)
        if result.exists: break
        if time.time() - start_time > timeout:
            msg = "The file should have been at '%s'." % result
            raise Exception("The timeout was exceeded. " + msg)
    # Let's move it #
    result.move_to(destination, overwrite=True)
    # Uncompress #
    if uncompress:
        with open(destination, 'rb') as f: header = f.read(4)
        if header == b"PK\x03\x04": destination.unzip_to(inplace=True)
    # Return #
    return destination
