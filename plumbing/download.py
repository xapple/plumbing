# -*- coding: utf-8 -*-

# Built-in modules #

# First party modules #
from autopaths import Path

# Third party modules #
import requests
from tqdm import tqdm
from retry import retry

################################################################################
def download_from_url(url,
                      destination = None,
                      uncompress  = True,
                      make_text   = True):
    """
    Download a resource from the internet, given its URL.

    By default the text of the resource is returned by this function,
    which works well if you want to grab some HTML. If you want to download
    a file to disk however, then you should specify *destination* as a file
    path and the contents will be placed there instead.

    By default will retry if an HTTP error arises.
    By default will uncompress files that are saved to disk if they are zipped.

    TODO: case where destination is a directory.
    """
    # Don't convert to text if saving to a file #
    if destination is not None: make_text = False
    # Don't uncompress if not saving to a file #
    if destination is None: uncompress = False
    # Function we will use #
    @retry(requests.exceptions.HTTPError, tries=8, delay=1, backoff=2)
    def download():
        response = requests.get(url)
        response.raise_for_status()
        if make_text: return response.text
        else:         return response.content
    # Download #
    content = download()
    # Destination #
    if destination is not None:
        destination = Path(destination)
        destination.directory.create_if_not_exists()
    # Uncompress #
    if uncompress:
        with open(destination) as f: header = f.read(4)
        if header == "PK\x03\x04": unzip(destination, inplace=True)
    # Return #
    if destination is None: return content
    else:                   return destination

################################################################################
def stream_from_url(source, destination, progress=False, uncompress=False):
    """
    Stream a file from an URL and place it somewhere on disk. Like wget.
    Uses requests and tqdm to display a progress bar if you want.
    By default it will uncompress files.
    #TODO: handle case where destination is a directory
    """
    # Check destination exists #
    destination = Path(destination)
    destination.directory.create_if_not_exists()
    # Over HTTP #
    response = requests.get(source, stream=True)
    total_size = int(response.headers.get('content-length'))
    block_size = int(total_size/1024)
    # Do it #
    with open(destination, "wb") as handle:
        if progress:
            for data in tqdm(response.iter_content(chunk_size=block_size), total=1024): handle.write(data)
        else:
            for data in response.iter_content(chunk_size=block_size): handle.write(data)
    # Uncompress #
    if uncompress:
        with open(destination) as f: header = f.read(4)
        if header == "PK\x03\x04": unzip(destination, inplace=True)
        # Add other compression formats here
    # Return #
    return destination
