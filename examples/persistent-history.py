#!/usr/bin/env python
"""
Simple example of a CLI that keeps a persistent history of all the entered
strings in a file. When you run this script for a second time, pressing
arrow-up will go back in history.
"""
from prompt_toolkit.contrib.shortcuts import get_input


def main():
    text = get_input('Say something: ', history_filename='.example-history-file')
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
