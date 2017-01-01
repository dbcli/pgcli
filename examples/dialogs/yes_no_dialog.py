#!/usr/bin/env python
"""
Example of confirmation (yes/no) dialog window.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts.dialogs import yes_no_dialog


def main():
    result = yes_no_dialog(
        title='Yes/No dialog example',
        text='Do you want to confirm?')

    print('Result = {}'.format(result))


if __name__ == '__main__':
    main()
