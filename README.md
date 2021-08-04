[![PyPI version](https://badge.fury.io/py/plumbing.svg)](https://badge.fury.io/py/plumbing)

# `plumbing` version 2.10.7

This project contains functions and classes that help with plumbing-type programing and pipeline building.

It contains many classes and functions which have not yet all been documented.

## Prerequisites

Since `plumbing` is written in python, it is compatible with all operating systems: Linux, macOS and Windows. The only prerequisite is `python3` (which is often installed by default) along with the `pip3` package manager.

To check if you have `python3` installed, type the following on your terminal:

    $ python3 -V

If you do not have `python3` installed, please refer to the section [obtaining python3](docs/installing_tips.md#obtaining-python3).

To check you have `pip3` installed, type the following on your terminal:

    $ pip3 -V

If you do not have `pip3` installed, please refer to the section [obtaining pip3](docs/installing_tips.md#obtaining-pip3).

## Installing

To install the `plumbing` package, simply type the following commands on your terminal:

    $ pip3 install --user plumbing

Alternatively, if you want to install it for all users of the system:

    $ sudo pip3 install plumbing

## Extra documentation

More documentation is available at:

<http://xapple.github.io/plumbing/plumbing>

This documentation is simply generated with:

    $ pdoc --html --output-dir docs --force plumbing