# Built-in modules #
from datetime import datetime

# Internal modules #
from plumbing.color import Color

################################################################################
class Timer(object):
    """Useful for timing the different steps in a pipeline.

    Use it like this:

        timer = Timer()
        timer.print_start()
        timer.print_elapsed()
        timer.print_end()
        timer.print_total_elapsed()

    Or like this:

        with Timer():
            time.sleep(2)
    """

    def __init__(self):
        self.start_time = datetime.now()
        self.last_mark = datetime.now()

    def print_start(self):
        print self.prefix + "Start at: %s" % (self.start_time) + self.suffix

    def print_end(self):
        self.end_time = datetime.now()
        print self.prefix + "End at: %s" % (self.end_time) + self.suffix

    def print_elapsed(self, reset=True):
        print self.prefix + "Elapsed time: %s" % (datetime.now() - self.last_mark) + self.suffix
        if reset: self.last_mark = datetime.now()

    def print_total_elapsed(self, reset=True):
        print self.prefix + "Total elapsed time: %s" % (datetime.now() - self.start_time) + self.suffix
        if reset: self.last_mark = datetime.now()

    @property
    def color(self):
        """Should we use color or not ? If we are not in a shell like ipython then not."""
        import __main__ as main
        if not hasattr(main, '__file__'): return True
        return False

    @property
    def prefix(self): return "" if not self.color else Color.grn
    @property
    def suffix(self): return "" if not self.color else Color.end

    def __enter__(self):
        """Start the timer and print."""
        self.start_time = datetime.now()
        self.print_start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Stop the timer and print."""
        self.print_end()
        self.print_total_elapsed()