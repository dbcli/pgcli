#!/usr/bin/env python
"""
A very simple progress bar which keep track of the progress as we consume an
iterator.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts.progress_bar import progress_bar
import time


def data():
    """
    A generator that produces items. len() doesn't work here, so the progress
    bar can't estimate the time it will take.
    """
    for i in range(1000):
        yield i


def main():
    with progress_bar() as pb:
        for i in pb(data()):
            time.sleep(.1)


if __name__ == '__main__':
    main()
