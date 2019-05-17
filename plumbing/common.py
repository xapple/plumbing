# -*- coding: utf-8 -*-

# Futures #
from __future__ import division

# Built-in modules #
import sys, os, time, re, random, math, json
import getpass, hashlib, collections
import unicodedata
from itertools import compress, product

# Third party modules #
from six import string_types

# One liners #
flatter = lambda x: [item for sublist in x for item in sublist]

################################################################################
def ascii(text):
    """Make a safe, ASCII version a string. For instance for use on the web."""
    return unicodedata.normalize('NFKD', unicode(text)).encode('ASCII', 'ignore')

def alphanumeric(text):
    r"""Make an ultra-safe, ASCII version a string.
    For instance for use as a filename.
    \w matches any alphanumeric character and the underscore."""
    return "".join([c for c in text if re.match(r'\w', c)])

################################################################################
def sanitize_text(text):
    r"""Make a safe representation of a string.
    Note: the `\s` special character matches any whitespace character.
    This is equivalent to the set [\t\n\r\f\v] as well as ` ` (whitespace)."""
    # First replace characters that have specific effects with their repr #
    text = re.sub("(\s)", lambda m: repr(m.group(0)).strip("'"), text)
    # Make it a unicode string (the try supports python 2 and 3) #
    try: text = text.decode('utf-8')
    except AttributeError: pass
    # Normalize it “
    text = unicodedata.normalize('NFC', text)
    return text

################################################################################
def camel_to_snake(text):
    """
    Will convert CamelCaseStrings to snake_case_strings.
    >>> camel_to_snake('CamelCase')
    'camel_case'
    >>> camel_to_snake('CamelCamelCase')
    'camel_camel_case'
    >>> camel_to_snake('Camel2Camel2Case')
    'camel2_camel2_case'
    >>> camel_to_snake('getHTTPResponseCode')
    'get_http_response_code'
    >>> camel_to_snake('get2HTTPResponseCode')
    'get2_http_response_code'
    >>> camel_to_snake('HTTPResponseCode')
    'http_response_code'
    >>> camel_to_snake('HTTPResponseCodeXYZ')
    'http_response_code_xyz'
    """
    step_one = re.sub('(.)([A-Z][a-z]+)',  r'\1_\2', text)
    step_two = re.sub('([a-z0-9])([A-Z])', r'\1_\2', step_one)
    return step_two.lower()

################################################################################
def bool_to_unicode(b):
    """Different possibilities for True: ☑️✔︎✓✅👍✔️
       Different possibilities for False: ✕✖︎✗✘✖️❌⛔️❎👎🛑🔴"""
    b = bool(b)
    if b is True:  return u"✅"
    if b is False: return u"❎"

###############################################################################
def access_dict_like_obj(obj, prop, new_value=None):
    """
    Access a dictionary like if it was an object with properties.
    If no "new_value", then it's a getter, otherwise it's a setter.
    >>> {'characters': {'cast': 'Jean-Luc Picard', 'featuring': 'Deanna Troi'}}
    >>> access_dict_like_obj(startrek, 'characters.cast', 'Pierce Brosnan')
    """
    props = prop.split('.')
    if new_value:
        if props[0] not in obj: obj[props[0]] = {}
        if len(props)==1: obj[prop] = new_value
        else: return access_dict_like_obj(obj[props[0]], '.'.join(props[1:]), new_value)
    else:
        if len(props)==1: return obj[prop]
        else: return access_dict_like_obj(obj[props[0]], '.'.join(props[1:]))

################################################################################
def all_combinations(items):
    """Generate all combinations of a given list of items."""
    return (set(compress(items,mask)) for mask in product(*[[0,1]]*len(items)))

################################################################################
def pad_equal_whitespace(string, pad=None):
    """Given a multiline string, add whitespaces to every line
    so that every line has the same length."""
    if pad is None: pad = max(map(len, string.split('\n'))) + 1
    return '\n'.join(('{0: <%i}' % pad).format(line) for line in string.split('\n'))

################################################################################
def pad_extra_whitespace(string, pad):
    """Given a multiline string, add extra whitespaces to the front of every line."""
    return '\n'.join(' ' * pad + line for line in string.split('\n'))

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
def uniquify_list(L):
    """Same order unique list using only a list compression."""
    return [e for i, e in enumerate(L) if L.index(e) == i]

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
def round_to_halves(number):
    """Round a number to the closest half integer.
    >>> round_to_halves(1.3)
    1.5
    >>> round_to_halves(2.6)
    2.5
    >>> round_to_halves(3.0)
    3.0
    >>> round_to_halves(4.1)
    4.0
    """
    return round(number * 2) / 2

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
    """Returns some thing like '2019-02-15 15:58:22 CET+0100'"""
    import datetime, tzlocal
    time_zone = tzlocal.get_localzone()
    now       = datetime.datetime.now(time_zone)
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
def sum_vectors_with_padding(vectors):
    """Given an arbitrary amount of NumPy one-dimensional vectors of floats,
    do an element-wise sum, padding with 0 any that are shorter than the
    longest array (see https://stackoverflow.com/questions/56166217).

    >>> v1 = numpy.array([0, 0, 5, 5, 1, 1, 1, 1, 0, 0])
    >>> v2 = numpy.array([4, 4, 4, 5, 5, 0, 0])
    >>> v3 = numpy.array([1, 1, 1])
    >>> sum_vectors_with_padding([v1, v2, v3])
    array([ 5,  5, 10, 10,  6,  1,  1,  1,  0,  0])
    """
    import numpy
    all_lengths = [len(i) for i in vectors]
    max_length  = max(all_lengths)
    out         = numpy.zeros(max_length)
    for l,v in zip(all_lengths, vectors): out[:l] += v
    return out

###############################################################################
def moving_average(interval, windowsize, borders=None):
    """This is essentially a convolution operation
     Several option exist for dealing with the border cases.

        * None: Here the returned signal will be smaller than the inputted interval.

        * zero_padding: Here the returned signal will be larger than the inputted
        interval and we will add zeros to the original interval before operating
         the convolution.

        * zero_padding_and_cut: Same as above only the result is truncated to be
         the same size as the original input.

        * copy_padding: Here the returned signal will be larger than the inputted
         interval and we will use the right and leftmost values for padding before
          operating the convolution.

        * copy_padding_and_cut: Same as above only the result is truncated to be
         the same size as the original input.

        * zero_stretching: Here we will compute the convolution only in the valid domain,
         then add zeros to the result so that the output is the same size as the input.

        * copy_stretching: Here we will compute the convolution only in the valid domain,
         then copy the right and leftmost values so that the output is the same
          size as the input.
        """
    # The window size in half #
    half = int(math.floor(windowsize/2.0))
    # The normalized rectangular signal #
    import numpy
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
    print("\r Done. \033[K")
    sys.stdout.flush()

###############################################################################
def natural_sort(item):
    """
    Sort strings that contain numbers correctly. Works in Python 2 and 3.

    >>> l = ['v1.3.12', 'v1.3.3', 'v1.2.5', 'v1.2.15', 'v1.2.3', 'v1.2.1']
    >>> l.sort(key=natural_sort)
    >>> l.__repr__()
    "['v1.2.1', 'v1.2.3', 'v1.2.5', 'v1.2.15', 'v1.3.3', 'v1.3.12']"
    """
    dre = re.compile(r'(\d+)')
    return [int(s) if s.isdigit() else s.lower() for s in re.split(dre, item)]

###############################################################################
def split_thousands(s):
    """
    Splits a number on thousands.

    >>> split_thousands(1000012)
    "1'000'012"
    """
    # Check input #
    if s is None: return "0"
    # If it's a string #
    if isinstance(s, string_types): s = float(s)
    # If it's a float that should be an int #
    if isinstance(s, float) and s.is_integer(): s = int(s)
    # Use python built-in #
    result = "{:,}".format(s)
    # But we want single quotes #
    result = result.replace(',', "'")
    # Return #
    return result

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
        if kwargs: raise TypeError("update() takes no keyword arguments")
        for s in args:
            for e in s: self.add(e)

    def add(self, elem):     self[elem] = None
    def discard(self, elem): self.pop(elem, None)
    def __le__(self, other): return all(e in other for e in self)
    def __lt__(self, other): return self <= other and self != other
    def __ge__(self, other): return all(e in self for e in other)
    def __gt__(self, other): return self >= other and self != other
    def __repr__(self):      return 'OrderedSet([%s])' % (', '.join(map(repr, self.keys())))
    def __str__(self):       return '{%s}' % (', '.join(map(repr, self.keys())))

    difference                  = property(lambda self: self.__sub__)
    difference_update           = property(lambda self: self.__isub__)
    intersection                = property(lambda self: self.__and__)
    intersection_update         = property(lambda self: self.__iand__)
    issubset                    = property(lambda self: self.__le__)
    issuperset                  = property(lambda self: self.__ge__)
    symmetric_difference        = property(lambda self: self.__xor__)
    symmetric_difference_update = property(lambda self: self.__ixor__)
    union                       = property(lambda self: self.__or__)

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
def download_from_url(source, destination, progress=False, uncompress=False):
    """Download a file from an URL and place it somewhere. Like wget.
    Uses requests and tqdm to display progress if you want.
    By default it will uncompress files.
    #TODO: handle case where destination is a directory"""
    # Modules #
    from tqdm import tqdm
    import requests
    from autopaths.file_path import FilePath
    # Check destination exists #
    destination = FilePath(destination)
    destination.directory.create_if_not_exists()
    # Over HTTP #
    response = requests.get(source, stream=True)
    total_size = int(response.headers.get('content-length'))
    block_size = int(total_size/1024)
    # Do it #
    with open(destination, "wb") as handle:
        if progress:
            for data in tqdm(response.iter_content(chunk_size=block_size), total=1024): handle.write(data)
        else:
            for data in response.iter_content(chunk_size=block_size): handle.write(data)
    # Uncompress #
    if uncompress:
        with open(destination) as f: header = f.read(4)
        if header == "PK\x03\x04": unzip(destination, inplace=True)
        # Add other compression formats here
    # Return #
    return destination

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
    """TODO:
    * Add a random string to the backup file.
    * Restore permissions after copy.
    """
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
            lines_found = data[0].count('\n')
            size -= lines_found
            num_bytes -= BUFSIZ
            block -= 1
        return '\n'.join(''.join(data).splitlines()[-window:])

def head(path, lines=20):
    with open(path, 'r') as handle:
        return ''.join(handle.next() for line in xrange(lines))

###############################################################################
def which(cmd, safe=False):
    """https://github.com/jc0n/python-which"""
    from autopaths.file_path import FilePath
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

###############################################################################
def query_yes_no(question, default="no"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:    prompt = " [y/n] "
    elif default == "yes": prompt = " [Y/n] "
    elif default == "no":  prompt = " [y/N] "
    else: raise ValueError("invalid default answer: '%s'" % default)
    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '': return valid[default]
        elif choice in valid:                    return valid[choice]
        else: sys.stdout.write("Please respond with 'yes' or 'no'\n")