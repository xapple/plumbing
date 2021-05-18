#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licensed.
Contact at www.sinclair.bio
"""

# Built-in modules #
import os, time, inspect, tempfile, pickle, hashlib, base64

# Internal modules #
from autopaths import Path

################################################################################
def cached(f):
    """Decorator for functions evaluated only once."""
    def memoized(*args, **kwargs):
        if hasattr(memoized, '__cache__'):
            return memoized.__cache__
        result = f(*args, **kwargs)
        memoized.__cache__ = result
        return result
    return memoized

###############################################################################
class property_cached(object):
    """
    This decorator converts a method with a single self argument
    into a property cached on the instance.

    In other words, it's like `@property` but memoized.

        from plumbing.cache import property_cached

        class Square:
            def __init__(self, size):
                self.size = size

            @property_cached
            def area(self):
                print("Evaluating...")
                return self.size * self.size

        shape = Square(5)
        print(shape.size)
        print(shape.area)  # Area computed the first time
        shape.area = 99    # Now update an attribute
        print(shape.area)  # Same result returned, not recomputed
        del shape.area     # This will purge the cache
        print(shape.area)  # Updated result, it's computed again
    """

    def __init__(self, func):
        self.func    = func
        self.__doc__ = getattr(func, '__doc__')
        self.name    = self.func.__name__

    def __get__(self, instance, owner):
        """
        If you see the current source code in a seemingly unrelated part of
        an auto-generated documentation, it means the program making the
        documentation was unable to correctly traverse a decorated property.
        """
        # For debugging purposes #
        if False: print("-> property cached `%s`" % instance)
        # If called from a class #
        if instance is None: return self
        # Does a cache exist for this instance? #
        self.check_cache(instance)
        # Is the answer in the cache? #
        if self.name in instance.__cache__: return instance.__cache__[self.name]
        # If not we will compute it #
        if inspect.isgeneratorfunction(self.func): result = tuple(self.func(instance))
        else:                                      result = self.func(instance)
        # Let's store the answer for later #
        instance.__cache__[self.name] = result
        # Return #
        return result

    def __set__(self, instance, value):
        # Does a cache exist for this instance? #
        self.check_cache(instance)
        # Overwrite the value #
        instance.__cache__[self.name] = value

    def __delete__(self, instance):
        # Does a cache exist for this instance? #
        self.check_cache(instance)
        # Remove the key #
        instance.__cache__.pop(self.name, None)

    def check_cache(self, instance):
        if '__cache__' not in instance.__dict__: instance.__cache__ = {}

###############################################################################
class property_pickled(object):
    """
    Same thing as `property_cached` but the cache will be stored on disk
    with the `pickle` module. So you should check that the return value of the
    function you decorate can be pickled. Otherwise checkout the `dill` module.

    The path of the pickle file will be determined by looking for the
    `cache_dir` attribute of the instance containing the cached property
    and combining the function name with a '.pickle' at the end.

    If no `cache_dir` attribute exists it, a default location will be
    chosen (tmpdir). But this will have for effect that all instances of the
    class will have the same cached value (works well for singletons only).

    The location will default to the temporary directory plus a very short
    hash of the function's import path, so you could get something like this:

        /var/temporary/pickled_properties/EfEZTAubgXI
    """

    def __init__(self, func, at=None):
        # Record the function that we are decorating #
        self.func    = func
        # Set the documentation string of the underlying function here #
        self.__doc__ = getattr(func, '__doc__')
        # Get the plain name of the function #
        self.name    = self.func.__name__
        # Optionally specify the location at which we should pickle #
        self.at      = at

    def __get__(self, instance, owner):
        """
        If you see this docstring or code in a seemingly unrelated part of
        an auto-generated documentation, it means the program making the
        documentation was unable to correctly traverse a decorated property.
        """
        # If called from a class #
        if instance is None: return self
        # Does a cache exist for this instance? #
        self.check_cache(instance)
        # Is the answer in the cache? #
        if self.name in instance.__cache__: return instance.__cache__[self.name]
        # Where should we look in the file system ? #
        path = self.get_pickle_path(instance)
        # Is the answer already on the file system? #
        if path.exists:
            with open(path, 'rb') as handle: result = pickle.load(handle)
            instance.__cache__[self.name] = result
            return result
        # If not we will compute it #
        if inspect.isgeneratorfunction(self.func): result = tuple(self.func(instance))
        else:                                      result = self.func(instance)
        # Let's store the answer for later in the cache #
        instance.__cache__[self.name] = result
        # And also store it on the disk #
        with open(path, 'wb') as handle: pickle.dump(result, handle)
        # Return #
        return result

    def __set__(self, instance, value):
        # Does a cache exist for this instance? #
        self.check_cache(instance)
        # Overwrite the value in memory #
        instance.__cache__[self.name] = value
        # Where should we look in the file system ? #
        path = self.get_pickle_path(instance)
        # And also overwrite it on the disk #
        with open(path, 'wb') as handle: pickle.dump(value, handle)

    def __delete__(self, instance):
        # Does a cache exist for this instance? #
        self.check_cache(instance)
        # Remove the key #
        instance.__cache__.pop(self.name, None)
        # And remove the file on disk #
        path = self.get_pickle_path(instance)
        path.remove()

    def check_cache(self, instance):
        if '__cache__' not in instance.__dict__: instance.__cache__ = {}

    def get_pickle_path(self, instance):
        # First check if an `at` parameter was specified #
        if self.at is not None: path = Path(getattr(instance, self.at))
        # Secondly check if the instance has a cache_dir specified #
        elif 'cache_dir' in instance.__dict__:
            path = Path(instance.cache_dir + self.name + '.pickle')
        # Otherwise we go the default route (no instance passed) #
        else: path = Path(self.get_default_path())
        # Make the directory #
        path.make_directory()
        return path

    def get_default_path(self):
        # Get the temporary directory (platform dependant) #
        path = tempfile.gettempdir() + '/pickled_properties/'
        # Create that directory if it doesn't exist #
        os.makedirs(path, exist_ok=True)
        # Find the function's import path in the package namespace #
        func_loc = self.func.__module__ + '.' + self.name
        # Make a short safe name from the import path #
        short_name = hashlib.md5(func_loc.encode()).digest()[:8]
        short_name = base64.urlsafe_b64encode(short_name).decode()
        short_name = short_name.replace('=','')
        # Return #
        return path + short_name

################################################################################
def property_pickled_at(at):
    """
    Same thing as above, but you can specify the name of another property as
    a string, that will be called on the instance once to determine the
    path at which to write and load the pickle file from. This property should
    hence return the same path for every equivalent instance.
    """
    def wrapper(function): return property_pickled(function, at=at)
    return wrapper

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
    from decorator import decorator
    return decorator(memoize_with_expiry)

###############################################################################
class LazyString(object):
    """A string-like object that will only compute its value once, when accessed."""

    def __str__(self): return self.value

    def __init__(self, function):
        self._value = None
        self.function = function

    @property
    def value(self):
        if self._value is None: self._value = self.function()
        return self._value

###############################################################################
class LazyDict(object):
    """A dictionary-like object that will only compute its value once, when accessed."""

    def __getitem__(self, item): return self.value[item]

    def __init__(self, function):
        self._value = None
        self.function = function

    @property
    def value(self):
        if self._value is None: self._value = self.function()
        return self._value

###############################################################################
class LazyList(object):
    """A list-like object that will only compute its value once, when accessed."""

    def __iter__(self): return iter(self.value)
    def __len__(self):  return len(self.value)

    def __init__(self, function):
        self._value = None
        self.function = function

    @property
    def value(self):
        if self._value is None: self._value = self.function()
        return self._value

###############################################################################
class class_property(property):
    """
    You can use this like this:

        class Foo(object):
            @class_property
            @classmethod
            @cached
            def bar(cls):
                return 1+1
    """

    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

###############################################################################
class invalidate_cache(object):
    """
    Adds a hook to allow for another property setter to
    invalidated a part of the cache.

        class Square(object):
            def __init__(self, size):
                self._size = size

            @property
            def size(self):
                return self._size

            @cached_property
            def area(self):
                print("Evaluating...")
                return self.size * self.size

            @size.setter
            @invalidate_cache("area")
            def size(self, size):
                self._size = size

    shape = Square(5)
    print(shape.size)
    print(shape.area)
    shape.size = 6
    print(shape.area)
    """

    def __init__(self, func):
        self.func    = func
        self.__doc__ = getattr(func, '__doc__')