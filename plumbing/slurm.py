"""
========================
Launching SLURM commands
========================

The ``slurm`` function makes launching SLURM commands easy to
write and easy to use.

To start a SLURM command type:

#TODO
"""

# Built-in modules #
import os, sh, pystache, tempfile, copy, getpass

################################################################################
slurm_template = """#!/bin/bash -l
#SBATCH -D {{change_dir}}
#SBATCH -J {{job_name}}
#SBATCH -o {{out_file}}
#SBATCH --mail-user {{email}}
#SBATCH --mail-type=END
#SBATCH -A {{project}}
#SBATCH -t {{time}}
#SBATCH -N {{machines}}
#SBATCH -n {{cores}}
#SBATCH --qos={{qos}}
#SBATCH -d {{dependency}}
echo "SBATCH: start at $(date) on $(hostname)"
{{command}}
echo "SBATCH: end at $(date)"
"""

################################################################################
current_dir = os.getcwd() + '/'

default_slurm_params = {
'change_dir': current_dir,
'job_name': 'test_slurm',
'out_file': current_dir + 'slurm.out',
'project': os.environ['SLURM_ACCOUNT'],
'time': '0:15:00',
'machines': '1',
'cores': '1',
'email': '',
'qos': 'normal',
'dependency': 'singleton',
}

################################################################################
class Job(object):
    """Represents a job being run by slurm."""

    def __init__(self, command='echo test', slurm_params={}, save_script=False):
        # Params #
        user_params = dict([(str(k), v) for k, v in slurm_params.items()])
        self.slurm_params = copy.copy(default_slurm_params)
        self.slurm_params.update(user_params)
        # Command #
        if isinstance(command,list): self.command = ' '.join(map(str, command))
        else: self.command = command
        self.slurm_params['command'] = self.command
        # Save script #
        self.save_script = save_script

    def __repr__(self): return '<%s object "%s">' % (self.__class__.__name__, self.name)

    @property
    def slurm_script(self):
        return pystache.Renderer(escape=lambda u: u).render(slurm_template, self.slurm_params)

    def launch(self):
        # Do it #
        handle = tempfile.NamedTemporaryFile(suffix='.sh',delete=False)
        handle.write(self.slurm_script)
        handle.close()
        sh.sbatch(handle.name)
        os.remove(handle.name)
        # Optional save #
        if self.save_script:
            path = self.slurm_params['change_dir'] + self.slurm_params['job_name'] + '.sh'
            with open(path, 'w') as handle: handle.write(self.slurm_script)

################################################################################
def jobs_info():
    text = sh.jobinfo('-u', getpass.getuser())
    lines = sh.grep("(null)", _in=text).split('\n')
    params = ['jobid','pos','partition','name','user','account','state','start_time','time_left','priority','cpus','nodelist','features','dependency']
    jobs = [dict(zip(params,line.split())) for line in lines if line]
    return jobs