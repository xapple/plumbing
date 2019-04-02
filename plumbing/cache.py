# Built-in modules #
import time, inspect
import pickle

# Internal modules #
from autopaths.file_path import FilePath

# Third party modules #
from decorator import decorator

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
    New implementation of the property cached decorator.

    It converts a method with a single self argument
    into a property cached on the instance.

    In other words, it's like @property but memoized.

        from plumbing.cache import cached_property
        class Square(object):
            def __init__(self, size):
                self.size = size

            @cached_property
            def area(self):
                print("Evaluating...")
                return self.size * self.size

        shape = Square(5)
        print(shape.size)
        print(shape.area)
        shape.area = 99
        print(shape.area)
        del shape.area
        print(shape.area)
    """

    def __init__(self, func):
        self.func    = func
        self.__doc__ = getattr(func, '__doc__')
        self.name    = self.func.__name__

    def __get__(self, instance, owner):
        # If called from a class #
        if instance is None: return self
        # Does a cache exist for this instance? #
        self.check_cache(instance)
        # Is the answer in the cache? #
        if self.name in instance.__cache__: return instance.__cache__[self.name]
        # If not we will compute it #
        if inspect.isgeneratorfunction(self.func): result = tuple(self.func(instance))
        else:                                      result = self.func(instance)
        instance.__cache__[self.name] = result
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

################################################################################
def property_pickled(f):
    """Same thing as above but the result will be stored on disk
    The path of the pickle file will be determined by looking for the
    `cache_dir` attribute of the instance containing the cached property.
    If no `cache_dir` attribute exists the `p` attribute will be accessed with
    the name of the property being cached."""
    # Called when you access the property #
    def retrieve_from_cache(self):
        # Is it in the cache ? #
        if '__cache__' not in self.__dict__: self.__cache__ = {}
        if f.__name__ in self.__cache__: return self.__cache__[f.__name__]
        # Where should we look in the file system ? #
        if 'cache_dir' in self.__dict__:
            path = FilePath(self.__dict__['cache_dir'] + f.func_name + '.pickle')
        else:
            path = getattr(self.p, f.func_name)
        # Is it on disk ? #
        if path.exists:
            with open(path) as handle: result = pickle.load(handle)
            self.__cache__[f.__name__] = result
            return result
        # Otherwise let's compute it #
        result = f(self)
        with open(path, 'w') as handle: pickle.dump(result, handle)
        self.__cache__[f.__name__] = result
        return result
    # Called when you set the property #
    def overwrite_cache(self, value):
        # Where should we look in the file system ? #
        if 'cache_dir' in self.__dict__:
            path = FilePath(self.__dict__['cache_dir'] + f.func_name + '.pickle')
        else:
            path = getattr(self.p, f.func_name)
        if value is None: path.remove()
        else: raise Exception("You can't set a pickled property, you can only delete it")
    # Return a wrapper #
    retrieve_from_cache.__doc__ = f.__doc__
    return property(retrieve_from_cache, overwrite_cache)

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
    """You can use this like this:
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