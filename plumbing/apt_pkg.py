#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licensed.
Contact at www.sinclair.bio
"""

# Built-in modules #
import sys, platform

# Internal modules #
from plumbing.check_cmd_found import check_cmd

# Third party modules #
import sh

################################################################################
def get_apt_packages(all_packages, verbose=False):
    """
    Checks if the given aptitude packages are presently installed on the
    current system. Provide a list of strings as input.
    If one of the packages given as input is not installed, we will install it.
    """
    for pkg_name in all_packages:
        if check_apt_pkg(pkg_name): continue
        else: install_apt_pkg(pkg_name, verbose, verbose)

################################################################################
def check_apt_pkg(pkg_name, exception=False):
    """
    Checks if the given aptitude package is presently installed on the
    current system.
    Optionally, raises an exception if the package is not found.
    """
    # Check the current OS #
    if platform.system() != 'Linux':
        msg = "The check_apt_pkg function is only designed to work on Linux"
        raise Exception(msg)
    # Call command #
    cmd = sh.Command('dpkg-query')
    result = cmd('-W', "--showformat='${Status}\\n'", pkg_name, _ok_code=[0,1])
    # Check result #
    if 'install ok installed' in result: return True
    # Make a message #
    msg = 'The package %s is not currently installed on this system. ' \
          'You can install it by typing: \n\n' \
          '    $ sudo apt install %s'
    msg = msg % (pkg_name, pkg_name)
    # Raise an exception #
    if exception: raise Exception(msg)
    # Return #
    return False

################################################################################
def install_apt_pkg(pkg_name, verbose=False, redirect=False):
    """
    Install a given apt package.
    Optionally, prints a status message before starting.
    Optionally, prints the output of apt on the current stdout.
    """
    # Optional message #
    if verbose: print("Installing apt package '%s'..." % pkg_name)
    # Check redirection #
    if redirect:
        sh.sudo.apt('install', '--yes', pkg_name, _out=sys.stdout, _err=sys.stderr)
    else:
        sh.sudo.apt('install', '--yes', pkg_name)

################################################################################
def check_apt_exists(exception=True):
    """
    Checks that the aptitude package manager is accessible on the current
    system.
    """
    # The message #
    msg = "You have encountered this error because we have attempted" \
          " the automatic installation of certain packages but are only" \
          " able do this using the `apt` package manager on supported OSes."
    # Check the current operating system #
    if platform.system() != 'Linux': raise Exception(msg)
    # Check the apt command exists #
    return check_cmd('apt', exception, msg)
