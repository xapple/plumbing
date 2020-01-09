# Built-in modules #
import subprocess, sys

# Constants #
module_names = {
    "biopython":    "Bio",
    "ipython":      "IPython",
    "scikit-learn": "sklearn",
    "scikit-bio":   "skbio",
    "biom-formt":   "biom",
}

################################################################################
def check_setup_py(mod_name):
    """
    Parses the required modules from a setup.py file and checks they are
    importable (e.g. available in the PYTHONPATH)
    """
    pass

################################################################################
# This provides extra information for certain packages #
exec_extra_clues = {
    'gsed': "The gsed package can be installed with `brew install gnu-sed` on macOS."
}

def check_executable(cmd_name):
    """
    Raises an exception if the executable `cmd_name` is not found.
    """
    # Use our own which implementation #
    from plumbing.common import which
    # Try to find it in the $PATH #
    if which(cmd_name, safe=True) is not None: return
    # Make a detailed message #
    msg = f"The executable '{cmd_name}' is required for this operation." \
          f" Unfortunately it cannot be found anywhere in your $PATH."   \
          f" Either you need to install '{cmd_name}'"                    \
          f" or you need to fix the $PATH environment variable."
    # Add any hints #
    if cmd_name in exec_extra_clues:
        msg += ' ' + exec_extra_clues.get(cmd_name)
    # Raise an exception #
    raise Exception(msg)

################################################################################
def check_module(mod_name):
    """Calls sys.exit() if the module *mod_name* is not found."""
    # Special cases #
    if mod_name in module_name: mod_name = module_name[mod_name]
    # Use a try except block #
    try:
        __import__(mod_name)
    except ImportError as e:
        if str(e) != 'No module named %s' % mod_name: raise e
        print('You do not seem to have the "%s" package properly installed.' \
              ' Either you never installed it or your $PYTHONPATH is not set up correctly.' \
              ' For more instructions see the README file. (%s)' % (mod_name, e))
        sys.exit()