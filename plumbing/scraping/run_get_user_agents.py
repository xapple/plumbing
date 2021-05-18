#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licensed.
Contact at www.sinclair.bio
"""

# Built-in modules #

# Internal modules #
import inspect, os

# First party modules #
from autopaths import Path

# Third party modules #

# Constants #
file_name = inspect.getframeinfo(inspect.currentframe()).filename
this_dir  = os.path.dirname(os.path.abspath(file_name)) + '/'
destin    = Path(this_dir + 'user_agent_strings.txt')

################################################################################
def get_popular_user_agents():
    """
    Retrieve most popular user agent strings.
    Can look at https://techblog.willshouse.com/2012/01/03/most-common-user-agents/
    """
    return ''

################################################################################
if __name__ == '__main__':
    content = get_popular_user_agents()
    destin.write(content)