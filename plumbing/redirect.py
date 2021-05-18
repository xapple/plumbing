# Built-in modules #
import sys

################################################################################
class RedirectStdStreams(object):
    """
    See file `plumbing/test/redirect/test_redirect.py`
    """

    def __init__(self, stdout=None, stderr=None):
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr

    def __enter__(self):
        # Save old ones #
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        # Flush everything #
        self.old_stdout.flush()
        self.old_stderr.flush()
        # Redirect #
        sys.stdout = self._stdout
        sys.stderr = self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        # Flush #
        self._stdout.flush()
        self._stderr.flush()
        # Restore #
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

################################################################################
class SuppressAllOutput(object):
    """For those annoying modules that can't shut-up about warnings."""

    def __enter__(self):
        # Standard error #
        sys.stderr.flush()
        self.old_stderr = sys.stderr
        sys.stderr = open('/dev/null', 'a+', 0)
        # Standard out #
        sys.stdout.flush()
        self.old_stdout = sys.stdout
        sys.stdout = open('/dev/null', 'a+', 0)

    def __exit__(self, exc_type, exc_value, traceback):
        # Standard error #
        sys.stderr.flush()
        sys.stderr = self.old_stderr
        # Standard out #
        sys.stdout.flush()
        sys.stdout = self.old_stdout

    def example(self):
        print("printing to stdout before suppression", file=sys.stdout, flush=True)
        print("printing to stderr before suppression", file=sys.stderr, flush=True)
        with SuppressAllOutput():
            print("printing to stdout during suppression", file=sys.stdout, flush=True)
            print("printing to stderr during suppression", file=sys.stderr, flush=True)
        print("printing to stdout after suppression", file=sys.stdout, flush=True)
        print("printing to stderr after suppression", file=sys.stderr, flush=True)
