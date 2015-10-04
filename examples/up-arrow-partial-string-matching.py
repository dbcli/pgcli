#!/usr/bin/env python
"""
Simple example of a CLI that demonstrates up-arrow partial string matching.

When you type some input, it's possible to use the up arrow to filter the
history on the items starting with the given input text.
"""
from __future__ import unicode_literals, print_function
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.filters import Always
from prompt_toolkit.interface import AbortAction


def main():
    # Create some history first. (Easy for testing.)
    history = InMemoryHistory()
    history.append('import os')
    history.append('print("hello")')
    history.append('print("world")')
    history.append('import path')

    # Print help.
    print('This CLI has up-arrow partial string matching enabled.')
    print('Type for instance "pri" followed by up-arrow and you')
    print('get the last items starting with "pri".')
    print('Press Control-C to retry. Control-D to exit.')
    print()

    text = prompt('Say something: ', history=history,
                  enable_history_search=Always(),
                  on_abort=AbortAction.RETRY)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
