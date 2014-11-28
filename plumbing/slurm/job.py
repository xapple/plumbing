# Built-in modules #
import os, re, platform
import base64, hashlib
from collections import OrderedDict

# Internal modules #
from plumbing.slurm.existing import projects, jobs
from plumbing.common import tail, flatter
from plumbing.color import Color
from plumbing.tmpstuff import new_temp_path
from plumbing.slurm import num_processors
from plumbing.autopaths import FilePath, DirectoryPath
from plumbing.cache import property_cached

# Third party modules #
import sh

# Constants #
hostname = platform.node()

################################################################################
class JobSLURM(object):
    """Makes launching SLURM jobs easy to write and easy to use. Here are some
    examples on how to use this class:

        for command in enumerate(['print "hi"', 'print "hello"']):
            job = JobSLURM(command, time='00:01:00', qos='short')
            job.run()

        for path in ['~/data/scafolds1.txt', '~/data/scafolds2.txt', '~/data/scafolds3.txt']:
            command =  ['import sh\n']
            command += ['script = sh.Command("analyze.py")\n']
            command += ['script(%s)' % path]
            job = JobSLURM(command, time='00:01:00', qos='short', job_name=path[-25:])
            job.run()
            print "Job %i is running !" % job.id
    """

    extensions = {
        'bash':   "sh",
        'python': "py"
    }

    shebang_headers = {
        'bash':   ["#!/bin/bash -l"],
        'python': ["#!/usr/bin/env python"]
    }

    slurm_headers = OrderedDict((
        ('job_name'  , {'tag': '#SBATCH -J %s',            'needed': True}),
        ('change_dir', {'tag': '#SBATCH -D %s',            'needed': True,  'default': os.path.abspath(os.getcwd())}),
        ('out_file'  , {'tag': '#SBATCH -o %s',            'needed': True,  'default': '/dev/null'}),
        ('project'   , {'tag': '#SBATCH -A %s',            'needed': False, 'default': "b2011035"}),
        ('time'      , {'tag': '#SBATCH -t %s',            'needed': True,  'default': '7-00:00:00'}),
        ('machines'  , {'tag': '#SBATCH -N %s',            'needed': True,  'default': '1'}),
        ('cores'     , {'tag': '#SBATCH -n %s',            'needed': True,  'default': num_processors}),
        ('partition' , {'tag': '#SBATCH -p %s',            'needed': True,  'default': 'node'}),
        ('email'     , {'tag': '#SBATCH --mail-user %s',   'needed': False, 'default': os.environ.get('EMAIL')}),
        ('email-when', {'tag': '#SBATCH --mail-type=%s',   'needed': True,  'default': 'END'}),
        ('qos'       , {'tag': '#SBATCH --qos=%s',         'needed': False, 'default': 'short'}),
        ('dependency', {'tag': '#SBATCH -d %s',            'needed': False, 'default': 'afterok:1'}),
        ('constraint', {'tag': '#SBATCH -C %s',            'needed': False, 'default': 'fat'}),
        ('cluster'   , {'tag': '#SBATCH -M %s',            'needed': False, 'default': 'milou'}),
        ('alloc'     , {'tag': '#SBATCH --reservation=%s', 'needed': False, 'default': 'miiiiiine'}),
        ('jobid'     , {'tag': '#SBATCH --jobid=%i',       'needed': False, 'default': 2173455}),
    ))

    script_headers = {
        'bash':   ['echo "SLURM: start at $(date) on $(hostname)"'],
        'python': ['import dateutil.tz, datetime, platform',
                   'now = datetime.datetime.now(dateutil.tz.tzlocal())',
                  r'now = now.strftime("%Y-%m-%d %Hh%Mm%Ss %Z%z")',
                   'node = platform.node()',
                   'print "SLURM: start at {0} on {1}".format(now, node)']}

    script_footers = {
        'bash':   ['echo "SLURM: end at $(date)"'],
        'python': ['now = datetime.datetime.now(dateutil.tz.tzlocal())'
                  r'now = now.strftime("%Y-%m-%d %Hh%Mm%Ss %Z%z")'
                   'print "SLURM: end at {0}".format(now)']}

    def __repr__(self): return '<%s object "%s">' % (self.__class__.__name__, self.name)

    @property
    def name(self): return self.kwargs['job_name']

    def __init__(self,
                 command     = ["import sys", "print 'Hello world'", "sys.exit()"],
                 language    = 'python',
                 base_dir    = None,
                 script_path = None,
                 **kwargs):
        # Required attributes #
        self.command  = command
        self.language = language
        self.kwargs   = kwargs
        # Set the file paths #
        self.set_paths(base_dir, script_path)
        # Check command type #
        if not isinstance(self.command, list): self.command = [self.command]
        # Get the name #
        if 'job_name' not in self.kwargs:
            hashed  = hashlib.md5(''.join(self.command)).digest()
            encoded = base64.urlsafe_b64encode(hashed)
            self.kwargs['job_name'] = encoded
        # Check we have a project otherwise choose the one with less hours #
        if hostname.startswith('milou'):
            if 'project' not in self.kwargs and 'SBATCH_ACCOUNT' not in os.environ:
                if projects: self.kwargs['project'] = projects[0]['name']

    def set_paths(self, base_dir, script_path):
        """Set the directory, the script path and the outfile path"""
        # Make absolute paths #
        if 'change_dir' in self.kwargs:
            self.kwargs['change_dir'] = DirectoryPath(os.path.abspath(self.kwargs['change_dir']))
        if 'out_file' in self.kwargs:
            self.kwargs['out_file']   = FilePath(os.path.abspath(self.kwargs['out_file']))
        # In case there is a base directory #
        if base_dir is not None:
            self.base_dir             = DirectoryPath(os.path.abspath(base_dir))
            self.script_path          = FilePath(base_dir + "run." + self.extensions[self.language])
            self.kwargs['change_dir'] = base_dir
            self.kwargs['out_file']   = FilePath(base_dir + "run.out")
        # Other cases #
        if base_dir is None and script_path is None: self.script_path = FilePath(new_temp_path())
        if script_path is not None: self.script_path = FilePath(os.path.abspath(script_path))

    @property_cached
    def slurm_params(self):
        """The list of parameters to give to the `sbatch` command."""
        # Main loop #
        result = OrderedDict()
        for param, info in self.slurm_headers.items():
            if not info['needed'] and not param in self.kwargs: continue
            if self.kwargs.get(param): result[param] = self.kwargs.get(param)
            else:                      result[param] = info['default']
        # Special cases #
        if result.get('cluster') == 'halvan': result['partition'] = 'halvan'
        # Return #
        return result

    @property
    def script(self):
        """The script to be submitted to the SLURM queue."""
        self.shebang_header = self.shebang_headers[self.language]
        self.slurm_header   = [self.slurm_headers[k]['tag'] % v for k,v in self.slurm_params.items()]
        self.script_header  = self.script_headers[self.language]
        self.script_footer  = self.script_footers[self.language]
        return '\n'.join(flatter([self.shebang_header,
                                  self.slurm_header,
                                  self.script_header,
                                  self.command,
                                  self.script_footer]))

    def make_script(self):
        """Make the script and return a FilePath object pointing to the script above."""
        self.script_path.write(self.script)
        self.script_path.permissions.make_executable()
        return self.script_path

    @property
    def status(self):
        """What is the status of the job ?"""
        # If there is no script it is either ready or a lost duplicate #
        if not self.script_path.exists:
            if self.name in     jobs.names: return "DUPLICATE"
            if self.name not in jobs.names: return "READY"
        # It is submitted already #
        if self.name in jobs.names:
            if jobs[self.short_name]['type'] == 'queued':  return "QUEUED"
            if jobs[self.short_name]['type'] == 'running': return "RUNNING"
        # So the script exists for sure but it is not in the queue #
        if not self.kwargs['out_file'].exists: return "ABORTED"
        # Let's look in log file #
        log_tail = tail(self.slurm_params['out_file'])
        if 'CANCELLED'     in log_tail: return "CANCELLED"
        if 'SLURM: end at' in log_tail: return "ENDED"
        # Default #
        return "INTERUPTED"

    @property
    def info(self):
        """Get the existing job information dictionary"""
        if self.short_name not in jobs: return {'status': self.status}
        else:                           return jobs[self.short_name]

    def run(self):
        """Will call self.launch() after performing some checks"""
        # Check already exists #
        if self.status == "READY": return self.launch()
        # Check name conflict #
        if self.status == "DUPLICATE":  message = "Job with same name '%s' already in queue, but we lost the script."
        if self.status == "QUEUED":     message = "Job '%s' already in queue."
        if self.status == "RUNNING":    message = "Job '%s' already running."
        if self.status == "ENDED":      message = "Job '%s' already ended successfully."
        if self.status == "ABORTED":    message = "Job '%s' was killed without any output file (?)."
        if self.status == "CANCELLED":  message = "Job '%s' was canceled while running."
        if self.status == "INTERUPTED": message = "Job '%s' is not running. Look at the log file."
        print Color.i_red + message % (self.name,) + Color.end
        print "Job might have run already (?). Not starting."

    def launch(self):
        """Make the script file and return the newly created job id"""
        # Make script file #
        self.make_script()
        # Do it #
        sbatch_out = sh.sbatch(self.script_path)
        jobs.expire()
        # Message #
        print Color.i_blu + "SLURM:" + Color.end + " " + str(sbatch_out),
        # Return id #
        self.id = int(re.findall("Submitted batch job ([0-9]+)", str(sbatch_out))[0])
        return self.id

    def interupt(self):
        if self.status != "QUEUED" and self.status != "RUNNING":
            raise Exception("Can't cancel job '%s'" % self.name)
        sh.scancel(self.info['id'])

    def wait(self):
        """Wait until the job is finished"""
        pass