#!/usr/bin/env python
"""
Example of button dialog window.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts.dialogs import button_dialog


def main():
    result = button_dialog(
        title='Button dialog example',
        text='Are you sure?',
        buttons=[
            ('Yes', True),
            ('No', False),
            ('Maybe...', None),
        ],
    )

    print('Result = {}'.format(result))


if __name__ == '__main__':
    main()
