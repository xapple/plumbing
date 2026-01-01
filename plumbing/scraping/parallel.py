#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licensed.
Contact at www.sinclair.bio
"""

###############################################################################
class MultiDownload():
    """
    Taken and adapted from:
    https://github.com/soda480/pypbars/blob/main/examples/example3.py

    But should take a look at:
    https://pypi.org/project/tqdm-multiprocess/
    """

    # The number of files to download in parallel #
    num_proc = 3

    def prepare_queue(self, queue):
        for _ in range(20):
            import random
            queue.put({'total': random.randint(100, 150)})

    def download_one(self, worker_id, total):
        for index in range(total):
            import time, random
            time.sleep(random.choice([.001, .003, .008]))
        return total

    def run_queue(self, worker_id, queue):
        result = 0
        while True:
            try:
                total = queue.get(timeout=1)['total']
                result += self.download_one(worker_id, total)
            except Empty:
                break
        return result

    def download_parallel(self):
        # Imports #
        from multiprocessing import Queue, Pool, get_context
        from pypbars import ProgressBars
        from list2term.multiprocessing import LinesQueue
        from list2term.multiprocessing import QueueManager
        # Make two queues #
        QueueManager.register('LinesQueue', LinesQueue)
        QueueManager.register('Queue', Queue)
        # Enter the queue #
        with QueueManager() as manager:
            # The lines queue #
            lines_queue = manager.LinesQueue(ctx=get_context())
            # The data queue #
            data_queue = manager.Queue()
            # Add all jobs to the queue #
            self.prepare_queue(data_queue)
            # Start a pool of workers #
            with Pool(self.num_proc) as pool:
                # Arguments that will be sent to the function #
                process_data = [('name%i'%i, data_queue, lines_queue)
                                for i in range(self.num_proc)]
                # Map our function to each item #
                results = pool.starmap_async(self.run_queue, process_data)
                # Get the lookup #
                lookup = [f'{data[0]}' for data in process_data]
                # Create ProgressBars #
                with ProgressBars(lookup        = lookup,
                                  show_prefix   = False,
                                  show_fraction = False,
                                  use_color     = True,
                                  show_duration = True,
                                  clear_alias   = True) as lines:
                    while True:
                        try:
                            item = lines_queue.get(timeout=0.1)
                            if item.endswith('->reset'):
                                i, message = lines.get_index_message(item)
                                lines[i].reset(clear_alias=False)
                            else:
                                lines.write(item)
                        except Empty:
                            if results.ready():
                                for i, _ in enumerate(lines):
                                    lines[i].complete = True
                                break
        # Return #
        return results.get()

###############################################################################
if __name__ == '__main__':
    print(MultiDownload().download_parallel())