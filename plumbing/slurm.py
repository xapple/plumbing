"""
========================
Launching SLURM commands
========================

The ``slurm`` function makes launching SLURM commands easy to
write and easy to use.

To start a SLURM command type:
"""

# Built-in modules #
import subprocess, sys, time

################################################################################
class Slurm(object):
    """Represents a job being run by slurm."""

    def __init__(self, prog_cmd, slurm_args):
        self.prog_cmd = prog_cmd
        self.slurm_args = slurm_args
        self.args = ['srun']
        self.args += map(str, slurm_args)
        self.args += map(str, prog_cmd)
        self.name = None if not '-J' in slurm_args else slurm_args[slurm_args.index('-J')+1]
        self.proc = None
        self.running = False
        self.failed = None
        self.retries = -1

    def __repr__(self): return '<%s object "%s">' % (self.__class__.__name__, self.name)

    def __getstate__(self):
        self.proc = None
        return self.__dict__

    def start(self):
        self.retries += 1
        self.failed = None
        self.running = True
        try: self.proc = subprocess.Popen(self.args, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        except OSError: raise ValueError("Program '%s' does not seem to exist in your $PATH." % self.args[0])

    def read(self):
        # Wait until completion #
        try: return_code = self.proc.wait()
        except KeyboardInterrupt as err:
            print "You aborted the process pid %i. It was: %s " % (self.proc.pid, self.args)
            raise err
        self.running = False
        # Read result #
        self.stdout, self.stderr = self.proc.stdout.read(), self.proc.stderr.read()
        if return_code != 0: self.failed = True
        else: self.failed = False

    def update(self):
        if self.running and self.finished: self.read()

    def change(**kwargs):
        pass

    @property
    def finished(self):
        if not self.proc: return False
        if self.proc.poll() == None: return False
        return True

    @property
    def return_code(self):
        if not self.proc: return None
        return self.proc.poll()

################################################################################
class Bunch(object):
    """Represents a bunch of jobs being run by slurm."""

    def __init__(self, jobs, max_sim_jobs=200, max_retries=3):
        self.jobs = jobs
        self.max_sim_jobs = max_sim_jobs
        self.max_retries = max_retries

    def update(self):
        for j in self.jobs: j.update()

    @property
    def never_started(self):
        return [j for j in self.jobs if j.retries == -1 and j.running == False]

    @property
    def running(self):
        return [j for j in self.jobs if j.running == True]

    @property
    def succeded(self):
        return [j for j in self.jobs if j.failed == False]

    @property
    def failed(self):
        return [j for j in self.jobs if j.failed == True]

    @property
    def will_retry(self):
        return [j for j in self.failed if j.retries < self.max_retries]

    @property
    def wont_retry(self):
        return [j for j in self.failed if j.retries >= self.max_retries]

    @property
    def should_launch(self):
        return self.never_started + self.will_retry

    @property
    def launch_now(self):
        available = self.max_sim_jobs - len(self.running)
        if self.should_launch and available: return self.should_launch[0:available]

    @property
    def with_retries(self):
        return [j for j in self.succeded if j.retries > 0]

################################################################################
class Runner(object):
    """Takes care of running a bunch of jobs on SLURM."""

    def __init__(self, bunch, update_interval=1):
        self.bunch = bunch
        self.update_interval = update_interval

    def message(self):
        print "Starting %i processes via SLURM" % len(self.bunch.jobs)
        sys.stdout.write("    \033[K")
        sys.stdout.flush()

    def message_update(self):
        template = "\r Waiting: %i | Running: %i | Failed: %i | Succeded: %i \033[K"
        params = ['never_started', 'running', 'wont_retry', 'succeded']
        params = tuple([len(getattr(self.bunch, k)) for k in params])
        sys.stdout.write(template % params)
        sys.stdout.flush()

    def message_final(self):
        params = ['succeded', 'with_retries', 'failed']
        params = tuple([len(getattr(self.bunch, k)) for k in params])
        print "\r %i processes succeeded (%i with retries) and %i failed" % params

    def run(self):
        self.message()
        try:
            while True:
                time.sleep(self.update_interval)
                self.bunch.update()
                if self.bunch.launch_now: self.bunch.launch_now[0].start()
                self.message_update()
                if self.done: break
        except KeyboardInterrupt as err:
            print "\nYou killed a SLURM runner with %i jobs." % (len(self.bunch.jobs))
            raise err
        self.message_final()

    @property
    def done(self):
        return not self.bunch.running and not self.bunch.should_launch

    def log_results(self, log_path):
        with open(log_path, 'a') as f:
            f.write("--------------  %s  -----------------\n" % time.asctime())
            for j in self.bunch.failed:
                f.write("(--*--) Failed job %s command after %i retries (--*--)\n" % (j.name, j.retries))
                f.write(' '.join(j.args))
                if j.stdout:
                    f.write("\n(*) Job %s standard out (*)\n" % j.name)
                    f.write(j.stdout)
                if j.stderr:
                    f.write("\n(*) Job %s standard error (*)\n" % j.name)
                    f.write(j.stderr)
            f.write("(--*--) Successes (--*--)\n")
            f.write(" ".join([j.name + " (%i retries)" % j.retries for j in self.bunch.succeded]))
            f.write("\n")

################################################################################
def run_jobs(jobs):
    return Runner(Bunch(jobs))