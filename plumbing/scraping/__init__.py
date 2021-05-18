#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licensed.
Contact at www.sinclair.bio
"""

# Built-in modules #
import os

# Internal modules #
from plumbing.scraping.headers import make_headers

# First party modules #
import autopaths
from autopaths import Path

# Third party modules #
import requests
from retry import retry

###############################################################################
@retry(requests.exceptions.HTTPError, tries=8, delay=1, backoff=2)
def request(url,
            header   = None,
            text     = False,
            content  = False,
            response = False,
            **kwargs):
    # Get #
    resp = requests.get(url, headers=header, **kwargs)
    # This will be caught by the decorator #
    resp.raise_for_status()
    # Pick what to return #
    if text:     return resp.text
    if content:  return resp.content
    if response: return resp

###############################################################################
def retrieve_from_url(url, user_agent=None, **kwargs):
    """
    Return the text content of a resource (e.g. the HTML).
    By default we will retry if an HTTP error arises.
    """
    # Custom user agent if needed #
    if user_agent is not None: header = make_headers(user_agent)
    else: header = ""
    # Download #
    content = request(url, header, text=True, **kwargs)
    # Return #
    return content

###############################################################################
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
                      uncompress  = False,
                      user_agent  = 1,
                      stream      = False,
                      progress    = False,
                      desc        = None,
                      **kwargs):
    """
    Save the resource as a file on disk.
    """
    # Custom user agent if needed #
    if user_agent is not None: header = make_headers(user_agent)
    else: header = ""
    # Download #
    if stream: response = request(url, header, response=True, stream=True, **kwargs)
    else:      content  = request(url, header, content=True, **kwargs)
    # Get total size #
    if stream:
        total_size = int(response.headers.get('content-length', -1))
        num_blocks = 1500
        block_size = int(total_size/num_blocks)
    # Sometimes we don't get content-length #
    if stream and total_size < 0:
        return download_from_url(url, destination, uncompress, user_agent,
                                 False, False, **kwargs)
    # Choose the right option for destination #
    destination = handle_destination(url, destination)
    # How the progress bar should look like #
    bar = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{remaining}, ' \
          '{rate_fmt}{postfix}]'
    # Delete the destination if there is any exception or a ctrl-c #
    try:
        # With streaming #
        if stream:
            generator = response.iter_content(chunk_size=block_size)
            if progress:
                # In the future replace with `from tqdm.rich import tqdm`
                from tqdm import tqdm
                bar = tqdm(bar_format   = bar,
                           desc         = desc,
                           total        = total_size,
                           unit         = 'iB',
                           unit_scale   = True)
                with open(destination, "wb") as handle:
                    for data in generator:
                        handle.write(data)
                        bar.update(len(data))
                    bar.close()
            else:
                with open(destination, "wb") as handle:
                    for data in generator: handle.write(data)
        # Without streaming #
        if not stream:
            with open(destination, "wb") as handle: handle.write(content)
    except:
        if os.path.exists(destination): os.remove(destination)
        raise
    # Uncompress the result #
    if uncompress:
        # To detect tar.gz we rely on the extension #
        if destination.endswith('.tar.gz'):
            return destination.untargz_to()
        # Otherwise read the magic number #
        with open(destination, 'rb') as f:
            header = f.read(4)
        # If it's a zip file #
        if header == b"PK\x03\x04":
            return destination.unzip_to(inplace=True)
        # If it's a gzip file #
        elif header[:3] == b"\x1f\x8b\x08":
            return destination.ungzip_to()
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

