# Built-in modules #
import tempfile

# Internal modules #
from autopaths.file_path import FilePath
from autopaths.dir_path  import DirectoryPath

################################################################################
def new_temp_path(**kwargs):
    """A new temporary path."""
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
    def __new__(cls, path=None, content=None, **kwargs):
        # Was the path specified? #
        if path is not None: handle = open(path, 'w')
        else:                handle = new_temp_handle(**kwargs)
        # Was the content specified? #
        if content is not None: handle.write(content)
        # Return #
        handle.close()
        path = handle.name
        # Super #
        return FilePath.__new__(cls, path)