# Built-in modules #
import os, stat, re, getpass, time, shutil
import base64, hashlib, socket
from collections import OrderedDict

# Internal modules #
import gefes
from gefes.common import get_git_tag, tail, is_integer, flatten
from gefes.common.color import Color
from gefes.common.tmpstuff import TmpFile, new_temp_path
from gefes.common.cache import expiry_every

# Third party modules #
import sh

# Constants #
hostname = socket.gethostname()
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
        elif isinstance(key, str): return [s for s in self if s['name'] == key][0]
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
    """Parses the output of `projinfo`"""
    params = ['name', 'used', 'allowed']

    def __iter__(self): return iter(self.status)
    def __getitem__(self, key):
        if isinstance(key, slice): return self.status[key]
        elif isinstance(key, int): return self.status[key]
        elif isinstance(key, str): return [s for s in self if s['name'] == key][0]
        else: raise TypeError("Invalid argument type.")
    def __contains__(self, key): return key in [s['name'] for s in self]

    @property
    @expiry_every(seconds=3600)
    def status(self):
        self.output = sh.projinfo()
        self.lines = [line.strip("'\n") for line in self.output if line.startswith('b')]
        cast = lambda x: (str(x[0]), float(x[1]), float(x[2]))
        self.items = [cast(line.split()) for line in self.lines]
        self.result = [dict(zip(self.params, item)) for item in self.items]
        self.result.sort(key = lambda x: x['used'])
        return self.result

################################################################################
class SLURMCommand(object):
    """Makes launching SLURM commands easy to write and easy to use. Here is an example way to use this class:

        for i, command in enumerate(['print "hi"', 'print "hello"']):
            job = SLURMCommand(command, time='00:01:00', qos='short', job_name='job%i'%i)
            job.run()
            print "Job %i is running !" % job.id

        for path in ['~/data/scafolds1.txt', '~/data/scafolds2.txt', '~/data/scafolds3.txt']:
            command = 'import sh\n'
            command += 'script = sh.Command("analyze.py")\n'
            command += 'script(%s)' % path
            job = SLURMCommand(command, time='00:01:00', qos='short', job_name=path[-25:])
            job.run()
            print "Job %i is running !" % job.id
    """

    shebang_headers = {
        'bash':   "#!/bin/bash -l",
        'python': "#!/usr/bin/env python"
    }

    slurm_headers = OrderedDict((
        ('change_dir', {'needed': True,  'tag': '#SBATCH -D %s',            'default': os.path.abspath(os.getcwd())}),
        ('job_name'  , {'needed': False, 'tag': '#SBATCH -J %s',            'default': 'test_slurm'}),
        ('out_file'  , {'needed': True,  'tag': '#SBATCH -o %s',            'default': '/dev/null'}),
        ('project'   , {'needed': False, 'tag': '#SBATCH -A %s',            'default': "b2011035"}),
        ('time'      , {'needed': True,  'tag': '#SBATCH -t %s',            'default': '7-00:00:00'}),
        ('machines'  , {'needed': True,  'tag': '#SBATCH -N %s',            'default': '1'}),
        ('cores'     , {'needed': True,  'tag': '#SBATCH -n %s',            'default': '16'}),
        ('partition' , {'needed': True,  'tag': '#SBATCH -p %s',            'default': 'node'}),
        ('email'     , {'needed': False, 'tag': '#SBATCH --mail-user %s',   'default': os.environ.get('EMAIL')}),
        ('email-when', {'needed': True,  'tag': '#SBATCH --mail-type=%s',   'default': 'END'}),
        ('qos'       , {'needed': False, 'tag': '#SBATCH --qos=%s',         'default': 'short'}),
        ('dependency', {'needed': False, 'tag': '#SBATCH -d %s',            'default': 'afterok:1'}),
        ('constraint', {'needed': False, 'tag': '#SBATCH -C %s',            'default': 'mem72GB'}),
        ('cluster'   , {'needed': False, 'tag': '#SBATCH -M %s',            'default': 'milou'}),
        ('alloc'     , {'needed': False, 'tag': '#SBATCH --reservation=%s', 'default': 'miiiiiine'}),
        ('jobid'     , {'needed': False, 'tag': '#SBATCH --jobid=%i',       'default': 2173455}),
    ))

    def __repr__(self): return '<%s object "%s">' % (self.__class__.__name__, self.name)

    def __init__(self, command='print "Hello world"', save_script=False, language='python', **kwargs):
        # Attributes #
        self.command = command
        self.save_script = save_script
        self.language = language
        # Absolute paths #
        if self.save_script: self.save_script = os.path.abspath(save_script)
        if 'change_dir' in kwargs: kwargs['change_dir'] = os.path.abspath(kwargs['change_dir'])
        if 'out_file' in kwargs: kwargs['out_file'] = os.path.abspath(kwargs['out_file'])
        # Check command type #
        if not isinstance(self.command, list): self.command = [self.command]
        # Check name #
        self.name = kwargs.get('job_name', self.slurm_headers['job_name']['default'])
        # Hash the name if it doesn't fit in the limit #
        if len(self.name) <= 25: self.short_name = self.name
        else: self.short_name = base64.urlsafe_b64encode(hashlib.md5(self.name).digest())
        kwargs['job_name'] = self.short_name
        # Check we have a project otherwise choose the one with less hours #
        if 'project' not in kwargs and 'SBATCH_ACCOUNT' not in os.environ:
            kwargs['project'] = projects[0]['name']
        # Script header #
        self.shebang_header = [self.shebang_headers[language]]
        # Slurm parameters #
        self.slurm_params = OrderedDict()
        for param, info in self.slurm_headers.items():
            if not info['needed'] and not param in kwargs: continue
            if kwargs.get(param): self.slurm_params[param] = kwargs.get(param)
            else:                 self.slurm_params[param] = info['default']
        # Special cases #
        if self.slurm_params.get('cluster') == 'halvan': self.slurm_params['partition'] = 'halvan'
        # Slurm header #
        self.slurm_header = [self.slurm_headers[k]['tag'] % v for k,v in self.slurm_params.items()]
        # Extra command #
        if language == 'bash':
            self.script_header = ['echo "SLURM: start at $(date) on $(hostname)"']
            self.script_footer = ['echo "SLURM: end at $(date)"']
        if language == 'python':
            self.script_header = ['import time, platform',
                                   'print "SLURM: start at {0} on {1}".format(time.asctime(), platform.node())']
            self.script_footer = ['print "SLURM: end at {0}".format(time.asctime())']
        # Script #
        self.script = (self.shebang_header, self.slurm_header, self.script_header, self.command, self.script_footer)
        self.script = '\n'.join(flatten(self.script))

    @property
    def status(self):
        # Does the script exist #
        script_exists = self.save_script and os.path.exists(self.save_script)
        if not script_exists and self.short_name not in jobs.names: return "READY"
        # It is in the job names #
        if script_exists and self.short_name in jobs.names:
            if jobs[self.short_name]['type'] == 'queued': return "QUEUED"
            if jobs[self.short_name]['type'] == 'running': return "RUNNING"
        # No log file exists #
        if script_exists and not os.path.exists(self.slurm_params['out_file']): return "ABORTED"
        # Look in log file #
        log_tail = tail(self.slurm_params['out_file'])
        if 'CANCELLED' in log_tail: return "CANCELLED"
        if 'SLURM: end at' in log_tail: return "ENDED"
        # Default #
        return "STOPPED"

    @property
    def info(self):
        if self.short_name not in jobs: return {'time_left': '0-00:00:00'}
        return jobs[self.short_name]

    def run(self):
        """Will call launch after performing some checks"""
        # Check already exists #
        if self.status == "READY": return self.launch()
        # Check already queued #
        if self.status == "QUEUED":
            print Color.i_red + "Job %s already in queue." % (self.name,) + Color.end
            return
        # Check already running #
        if self.status == "RUNNING":
            print Color.i_red + "Job %s already in queue." % (self.name,) + Color.end
            return
        # Check already ended #
        if self.status == "ENDED":
            print Color.i_red + "Job %s already ended." % (self.name,) + Color.end
            return
        # Check already exists #
        if self.status == "CANCELLED": return self.restart()
        # Fallback #
        print "Job might have run already. Not starting."

    def launch(self):
        # Make script file #
        self.write_script()
        # Do it #
        sbatch_out = sh.sbatch(self.script_path)
        jobs.expire()
        # Message #
        print Color.i_blu + "SLURM:" + Color.end + " " + str(sbatch_out),
        # Clean up #
        if not self.save_script: os.remove(self.script_path)
        # Return id #
        self.id = int(re.findall("Submitted batch job ([0-9]+)", str(sbatch_out))[0])
        return self.id

    def write_script(self):
        if self.save_script is True:
            self.script_path = new_temp_path()
        if self.save_script:
            self.script_path = self.save_script
            with open(self.script_path, 'w') as handle: handle.write(self.script)
            os.chmod(self.script_path, os.stat(self.script_path).st_mode | stat.S_IEXEC)
        else:
            self.script_path = TmpFile.from_string(self.script).path

    def interupt(self):
        sh.scancel(self.id)
        if self.save_script: os.remove(self.save_script)
        if 'out_file' in self.slurm_params: os.remove(self.slurm_params['out_file'])

    def restart(self):
        # Make script #
        pass

################################################################################
class SLURMJob(object):
    """Takes care of running a python job through SLURM and logs results.
    Will run it remotely in a new interpreter with a static copy of a module."""

    def __repr__(self): return '<%s object "%s">' % (self.__class__.__name__, self.name)

    def __init__(self, command, log_base_dir, module=gefes, **kwargs):
        # Log directory #
        dir_name = "%4d-%02d-%02d|%02d-%02d-%02d"
        dir_name = dir_name % time.localtime()[0:6]
        self.log_dir = log_base_dir + dir_name + '/'
        os.mkdir(self.log_dir)
        # Copy module there #
        module_dir = os.path.dirname(module.__file__)
        module_name = module.__name__
        repos_dir = os.path.abspath(module_dir + '/../')
        project_name = os.path.basename(repos_dir)
        shutil.copytree(repos_dir, self.log_dir + project_name)
        static_module_dir = self.log_dir + project_name + '/'
        # Archive version #
        self.module_version = module.__version__ + ' ' + get_git_tag(repos_dir)
        # Check command type #
        if not isinstance(command, list): command = [command]
        # Make script #
        script =  ["import os, sys"]
        script += ["sys.path.insert(0, '%s')" % static_module_dir]
        script += ["import %s" % module_name]
        script += ["print 'Using version from {0}'.format(os.path.abspath(%s.__file__))" % module_name]
        script += command
        # Output #
        script_path = self.log_dir + "run.py"
        output_path = self.log_dir + "run.out"
        # Change directory #
        if 'change_dir' not in kwargs: kwargs['change_dir'] = self.log_dir
        # Make SLURM object #
        self.slurm_command = SLURMCommand(script, save_script=script_path, out_file=output_path, **kwargs)

    def run(self):
        return self.slurm_command.run()

################################################################################
if 'SLURM_NTASKS' in os.environ:
    nr_threads = int(os.environ['SLURM_NTASKS'])
elif 'SLURM_JOB_CPUS_PER_NODE' in os.environ:
     text = os.environ['SLURM_JOB_CPUS_PER_NODE']
     if is_integer(text): nr_threads = int(text)
     else:
        n, N = re.findall("([1-9]+)\(x([1-9]+)\)", text)[0]
        nr_threads = int(n) * int(N)
else:
    nr_threads = 1

################################################################################
jobs = ExistingJobs()
projects = ExistingProjects()
