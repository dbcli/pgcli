#!/usr/bin/env python
"""
More complex demonstration of what's possible with the progress bar.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts.progress_bar import progress_bar
from prompt_toolkit import HTML
import time
import threading


def main():
    with progress_bar(
            title=HTML('<b>Example of many parallel tasks.</b>'),
            bottom_toolbar=HTML('<b>[Control-L]</b> clear  <b>[Control-C]</b> abort')) as pb:

        def run_task(label, total, sleep_time):
            for i in pb(range(total), label=label):
                time.sleep(sleep_time)

        threads = [
            threading.Thread(target=run_task, args=('First task', 50, .1)),
            threading.Thread(target=run_task, args=('Second task', 100, .1)),
            threading.Thread(target=run_task, args=('Third task', 8, 3)),
            threading.Thread(target=run_task, args=('Fourth task', 200, .1)),
            threading.Thread(target=run_task, args=('Fifth task', 40, .2)),
            threading.Thread(target=run_task, args=('Sixth task', 220, .1)),
            threading.Thread(target=run_task, args=('Seventh task', 85, .05)),
            threading.Thread(target=run_task, args=('Eight task', 200, .05)),
        ]

        for t in threads:
            t.daemon = True
            t.start()

        # Wait for the threads to finish. We use a timeout for the join() call,
        # because on Windows, join cannot be interrupted by Control-C or any other
        # signal.
        for t in threads:
            while t.is_alive():
                t.join(timeout=.5)


if __name__ == '__main__':
    main()
