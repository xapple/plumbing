# Built-in modules #
import os, sys

################################################################################
class RedirectStdStreams(object):
    """
    See file plumbing/test/redirect/test_redirect.py
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