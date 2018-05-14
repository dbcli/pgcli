#!/usr/bin/env python
"""
Simple example of a CLI that keeps a persistent history of all the entered
strings in a file. When you run this script for a second time, pressing
arrow-up will go back in history.
"""
from __future__ import unicode_literals
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory


def main():
    our_history = FileHistory('.example-history-file')

    # The history needs to be passed to the `PromptSession`. It can't be passed
    # to the `prompt` call because only one history can be used during a
    # session.
    session = PromptSession(history=our_history)

    while True:
        text = session.prompt('Say something: ')
        print('You said: %s' % text)


if __name__ == '__main__':
    main()
