# Built-in modules #
import os, re, multiprocessing

# Internal modules #
from plumbing.common import is_integer

# Third party modules #

################################################################################
def count_processors():
    if 'SLURM_NTASKS' in os.environ: return int(os.environ['SLURM_NTASKS'])
    elif 'SLURM_JOB_CPUS_PER_NODE' in os.environ:
         text = os.environ['SLURM_JOB_CPUS_PER_NODE']
         if is_integer(text): return int(text)
         else:
            n, N = re.findall("([1-9]+)\(x([1-9]+)\)", text)[0]
            return int(n) * int(N)
    else: return multiprocessing.cpu_count()

################################################################################
num_processors = count_processors()