# Built-in module #
import inspect, os

# Internal modules #
from plumbing.redirect import RedirectStdStreams

# Constants #
file_name = inspect.getframeinfo(inspect.currentframe()).filename
this_dir  = os.path.dirname(os.path.abspath(file_name)) + '/'

# Test #
print('I should be in the standard out')
with open(this_dir + 'test_redirect.log', 'w') as log_handle:
    with RedirectStdStreams(stdout=log_handle, stderr=log_handle):
        print("I should go to a file")
print("I should also be in the standard out")