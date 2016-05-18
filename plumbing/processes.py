"""
Processes and parallelism
=========================

The ``processes`` module provides some convenience functions
for using processes in python.

Adapted from http://stackoverflow.com/a/16071616/287297

Example usage:

    print prll_map(lambda i: i * 2, [1, 2, 3, 4, 6, 7, 8])

Comments:

"It spawns a predefined amount of workers and only iterates through the input list if there exists an idle worker. I also enabled the "daemon" mode for the workers so that KeyboardInterupt works as expected."

All the stdouts are sent back to the parent stdout, intertwined.
"""

# Modules #
import multiprocessing

################################################################################
def target_func(f, q_in, q_out):
    while True:
        i, x = q_in.get()
        if i is None:
            break
        q_out.put((i, f(x)))

################################################################################
def prll_map(function_to_apply, items, cpus=None):
    # Number of cores #
    if cpus is None: cpus = min(multiprocessing.cpu_count(), 32)
    # Create queues #
    q_in = multiprocessing.Queue(1)
    q_out = multiprocessing.Queue()
    # Process list #
    processes = [multiprocessing.Process(target = target_func,
                                         args   = (function_to_apply, q_in, q_out))
                 for _ in range(cpus)]
    # Start them all #
    for proc in processes:
        proc.daemon = True
        proc.start()
    # Undocumented #
    sent = [q_in.put((i, x)) for i, x in enumerate(items)]
    [q_in.put((None, None)) for _ in range(cpus)]
    res = [q_out.get() for _ in range(len(sent))]
    # Wait for them to finish #
    [proc.join() for proc in processes]
    # Return results #
    return [x for i, x in sorted(res)]