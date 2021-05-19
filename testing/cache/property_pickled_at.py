#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to test the functionality of the property_pickled decorator.

Written by Lucas Sinclair. MIT Licensed.

Call it like this:

    $ ipython3 -i ~/repos/plumbing/test/cache/property_pickled_at.py
"""

# Built-in modules #
import os

# Internal modules #
from plumbing.cache import property_pickled_at

###############################################################################
class Square:
    def __init__(self, size):
        self.size = size

    @property_pickled_at("area_cache_path")
    def area(self):
        print("Evaluating...")
        return self.size * self.size

    @property
    def area_cache_path(self):
        path = "~/repos/plumbing/tests/cache/area_cache.pickle"
        return os.path.expanduser(path)

###############################################################################
shape = Square(5)
print(shape.area)