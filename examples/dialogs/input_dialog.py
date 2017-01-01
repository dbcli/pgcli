#!/usr/bin/env python
"""
Example of an input box dialog.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts.dialogs import input_dialog


def main():
    result = input_dialog(
        title='Input dialog example',
        text='Please type your name:')

    print('Result = {}'.format(result))


if __name__ == '__main__':
    main()
