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
    You can use this class like this when making pipelines:

        class Sample(object):
            all_paths = '''
                /raw/raw.sff
                /raw/raw.fastq
                /clean/trim.fastq
                /clean/clean.fastq'''

            def __init__(self, base_dir):
                self.p = AutoPaths(base_dir, self.all_paths)

            def clean(self):
                shutil.move(self.p.raw_sff, self.p.clean_fastq)
    """

    def __init__(self, base_dir, all_paths):
        # Attributes #
        self._base_dir = base_dir
        self._all_paths = all_paths
        self._tmp_dir = None
        # Parse input #
        self._paths = [Path(p.lstrip(' '),base_dir) for p in all_paths.split('\n')]

    def __getattr__(self, key):
        # Let magic pass through #
        if key.startswith('__') and key.endswith('__'): return object.__getattr__(key)
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
        # Multiple matches, advantage file name #
        if len(result) > 1:
            best_score = max([p.score(items) for p in result])
            result = [p for p in result if p.score(items) >= best_score]
        # Multiple matches, take the one with less parts #
        if len(result) > 1:
            shortest = min([len(p) for p in result])
            result = [p for p in result if len(p) <= shortest]
        # Multiple matches, maybe it's a directory #
        if len(result) > 1 and directory:
            if len(set([p.dir for p in result])) == 1: result = [result[0]]
        # Multiple matches, error #
        if len(result) > 1:
            raise Exception("Found several paths matching '%s'" % key)
        # Make the directory #
        result = result.pop()
        if not os.path.exists(result.complete_dir): os.makedirs(result.complete_dir)
        # Directory case #
        return result.complete_dir if directory else result.complete_path

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
        return sum([1.0 if i in self.name_items else 0.5 for i in items if i in self])

    @property
    def complete_path(self):
        return '/' + os.path.relpath(self.base_dir + self.path, '/')

    @property
    def complete_dir(self):
        return '/' + os.path.relpath(self.base_dir + self.dir, '/') + '/'