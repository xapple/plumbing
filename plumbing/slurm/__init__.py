# Built-in modules #
import os, re, multiprocessing

# Internal modules #
from plumbing.common import is_integer

# Third party modules #

################################################################################
def count_processors():
    """How many cores does the current computer have ?"""
    if 'SLURM_NTASKS' in os.environ: return int(os.environ['SLURM_NTASKS'])
    elif 'SLURM_JOB_CPUS_PER_NODE' in os.environ:
         text = os.environ['SLURM_JOB_CPUS_PER_NODE']
         if is_integer(text): return int(text)
         else:
            n, N = re.findall("([1-9]+)\(x([1-9]+)\)", text)[0]
            return int(n) * int(N)
    else: return multiprocessing.cpu_count()

################################################################################
def guess_server_name():
    """We often use the same servers, which one are we running on now ?"""
    if   os.environ.get('CSCSERVICE')          == 'sisu':         return "sisu"
    elif os.environ.get('SLURM_JOB_PARTITION') == 'halvan':       return "halvan"
    elif os.environ.get('SNIC_RESOURCE')       == 'milou':        return "milou"
    elif os.environ.get('LAPTOP')              == 'macbook_air':  return "macbook_air"
    else:                                                         return "unknown"

################################################################################
num_processors = count_processors()
current_server = guess_server_name()