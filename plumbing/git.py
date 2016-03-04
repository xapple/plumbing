# Built-in modules #
import os

# Internal modules #
from plumbing.autopaths import DirectoryPath

# Third party modules #
import sh

###############################################################################
class GitRepo(DirectoryPath):
    """A git repository with some convenience methods."""

    def __init__(self, path):
        # Super #
        DirectoryPath.__init__(self, path)
        # The git directory #
        self.git_dir = self.path + '.git'
        # Check exists #
        if not os.path.exists(self.git_dir):
            raise Exception("No git repository at '%s'" % (self.git_dir))
        # Default arguments #
        self.default = ["--git-dir=" + self.git_dir, "--work-tree=" + self.path]

    @property
    def tag(self):
        """For instance: u'1.0.3-69-gf0c796d-dirty'"""
        tag = sh.git(self.default + ["describe", "--tags", "--dirty", "--always"])
        return tag.strip('\n')

    @property
    def hash(self):
        """For instance: u'f0c796dae64a5a118d88e60523c011d535e8c476'"""
        sha1 = sh.git(self.default + ["rev-parse", "HEAD"])
        return sha1.strip('\n')

    @property
    def short_hash(self):
        """For instance: u'f0c796dae64a5a118d88e60523c011d535e8c476'"""
        sha1 = sh.git(self.default + ["rev-parse", "--short", "HEAD"])
        return sha1.strip('\n')

    @property
    def branch(self):
        """For instance: u'master'"""
        result = sh.git(self.default + ['symbolic-ref', '--short', 'HEAD'])
        return result.strip('\n')

    @property
    def remote_branch(self):
        """For instance: u'origin/master'"""
        result = sh.git(self.default + ['rev-parse', '--symbolic-full-name', '--abbrev-ref', '@{u}'])
        return result.strip('\n')
