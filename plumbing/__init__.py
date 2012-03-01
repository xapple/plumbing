"""
============
Introduction
============
The plumbing software is a package written in Python. It is designed to help with plumbing-type programmation.

============
Installation
============
To install you can simply type::

    $ sudo easy_install plumbing

If you don't have permission to install it like that, you can simply download the code and include the directory in your python path::

    $ wget http://pypi.python.org/packages/source/e/plumbing/plumbing-1.0.0.tar.gz
    $ tar -xzf plumbing-1.0.0.tar.gz
    $ cd plumbing-1.0.0/
    $ sed -i "$ a\export PYTHONPATH=`pwd`/:\$PYTHONPATH" ~/.bashrc
    $ source ~/.bashrc

========
Examples
========
Here is a way to use it::

    import plumbing
"""

b'This module needs Python 2.6 or later.'

# Special variables #
__version__ = '1.0.0'

# Built-in modules #
import sys

################################################################################
class program(object):
    """Lorem ipsum."""

    def __init__(self):
        sys.exit()
