# Built-in modules #
import os, sys, time, datetime

# Internal modules #
from plumbing.common import flatten
from plumbing.color import Color

# Third party modules #
import threadpool

# Constants #

###############################################################################
class Runner(object):
    """General purpose runner"""

    @property
    def color(self):
        import __main__ as main
        if not hasattr(main, '__file__'): return True
        return False

    def run(self, steps=None, **kwargs):
        # Message #
        if self.color: print Color.f_cyn + "Running %s" % (self.parent) + Color.end
        else: print "Running %s" % self.parent
        # Do steps #
        if not steps: steps = self.default_steps
        for step in steps:
            name, params = step.items()[0]
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
            else: return flatten([get_children(o, name, level-1) for o in obj.children])
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
        return fns

    def run_step(self, name, fns, *args, **kwargs):
        # Default threads #
        threads = kwargs.pop('threads', True)
        # Start timer #
        start_time = time.time()
        # Message #
        if self.color: print "Running step: " + Color.f_grn + name + Color.end
        else: print "Running step: " + name
        sys.stdout.flush()
        # Threads #
        if threads and len(fns) > 1:
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
    def latest_log(self):
        if not self.parent.loaded: self.parent.load()
        def logs():
            for dir_name in os.listdir(self.parent.p.logs_dir):
                dir_path = os.path.join(self.parent.p.logs_dir, dir_name)
                if not os.path.isdir(dir_path): continue
                yield dir_path + '/'
        return max(logs(), key=lambda x: os.stat(x).st_mtime)