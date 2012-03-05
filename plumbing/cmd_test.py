"""
Contains the unittests for plumbing
"""

# Built-in module #
import os

# Internal modules #
from plumbing import command

# Unittesting module #
try:
    import unittest2 as unittest
except ImportError:
    import unittest

# Nosetest flag #
__test__ = True

###################################################################################
@command
def touch(filename):
    return {"arguments": ["touch", filename],
            "return_value": filename}

###################################################################################
class Test(unittest.TestCase):
    def runTest(self):
        # Simple touch #
        name = "myfile"
        got = touch(name)
        self.assertEqual(got, name)
        self.assertTrue(os.path.exists(name))
        os.remove(name)
        # Parallel touch #
        name1 = "myfile1"
        name2 = "myfile2"
        future1 = touch.parallel(name1)
        future2 = touch.parallel(name2)
        got1 = future1.wait()
        got2 = future2.wait()
        self.assertEqual(got1, name1)
        self.assertEqual(got2, name2)
        self.assertTrue(os.path.exists(name1))
        self.assertTrue(os.path.exists(name2))
        os.remove(name1)
        os.remove(name2)
        # LSF touch #
        path = "/scratch/cluster/el/daily/%s/plumbing_test" % os.environ['USER']
        os.makedirs(path)
        future = touch.lsf(path)
        got = future.wait()
        self.assertEqual(got, path)
        self.assertTrue(os.path.exists(path))
        os.remove(path)

###################################################################################
if __name__ == '__main__':
    Test().runTest()
