# Built-in modules #
import os, stat, tempfile, re, subprocess, shutil, codecs, gzip
import glob, warnings

# Internal modules #
from plumbing.common import append_to_file, prepend_to_file
from plumbing.common import md5sum, natural_sort, unzip

# Third party modules #
import sh

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
        # Don't nest DirectoryPaths or the like #
        if hasattr(base_dir, 'path'): base_dir = base_dir.path
        # Attributes #
        self._base_dir  = base_dir
        self._all_paths = all_paths
        self._tmp_dir   = tempfile.gettempdir() + '/'
        # Parse input #
        self._paths = [PathItems(p.lstrip(' '), base_dir) for p in all_paths.split('\n')]

    def __call__(self, key):    return self.__getattr__(key)
    def __getitem__(self, key): return self.__getattr__(key)

    def __getattr__(self, key):
        # Let built-ins pass through to object #
        if key.startswith('__') and key.endswith('__'): return object.__getattr__(key)
        # Special cases that should do to the actual dictionary #
        if key.startswith('_'): return self.__dict__[key]
        # Temporary items #
        if key == 'tmp_dir': return self.__dict__['_tmp_dir']
        if key == 'tmp': return self.__dict__['tmp']
        # Search #
        items = key.split('_')
        # Is it a directory ? #
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
        directory = DirectoryPath(result.complete_dir)
        if not directory.exists: directory.create(safe=True)
        # Return #
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
        directory = DirectoryPath(result.complete_dir)
        if not directory.exists: directory.create(safe=True)
        # Return #
        return directory

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

    @classmethod
    def clean_path(cls, path):
        """Given a path, return a cleaned up version for initialization."""
        # Conserve 'None' object style #
        if path is None: return None
        # Don't nest DirectoryPaths or the like #
        if hasattr(path, 'path'): path = path.path
        # Expand the tilda #
        if "~" in path: path = os.path.expanduser(path)
        # Our standard is to end with a slash for directories #
        if not path.endswith('/'): path += '/'
        # Return the result #
        return path

    def __new__(cls, path, *args, **kwargs):
        """A DirectoryPath is in fact a string"""
        return str.__new__(cls, cls.clean_path(path))

    def __init__(self, path):
        self.path = self.clean_path(path)

    def __add__(self, other):
        return self.path + other

    @property
    def p(self):
        if not hasattr(self, 'all_paths'):
            raise Exception("You need to define 'all_paths' to use this function")
        return AutoPaths(self.path, self.all_paths)

    @property
    def name(self):
        """Just the directory name"""
        return os.path.basename(os.path.dirname(self.path))

    @property
    def prefix_path(self):
        """The full path without the extension"""
        return os.path.splitext(self.path)[0].rstrip('/')

    @property
    def absolute_path(self):
        """The absolute path starting with a `/`"""
        return os.path.abspath(self.path) + '/'

    @property
    def directory(self):
        """The full path of the directory containing this one."""
        return DirectoryPath(os.path.dirname(os.path.dirname(self.path)))

    #-------------------------- Recursive contents ---------------------------#
    @property
    def contents(self):
        """The files and directories in this directory, recursively."""
        for root, dirs, files in os.walk(self.path, topdown=False):
            for d in dirs:  yield DirectoryPath(os.path.join(root, d))
            for f in files: yield FilePath(os.path.join(root, f))

    @property
    def files(self):
        """The files in this directory, recursively."""
        for root, dirs, files in os.walk(self.path, topdown=False):
            for f in files: yield FilePath(os.path.join(root, f))

    @property
    def directories(self):
        """The directories in this directory, recursively."""
        for root, dirs, files in os.walk(self.path, topdown=False):
            for d in dirs: yield DirectoryPath(os.path.join(root, d))

    #----------------------------- Flat contents -----------------------------#
    @property
    def flat_contents(self):
        """The files and directories in this directory non-recursively."""
        for root, dirs, files in os.walk(self.path):
            for d in dirs:  yield DirectoryPath(os.path.join(root, d))
            for f in files: yield FilePath(os.path.join(root, f))
            break

    @property
    def flat_files(self):
        """The files in this directory non-recursively, and sorted.
        #TODO: check for permission denied in directory."""
        result = []
        for root, dirs, files in os.walk(self.path):
            result = [FilePath(os.path.join(root, f)) for f in files]
            break
        result.sort(key=lambda x: natural_sort(x.path))
        return result

    @property
    def flat_directories(self):
        """The directories in this directory non-recursively, and sorted."""
        result = []
        for root, dirs, files in os.walk(self.path):
            result = [DirectoryPath(os.path.join(root, d)) for d in dirs]
            break
        result.sort(key=lambda x: natural_sort(x.path))
        return result

    #-------------------------------- Other ----------------------------------#
    @property
    def is_symlink(self):
        """Is this directory a symbolic link to an other directory?"""
        return os.path.islink(self.path.rstrip('/'))

    @property
    def exists(self):
        """Does it exist in the file system?"""
        return os.path.lexists(self.path) # Include broken symlinks

    @property
    def empty(self):
        """Does the directory contain no files?"""
        return len(list(self.flat_contents)) == 0

    @property
    def permissions(self):
        """Convenience object for dealing with permissions."""
        return FilePermissions(self.path)

    @property
    def mod_time(self):
        """The modification time"""
        return os.stat(self.path).st_mtime

    def remove(self):
        if not self.exists: return False
        if self.is_symlink: return self.remove_when_symlink()
        shutil.rmtree(self.path, ignore_errors=True)
        return True

    def remove_when_symlink(self):
        if not self.exists: return False
        os.remove(self.path.rstrip('/'))
        return True

    def create(self, safe=False, inherit=True):
        # Create it #
        if not safe:
            os.makedirs(self.path)
            if inherit: os.chmod(self.path, self.directory.permissions.number)
        if safe:
            try:
                os.makedirs(self.path)
                if inherit: os.chmod(self.path, self.directory.permissions.number)
            except OSError: pass

    def create_if_not_exists(self):
        if not self.exists: self.create()

    def zip(self, keep_orig=False):
        """Make a zip archive of the directory"""
        shutil.make_archive(self.prefix_path , "zip", self.directory, self.name)
        if not keep_orig: self.remove()

    def link_from(self, where, safe=False):
        """Make a link here pointing to another directory somewhere else.
        The destination is hence self.path and the source is *where*"""
        if not safe:
            self.remove()
            return os.symlink(where, self.path.rstrip('/'))
        if safe:
            try: self.remove()
            except OSError: pass
            try: os.symlink(where, self.path.rstrip('/'))
            except OSError: warnings.warn("Symlink of %s to %s did not work" % (where, self))

    def copy(self, path):
        assert not os.path.exists(path)
        shutil.copytree(self.path, path)

    def glob(self, pattern):
        """Perform a glob search in this directory."""
        files = glob.glob(self.path + pattern)
        return map(FilePath, files)

    def find(self, pattern):
        """Find a file in this directory."""
        f = glob.glob(self.path + pattern)[0]
        return FilePath(f)

################################################################################
class FilePath(str):
    """I can never remember all those darn `os.path` commands, so I made a class
    that wraps them with an easier and more pythonic syntax.

        path = FilePath('/home/root/text.txt')
        print path.extension
        print path.directory
        print path.filename

    You can find lots of the common things you would need to do with file paths.
    Such as: path.make_executable() etc etc."""

    def __repr__(self):    return '<%s object "%s">' % (self.__class__.__name__, self.path)
    def __nonzero__(self): return self.path != None and self.count_bytes != 0
    def __list__(self):    return self.count
    def __iter__(self):
        with open(self.path, 'r') as handle:
            for line in handle: yield line
    def __len__(self):
        if self.path is None: return 0
        return self.count

    def __new__(cls, path, *args, **kwargs):
        """A FilePath is in fact a string"""
        return str.__new__(cls, cls.clean_path(path))

    def __init__(self, path):
        self.path = self.clean_path(path)

    def __sub__(self, directory):
        """Subtract a directory from the current path to get the relative path
        of the current file from that directory."""
        return os.path.relpath(self.path, directory)

    @classmethod
    def clean_path(cls, path):
        """Given a path, return a cleaned up version for initialization"""
        # Conserve None object style #
        if path is None: return None
        # Don't nest FilePaths or the like #
        if hasattr(path, 'path'): path = path.path
        # Expand tilda #
        if "~" in path: path = os.path.expanduser(path)
        # Expand star #
        if "*" in path:
            matches = glob.glob(path)
            if len(matches) < 1: raise Exception("Found exactly no files matching '%s'" % path)
            if len(matches) > 1: raise Exception("Found several files matching '%s'" % path)
            path = matches[0]
        # Return the result #
        return path

    @property
    def first(self):
        """Just the first line"""
        with open(self.path, 'r') as handle:
            for line in handle: return line

    @property
    def exists(self):
        """Does it exist in the file system"""
        return os.path.lexists(self.path) # Returns True even for broken symbolic links

    @property
    def prefix_path(self):
        """The full path without the (last) extension and trailing period"""
        return str(os.path.splitext(self.path)[0])

    @property
    def prefix(self):
        """Just the filename without the (last) extension and trailing period"""
        return str(os.path.basename(self.prefix_path))

    @property
    def short_prefix(self):
        """Just the filename without any extension or periods"""
        return self.filename.split('.')[0]

    @property
    def filename(self):
        """Just the filename with the extension"""
        return str(os.path.basename(self.path))

    @property
    def directory(self):
        """The directory containing this file"""
        # The built-in function #
        directory = os.path.dirname(self.path)
        # Maybe we need to go the absolute path way #
        if not directory: directory = os.path.dirname(self.absolute_path)
        # Return #
        return DirectoryPath(directory + '/')

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
    def count(self):
        """We are going to default to the number of lines"""
        return int(sh.wc('-l', self.path).split()[0])

    @property
    def size(self):
        """Human readable file size"""
        return Filesize(self.count_bytes)

    @property
    def permissions(self):
        """Convenience object for dealing with permissions"""
        return FilePermissions(self.path)

    @property
    def contents(self):
        """The contents as a string"""
        with open(self.path, 'r') as handle: return handle.read()

    @property
    def absolute_path(self):
        """The absolute path starting with a `/`"""
        return FilePath(os.path.abspath(self.path))

    @property
    def physical_path(self):
        """The physical path like in `pwd -P`"""
        return FilePath(os.path.realpath(self.path))

    @property
    def relative_path(self):
        """The relative path when compared with current directory"""
        return FilePath(os.path.relpath(self.physical_path))

    @property
    def md5(self):
        """Return the md5 checksum."""
        return md5sum(self.path)

    @property
    def might_be_binary(self):
        """Try to quickly guess if the file is binary."""
        from binaryornot.check import is_binary
        return is_binary(self.path)

    @property
    def contains_binary(self):
        """Return True if the file contains binary characters."""
        from binaryornot.helpers import is_binary_string
        return is_binary_string(self.contents)

    def read(self, encoding=None):
        with codecs.open(self.path, 'r', encoding) as handle: content = handle.read()
        return content

    def create(self):
        with open(self.path, 'w'): pass

    def write(self, content, encoding=None):
        if encoding is None:
            with open(self.path, 'w') as handle: handle.write(content)
        else:
            with codecs.open(self.path, 'w', encoding) as handle: handle.write(content)

    def writelines(self, content, encoding=None):
        if encoding is None:
            with open(self.path, 'w') as handle: handle.writelines(content)
        else:
            with codecs.open(self.path, 'w', encoding) as handle: handle.writelines(content)

    def remove(self):
        if not self.exists: return False
        os.remove(self.path)
        return True

    def copy(self, path):
        shutil.copy2(self.path, path)

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

    def must_exist(self):
        """Raise an exception if the path doesn't exist."""
        if not self.exists: raise Exception("The file path '%s' does not exist." % self.path)

    def head(self, lines=10):
        """Return the first few lines."""
        content = iter(self)
        for x in xrange(lines):
            yield content.next()

    def move_to(self, path):
        """Move the file."""
        assert not os.path.exists(path)
        shutil.move(self.path, path)

    def link_from(self, path, safe=False):
        """Make a link here pointing to another file somewhere else.
        The destination is hence self.path and the source is *path*."""
        # Get source and destination #
        source      = path
        destination = self.path
        # Do it #
        if not safe:
            if os.path.exists(destination): os.remove(destination)
            os.symlink(source, destination)
        # Do it safely #
        if safe:
            try: os.remove(destination)
            except OSError: pass
            try: os.symlink(source, destination)
            except OSError: pass

    def link_to(self, path, safe=False, absolute=True):
        """Create a link somewhere else pointing to this file.
        The destination is hence *path* and the source is self.path."""
        # Get source and destination #
        if absolute: source = self.absolute_path
        else:        source = self.path
        destination = path
        # Do it #
        if not safe:
            if os.path.exists(destination): os.remove(destination)
            os.symlink(source, destination)
        # Do it safely #
        if safe:
            try: os.remove(destination)
            except OSError: pass
            try: os.symlink(source, destination)
            except OSError: pass

    def gzip_to(self, path=None):
        """Make a gzipped version of the file at a given path"""
        if path is None: path = self.path + ".gz"
        with open(self.path, 'rb') as orig_file:
            with gzip.open(path, 'wb') as new_file:
                new_file.writelines(orig_file)
        return FilePath(path)

    def ungzip_to(self, path=None):
        """Make an unzipped version of the file at a given path"""
        if path is None: path = self.path[:3]
        with gzip.open(self, 'rb') as orig_file:
            with open(path, 'wb') as new_file:
                new_file.writelines(orig_file)
        return FilePath(path)

    def zip_to(self, path=None):
        """Make a zipped version of the file at a given path."""
        pass

    def unzip_to(self, destination=None, inplace=False):
        """Make an unzipped version of the file at a given path"""
        return unzip(self.path, destination=destination, inplace=inplace)

    def append(self, what):
        """Append some text or an other file to the current file"""
        if isinstance(what, FilePath): what = what.contents
        append_to_file(self.path, what)

    def prepend(self, what):
        """Append some text or an other file to the current file"""
        if isinstance(what, FilePath): what = what.contents
        prepend_to_file(self.path, what)

################################################################################
class Filesize(object):
    """
    Container for a size in bytes with a human readable representation
    Use it like this:

        >>> size = Filesize(123123123)
        >>> print size
        '117.4 MiB'
    """

    chunk      = 1000 # Could be 1024 if you like old-style sizes
    units      = ['bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']
    precisions = [0, 0, 1, 2, 2, 2]

    def __init__(self, size):
        self.size = size

    def __int__(self):
        return self.size

    def __eq__(self, other):
        return self.size == other

    def __str__(self):
        if self.size == 0: return '0 bytes'
        from math import log
        unit = self.units[min(int(log(self.size, self.chunk)), len(self.units) - 1)]
        return self.format(unit)

    def format(self, unit):
        # Input checking #
        if unit not in self.units: raise Exception("Not a valid file size unit: %s" % unit)
        # Special no plural case #
        if self.size == 1 and unit == 'bytes': return '1 byte'
        # Compute #
        exponent      = self.units.index(unit)
        quotient      = float(self.size) / self.chunk**exponent
        precision     = self.precisions[exponent]
        format_string = '{:.%sf} {}' % (precision)
        # Return a string #
        return format_string.format(quotient, unit)

################################################################################
class FilePermissions(object):
    """Container for reading and setting a files permissions"""

    def __init__(self, path):
        self.path = path

    @property
    def number(self):
        """The permission bits as an octal integer"""
        return os.stat(self.path).st_mode & 0777

    def make_executable(self):
        return os.chmod(self.path, os.stat(self.path).st_mode | stat.S_IEXEC)

    def only_readable(self):
        """Remove all writing privileges"""
        return os.chmod(self.path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
