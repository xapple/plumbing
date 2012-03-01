"""
Contains the unittests for plumbing
"""

# Internal modules #
import plumbing

# Unittesting module #
try:
    import unittest2 as unittest
except ImportError:
    import unittest

# Nosetest flag #
__test__ = True

###################################################################################
class Test(unittest.TestCase):
    def runTest(self):
        self.assertEqual(1, 1)
