# Built-in modules #
import os, sys

# Internal modules #
from plumbing.autopaths import DirectoryPath

# Third party modules #
import sh

###############################################################################
class GitRepo(DirectoryPath):
    """A git repository with some convenience methods.
    Requires at least git 2.7 (release January 5th, 2015)."""

    def __nonzero__(self):
        return os.path.exists(self.git_dir)

    def __init__(self, path, empty=False):
        # Super #
        DirectoryPath.__init__(self, path)
        # The git directory #
        self.git_dir = self.path + '.git'
        # Check exists #
        if not empty and not self:
            raise Exception("No git repository at '%s'" % (self.git_dir))
        # Default arguments #
        self.default = ["--git-dir=" + self.git_dir, "--work-tree=" + self.path]

    #------------------------------- Properties ------------------------------#
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
        """For instance: u'f0c796d'"""
        sha1 = sh.git(self.default + ["rev-parse", "--short", "HEAD"])
        return sha1.strip('\n')

    @property
    def branch(self):
        """For instance: u'master'"""
        result = sh.git(self.default + ['symbolic-ref', '--short', 'HEAD'])
        return result.strip('\n')

    @property
    def branches(self):
        """All branches in a list"""
        result = sh.git(self.default + ['branch', '-a', '--no-color'])
        return [l.strip(' *\n') for l in result.split('\n') if l.strip(' *\n')]

    @property
    def remote_branch(self):
        """For instance: u'origin/master'"""
        result = sh.git(self.default + ['rev-parse', '--symbolic-full-name', '--abbrev-ref', '@{u}'])
        return result.strip('\n')

    @property
    def remote_url(self):
        """For instance: u'origin/master'"""
        result = sh.git(self.default + ['remote', 'get-url', 'origin'])
        return result.strip('\n')

    #--------------------------------- Methods -------------------------------#
    def re_clone(self, repo_dir):
        """Clone again, somewhere else"""
        sh.git('clone', self.remote_url, repo_dir)
        return GitRepo(repo_dir)

    def add(self, what):
        return sh.git(self.default + ['add', what])

    def commit(self, message):
        return sh.git(self.default + ['commit', '-m', '"' + message + '"'])

    def push(self, source=None, destination=None, tags=False, shell=False):
        # Command #
        command = self.default + ['push']
        # Tags #
        if tags: command.append('--tags')
        # Source and dest #
        if source:                 command.append(source)
        if source and destination: command.append(destination)
        # Show on shell #
        if shell: return sh.git(command, _out=sys.stdout, _err=sys.stderr)
        else:     return sh.git(command)

    def tag_head(self, tag):
        return sh.git(self.default + ['tag', tag, 'HEAD'])