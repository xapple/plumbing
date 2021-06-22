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

# Make a detailed message #
msg_base = "The executable '%s' is required for this operation." \
           " Unfortunately it cannot be found anywhere in your $PATH." \
           " Either you need to install '%s' on your system" \
           " or you need to fix the $PATH environment variable."

################################################################################
def check_cmd(cmd_name, exception=True, extra_msg=None, fancy_box=True):
    """
    Checks if the given executable is found in the path.
    Optionally, raises an exception if the executable `cmd_name` is not found.
    Optionally, print an extra message as a string alongside the exception.
    """
    # Use our own which implementation #
    from plumbing.common import which
    # Try to find it in the $PATH #
    if which(cmd_name, safe=True) is not None: return True
    # Prepare the message #
    msg = msg_base % (cmd_name, cmd_name)
    # Add any hints #
    if cmd_name in extra_clues: msg += '\n\n' + extra_clues.get(cmd_name)
    # Add a custom extra message #
    if extra_msg: msg += '\n\n' + extra_msg
    # If we want to print it with style in a box #
    if fancy_box:
        from plumbing.common import rich_panel_print
        rich_panel_print(msg, "Command Not Found")
        msg = "The executable '%s' cannot be found." % cmd_name
    # Raise an exception #
    if exception: raise Exception(msg)
    # Return #
    return False