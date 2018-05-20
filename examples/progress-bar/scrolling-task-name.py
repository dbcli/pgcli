#!/usr/bin/env python
"""
A very simple progress bar where the name of the task scrolls, because it's too long.
iterator.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import ProgressBar
import time


def main():
    with ProgressBar(title='Scrolling task name (make sure the window is not too big).') as pb:
        for i in pb(range(800), label='This is a very very very long task that requires horizontal scrolling ...'):
            time.sleep(.01)


if __name__ == '__main__':
    main()
