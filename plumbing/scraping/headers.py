#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licensed.
Contact at www.sinclair.bio
"""

# Built-in modules #

# Internal modules #

# First party modules #

# Third party modules #

# Constants #
popular_agents = None

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
            from .run_get_user_agents import destin
            popular_agents = destin.lines
        # Remove forbidden characters #
        string = popular_agents[user_agent-1]
        string = string.strip('\n')
        # Update #
        headers.update({'User-Agent': string})
    # Return #
    return headers
