#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licensed.
Contact at www.sinclair.bio
"""

# Built-in modules #

# First party modules #

# Third party modules #

################################################################################
# This provides extra information for certain packages #

extra_clues = {
    'apt': "It is likely the `apt` command is missing because we are not "
           "currently running on the Ubuntu or Debian operating system.",
    'gsed': "The gsed package can be installed with `brew install gnu-sed`"
            " on macOS."
}

################################################################################
def check_cmd(cmd_name, exception=True, extra_msg=None):
    """
    Checks if the given executable is found in the path.
    Optionally, raises an exception if the executable `cmd_name` is not found.
    Optionally, print an extra message as a string alongside the exception.
    """
    # Use our own which implementation #
    from plumbing.common import which
    # Try to find it in the $PATH #
    if which(cmd_name, safe=True) is not None: return True
    # Make a detailed message #
    msg = f"The executable '{cmd_name}' is required for this operation." \
          f" Unfortunately it cannot be found anywhere in your $PATH."   \
          f" Either you need to install '{cmd_name}'"                    \
          f" or you need to fix the $PATH environment variable."
    # Add any hints #
    if cmd_name in extra_clues: msg += '\n\n' + extra_clues.get(cmd_name)
    # Add a custom extra message #
    if extra_msg: msg += '\n\n' + extra_msg
    # Raise an exception #
    if exception: raise Exception(msg)
    # Return #
    return False