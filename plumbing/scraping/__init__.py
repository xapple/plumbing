#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licenced.
"""

# Built-in modules #

# Internal modules #

# First party modules #
import autopaths
from autopaths import Path

# Third party modules #
import requests
from tqdm import tqdm
from retry import retry

# Constants #
popular_agents = None

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
    headers = make_headers(user_agent)
    # Download #
    if stream: response = request(url, headers, response=True, stream=True, **kwargs)
    else:      content  = request(url, headers, content=True, **kwargs)
    # Get total size #
    if stream:
        total_size = int(response.headers.get('content-length'))
        block_size = int(total_size/1024)
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
        with open(destination) as f: header = f.read(4)
        if header == "PK\x03\x04": destination.unzip_to(inplace=True)
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

###############################################################################
def make_headers(user_agent = None):
    """
    Will determine the right headers to pass along with the request.

    If you set the user_agent to None, we will send the default one
    which looks like: "python-requests/2.2.1 CPython/2.7.5 Darwin/13.1.0"
    If you set the user agent to a string, we will send that string.
    If you set the user agent to an integer N we will attempt to use the
    Nth most common user agent string currently in use on the web.
    It will look something like: "'Mozilla/5.0 (Windows NT 10.0; Win64; x64)
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'"
    """
    # We start with nothing #
    headers = {}
    # If we got a string for user agent #
    if isinstance(user_agent, str):
        headers.update({'User-Agent': user_agent})
    # If we got a number for user agent #
    if isinstance(user_agent, int):
        # Load the file from disk if it's not already #
        global popular_agents
        if popular_agents is None:
            from .get_user_agents import destin
            popular_agents = list(destin)
        # Remove forbidden characters #
        string = popular_agents[user_agent-1]
        string = string.strip('\n')
        # Update #
        headers.update({'User-Agent': string})
    # Return #
    return headers
