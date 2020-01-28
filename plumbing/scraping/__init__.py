#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licenced.
"""

# Built-in modules #

# Internal modules #
from plumbing.scraping.headers import make_headers

# First party modules #
import autopaths
from autopaths import Path

# Third party modules #
import requests
from tqdm import tqdm
from retry import retry

###############################################################################
def retrieve_from_url(url, user_agent=1, **kwargs):
    """
    Return the text content of a resource (e.g. the HTML).
    By default we will retry if an HTTP error arises.
    """
    # Custom user agent if needed #
    headers = make_headers(user_agent)
    # Download #
    content = request(url, headers, text=True, **kwargs)
    # Return #
    return content

def stream_from_url(*args, **kwargs):
    """
    Save the resource as a file on disk iteratively by first asking
    for the 'content-length' header entry and downloading in chunks.
    By default we will retry if an HTTP error arises.
    By default we will uncompress a downloaded file if it is zipped.
    """
    # Just redirect to download_from_url #
    kwargs.update({'steam': True})
    return download_from_url(*args, **kwargs)

def download_from_url(url,
                      destination = None,
                      uncompress  = True,
                      user_agent  = 1,
                      stream      = False,
                      progress    = False,
                      **kwargs):
    """
    Save the resource as a file on disk.
    """
    # Custom user agent if needed #
    header = make_headers(user_agent)
    # Download #
    if stream: response = request(url, header, response=True, stream=True, **kwargs)
    else:      content  = request(url, header, content=True, **kwargs)
    # Get total size #
    if stream:
        total_size = int(response.headers.get('content-length', -1))
        block_size = int(total_size/1024)
    # Sometimes we don't get content-length #
    if stream and total_size < 0:
        return download_from_url(url, destination, uncompress, user_agent,
                                 False, False, **kwargs)
    # Choose the right option for destination #
    destination = handle_destination(url, destination)
    # Write streaming #
    with open(destination, "wb") as handle:
        if stream:
            generator = response.iter_content(chunk_size=block_size)
            if progress:
                for data in tqdm(generator, total=1024):
                    handle.write(data)
            else:
                for data in generator:
                    handle.write(data)
        else:
            handle.write(content)
    # Uncompress #
    if uncompress:
        with open(destination, 'rb') as f: header = f.read(4)
        if header == b"PK\x03\x04": destination.unzip_to(inplace=True)
    # Return #
    return destination

###############################################################################
def handle_destination(url, destination):
    """
    The destination can be either unspecified or can contain either a file path
    or a directory path.
    """
    # Choose a default for destination #
    if destination is None:
        destination = autopaths.tmp_path.new_temp_file()
    # Directory case - choose a filename #
    elif destination.endswith('/'):
        filename    = url.split("/")[-1].split("?")[0]
        destination = Path(destination + filename)
        destination.directory.create_if_not_exists()
    # Normal case #
    else:
        destination = Path(destination)
        destination.directory.create_if_not_exists()
    # Return #
    return destination

###############################################################################
@retry(requests.exceptions.HTTPError, tries=8, delay=1, backoff=2)
def request(url,
            headers  = None,
            text     = False,
            content  = False,
            response = False,
            **kwargs):
    # Get #
    resp = requests.get(url, headers=headers, **kwargs)
    resp.raise_for_status()
    # Pick what to return #
    if text:     return resp.text
    if content:  return resp.content
    if response: return resp

