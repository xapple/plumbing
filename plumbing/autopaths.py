# Built-in modules #
import os, stat, tempfile, re, subprocess, shutil

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

    def __repr__(self): return '<%s object on "%s">' % (self.__class__.__name__, self._base_dir)

    def __init__(self, base_dir, all_paths):
        # Attributes #
        self._base_dir = base_dir
        self._all_paths = all_paths
        self._tmp_dir = tempfile.gettempdir() + '/'
        # Parse input #
        self._paths = [PathItems(p.lstrip(' '),base_dir) for p in all_paths.split('\n')]

    def __getattr__(self, key):
        # Let magic pass through #
        if key.startswith('__') and key.endswith('__'): return object.__getattr__(key)
        # Special cases #
        if key.startswith('_'): return self.__dict__[key]
        # Temporary items #
        if key == 'tmp_dir': return self.__dict__['_tmp_dir']
        if key == 'tmp': return self.__dict__['tmp']
        # Search #
        items = key.split('_')
        # Directory case #
        if items[-1] == 'dir':
            items.pop(-1)
            return self.search_for_dir(key, items)
        else:
            return self.search_for_file(key, items)

    def search_for_file(self, key, items):
        # Search #
        matches = [set([p for p in self._paths if i in p]) for i in items]
        result = set.intersection(*matches)
        # No matches #
        if len(result) == 0:
            raise Exception("Could not find any path matching '%s'" % key)
        # Multiple matches, advantage file name #
        if len(result) > 1:
            best_score = max([p.score_file(items) for p in result])
            result = [p for p in result if p.score_file(items) >= best_score]
        # Multiple matches, take the one with less parts #
        if len(result) > 1:
            shortest = min([len(p) for p in result])
            result = [p for p in result if len(p) <= shortest]
        # Multiple matches, error #
        if len(result) > 1:
            raise Exception("Found several paths matching '%s'" % key)
        # Make the directory #
        result = result.pop()
        try:
            if not os.path.exists(result.complete_dir): os.makedirs(result.complete_dir)
        except OSError:
            pass
        # End #
        return FilePath(result.complete_path)

    def search_for_dir(self, key, items):
        # Search #
        matches = [set([p for p in self._paths if i in p]) for i in items]
        result = set.intersection(*matches)
        # No matches #
        if len(result) == 0:
            raise Exception("Could not find any path matching '%s'" % key)
        # Multiple matches, advantage dir name #
        if len(result) > 1:
            best_score = max([p.score_dir(items) for p in result])
            result = [p for p in result if p.score_dir(items) >= best_score]
        # Multiple matches, take the one with less parts #
        if len(result) > 1:
            shortest = min([len(p) for p in result])
            result = [p for p in result if len(p) <= shortest]
        # Multiple matches, maybe they all are the same directory #
        if len(result) > 1:
            if len(set([p.dir for p in result])) == 1: result = [result[0]]
        # Multiple matches, error #
        if len(result) > 1:
            raise Exception("Found several paths matching '%s'" % key)
        # Make the directory #
        result = result.pop()
        try:
            if not os.path.exists(result.complete_dir): os.makedirs(result.complete_dir)
        except OSError:
            pass
        # End #
        return DirectoryPath(result.complete_dir)

    @property
    def tmp_dir(self):
        if not self._tmp_dir: self._tmp_dir = tempfile.mkdtemp() + '/'
        return self._tmp_dir

    @property
    def tmp(self):
        return self.tmp_dir + 'autopath.tmp'

################################################################################
class PathItems(object):
    delimiters = '_', '.', '/'
    pattern = re.compile('|'.join(map(re.escape, delimiters)))

    def __repr__(self): return '<%s object "%s">' % (self.__class__.__name__, self.path)

    def __init__(self, path, base_dir):
        self.path = path
        self.base_dir = base_dir
        self.dir, self.name = os.path.split(path)
        self.name_items = self.pattern.split(self.name) if self.name else []
        self.dir_items = self.pattern.split(self.dir) if self.dir else []
        self.all_items = self.name_items + self.dir_items

    def __contains__(self, i):
        return i in self.all_items

    def __len__(self):
        return len(self.all_items)

    def score_file(self, items):
        return sum([1.0 if i in self.name_items else 0.5 for i in items if i in self])

    def score_dir(self, items):
        return sum([1.0 if i in self.dir_items else 0.5 for i in items if i in self])

    @property
    def complete_path(self):
        return '/' + os.path.relpath(self.base_dir + self.path, '/')

    @property
    def complete_dir(self):
        return '/' + os.path.relpath(self.base_dir + self.dir, '/') + '/'

################################################################################
class DirectoryPath(str):

    def __repr__(self): return '<%s object "%s">' % (self.__class__.__name__, self.path)

    def __new__(cls, path, *args, **kwargs):
        if not path.endswith('/'): path += '/'
        return str.__new__(cls, path)

    def __init__(self, path):
        if not path.endswith('/'): path += '/'
        self.path = path

    def __add__(self, other):
        return self.path + other

    @property
    def name(self):
        """Just the directory name"""
        return os.path.basename(os.path.dirname(self.path))

    @property
    def prefix_path(self):
        """The full path without the extension"""
        return os.path.splitext(self.path)[0].rstrip('/')

    @property
    def directory(self):
        """The full path of directory containing this one"""
        return DirectoryPath(os.path.dirname(os.path.dirname(self.path)))

    @property
    def contents(self):
        """The files and directories as a list"""
        return os.listdir(self.path)

    @property
    def exists(self):
        """Does it exist in the file system"""
        return os.path.lexists(self.path)

    def remove(self):
        if not self.exists: return False
        shutil.rmtree(self.path, ignore_errors=True)
        return True

    def create(self):
        os.makedirs(self.path)

    def zip(self, keep_orig=False):
        """Make a zip archive of the directory"""
        shutil.make_archive(self.prefix_path , "zip", self.directory, self.name)
        if not keep_orig: self.remove()

################################################################################
class FilePath(str):

    def __repr__(self): return '<%s object "%s">' % (self.__class__.__name__, self.path)

    def __iter__(self): return open(self.path)

    def __new__(cls, path, *args, **kwargs):
        return str.__new__(cls, path)

    def __init__(self, path):
        self.path = path

    @property
    def exists(self):
        """Does it exist in the file system"""
        return os.path.lexists(self.path)

    @property
    def prefix_path(self):
        """The full path without the extension"""
        return str(os.path.splitext(self.path)[0])

    @property
    def prefix(self):
        """Just the filename without the extension"""
        return str(os.path.basename(self.prefix_path))

    @property
    def filename(self):
        """Just the filename with the extension"""
        return str(os.path.basename(self.path))

    @property
    def directory(self):
        return DirectoryPath(str(os.path.dirname(self.path) + '/'))

    @property
    def extension(self):
        """The extension with the leading period"""
        return os.path.splitext(self.path)[1]

    @property
    def count_bytes(self):
        """The number of bytes"""
        if not self.exists: return 0
        return os.path.getsize(self.path)

    @property
    def size(self):
        """Human readable size"""
        return Filesize(self.count_bytes)

    @property
    def contents(self):
        """The contents as a string"""
        return open(self.path).read()

    def remove(self):
        if not self.exists: return False
        os.remove(self.path)
        return True

    def create(self):
        with open(self.path, 'w'): pass

    def write(self, content):
        with open(self.path, 'w') as handle: handle.write(content)

    def writelines(self, content):
        with open(self.path, 'w') as handle: handle.writelines(content)

    def link_from(self, path, safe=False):
        # Standard #
        if not safe:
            self.remove()
            return os.symlink(path, self.path)
        # No errors #
        else:
            try: os.remove(self.path)
            except OSError: pass
            try: os.symlink(path, self.path)
            except OSError: pass

    def copy(self, path):
        shutil.copy2(self.path, path)

    def make_executable(self):
        return os.chmod(self.path, os.stat(self.path).st_mode | stat.S_IEXEC)

    def execute(self):
        return subprocess.call([self.path])

    def replace_extension(self, new_extension='txt'):
        """Return a new path with the extension swapped out"""
        return FilePath(os.path.splitext(self.path)[0] + '.' + new_extension)

    def new_name_insert(self, string):
        """Return a new name by appending a string before the extension"""
        return self.prefix_path + "." + string + self.extension

    def make_directory(self):
        """Create the directory the file is supposed to be in if it does not exist"""
        if not self.directory.exists: self.directory.create()

################################################################################
class Filesize(object):
    """
    Container for a size in bytes with a human readable representation
    Use it like this:

        >>> size = Filesize(123123123)
        >>> print size
        '117.4 MB'
    """

    chunk = 1000
    units = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
    precisions = [0, 0, 1, 2, 2, 2]

    def __init__(self, size):
        self.size = size

    def __int__(self):
        return self.size

    def __str__(self):
        if self.size == 0: return '0 bytes'
        from math import log
        unit = self.units[min(int(log(self.size, self.chunk)), len(self.units) - 1)]
        return self.format(unit)

    def format(self, unit):
        if unit not in self.units: raise Exception("Not a valid file size unit: %s" % unit)
        if self.size == 1 and unit == 'bytes': return '1 byte'
        exponent = self.units.index(unit)
        quotient = float(self.size) / self.chunk**exponent
        precision = self.precisions[exponent]
        format_string = '{:.%sf} {}' % (precision)
        return format_string.format(quotient, unit)
