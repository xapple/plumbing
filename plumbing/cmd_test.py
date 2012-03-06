"""
Contains the unittests for plumbing
"""

# Built-in module #
import os

# Internal modules #
from plumbing import command
from plumbing.common import check_executable

# Testing module #
from nose.plugins.skip import SkipTest

###################################################################################
@command
def touch(filename):
    return {"arguments": ["touch", filename],
            "return_value": filename}

###################################################################################
def test_simple_touch():
    name = "myfile"
    got = touch(name)
    assert got == name
    assert os.path.exists(name)
    os.remove(name)

def test_parallel_touch():
    name1 = "myfile1"
    name2 = "myfile2"
    future1 = touch.parallel(name1)
    future2 = touch.parallel(name2)
    got1 = future1.wait()
    got2 = future2.wait()
    assert got1 == name1
    assert got2 == name2
    assert os.path.exists(name1)
    assert os.path.exists(name2)
    os.remove(name1)
    os.remove(name2)

def test_lsf_touch():
    if not check_executable('bsub'): raise SkipTest
    path = "/scratch/cluster/daily/%s/plumbing_test" % os.environ['USER']
    directory = os.path.dirname(path)
    if not os.path.exists(directory): os.makedirs(directory)
    future = touch.lsf(path)
    got = future.wait()
    assert got == path
    assert os.path.exists(path)
    os.remove(path)
