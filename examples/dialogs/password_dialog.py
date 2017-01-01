#!/usr/bin/env python
"""
Example of an password input dialog.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts.dialogs import input_dialog


def main():
    result = input_dialog(
        title='Password dialog example',
        text='Please type your password:',
        password=True)

    print('Result = {}'.format(result))


if __name__ == '__main__':
    main()
