# Built-in modules #
import getpass

# Internal modules #
from plumbing.cache import expiry_every
from plumbing.common import which

# Third party modules #
import sh

# Constants #
user = getpass.getuser()

################################################################################
class ExistingJobs(object):
    """Parses the output of `squeue` calls"""

    queued_command = ["--array", "--format='%.8A %.9P %.25j %.8u %.14a %.2t %.19S %.10L %.8Q %.4C %.16R %.12f %E'", "--sort=-p,i", "-t", "PENDING", "-u", user]
    running_command = ["-t", "r,cg", "--array", "--format='%.8A %.9P %.25j %.8u %.14a %.2t %.19S %.10L %.6D %.4C %R'", "-S", "e", "-u", user]

    queued_params = ['jobid','partition','name','user','account','state',
                     'start_time','time_left','priority','cpus','nodelist',
                     'features','dependency']
    running_params = ['jobid','partition','name','user','account','state',
                     'start_time','time_left','nodes','cpus','nodelist']

    def __iter__(self): return iter(self.status)
    def __getitem__(self, key):
        if isinstance(key, slice): return self.status[key]
        elif isinstance(key, int): return self.status[key]
        elif isinstance(key, basestring): return [s for s in self if s['name'] == key][0]
        else: raise TypeError("Invalid argument type.")
    def __contains__(self, key): return key in [s['name'] for s in self]

    @property
    @expiry_every(seconds=30)
    def status(self):
        # Parse #
        self.queued = [line for line in sh.squeue(self.queued_command) if not line.startswith("'   JOBID")]
        self.running = [line for line in sh.squeue(self.running_command) if not line.startswith("'   JOBID")]
        # Structure #
        self.queued = [dict(zip(self.queued_params, line.strip("'\n").split())) for line in self.queued if line]
        self.running = [dict(zip(self.running_params, line.strip("'\n").split())) for line in self.running if line]
        # Add info #
        for job in self.queued: job['type'] = 'queued'
        for job in self.running: job['type'] = 'running'
        # Return #
        return self.running + self.queued

    def expire(self):
        if hasattr(self.status, '__cache__'): del self.status.__cache__

    @property
    def names(self):
        return [job['name'] for job in self.status]

################################################################################
class ExistingProjects(object):
    """Parses the output of `projinfo` on Uppmax"""
    params = ['name', 'used', 'allowed']

    def __iter__(self): return iter(self.status)
    def __getitem__(self, key):
        if isinstance(key, slice): return self.status[key]
        elif isinstance(key, int): return self.status[key]
        elif isinstance(key, str): return [s for s in self if s['name'] == key][0]
        else: raise TypeError("Invalid argument type.")
    def __contains__(self, key): return key in [s['name'] for s in self]
    def __nonzero__(self): return bool(self.status)

    @property
    @expiry_every(seconds=3600)
    def status(self):
        if not which('projinfo', safe=True): return None
        self.output = sh.projinfo()
        self.lines = [line.strip("'\n") for line in self.output if line.startswith('b')]
        cast = lambda x: (str(x[0]), float(x[1]), float(x[2]))
        self.items = [cast(line.split()) for line in self.lines]
        self.result = [dict(zip(self.params, item)) for item in self.items]
        self.result.sort(key = lambda x: x['used'])
        return self.result

################################################################################
jobs = ExistingJobs()
projects = ExistingProjects()
