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

Thirdly, ``return_value`` should be a value to return, or a callable
object which takes ``(stdout,strerr)`` as parameters and returns the value
that will be passed back to the user when this program is run.
You can also simply specify ``"stdout"`` to have the output of the
process returned directly.

For example, to wrap ``touch``, we write a one argument function that
takes the filename of the file to touch, and apply the ``@command``
decorator to it::

    from plumbing.common import command

    @command
    def touch(filename):
        return {"arguments": ["touch", filename],
                "return_value": filename}

We can now call this function directly::

     f = touch("myfile")

The value returned by touch is ``"myfile"``, the name of
the touched file.

A more complicated example would include binding the BLASTP algorithm::

    from plumbing.common import command

    @command
    def blastp(database, sequences, **kwargs):
         \"\"\"Will launch the 'blastp' algorithm using the NCBI executable.

        :param database: The path to the database to blast against.
        :param sequences: A fasta formated string.
        :param **kwargs: Extra parameters that will be passed to the executable
                        For instance, you could specify "e=1e-20".
        :returns: A list of top hits in blast format.
        \"\"\"
        return {"arguments": ["blastall", "-p", "blastp", "-d" database] +
                             [a for k,v in kwargs.items() for a in ('-'+k,v)],
                "stdin": sequences)
                "return_value": 'stdout'}

As shown above, we can now call this function directly::

     hits = blastp("swissprot", open("proteins.fasta").read())

The value returned by blastp is a long string containing all the
results from the BLASTP algorithm.

Often you want to call a function, but not block when it returns
so you can run several in parallel. ``@command`` also creates a
method ``parallel`` which does this. The return value is a
Future object with a single method: ``wait()``. When you call
``wait()``, it blocks until the program finishes, then returns the
same value that you would get from calling the function directly.
So, to touch two files, and not block until both commands have
started, you would write::

    a = blastp.parallel("nr", open("fasta1").read(), e=1e-20)
    b = blastp.parallel("nr", open("fasta2").read(), e=1e-20)
    hitsA = a.wait()
    hitsB = b.wait()

The ``parallel`` method will runs processes without blocking.
Other methods exists for running commands in parallel.
For example, on systems using the SLURM batch submission
system, you can run commands via batch submission by using the
``slurm`` method and optionally adding the time and account info::

    p = blastp.slurm("nr", open("fasta").read(), time='1:00:00')
    hits = p.wait()

On systems using the LSF batch submission system, you can run
commands via batch submission by using the ``lsf`` method::

    p = blastp.lsf("nr", open("fasta").read(), queue='long')
    hits = p.wait()
"""

# Built-in modules #
import subprocess, sys, time

# Variables #
PARRALEL_JOBS = []

################################################################################
def start_process(args):
    """Run a process using subprocess module"""
    try:
        return subprocess.Popen(args, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    except OSError:
        raise ValueError("Program '%s' does not seem to exist in your $PATH." % args[0])

################################################################################
def pause_for_parallel_jobs(update_interval=2):
    """Wait until all parallel jobs are done and print a status update"""
    global PARRALEL_JOBS
    while True:
        PARRALEL_JOBS = [job for job in PARRALEL_JOBS if not job.finished]
        if not PARRALEL_JOBS:
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()
            return
        sys.stdout.write("\r    %i parallel jobs still running.\033[K" % len(PARRALEL_JOBS))
        sys.stdout.flush()
        time.sleep(update_interval)

################################################################################
class CommandFailed(Exception):
    """Thrown when a program bound by ``@command``
    exits with a value other than ``0``."""

    def __init__(self, args, stderr, name=None):
        message = "Running '%s' failed." % " ".join(args)
        if name: message += " The job name was: '%s'." % name
        if stderr: message += " The error reported is:\n\n" + stderr
        Exception.__init__(self, message)

################################################################################
class command(object):
    """Decorator used to wrap external programs."""

    def __init__(self, function):
        self.function = function
        self.__doc__ = function.__doc__
        self.__name__ = function.__name__

    def __call__(self, *args, **kwargs):
        """Run a program locally, and block until it completes."""
        # Call the user defined function #
        cmd_dict = self.function(*args, **kwargs)
        cmd_dict['arguments'] = [str(a) for a in cmd_dict['arguments']]
        args = cmd_dict['arguments']
        # Start a process #
        proc = start_process(args)
        # Wait until completion #
        try: stdout, stderr = proc.communicate(cmd_dict.get("stdin"))
        except KeyboardInterrupt as err:
            print "You aborted the process pid %i. It was: %s " % (proc.pid, args)
            raise err
        # Check for failure #
        if proc.returncode != 0: raise CommandFailed(args, stderr)
        # Return result #
        result = cmd_dict.get("return_value")
        if callable(result): return result(stdout, stderr)
        elif result == 'stdout': return stdout
        else: return result

    def parallel(self, *args, **kwargs):
        """Run a program and return a Future object."""
        # Call the user defined function #
        cmd_dict = self.function(*args, **kwargs)
        cmd_dict['arguments'] = [str(a) for a in cmd_dict['arguments']]
        # Start a process #
        proc = start_process(cmd_dict['arguments'])
        # Write to the standard in #
        if 'stdin' in cmd_dict:
            proc.stdin.write(cmd_dict["stdin"])
            proc.stdin.close()
        # The Future object takes it from here #
        future = Future(proc, cmd_dict)
        # Let's keep a reference of it #
        PARRALEL_JOBS.append(future)
        # Hand it back to the user #
        return future

    def slurm(self, *args, **kwargs):
        """Run a program via the SLURM system and return a Future object."""
        # Optional name #
        name = kwargs.get('name')
        # Define special parameters #
        special_params = (('time','-t'), ('account','-A'), ('name','-J'))
        # Compose the command #
        slurm_cmd = ['srun', '-n', '1', '-Q']
        # Get optional parameters #
        for param,key in special_params:
            if param in kwargs: slurm_cmd += [key, kwargs.pop(param)]
        # Call the user defined function #
        cmd_dict = self.function(*args, **kwargs)
        cmd_dict['arguments'] = [str(a) for a in cmd_dict['arguments']]
        # Get optional keyword parameters #
        qos = kwargs.pop('qos') if 'qos' in kwargs else None
        if qos: slurm_cmd += ['--qos='+qos]
        # Update the command #
        cmd_dict["arguments"] = slurm_cmd + cmd_dict["arguments"]
        # Start a process #
        proc = start_process(cmd_dict['arguments'])
        # Write the standard in #
        if 'stdin' in cmd_dict:
            proc.stdin.write(cmd_dict["stdin"])
            proc.stdin.close()
        # The Future object takes it from here #
        future = Future(proc, cmd_dict, name)
        # Let's keep a reference of it #
        PARRALEL_JOBS.append(future)
        # Hand it back to the user #
        return future

    def lsf(self, *args, **kwargs):
        """Run a program via the LSF system and return a Future object."""
        # Optional name #
        name = kwargs.get('name')
        # Get extra optional keyword parameters #
        queue = kwargs.pop('queue') if 'queue' in kwargs else None
        # Call the user defined function #
        cmd_dict = self.function(*args, **kwargs)
        cmd_dict['arguments'] = [str(a) for a in cmd_dict['arguments']]
        # Compose the command #
        bsub_cmd = ["bsub", "-o", "/dev/null", "-e", "/dev/null", "-K", "-r"]
        if queue: bsub_cmd += ['-q', queue]
        cmd_dict["arguments"] = bsub_cmd + cmd_dict["arguments"]
        # Start a process #
        proc = start_process(cmd_dict['arguments'])
        # Write the standard in #
        if 'stdin' in cmd_dict:
            proc.stdin.write(cmd_dict["stdin"])
            proc.stdin.close()
        # The FutureLSF object takes it from here #
        future = Future(proc, cmd_dict, name)
        # Let's keep a reference of it #
        PARRALEL_JOBS.append(future)
        # Hand it back to the user #
        return future

################################################################################
class Future(object):
    """Object returned when functions decorated with ``@command``
    are executed in parallel with ``parallel()``."""

    def __init__(self, proc, cmd_dict, name=None):
        self.proc = proc
        self.cmd_dict = cmd_dict
        self.name = name

    @property
    def finished(self):
        if self.proc.poll() is None: return False
        else: return True

    @property
    def return_code(self):
        return self.proc.poll()

    def wait(self):
        # Wait until completion #
        try: return_code = self.proc.wait()
        except KeyboardInterrupt as err:
            print "You aborted the process pid %i. It was: %s " % (self.proc.pid, self.cmd_dict["arguments"])
            raise err
        # Read result #
        stdout, stderr = self.proc.stdout.read(), self.proc.stderr.read()
        # Check for failure #
        if return_code != 0: raise CommandFailed(self.cmd_dict["arguments"], stderr, self.name)
        # Return result #
        result = self.cmd_dict.get("return_value")
        if callable(result): return result(stdout, stderr)
        elif result == 'stdout': return stdout
        else: return result