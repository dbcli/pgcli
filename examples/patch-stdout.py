#!/usr/bin/env python
"""
An example that demonstrates how `patch_stdout` works.

This makes sure that output from other threads doesn't disturb the rendering of
the prompt, but instead is printed nicely above the prompt.
"""
from __future__ import unicode_literals

from prompt_toolkit import prompt
import threading
import time


def main():
    # Print a counter every second in another thread.
    running = True

    def thread():
        i = 0
        while running:
            i += 1
            print('i=%i' % i)
            time.sleep(1)
    threading.Thread(target=thread).start()

    # Now read the input. The print statements of the other thread
    # should not disturb anything.
    result = prompt('Say something: ', patch_stdout=True)
    print('You said: %s' % result)

    # Stop thrad.
    running = False


if __name__ == '__main__':
    main()
