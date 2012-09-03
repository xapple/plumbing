"""
================
Warping programs
================

The ``@command`` decorator makes binding command line executables
easy to write and easy to use.

To wrap a program, write a function that takes whatever arguments
you will need to run the program like if it where on the shell.
The function should return a dictionary containing several keys:

    * mandatory: ``arguments``
    * optional: ``stdin``
    * optional: ``return_value``.

Firstly, ``arguments`` should be a list of strings which is
the actual command and arguments to be executed (e.g. ``["touch", filename]``).

Secondly, ``stdin`` should be a value to feed the subprocess once it is launched.

Thirdly, ``return_value`` be a value to return, or a callable
object which takes a stdout plus strerr as parameters and returns the value
that will be passed back to the user when this program is run.
You can also simply specify ``"stdout"`` to have the output of the
process returned directly.

For example, to wrap ``touch``, we write a one argument function that
takes the filename of the file to touch, and apply the ``@command``
decorator to it::

    from plumbing import command

    @command
    def touch(filename):
        return {"arguments": ["touch", filename],
                "return_value": filename}

We can now call this function directly::

     f = touch("myfile")

The value returned by touch is ``"myfile"``, the name of
the touched file.

A more complicated example would include binding the BLASTP algorithm::

    from plumbing import command

    @command
    def blastp(database, sequences, **kwargs):
        \"\"\"Will launch the 'blastp' algorithm using the NCBI executable.

       :param database: The path to the database to blast against.
       :param sequences: A fasta string.
       :param **kwargs: Extra parameters that will be passed to the executable
                        For instance you could specify "e=1e-20".
       :returns: A list of top hits in blast format.
       \"\"\"
        return {"arguments": ["blastall", "-p", "blastp", "-d" database] +
                             [a for k,v in kwargs.items() for a in ('-'+k,v)],
                "stdin": sequences)
                "return_value": 'stdout'}

Often you want to call a function, but not block when it returns
so you can run several in parallel. ``@command`` also creates a
method ``parallel`` which does this. The return value is a
Future object with a single method: ``wait()``. When you call
``wait()``, it blocks until the program finishes, then returns the
same value that you would get from calling the function directly.
So, to touch two files, and not block until both commands have
started, you would write::

    a = blastp.parallel("nr", open("fasta1".read(), e=1e-20)
    b = blastp.parallel("nr", open("fasta2".read(), e=1e-20)
    hitsA = a.wait()
    hitsB = b.wait()

The ``parallel`` method will runs processes in different threads.
Other methods exists for running commands in parallel.
For example, on systems using the SLURM batch submission
system, you can run commands via batch submission by using the
``slurm`` method and adding the mandatory time and account info::

    p = blastp.slurm("nr", open("fasta".read(), time='1:00:00', account='b2011035')
    hits = p.wait()

On systems using the LSF batch submission system, you can run
commands via batch submission by using the ``lsf`` method::

    p = blastp.lsf("nr", open("fasta".read())
    hits = p.wait()

"""

# Built-in modules #
import subprocess

# Internal modules #
from plumbing.common import non_blocking

################################################################################
class Future(object):
    """Object returned when functions decorated with ``@command``
    are executed in parallel with ``parallel()`` or ``lsf()``"""

    def __init__(self, target_fn):
        self.fn = non_blocking(target_fn)

    def start(self, *args, **kwargs):
        self.thread = self.fn(*args, **kwargs)

    def wait(self):
        return self.thread.join()

################################################################################
class CommandFailed(Exception):
    """Thrown when a program bound by ``@command``
    exits with a value other than ``0``."""

    def __init__(self, command, stderr):
        self.command = command
        self.stderr = stderr

    def __str__(self):
        message = "Running '%s' failed." % " ".join(command)
        if self.stderr: message += "\nSTDERR:\n" % "" + self.stderr
        return message

################################################################################
class command(object):
    """Decorator used to wrap external programs."""

    def __init__(self, function):
        self.function = function
        self.__doc__ = function.__doc__
        self.__name__ = function.__name__

    def __call__(self, *args, **kwargs):
        """Run a program locally, and block until it completes."""
        return self.run(self.function(*args, **kwargs))

    def parallel(self, *args, **kwargs):
        """Run a program in an other thread and return a Future object."""
        return self.run_non_blocking(self.function(*args, **kwargs))

    def run(self, cmd_dict):
        """Core function, spans the subprocess"""
        # Start it #
        cmd = cmd_dict["arguments"]
        try: proc = subprocess.Popen(cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        except OSError: raise ValueError("Program '%s' does not seem to exist in your $PATH." % cmd_dict['arguments'][0])
        # Communicate with it #
        try: stdout, stderr = proc.communicate(cmd_dict.get("stdin"))
        except KeyboardInterrupt as err:
            print "(pid %s) You aborted the following command: %s " % (cmd, proc.pid)
            raise err
        # Check for failure #
        if proc.returncode != 0: raise CommandFailed(cmd, stderr)
        # Return result #
        result = cmd_dict.get("return_value")
        if callable(result): return result(stdout, stderr)
        elif result == 'stdout': return stdout
        else: return result

    def run_non_blocking(self, cmd_dict):
        """Same thing as run, but does it in a different thread"""
        future = Future(self.run)
        future.start(cmd_dict)
        return future

    #-------------------------------------------------------------------------#
    def slurm(self, *args, **kwargs):
        """Run a program via the SLURM system."""
        # Get extra parameters #
        time = kwargs.pop('time') if 'time' in kwargs else None
        account = kwargs.pop('account') if 'account' in kwargs else None
        # Compose the command #
        cmd_dict = self.function(*args, **kwargs)
        slurm_cmd = ['salloc', '-n', '1', '-t', time, '-A', account, '-Q']
        slurm_cmd += ['-A', account] if account else []
        slurm_cmd += ['-t', time] if time else []
        cmd_dict["arguments"] = slurm_cmd + cmd_dict["arguments"]
        # Retrurn it #
        return self.run_non_blocking(cmd_dict)

    def lsf(self, *args, **kwargs):
        """Run a program via the LSF system."""
        cmd_dict = self.function(*args, **kwargs)
        cmd_dict["arguments"].insert(0,)
        return self.run_non_blocking(cmd_dict)
