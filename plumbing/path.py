"""
=============================
Path and pipelines with files
=============================

The ``path`` module provides some convenience objects
for building pipelines with many files.
"""

# Modules #
import tempfile, os, re

################################################################################
class AutoPaths(object):
    """
    self.p.raw_sff         /raw/raw.sff
    self.p.sff             /raw/raw.sff
    self.p.raw_dir         /raw/
    self.p.manifest        /raw/manifest.txt
    self.p.blast_out       /blast/blast.out.xml
    """

    def __init__(self, base_dir, all_paths):
        # Attributes #
        self._base_dir = base_dir
        self._all_paths = all_paths
        self._tmp_dir = None
        # Parse input #
        self._paths = [Path(p.lstrip(' '),base_dir) for p in all_paths.split('\n')]

    def __getattr__(self, key):
        # Special cases #
        if key.startswith('_'): return self.__dict__[key]
        if key == 'tmp_dir': return self.__dict__['tmp_dir']
        if key == 'tmp': return self.__dict__['tmp']
        # Search #
        items = key.split('_')
        # Directory case #
        if items[-1] == 'dir': directory = items.pop(-1)
        else: directory = False
        # Search #
        matches = [set([p for p in self._paths if i in p]) for i in items]
        result = set.intersection(*matches)
        # No matches #
        if len(result) == 0:
            raise Exception("Could not find any path matching '%s'" % key)
        # Multiple matches #
        if len(result) > 1:
            best_score = max([p.score(items) for p in result])
            result = [p for p in result if p.score(items) >= best_score]
        # Still multiple matches #
        if len(result) > 1:
            shortest = min([len(p) for p in result])
            result = [p for p in result if len(p) <= shortest]
        # Maybe it's a directory #
        if len(result) > 1 and directory:
            if len(set([p.dir for p in result])) == 1: result = [result[0]]
        # Error #
        if len(result) > 1:
            raise Exception("Found several paths matching '%s'" % key)
        # Directory case #
        if directory: return result.pop().real_dir
        else: return result.pop().real_path

    @property
    def tmp_dir(self):
        if not self._tmp_dir: self._tmp_dir = tempfile.mkdtemp() + '/'
        return self._tmp_dir

    @property
    def tmp(self):
        return self.tmp_dir + 'autopath.tmp'

################################################################################
class Path(object):
    delimiters = '_', '.', '/'
    pattern = re.compile('|'.join(map(re.escape, delimiters)))

    def __init__(self, path, base_dir):
        self.path = path
        self.base_dir = base_dir
        self.dir, self.name = os.path.split(path)
        self.name_items = self.pattern.split(self.name)
        self.dir_items = self.pattern.split(self.dir)
        self.all_items = self.name_items + self.dir_items

    def __contains__(self, i):
        return i in self.all_items

    def __len__(self):
        return len(self.name_items)

    def score(self, items):
        return 1

    @property
    def real_path(self):
        return os.path.realpath(self.base_dir + self.path)

    @property
    def real_dir(self):
        return os.path.realpath(self.base_dir + self.dir) + '/'