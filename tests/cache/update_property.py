# Built-in module #
import time

# Internal modules #
from plumbing.cache import property_cached
from plumbing.common import pretty_now

###############################################################################
class Employee(object):

    @property_cached
    def check_in_time(self):
        print("Evaluating...")
        return pretty_now()

###############################################################################
bob = Employee()
print(bob.check_in_time)

time.sleep(2)
print(bob.check_in_time)

bob.__dict__.get('__cache__').pop('check_in_time')
print(bob.check_in_time)