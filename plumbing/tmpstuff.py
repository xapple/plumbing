# Built-in modules #
import tempfile

# Internal modules #
from autopaths.file_path import FilePath
from autopaths.dir_path  import DirectoryPath

################################################################################
def new_temp_path(**kwargs):
    """A new temporary path"""
    handle = tempfile.NamedTemporaryFile(**kwargs)
    path = handle.name
    handle.close()
    return path

################################################################################
def new_temp_file(**kwargs):
    """A new temporary file"""
    return TmpFile.empty(**kwargs)

################################################################################
def new_temp_dir(**kwargs):
    return DirectoryPath(tempfile.mkdtemp() + '/')

################################################################################
class TmpFile(FilePath):
    def __repr__(self): return self.path

    @classmethod
    def empty(cls, **kwargs): return cls(**kwargs)

    @classmethod
    def from_string(cls, string, **kwargs): return cls(content=string, **kwargs)

    def __enter__(self):
        self.handle = open(self.path, 'w')
        return self

    def __exit__(self, *exc_info):
        self.handle.close()

    def __new__(cls, path=None, content=None, **kwargs):
        handle = open(path, 'w') if path else tempfile.NamedTemporaryFile(delete=False, **kwargs)
        if content: handle.write(content)
        handle.close()
        return FilePath.__new__(cls, handle.name)

    def __init__(self, path=None, content=None, **kwargs):
        if not path: path = str(self)
        self.path = path