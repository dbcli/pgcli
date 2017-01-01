#!/usr/bin/env python
"""
Simple example of a CLI that keeps a persistent history of all the entered
strings in a file. When you run this script for a second time, pressing
arrow-up will go back in history.
"""
from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory


def main():
    our_history = FileHistory('.example-history-file')
    text = prompt('Say something: ', history=our_history)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
