#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licenced.
"""

# Built-in modules #
import os, shutil

# Internal modules #
from plumbing.scraping import handle_destination

# First party modules #

# Third party modules #
from selenium import webdriver

# Constants #
driver = None
download_dir = None

###############################################################################
def make_driver():
    """
    Create a headless webdriver with selenium.
    """
    # Paths #
    chromedriver_path = shutil.which('chromedriver')
    # Start a service #
    service = webdriver.chrome.service.Service(chromedriver_path)
    service.start()
    # Add options #
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options = options.to_capabilities()
    # Create the driver #
    driver = webdriver.Remote(service.service_url, options)
    # #TODO Change the download dir #
    download_dir = os.getcwd()
    # Return #
    return driver, download_dir

###############################################################################
def download_via_browser(url,
                         destination = None,
                         uncompress  = True):
    """
    Save the resource as a file on disk by running a full browser to avoid
    being blocked by the server.
    """
    # Choose the right option for destination #
    destination = handle_destination(url, destination)
    # Make a driver if we don't already have one #
    global driver, download_dir
    if driver is None: driver, download_dir = make_driver()
    # Get resource #
    driver.get(url)
    # It should land in the downloads directory #
    predicted_name = url.split("/")[-1].split("?")[0]
    result = download_dir + predicted_name
    assert result.exists
    # Let's move it #
    result.move(destination)
    # Uncompress #
    if uncompress:
        with open(destination) as f: header = f.read(4)
        if header == "PK\x03\x04": destination.unzip_to(inplace=True)
    # Return #
    return destination
