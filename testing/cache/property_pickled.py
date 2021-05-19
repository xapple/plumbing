#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to test the functionality of the property_pickled decorator.

Written by Lucas Sinclair. MIT Licensed.

Call it like this:

    $ ipython3 -i ~/repos/plumbing/test/cache/property_pickled.py
"""

# Internal modules #
from plumbing.cache import property_pickled

###############################################################################
class Square:
    def __init__(self, size):
        self.size = size

    @property_pickled
    def area(self):
        print("Evaluating...")
        return self.size * self.size

###############################################################################
shape = Square(5)
print(shape.area)