#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licensed.
Contact at www.sinclair.bio
"""

# Built-in modules #
from datetime import datetime

# Internal modules #
from plumbing.cache import property_cached
from plumbing.color import Color

################################################################################
class Timer(object):
    """
    Useful for timing the different steps in a pipeline.

    Use it like this:

        from plumbing.timer import Timer
        timer = Timer()
        timer.print_start()
        timer.print_elapsed()
        timer.print_end()
        timer.print_total_elapsed()

    Or like this:

        with Timer():
            time.sleep(2)
    """

    def get_now(self):
        # What precision to use #
        if self.high_precision:
            return datetime.now()
        else:
            return datetime.now().replace(microsecond=0)

    def __init__(self, high_precision=False):
        self.high_precision = high_precision
        self.start_time = self.get_now()
        self.last_mark  = self.get_now()

    def print_start(self):
        # Parameters #
        time = self.start_time
        msg  = "Start at: %s" % time
        # Print #
        self.print(self.prefix + msg + self.suffix)

    def print_end(self):
        # Set #
        self.end_time = self.get_now()
        # Parameters #
        time = self.end_time
        msg  = "End at: %s" % time
        # Print #
        self.print(self.prefix + msg + self.suffix)

    def print_elapsed(self, reset=True):
        # Parameters #
        time = self.get_now() - self.last_mark
        msg  = "Elapsed time: %s" % time
        # Print #
        self.print(self.prefix + msg + self.suffix)
        # Set #
        if reset: self.last_mark = self.get_now()

    def print_total_elapsed(self, reset=True):
        # Parameters #
        time = self.get_now() - self.start_time
        msg = "Total elapsed time: %s"
        msg = msg % time
        # Print #
        self.print(self.prefix + msg + self.suffix)
        # Set #
        if reset: self.last_mark = self.get_now()

    @property_cached
    def color(self):
        """
        Should we use color or not ?
        If we are not in a shell like ipython then not.
        """
        import __main__ as main
        return not hasattr(main, '__file__')

    @property
    def prefix(self): return "" if not self.color else Color.grn

    @property
    def suffix(self): return "" if not self.color else Color.end

    def __enter__(self):
        """Start the timer and print."""
        self.start_time = self.get_now()
        self.print_start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Stop the timer and print."""
        self.print_end()
        self.print_total_elapsed()

    def print(self, *args, **kwargs):
        print(*args, **kwargs)

################################################################################
class LogTimer(Timer):
    """
    Same as a Timer, except the messages go to a logger object instead of
    being printed to the standard out.
    """

    def __init__(self, log, high_precision=False):
        super(LogTimer, self).__init__(high_precision)
        self.color = False
        self.log = log

    def print(self, msg):
        self.log.info(msg)