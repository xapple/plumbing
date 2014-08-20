# Built-in modules #
import sys, os, time, shutil, re, random, math

# Third party modules #
import sh, numpy

################################################################################
def average(iterator):
    """Iterative mean"""
    count = 0
    total = 0
    for num in iterator:
        count += 1
        total += num
    return float(total)/count

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

################################################################################
def flatten(L):
    for sublist in L:
        if hasattr(sublist, '__iter__'):
            for item in flatten(sublist): yield item
        else: yield sublist

################################################################################
def isubsample(full_sample, k, full_sample_len=None):
    """Downsample an enumerable list of things"""
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

################################################################################
def imean(numbers):
    """Iterative mean"""
    count = 0
    total = 0
    for num in numbers:
        count += 1
        total += num
    return float(total)/count

################################################################################
def get_git_tag(directory):
    if os.path.exists(directory + '/.git'):
        return sh.git("--git-dir=" + directory + '/.git', "describe", "--tags", "--dirty", "--always").strip('\n')
    else:
        return None

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

def reversed_blocks(handle, blocksize=4096):
    """Generate blocks of file's contents in reverse order."""
    handle.seek(0, os.SEEK_END)
    here = handle.tell()
    while 0 < here:
        delta = min(blocksize, here)
        here -= delta
        handle.seek(here, os.SEEK_SET)
        yield handle.read(delta)

###############################################################################
def move_with_overwrite(source, dest):
    if os.path.exists(dest):
        if os.path.isdir(dest): shutil.rmtree(dest)
        else: os.remove(dest)
    shutil.move(source, dest)

###############################################################################
def replace_extension(path, new_ext):
    if not new_ext.startswith('.'): new_ext = '.' + new_ext
    base, ext = os.path.splitext(path)
    return base + new_ext

###############################################################################
def find_file_by_name(name, root=os.curdir):
    for dirpath, dirnames, filenames in os.walk(os.path.abspath(root)):
        if name in filenames: return os.path.join(dirpath, name)
    raise Exception("Could not find file '%s' in '%s'") % (name, root)

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
def which(cmd):
    """https://github.com/jc0n/python-which"""
    def is_executable(path):
        return os.path.exists(path) and os.access(path, os.X_OK)
    path, name = os.path.split(cmd)
    if path:
        if is_executable(cmd): return cmd
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            candidate = os.path.join(path, cmd)
            if is_executable(candidate): return candidate
    raise Exception('which failed to locate a proper command path "%s"' % cmd)

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

################################################################################
def head(path, window=20):
    with open(path, 'r') as handle:
        return ''.join(handle.next() for line in xrange(window))

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
def is_integer(string):
    try: int(string)
    except ValueError: return False
    return True
