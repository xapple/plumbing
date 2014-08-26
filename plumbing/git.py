# Built-in modules #
import os

# Third party modules #
import sh

###############################################################################
class GitRepo(object):
    """A git repository with some convenience methods"""

    def __init__(self, directory):
        if not directory.endswith('/'): directory += '/'
        self.directory = directory
        self.git_dir = directory + '.git'
        if not os.path.exists(self.git_dir):
            raise Exception("No git repository at '%s'" % (self.git_dir))

    @property
    def tag(self):
        tag = sh.git("--git-dir=" + self.git_dir, "describe", "--tags", "--dirty", "--always")
        return tag.strip('\n')

    @property
    def hash(self):
        sha1 = sh.git("--git-dir=" + self.git_dir, "rev-parse", "HEAD")
        return sha1.strip('\n')

    @property
    def branch(self):
        return sh.git("--git-dir=" + self.git_dir, 'symbolic-ref', '--short', 'HEAD').strip('\n')

    @property
    def remote_branch(self):
        return sh.git("--git-dir=" + self.git_dir, 'rev-parse', '--symbolic-full-name', '--abbrev-ref', '@{u}').strip('\n')
