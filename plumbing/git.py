# Built-in modules #
import os, sys

# Internal modules #
from autopaths.dir_path import DirectoryPath

# Third party modules #
if os.name == "posix": import sh
if os.name == "nt":    import pbs

###############################################################################
class GitRepo(DirectoryPath):
    """A git repository with some convenience methods.
    Requires at least git 2.7 (released January 5th, 2015)
    for all methods to work correctly."""

    def __bool__(self):
        return os.path.exists(self.git_dir)
    __nonzero__ = __bool__

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

    def git(self, *args, **kwargs):
        if os.name == "posix":
            return sh.git(*args, **kwargs)
        if os.name == "nt":
            return pbs.Command("git")(*args, **kwargs)

    #------------------------------- Properties ------------------------------#
    @property
    def tag(self):
        """For instance: u'1.0.3-69-gf0c796d-dirty'"""
        tag = self.git(self.default + ["describe", "--tags", "--dirty", "--always"])
        return tag.strip('\n')

    @property
    def hash(self):
        """For instance: u'f0c796dae64a5a118d88e60523c011d535e8c476'"""
        sha1 = self.git(self.default + ["rev-parse", "HEAD"])
        return sha1.strip('\n')

    @property
    def short_hash(self):
        """For instance: u'f0c796d'"""
        sha1 = self.git(self.default + ["rev-parse", "--short", "HEAD"])
        return sha1.strip('\n')

    @property
    def branch(self):
        """For instance: u'master'"""
        result = self.git(self.default + ['symbolic-ref', '--short', 'HEAD'])
        return result.strip('\n')

    @property
    def branches(self):
        """All branches in a list"""
        result = self.git(self.default + ['branch', '-a', '--no-color'])
        return [l.strip(' *\n') for l in result.split('\n') if l.strip(' *\n')]

    @property
    def remote_branch(self):
        """For instance: u'origin/master'"""
        result = self.git(self.default + ['rev-parse', '--symbolic-full-name', '--abbrev-ref', '@{u}'])
        return result.strip('\n')

    @property
    def remote_url(self):
        """For instance: u'origin/master'"""
        result = self.git(self.default + ['remote', 'get-url', 'origin'])
        return result.strip('\n')

    #--------------------------------- Methods -------------------------------#
    def clone_from(self, remote_url):
        """Clone it when it doesn't exist yet."""
        assert not self
        self.git('clone', remote_url, self.path)

    def re_clone(self, repo_dir):
        """Clone again, somewhere else"""
        self.git('clone', self.remote_url, repo_dir)
        return GitRepo(repo_dir)

    def add(self, what):
        return self.git(self.default + ['add', what])

    def commit(self, message):
        return self.git(self.default + ['commit', '-m', message])

    def push(self, source=None, destination=None, tags=False, shell=False):
        # Command #
        command = self.default + ['push']
        # Tags #
        if tags: command.append('--tags')
        # Source and dest #
        if source:                 command.append(source)
        if source and destination: command.append(destination)
        # Show on shell #
        if shell: return self.git(command, _out=sys.stdout, _err=sys.stderr)
        else:     return self.git(command)

    def tag_head(self, tag):
        return self.git(self.default + ['tag', tag, 'HEAD'])