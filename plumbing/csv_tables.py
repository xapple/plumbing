# Built-in modules #
import os, shutil, csv
from itertools import izip

# Internal modules #
from illumitag.common.autopaths import FilePath
from illumitag.common.tmpstuff import TmpFile

# Third party modules #
import sh

################################################################################
class CSVTable(FilePath):
    d = ','

    def __init__(self, path, d=None):
        self.path = path
        if d is not None: self.d = d

    def remove_first_line(self):
        sh.sed('-i', '1d', self.path)

    def replace_title(self, before, after):
        sh.sed('-i', '1s/%s/%s/' % (before, after), self.path)

    def rewrite_lines(self, lines, path=None):
        if not path:
            with TmpFile() as tmpfile: tmpfile.handle.writelines(lines)
            os.remove(self.path)
            shutil.move(tmpfile.path, self.path)
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
        rows = izip(*csv.reader(open(self.path), delimiter=self.d))
        for row in rows: yield d.join(row) + '\n'
    def transpose(self, path=None, d=None):
        self.rewrite_lines(self.transposed_lines(self.d if d is None else d), path)

################################################################################
class TSVTable(CSVTable):
    d = '\t'