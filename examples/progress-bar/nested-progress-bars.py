#!/usr/bin/env python
"""
Example of nested progress bars.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts.progress_bar import progress_bar
from prompt_toolkit import HTML
import time


def main():
    with progress_bar(
            title=HTML('<b fg="#aa00ff">Nested progress bars</b>'),
            bottom_toolbar=HTML(' <b>[Control-L]</b> clear  <b>[Control-C]</b> abort')) as pb:

        for i in pb(range(6), label='Main task'):
            for j in pb(range(200), label='Subtask <%s>' % (i + 1, ), remove_when_done=True):
                time.sleep(.01)


if __name__ == '__main__':
    main()
