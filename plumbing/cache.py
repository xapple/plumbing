# Built-in modules #
import time, pickle, inspect

# Internal modules #

# Third party modules #
from decorator import decorator

################################################################################
def property_cached(f):
    """Decorator for properties evaluated only once.
    It can be used to created a cached property like this:

        class Employee(object):
            @property_cached
            def salary(self):
                return time.time()
        bob = Employee()
        print bob.salary
    """
    def add_to_cache(self):
        if inspect.isgeneratorfunction(f): result = tuple(f(self))
        else: result = f(self)
        self.__cache__[f.__name__] = result
    def retrieve_from_cache(self):
        if '__cache__' not in self.__dict__: self.__cache__ = {}
        if f.__name__ not in self.__cache__: add_to_cache(self)
        return self.__cache__[f.__name__]
    retrieve_from_cache.__doc__ = f.__doc__
    return property(retrieve_from_cache)

################################################################################
def expiry_every(seconds=0):
    def memoize_with_expiry(func, *args, **kwargs):
        # Get the cache #
        if not hasattr(func, '__cache__'): func.__cache__ = [(0,0)]
        cache = func.__cache__
        # Check the cache #
        if cache:
            result, timestamp = cache[0]
            age = time.time() - timestamp
            if age < seconds: return result
        # Update the cache #
        result = func(*args, **kwargs)
        cache[0] = (result, time.time())
        # Return #
        return result
    return decorator(memoize_with_expiry)

################################################################################
def pickled_property(f):
    def get_method(self):
        # Is it on disk #
        path = getattr(self.p, f.func_name)
        if path.exists:
            with open(path) as handle: result = pickle.load(handle)
            f.__cache__ = result
            return result
        # Let's compute it #
        result = f(self)
        with open(path, 'w') as handle: pickle.dump(result, handle)
        return result
    # Return a wrapper #
    get_method.__doc__ = f.__doc__
    return property(get_method)