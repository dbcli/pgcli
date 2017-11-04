#!/usr/bin/env python
"""
A very simple progress bar which keep track of the progress as we consume an
iterator.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts.progress_bar import progress_bar
import time


def main():
    with progress_bar() as pb:
        for i in pb(range(800)):
            time.sleep(.01)


if __name__ == '__main__':
    main()
