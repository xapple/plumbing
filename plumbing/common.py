# -*- coding: utf-8 -*-

# Built-in modules #
import sys, os, time, re, random, math, json
import getpass, hashlib, datetime, collections
from itertools import compress, product

# Third party modules #
import numpy, dateutil

# One liners #
flatter = lambda x: [item for sublist in x for item in sublist]

################################################################################
def ascii(text):
    """Make a safe, ASCII version a string. For instance for use on the web."""
    import unicodedata
    return unicodedata.normalize('NFKD', unicode(text)).encode('ASCII', 'ignore')

################################################################################
def sanitize(text):
    """Make an ultra-safe, ASCII version a string.
    For instance for use as a filename."""
    return "".join([c for c in text if re.match(r'\w', c)])

################################################################################
def bool_to_unicode(b):
    """Different possibilities for True: ☑️✔︎✓✅👍
       Different possibilities for False: ✕✖︎✗✘✖️❌⛔️❎👎"""
    if not isinstance(b, bool): b = bool(b)
    if b is True:  return u"✅"
    if b is False: return u"❎"

################################################################################
def all_combinations(items):
    """Generate all combinations of a given list of items."""
    return (set(compress(items,mask)) for mask in product(*[[0,1]]*len(items)))

################################################################################
def pad_with_whitespace(string, pad=None):
    """Given a multiline string, add whitespaces to every line
    so that every line has the same length."""
    if pad is None: pad = max(map(len, string.split('\n'))) + 1
    return '\n'.join(('{0: <%i}' % pad).format(line) for line in string.split('\n'))

###############################################################################
def mirror_lines(string):
    """Given a multiline string, return its reflection along a vertical axis.
    Can be useful for the visualization of text version of trees."""
    return '\n'.join(line[::-1] for line in string.split('\n'))

###############################################################################
def concatenate_by_line(first, second):
    """Zip two strings together, line wise"""
    return '\n'.join(x+y for x,y in zip(first.split('\n'), second.split('\n')))

################################################################################
def sort_string_by_pairs(strings):
    """Group a list of strings by pairs, by matching those with only
    one character difference between each other together."""
    assert len(strings) % 2 == 0
    pairs = []
    strings = list(strings) # This shallow copies the list
    while strings:
        template = strings.pop()
        for i, candidate in enumerate(strings):
            if count_string_diff(template, candidate) == 1:
                pair = [template, strings.pop(i)]
                pair.sort()
                pairs.append(pair)
                break
    return pairs

################################################################################
def count_string_diff(a,b):
    """Return the number of characters in two strings that don't exactly match"""
    shortest = min(len(a), len(b))
    return sum(a[i] != b[i] for i in range(shortest))

################################################################################
def iflatten(L):
    """Iterative flatten."""
    for sublist in L:
        if hasattr(sublist, '__iter__'):
            for item in iflatten(sublist): yield item
        else: yield sublist

################################################################################
def average(iterator):
    """Iterative mean."""
    count = 0
    total = 0
    for num in iterator:
        count += 1
        total += num
    return float(total)/count

################################################################################
def get_next_item(iterable):
    """Gets the next item of an iterable.
    If the iterable is exhausted, returns None."""
    try: x = iterable.next()
    except StopIteration: x = None
    except AttributeError: x = None
    return x

################################################################################
def pretty_now():
    """Returns some thing like '2014-07-24 11:12:45 CEST+0200'"""
    now = datetime.datetime.now(dateutil.tz.tzlocal())
    return now.strftime("%Y-%m-%d %H:%M:%S %Z%z")

################################################################################
def andify(list_of_strings):
    """
    Given a list of strings will join them with commas
    and a final "and" word.

    >>> andify(['Apples', 'Oranges', 'Mangos'])
    'Apples, Oranges and Mangos'
    """
    result = ', '.join(list_of_strings)
    comma_index = result.rfind(',')
    if comma_index > -1: result = result[:comma_index] + ' and' + result[comma_index+1:]
    return result

################################################################################
def num_to_ith(num):
    """1 becomes 1st, 2 becomes 2nd, etc."""
    value             = str(num)
    before_last_digit = value[-2]
    last_digit        = value[-1]
    if len(value) > 1 and before_last_digit == '1': return value +'th'
    if last_digit == '1': return value + 'st'
    if last_digit == '2': return value + 'nd'
    if last_digit == '3': return value + 'rd'
    return value + 'th'

################################################################################
def isubsample(full_sample, k, full_sample_len=None):
    """Down-sample an enumerable list of things"""
    # Determine length #
    if not full_sample_len: full_sample_len = len(full_sample)
    # Check size coherence #
    if not 0 <= k <= full_sample_len:
        raise ValueError('Required that 0 <= k <= full_sample_length')
    # Do it #
    picked = 0
    for i, element in enumerate(full_sample):
        prob = (k-picked) / (full_sample_len-i)
        if random.random() < prob:
            yield element
            picked += 1
    # Did we pick the right amount #
    assert picked == k

###############################################################################
def moving_average(interval, windowsize, borders=None):
    """This is essentially a convolving operation. Several option exist for dealing with the border cases.

        * None: Here the returned signal will be smaller than the inputted interval.

        * zero_padding: Here the returned signal will be larger than the inputted interval and we will add zeros to the original interval before operating the convolution.

        * zero_padding_and_cut: Same as above only the result is truncated to be the same size as the original input.

        * copy_padding: Here the returned signal will be larger than the inputted interval and we will use the right and leftmost values for padding before operating the convolution.

        * copy_padding_and_cut: Same as above only the result is truncated to be the same size as the original input.

        * zero_stretching: Here we will compute the convolution only in the valid domain, then add zeros to the result so that the output is the same size as the input.

        * copy_stretching: Here we will compute the convolution only in the valid domain, then copy the right and leftmost values so that the output is the same size as the input.
        """
    # The window size in half #
    half = int(math.floor(windowsize/2.0))
    # The normalized rectangular signal #
    window = numpy.ones(int(windowsize))/float(windowsize)
    # How do we deal with borders #
    if borders == None:
        return numpy.convolve(interval, window, 'valid')
    if borders == 'zero_padding':
        return numpy.convolve(interval, window, 'full')
    if borders == 'zero_padding_and_cut':
        return numpy.convolve(interval, window, 'same')
    if borders == 'copy_padding':
        new_interval = [interval[0]]*(windowsize-1) + interval + [interval[-1]]*(windowsize-1)
        return numpy.convolve(new_interval, window, 'valid')
    if borders == 'copy_padding_and_cut':
        new_interval = [interval[0]]*(windowsize-1) + interval + [interval[-1]]*(windowsize-1)
        return numpy.convolve(new_interval, window, 'valid')[half:-half]
    if borders == 'zero_stretching':
        result = numpy.convolve(interval, window, 'valid')
        pad = numpy.zeros(half)
        return numpy.concatenate((pad, result, pad))
    if borders == 'copy_stretching':
        result = numpy.convolve(interval, window, 'valid')
        left = numpy.ones(half)*result[0]
        right = numpy.ones(half)*result[-1]
        return numpy.concatenate((left, result, right))

################################################################################
def wait(predicate, interval=1, message=lambda: "Waiting..."):
    """Wait until the predicate turns true and display a turning ball."""
    ball, next_ball = u"|/-\\", "|"
    sys.stdout.write("    \033[K")
    sys.stdout.flush()
    while not predicate():
        time.sleep(1)
        next_ball = ball[(ball.index(next_ball) + 1) % len(ball)]
        sys.stdout.write("\r " + str(message()) + " " + next_ball + " \033[K")
        sys.stdout.flush()
    print "\r Done. \033[K"
    sys.stdout.flush()

###############################################################################
def natural_sort(item):
    """
    Sort strings that contain numbers correctly.

    >>> l = ['v1.3.12', 'v1.3.3', 'v1.2.5', 'v1.2.15', 'v1.2.3', 'v1.2.1']
    >>> l.sort(key=natural_sort)
    >>> l.__repr__()
    "['v1.2.1', 'v1.2.3', 'v1.2.5', 'v1.2.15', 'v1.3.3', 'v1.3.12']"
    """
    if item is None: return 0
    def try_int(s):
        try: return int(s)
        except ValueError: return s
    return map(try_int, re.findall(r'(\d+|\D+)', item))

###############################################################################
def split_thousands(s, tSep='\'', dSep='.'):
    """
    Splits a number on thousands.
    http://code.activestate.com/recipes/498181-add-thousands-separator-commas-to-formatted-number/

    >>> split_thousands(1000012)
    "1'000'012"
    """
    # Check input #
    if s is None: return 0
    # Check for int #
    if round(s, 13) == s: s = int(s)
    # Make string #
    if not isinstance(s, str): s = str(s)
    # Unreadable code #
    cnt = 0
    numChars = dSep + '0123456789'
    ls = len(s)
    while cnt < ls and s[cnt] not in numChars: cnt += 1
    lhs = s[0:cnt]
    s = s[cnt:]
    if dSep == '': cnt = -1
    else: cnt = s.rfind(dSep)
    if cnt > 0:
        rhs = dSep + s[cnt+1:]
        s = s[:cnt]
    else:
        rhs = ''
    splt=''
    while s != '':
        splt= s[-3:] + tSep + splt
        s = s[:-3]
    return lhs + splt[:-1] + rhs

################################################################################
def gps_deg_to_float(data):
    m = re.search(u"(\d+?)°(\d+?)\'(\d+?)\'\'", data.strip())
    degs, mins, secs = [0.0 if m.group(i) is None else int(m.group(i)) for i in range(1, 4)]
    comp_dir = -1 if data[-1] in ('N', 'E') else 1
    return (degs + (mins / 60) + (secs / 3600)) * comp_dir

################################################################################
def is_integer(string):
    try: int(string)
    except ValueError: return False
    return True

################################################################################
def reverse_compl_with_name(old_seq):
    """Reverse a SeqIO sequence, but keep its name intact."""
    new_seq = old_seq.reverse_complement()
    new_seq.id = old_seq.id
    new_seq.description = old_seq.description
    return new_seq

################################################################################
class GenWithLength(object):
    """A generator with a length attribute"""
    def __init__(self, gen, length): self.gen, self.length = gen, length
    def __iter__(self): return self.gen
    def __len__(self):  return self.length

###############################################################################
class Password(object):
    """A password object that will only prompt the user once per session"""
    def __str__(self): return self.value
    def __init__(self, prompt=None):
        self._value = None
        self.prompt = prompt

    @property
    def value(self):
        if self._value == None: self._value = getpass.getpass(self.prompt)
        return self._value

################################################################################
class OrderedSet(collections.OrderedDict, collections.MutableSet):
    """A recipe for an ordered set.
    http://stackoverflow.com/a/1653978/287297"""

    def update(self, *args, **kwargs):
        if kwargs:
            raise TypeError("update() takes no keyword arguments")

        for s in args:
            for e in s:
                self.add(e)

    def add(self, elem):
        self[elem] = None

    def discard(self, elem):
        self.pop(elem, None)

    def __le__(self, other):
        return all(e in other for e in self)

    def __lt__(self, other):
        return self <= other and self != other

    def __ge__(self, other):
        return all(e in self for e in other)

    def __gt__(self, other):
        return self >= other and self != other

    def __repr__(self):
        return 'OrderedSet([%s])' % (', '.join(map(repr, self.keys())))

    def __str__(self):
        return '{%s}' % (', '.join(map(repr, self.keys())))

    difference = property(lambda self: self.__sub__)
    difference_update = property(lambda self: self.__isub__)
    intersection = property(lambda self: self.__and__)
    intersection_update = property(lambda self: self.__iand__)
    issubset = property(lambda self: self.__le__)
    issuperset = property(lambda self: self.__ge__)
    symmetric_difference = property(lambda self: self.__xor__)
    symmetric_difference_update = property(lambda self: self.__ixor__)
    union = property(lambda self: self.__or__)

################################################################################
class SuppressAllOutput(object):
    """For those annoying modules that can't shut-up about warnings."""

    def __enter__(self):
        # Standard error #
        sys.stderr.flush()
        self.old_stderr = sys.stderr
        sys.stderr = open('/dev/null', 'a+', 0)
        # Standard out #
        sys.stdout.flush()
        self.old_stdout = sys.stdout
        sys.stdout = open('/dev/null', 'a+', 0)

    def __exit__(self, exc_type, exc_value, traceback):
        # Standard error #
        sys.stderr.flush()
        sys.stderr = self.old_stderr
        # Standard out #
        sys.stdout.flush()
        sys.stdout = self.old_stdout

    def test():
        print >>sys.stdout, "printing to stdout before suppression"
        print >>sys.stderr, "printing to stderr before suppression"
        with SuppressAllOutput():
            print >>sys.stdout, "printing to stdout during suppression"
            print >>sys.stderr, "printing to stderr during suppression"
        print >>sys.stdout, "printing to stdout after suppression"
        print >>sys.stderr, "printing to stderr after suppression"

################################################################################
def load_json_path(path):
    """Load a file with the json module, but report errors better if it
    fails. And have it ordered too !"""
    with open(path) as handle:
        try: return json.load(handle, object_pairs_hook=collections.OrderedDict)
        except ValueError as error:
            message = "Could not decode JSON file '%s'." % path
            message = "-"*20 + "\n" + message + "\n" + str(error) + "\n" + "-"*20 + "\n"
            sys.stderr.write(message)
            raise error

###############################################################################
def find_file_by_name(name, root=os.curdir):
    for dirpath, dirnames, filenames in os.walk(os.path.abspath(root)):
        if name in filenames: return os.path.join(dirpath, name)
    raise Exception("Could not find file '%s' in '%s'" % (name, root))

################################################################################
def md5sum(file_path, blocksize=65536):
    """Compute the md5 of a file. Pretty fast."""
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(blocksize), ""):
            md5.update(block)
    return md5.hexdigest()

################################################################################
def download_from_url(source, destination, progress=False, uncompress=True):
    """Download a file from an URL and place it somewhere. Like wget.
    Uses requests and tqdm to display progress if you want.
    By default it will uncompress files."""
    from tqdm import tqdm
    import requests
    response = requests.get(source, stream=True)
    with open(destination, "wb") as handle:
        if progress:
            for data in tqdm(response.iter_content()): handle.write(data)
        else:
            for data in response.iter_content(): handle.write(data)
    if uncompress:
        with open(destination, 'r') as f: header = f.read(4)
        if header == "PK\x03\x04": unzip(destination, inplace=True)
        # Add other compression formats here

################################################################################
def unzip(source, destination=None, inplace=False, single=True):
    """Unzip a standard zip file. Can specify the destination of the
    uncompressed file, or just set inplace=True to delete the original."""
    # Load #
    import zipfile, tempfile, shutil
    # Check #
    assert zipfile.is_zipfile(source)
    # Load #
    z = zipfile.ZipFile(source)
    if single or inplace: assert len(z.infolist()) == 1
    # Single file #
    if single:
        member = z.infolist()[0]
        tmpdir = tempfile.mkdtemp() + '/'
        z.extract(member, tmpdir)
        z.close()
        if inplace: shutil.move(tmpdir + member.filename, source)
        else:       shutil.move(tmpdir + member.filename, destination)
    # Multifile - no security, dangerous #
    if not single:
        z.extractall()

###############################################################################
def reversed_lines(path):
    """Generate the lines of file in reverse order."""
    with open(path, 'r') as handle:
        part = ''
        for block in reversed_blocks(handle):
            for c in reversed(block):
                if c == '\n' and part:
                    yield part[::-1]
                    part = ''
                part += c
        if part: yield part[::-1]

###############################################################################
def reversed_blocks(handle, blocksize=4096):
    """Generate blocks of file's contents in reverse order."""
    handle.seek(0, os.SEEK_END)
    here = handle.tell()
    while 0 < here:
        delta = min(blocksize, here)
        here -= delta
        handle.seek(here, os.SEEK_SET)
        yield handle.read(delta)

################################################################################
def prepend_to_file(path, data, bufsize=1<<15):
    # Backup the file #
    backupname = path + os.extsep + 'bak'
    # Remove previous backup if it exists #
    try: os.unlink(backupname)
    except OSError: pass
    os.rename(path, backupname)
    # Open input/output files,  note: outputfile's permissions lost #
    with open(backupname) as inputfile:
        with open(path, 'w') as outputfile:
            outputfile.write(data)
            buf = inputfile.read(bufsize)
            while buf:
                outputfile.write(buf)
                buf = inputfile.read(bufsize)
    # Remove backup on success #
    os.remove(backupname)

def append_to_file(path, data):
    with open(path, "a") as handle:
        handle.write(data)

################################################################################
def tail(path, window=20):
    with open(path, 'r') as f:
        BUFSIZ = 1024
        f.seek(0, 2)
        num_bytes = f.tell()
        size = window + 1
        block = -1
        data = []
        while size > 0 and num_bytes > 0:
            if num_bytes - BUFSIZ > 0:
                # Seek back one whole BUFSIZ
                f.seek(block * BUFSIZ, 2)
                # Read BUFFER
                data.insert(0, f.read(BUFSIZ))
            else:
                # File too small, start from beginning
                f.seek(0,0)
                # Only read what was not read
                data.insert(0, f.read(num_bytes))
            linesFound = data[0].count('\n')
            size -= linesFound
            num_bytes -= BUFSIZ
            block -= 1
        return '\n'.join(''.join(data).splitlines()[-window:])

def head(path, lines=20):
    with open(path, 'r') as handle:
        return ''.join(handle.next() for line in xrange(lines))

###############################################################################
def which(cmd, safe=False):
    """https://github.com/jc0n/python-which"""
    from plumbing.autopaths import FilePath
    def is_executable(path):
        return os.path.exists(path) and os.access(path, os.X_OK) and not os.path.isdir(path)
    path, name = os.path.split(cmd)
    if path:
        if is_executable(cmd): return FilePath(cmd)
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            candidate = os.path.join(path, cmd)
            if is_executable(candidate): return FilePath(candidate)
    if not safe: raise Exception('which failed to locate a proper command path "%s"' % cmd)
