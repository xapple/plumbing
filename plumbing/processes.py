"""
Processes and parallelism
=========================

The ``processes`` module provides some convenience functions
for using parallel processes in python.

Adapted from http://stackoverflow.com/a/16071616/287297

Example usage:

    print prll_map(lambda i: i * 2, [1, 2, 3, 4, 6, 7, 8], 32, verbose=True)

Comments:

"It spawns a predefined amount of workers and only iterates through the input list
 if there exists an idle worker. I also enabled the "daemon" mode for the workers so
 that KeyboardInterupt works as expected."

Pitfalls: all the stdouts are sent back to the parent stdout, intertwined.

Alternatively, use this fork of multiprocessing:
https://github.com/uqfoundation/multiprocess
"""

# Modules #
import multiprocessing
from tqdm import tqdm

# Optionally switch to dill #
#import multiprocess as multiprocessing

################################################################################
def apply_function(func_to_apply, queue_in, queue_out):
    while not queue_in.empty():
        num, obj = queue_in.get()
        queue_out.put((num, func_to_apply(obj)))

################################################################################
def prll_map(func_to_apply, items, cpus=None, verbose=True):
    # Number of processes to use #
    if cpus is None: cpus = min(multiprocessing.cpu_count(), 32)
    # Create queues #
    q_in  = multiprocessing.Queue()
    q_out = multiprocessing.Queue()
    # Process list #
    new_proc  = lambda t,a: multiprocessing.Process(target=t, args=a)
    processes = [new_proc(apply_function, (func_to_apply, q_in, q_out)) for x in range(cpus)]
    # Put all the items (objects) in the queue #
    sent = [q_in.put((i, x)) for i, x in enumerate(items)]
    # Start them all #
    for proc in processes:
        proc.daemon = True
        proc.start()
    # Display progress bar or not #
    if verbose:
        results = [q_out.get() for x in tqdm(range(len(sent)))]
    else:
        results = [q_out.get() for x in range(len(sent))]
    # Wait for them to finish #
    for proc in processes: proc.join()
    # Return results #
    return [x for i, x in sorted(results)]

################################################################################
def test():
    def slow_square(x):
        import time
        time.sleep(2)
        return x**2
    objs    = range(20)
    squares = prll_map(slow_square, objs, 4, verbose=True)
    print("Result: %s" % squares)
