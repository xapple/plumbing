# Built-in modules #
import sys, time, datetime

# Internal modules #
from plumbing.common import iflatten
from plumbing.color import Color
from plumbing.slurm.logged import LoggedJobSLURM

# Third party modules #
import threadpool

# Constants #

###############################################################################
class Runner(object):
    """General purpose runner. Can execute functions on objects, via SLURM
    or locally. You should inherit from this class."""
    modules       = []
    job_name      = "unnamed"
    default_time  = '7-00:00:00'
    default_steps = [{'run': {}}]

    @property
    def extra_slurm_params(self): return {}

    def __init__(self, parent):
        self.parent = parent

    @property
    def color(self):
        """Should we use color or not ? If we are not in a shell, then not."""
        import __main__ as main
        if not hasattr(main, '__file__'): return True
        return False

    def run(self, steps=None, **kwargs):
        # Message #
        if self.color: print Color.f_cyn + "Running %s" % (self.parent) + Color.end
        else: print "Running %s" % self.parent
        # Check input #
        if not steps:                     steps = self.default_steps
        if isinstance(steps, basestring): steps = [steps]
        # Do all the steps #
        for step in steps:
            if isinstance(step, basestring):  name, params = step, {}
            if isinstance(step, dict):        name, params = step.items()[0]
            params.update(kwargs)
            fns = self.find_fns(name)
            self.run_step(name, fns, **params)
        # Report success #
        print "Success. Results are in %s" % self.parent.base_dir

    def find_fns(self, name):
        # Special case #
        if '.' in name:
            target = self.parent
            for attribute in name.split('.'):
                target = getattr(target, attribute)
            return [target]
        # Functions #
        def get_children(obj, name, level):
            if level == 0:
                if not hasattr(obj, name): return []
                else: return [getattr(obj, name)]
            else: return iflatten([get_children(o, name, level-1) for o in obj.children])
        # Recursive #
        fns = None
        level = 0
        while True:
            target = self.parent
            for i in range(level):
                if hasattr(target, 'first'): target = target.first
                else: target = None
            if target is None: raise Exception("Could not find function '%s'" % name)
            if hasattr(target, name):
                fns = get_children(self.parent, name, level)
                break
            level += 1
        assert fns
        return fns

    def run_step(self, name, fns, *args, **kwargs):
        # Default threads #
        if '.' in name: threads = kwargs.pop('threads', False)
        else:           threads = kwargs.pop('threads', True)
        # Start timer #
        start_time = time.time()
        # Message #
        if self.color: print "Running step: " + Color.f_grn + name + Color.end
        else: print "Running step: " + name
        sys.stdout.flush()
        # Threads #
        if threads and len(list(fns)) > 1:
            self.thpool = threadpool.ThreadPool(8)
            for fn in fns: self.thpool.putRequest(threadpool.WorkRequest(fn))
            self.thpool.wait()
            self.thpool.dismissWorkers(8)
            del self.thpool
        else:
            for fn in fns: fn(*args, **kwargs)
        # Stop timer #
        run_time = datetime.timedelta(seconds=round(time.time() - start_time))
        if self.color: print Color.ylw + "Run time: '%s'" % (run_time) + Color.end
        else: print "Run time: '%s'" % (run_time)
        sys.stdout.flush()

    @property
    def logs(self):
        """Find the log directory and return all the logs sorted."""
        if not self.parent.loaded: self.parent.load()
        logs = self.parent.p.logs_dir.flat_directories
        logs.sort(key=lambda x: x.mod_time)
        return logs

    @property
    def latest_log(self):
        """Find the latest log in all the logs."""
        return self.logs[-1]

    #-------------------------------------------------------------------------#
    def run_locally(self, steps=None, **kwargs):
        """A convenience method to run the same result as a SLURM job
        but locally in a non-blocking way."""
        self.slurm_job = LoggedJobSLURM(self.command(steps),
                                        base_dir = self.parent.p.logs_dir,
                                        modules  = self.modules,
                                        **kwargs)
        self.slurm_job.run_locally()

    #-------------------------------------------------------------------------#
    def run_slurm(self, steps=None, **kwargs):
        """Run the steps via the SLURM queue."""
        # Optional extra SLURM parameters #
        params = self.extra_slurm_params
        params.update(kwargs)
        # Mandatory extra SLURM parameters #
        if 'time'       not in params: params['time']       = self.default_time
        if 'job_name'   not in params: params['job_name']   = self.job_name
        if 'email'      not in params: params['email']      = None
        if 'dependency' not in params: params['dependency'] = 'singleton'
        # Send it #
        self.slurm_job = LoggedJobSLURM(self.command(steps),
                                        base_dir = self.parent.p.logs_dir,
                                        modules  = self.modules,
                                        **params)
        # Return the Job ID #
        return self.slurm_job.run()
