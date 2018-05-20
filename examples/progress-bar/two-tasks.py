#!/usr/bin/env python
"""
Two progress bars that run in parallel.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import ProgressBar
import time
import threading


def main():
    with ProgressBar() as pb:
        # Two parallal tasks.
        def task_1():
            for i in pb(range(100)):
                time.sleep(.05)

        def task_2():
            for i in pb(range(150)):
                time.sleep(.08)

        # Start threads.
        t1 = threading.Thread(target=task_1)
        t2 = threading.Thread(target=task_2)
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()

        # Wait for the threads to finish. We use a timeout for the join() call,
        # because on Windows, join cannot be interrupted by Control-C or any other
        # signal.
        for t in [t1, t2]:
            while t.is_alive():
                t.join(timeout=.5)


if __name__ == '__main__':
    main()
