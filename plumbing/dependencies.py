#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licensed.
Contact at www.sinclair.bio
"""

# Built-in modules #
import re

# Modules that's don't have the same PyPI name as import name #
module_names = {
    "biopython":    "Bio",
    "ipython":      "IPython",
    "scikit-learn": "sklearn",
    "scikit-bio":   "skbio",
    "biom-formt":   "biom",
}

################################################################################
def check_setup_py(path_of_setup):
    """
    Parses the required modules from a `setup.py` file and checks they are
    importable and have the minimum required version installed.

    Some ideas for extracting dependency information from a `setup.py` file:
    https://stackoverflow.com/questions/24236266/

    Instead let's try the `parsesetup` package.
    Note: The code in the setup.py will be evaluated.

    Other interesting projects:
    https://pypi.org/project/requirements-parser/

    Typically you can use this function like this:

        >>> from plumbing.dependencies import check_setup_py
        >>> check_setup_py('~/module_name/setup.py')
    """
    # First let's check we have that module #
    check_module('parsesetup')
    import parsesetup
    # Parse it #
    from autopaths.file_path import FilePath
    path_of_setup = FilePath(path_of_setup)
    # Run it #
    setup_args = parsesetup.parse_setup(path_of_setup, trusted=True)
    requires = setup_args.get('install_requires', [])
    # Parse it #
    requires = [re.split(r'==|>=', req) for req in requires]
    requires = [req if len(req)==2 else (req[0], None) for req in requires]
    requires = dict(requires)
    # Loop #
    for package, version in requires.items(): check_module(package, version)

################################################################################
def check_module(mod_name, min_version=None):
    """
    Raise an exception if the given module is either not found or has a
    version that is below the minimum required version number (if specified).

    Typically you can use this function like this:

        >>> from plumbing.dependencies import check_module
        >>> check_module('lxml', '4.5.3')

    If this is not the case the following exception will be raised:

        ImportError: The minimum version required for the "lxml" package is
        <4.5.3>. You have version <4.5.2> installed. Please update the package
         to the latest version and try again.
    """
    # Special cases with modules that change names #
    if mod_name in module_names:
        pypi_name = mod_name
        imrt_name = module_names[mod_name]
        full_name = pypi_name + ' (' + imrt_name + ')'
    else:
        pypi_name = mod_name
        imrt_name = mod_name
        full_name = mod_name
    # Special case for `sh` which doens't set __spec__ #
    if imrt_name == 'sh': return
    # Use a function available in python >= 3.6 #
    import importlib
    spec = importlib.util.find_spec(imrt_name)
    # Message #
    msg = 'You do not seem to have the "%s" package installed. Either you' \
          ' never installed it or your `$PYTHONPATH` is not set up' \
          ' correctly. For more instructions see the `README.md` file.'
    # If we didn't find it #
    if spec is None: raise ModuleNotFoundError(msg % full_name)
    # Did the user request we also check the version #
    if min_version is None: return
    # Just import it and capture the version #
    module = __import__(imrt_name)
    if hasattr(module, '__version__'):
        cur_version = module.__version__
    else:
        # Otherwise use a function available in python >= 3.8 #
        from importlib.metadata import version
        cur_version = version(imrt_name)
    # Message #
    msg = 'The minimum version required for the "%s" package is <%s>.' \
          ' You have version <%s> installed. Please update the package to' \
          ' the latest version and try again.'
    msg = msg % (full_name, min_version, cur_version)
    # Parse the versions #
    from packaging.version import Version
    cur_version = Version(cur_version)
    min_version = Version(min_version)
    # If the version is too low #
    if cur_version < min_version: raise ImportError(msg)



