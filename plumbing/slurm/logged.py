# Built-in modules #
import os
import dateutil.tz, datetime

# Internal modules #
from plumbing.common import get_git_tag
from plumbing.slurm.job import JobSLURM

# Third party modules #
import sh

################################################################################
class LoggedJobSLURM(JobSLURM):
    """Takes care of running a python job through SLURM and logs results.
    Will run it remotely in a new interpreter with a static copy of all
    required modules."""

    def __init__(self, command,
                 language = 'python',
                 base_dir = os.path.abspath(os.getcwd()),
                 modules  = None,
                 **kwargs):
        # Check the modules variable is a list #
        if modules is None:                 self.modules = []
        elif not isinstance(modules, list): self.modules = list(modules)
        else:                               self.modules = modules
        # Check command type #
        if not isinstance(command, list): command = [command]
        # Log directory #
        now = datetime.datetime.now(dateutil.tz.tzlocal())
        log_name = now.strftime("%Y-%m-%da%Hh%Mm%Ss%Z%z")
        base_dir = base_dir + log_name + '/'
        os.makedirs(base_dir)
        # Modules directory #
        modules_dir = base_dir + "modules/"
        os.makedirs(modules_dir)
        # The script to be sent #
        script =  []
        # Copy modules to the log directory #
        for module in self.modules:
            module_dir        = os.path.dirname(module.__file__)
            module_name       = module.__name__
            repos_dir         = os.path.abspath(module_dir + '/../')
            project_name      = os.path.basename(repos_dir)
            static_module_dir = modules_dir + project_name + '/'
            module_version    = module.__version__ + ' ' + get_git_tag(repos_dir)
            # Copy #
            print "Making static copy of module '%s' for SLURM job..." % module_name
            sh.cp('-R', repos_dir, static_module_dir)
            # Make script #
            script.insert(0, "sys.path.insert(0, '%s')" % static_module_dir)
            script += ["import %s" % module_name]
            script += ["print 'Using module {0}'.format(os.path.abspath(%s.__file__))" % module_name]
            script += ["print 'Using version %s'" % module_version]
        # Prepend to the script to be sent #
        script.insert(0, "import os, sys")
        # Add the user's command to the script #
        script += command
        # Super #
        JobSLURM.__init__(self, script, language, base_dir, **kwargs)