#!/usr/bin/env python
"""
Example of a radio list box dialog.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts.dialogs import radiolist_dialog


def main():
    result = radiolist_dialog(
        values=[
            ('red', 'Red'),
            ('green', 'Green'),
            ('blue', 'Blue'),
            ('orange', 'Orange'),
        ],
        title='Radiolist dialog example',
        text='Please select a color:')

    print('Result = {}'.format(result))


if __name__ == '__main__':
    main()
