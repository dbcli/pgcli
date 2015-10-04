#!/usr/bin/env python
"""
Simple example of a CLI that demonstrates fish-style auto suggestion.

When you type some input, it will match the input against the history. If One
entry of the history starts with the given input, then it will show the
remaining part as a suggestion. Pressing the right arrow will insert this
suggestion.
"""
from __future__ import unicode_literals, print_function
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.interface import AbortAction
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory


def main():
    # Create some history first. (Easy for testing.)
    history = InMemoryHistory()
    history.append('import os')
    history.append('print("hello")')
    history.append('print("world")')
    history.append('import path')

    # Print help.
    print('This CLI has fish-style auto-suggestion enable.')
    print('Type for instance "pri", then you\'ll see a suggestion.')
    print('Press the right arrow to insert the suggestion.')
    print('Press Control-C to retry. Control-D to exit.')
    print()

    text = prompt('Say something: ', history=history,
                  auto_suggest=AutoSuggestFromHistory(),
                  enable_history_search=True,
                  on_abort=AbortAction.RETRY)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
