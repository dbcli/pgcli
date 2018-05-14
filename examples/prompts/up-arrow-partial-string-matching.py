#!/usr/bin/env python
"""
Simple example of a CLI that demonstrates up-arrow partial string matching.

When you type some input, it's possible to use the up arrow to filter the
history on the items starting with the given input text.
"""
from __future__ import unicode_literals, print_function
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory


def main():
    # Create some history first. (Easy for testing.)
    history = InMemoryHistory()
    history.append_string('import os')
    history.append_string('print("hello")')
    history.append_string('print("world")')
    history.append_string('import path')

    # Print help.
    print('This CLI has up-arrow partial string matching enabled.')
    print('Type for instance "pri" followed by up-arrow and you')
    print('get the last items starting with "pri".')
    print('Press Control-C to retry. Control-D to exit.')
    print()

    session = PromptSession(history=history, enable_history_search=True)

    while True:
        try:
            text = session.prompt('Say something: ')
        except KeyboardInterrupt:
            pass  # Ctrl-C pressed. Try again.
        else:
            break

    print('You said: %s' % text)


if __name__ == '__main__':
    main()
