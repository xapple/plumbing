"""
================
Warping programs
================

The ``@command`` decorator makes binding command line executables
easy to write and easy to use.

To wrap a program, write a function that takes whatever arguments
you will need. The function should return a dictionary containing two keys,
``arguments`` and optionally ``return_value``.
Firstly, ``arguments`` should point to a list of strings which is
the actual command and arguments to be executed (e.g. ``["touch", filename]``).
Secondly, ``return_value`` can point to a value to return, or a callable
object which takes a ``CommandOutput`` object and returns the value
that will be passed back to the user when this program is run.

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

Often you want to call a function, but not block when it returns
so you can run several in parallel. ``@command`` also creates a
method ``parallel`` which does this. The return value is a
Future object with a single method: ``wait()``. When you call
``wait()``, it blocks until the program finishes, then returns the
same value that you would get from calling the function directly.
So, to touch two files, and not block until both commands have
started, you would write::

    a = touch.parallel("myfile1")
    b = touch.parallel("myfile2")
    a.wait()
    b.wait()

The ``parallel`` method will runs processes in different threads.
Other methods exists for running commands in parallel.
For example, on systems using the LSF batch submission
system, you can run commands via batch submission by using the
``lsf`` method::

    a = touch.lsf("myfile")
    f = a.wait()

Some programs do not accept an output file as an argument and only
write to ``stdout``. Alternately, you might need to capture
``stderr`` to a file. All the methods of ``@command`` accept
keyword arguments ``stdout`` and ``stderr`` to specify files to
write these streams to. If they are omitted, then both streams
are captured and returned in the ``CommandOutput`` object.
"""

# Built-in modules #
import os, tempfile, time, subprocess

# Internal modules #
from plumbing.common import random_name, non_blocking, check_executable

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
class CommandOutput(object):
    """Object passed to return_value functions after commands are done.
    Programs bound with ``@command`` can call a function when they are
    finished to create a return value from their output. The output
    is passed as a ``CommandOutput`` object.
    """

    def __init__(self, return_code, pid, arguments, stdout, stderr):
        self.return_code = return_code
        self.pid = pid
        self.arguments = arguments
        self.stdout = stdout
        self.stderr = stderr

################################################################################
class CommandFailed(Exception):
    """Thrown when a program bound by ``@command``
    exits with a value other than ``0``."""

    def __init__(self, output):
        self.output = output

    def __str__(self):
        message = "Running '%s' failed." % " ".join(self.output.arguments)
        if self.output.stdout: message += "stdout:\n%s" % "".join(self.output.stdout)
        if self.output.stderr: message += "stderr:\n%s" % "".join(self.output.stderr)
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
        # Get the input #
        stdout = subprocess.PIPE if not 'stdout' in kwargs else open(kwargs.pop('stdout'), 'w')
        stderr = subprocess.PIPE if not 'stderr' in kwargs else open(kwargs.pop('stderr'), 'w')
        cmd_dict = self.function(*args, **kwargs)
        # Run it #
        try: proc = subprocess.Popen(cmd_dict["arguments"], bufsize=-1, stdout=stdout, stderr=stderr)
        except OSError: raise ValueError("Program %s does not seem to exist in your $PATH." % cmd_dict['arguments'][0])
        return_code = proc.wait()
        # Get the output #
        stdout_value = proc.stdout.readlines() if not isinstance(stdout,file) else None
        stderr_value = proc.stderr.readlines() if not isinstance(stderr,file) else None
        output = CommandOutput(return_code, proc.pid, cmd_dict["arguments"], stdout_value, stderr_value)
        # Check for sucess #
        if return_code != 0: raise CommandFailed(output)
        # Return result #
        result = cmd_dict.get("return_value")
        return result if not callable(result) else result(output)

    def parallel(self, *args, **kwargs):
        """Run a program in an other thread and return a Future object."""
        future = Future(self.__call__)
        future.start(*args, **kwargs)
        return future

    def lsf(self, *args, **kwargs):
        """Run a program via the LSF system and return a Future object."""
        # Check that bsub is available #
        if not check_executable('bsub'):
            raise OSError("The executable 'bsub' cannot be found on this machine.")
        # Get a directory writable by the cluster #
        default_lsf_dir = "/scratch/cluster/weekly/"
        if 'tmp_dir' in kwargs: tmp_dir = kwargs.pop('tmp_dir')
        else:
            if os.path.exists(default_lsf_dir):
                tmp_dir = default_lsf_dir + os.environ['USER'] + "/"
                if not os.path.exists(tmp_dir): os.mkdir(tmp_dir)
            else:
                tmp_dir = tempfile.tempdir()
        # Get the standard out #
        if 'stdout' in kwargs:
            stdout = kwargs.pop('stdout')
            load_stdout = False
        else:
            stdout = tmp_dir + random_name()
            load_stdout = True
        # Get the standard error #
        if 'stderr' in kwargs:
            stderr = kwargs.pop('stderr')
            load_stderr = False
        else:
            stderr = tmp_dir + random_name()
            load_stderr = True
        # Get other optional parameters
        queue = kwargs.pop('queue') if 'queue' in kwargs else None
        # Call the user function #
        cmd_dict = self.function(*args, **kwargs)
        # Compose the remote command #
        remote_cmd = " ".join(cmd_dict["arguments"])
        remote_cmd += " > " + stdout
        remote_cmd = " ( " + remote_cmd + " ) >& " + stderr
        # Compose the 'bsub' command #
        bsub_cmd = ["bsub"]
        if queue: bsub_cmd += ["-q", queue]
        bsub_cmd += ["-o", "/dev/null", "-e", "/dev/null", "-K", "-r", remote_cmd]
        # Run this function in a thread #
        def target_function():
            nullout = open(os.path.devnull, 'w')
            try: proc = subprocess.Popen(bsub_cmd, bufsize=-1, stdout=nullout, stderr=nullout)
            except OSError: raise ValueError("Program %s does not seem to exist in your $PATH." % cmd_dict['arguments'][0])
            return_code = proc.wait()
            # We need to wait until the stdout file actually show up #
            while not os.path.exists(stdout): time.sleep(0.1)
            if load_stdout:
                with open(stdout, 'r') as f: stdout_value = f.readlines()
                os.remove(stdout)
            else:
                stdout_value = None
            # We need to wait until the stderr file actually show up #
            while not os.path.exists(stderr): time.sleep(0.1)
            if load_stderr:
                with open(stderr, 'r') as f: stderr_value = f.readlines()
                os.remove(stderr)
            else:
                stderr_value = None
            # Get the output #
            output = CommandOutput(return_code, proc.pid, bsub_cmd, stdout_value, stderr_value)
            # Check for sucess #
            if return_code != 0: raise CommandFailed(output)
            # Return result #
            result = cmd_dict.get("return_value")
            return result if not callable(result) else result(output)
        # Create a Future object #
        future = Future(target_function)
        future.start()
        return future