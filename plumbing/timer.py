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

    def get_now(self):
        return datetime.now().replace(microsecond=0)

    def __init__(self):
        self.start_time = self.get_now()
        self.last_mark  = self.get_now()

    def print_start(self):
        # Parameters #
        time = self.start_time
        msg  = "Start at: %s" % time
        # Print #
        print(self.prefix + msg + self.suffix)

    def print_end(self):
        # Set #
        self.end_time = self.get_now()
        # Parameters #
        time = self.end_time
        msg  = "End at: %s" % time
        # Print #
        print(self.prefix + msg + self.suffix)

    def print_elapsed(self, reset=True):
        # Parameters #
        time = self.get_now() - self.last_mark
        msg  = "Elapsed time: %s" % time
        # Print #
        print(self.prefix + msg + self.suffix)
        # Set #
        if reset: self.last_mark = self.get_now()

    def print_total_elapsed(self, reset=True):
        # Parameters #
        time = self.get_now() - self.start_time
        msg  = "Total elapsed time: %s" % time
        # Print #
        print(self.prefix + msg + self.suffix)
        # Set #
        if reset: self.last_mark = self.get_now()

    @property
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