"""
=======================
Threads and parallelism
=======================

The ``thread`` module provides some convenience functions
for using threads in python.
"""

# Modules #
import threading

################################################################################
class ReturnThread(threading.Thread):
    """Like a normal thread, but the target function's return value is captured."""
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, verbose=None):
        threading.Thread.__init__(self, group, target, name, args, kwargs, verbose)
        self._return = None

    def run(self):
        try:
            if self._Thread__target:
                self._return = self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
        finally:
            del self._Thread__target, self._Thread__args, self._Thread__kwargs

    def join(self, timeout=None):
        threading.Thread.join(self, timeout)
        return self._return

################################################################################
def non_blocking(func):
    """Decorator to run a function in a different thread.
    It can be used to execute a command in a non-blocking way
    like this::

        @non_blocking
        def add_one(n):
            print 'starting'
            import time
            time.sleep(2)
            print 'ending'
            return n+1

        thread = add_one(5) # Starts the function
        result = thread.join() # Waits for it to complete
        print result
    """
    from functools import wraps
    @wraps(func)
    def non_blocking_version(*args, **kwargs):
        t = ReturnThread(target=func, args=args, kwargs=kwargs)
        t.start()
        return t
    return non_blocking_version
