# Built-in modules #
import os, shutil, csv
from six.moves import zip

# Internal modules #
from autopaths.file_path import FilePath
from autopaths.tmp_path  import new_temp_file

# Third party modules #
import pandas
if os.name == "posix": import sh
if os.name == "nt":    import pbs

################################################################################
class CSVTable(FilePath):
    d = ','

    def __init__(self, path, d=None):
        if isinstance(path, FilePath): path = path.path
        self.path = path
        if d is not None: self.d = d

    def remove_first_line(self):
        sh.sed('-i', '1d', self.path)

    def replace_title(self, before, after):
        sh.sed('-i', '1s/%s/%s/' % (before, after), self.path)

    def rewrite_lines(self, lines, path=None):
        if path is None:
            tmp_file = new_temp_file()
            tmp_file.writelines(lines)
            os.remove(self.path)
            shutil.move(tmp_file.path, self.path)
        else:
            with open(path, 'w') as handle: handle.writelines(lines)

    def integer_lines(self):
        handle = open(self.path)
        yield handle.next()
        for line in handle:
            line = line.split()
            yield line[0] + self.d + self.d.join(map(str, map(int, map(float, line[1:])))) + '\n'
    def to_integer(self, path=None):
        self.rewrite_lines(self.integer_lines(), path)

    def min_sum_lines(self, minimum):
        handle = open(self.path)
        yield handle.next()
        for line in handle:
            if sum(map(int, line.split()[1:])) >= minimum: yield line
    def filter_line_sum(self, minimum, path=None):
        self.rewrite_lines(self.min_sum_lines(minimum), path)

    def transposed_lines(self, d):
        rows = zip(*csv.reader(open(self.path), delimiter=self.d))
        for row in rows: yield d.join(row) + '\n'
    def transpose(self, path=None, d=None):
        self.rewrite_lines(self.transposed_lines(self.d if d is None else d), path)

    def to_dataframe(self, **kwargs):
        """Load up the CSV file as a pandas dataframe"""
        return pandas.io.parsers.read_csv(self.path, sep=self.d, **kwargs)

################################################################################
class TSVTable(CSVTable):
    d = '\t'