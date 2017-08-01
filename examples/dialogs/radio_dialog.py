#!/usr/bin/env python
"""
Example of a radio list box dialog.
"""
from __future__ import unicode_literals
from prompt_toolkit.formatted_text import HTML
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

    # With HTML.
    result = radiolist_dialog(
        values=[
            ('red', HTML('<style bg="red" fg="white">Red</style>')),
            ('green', HTML('<style bg="green" fg="white">Green</style>')),
            ('blue', HTML('<style bg="blue" fg="white">Blue</style>')),
            ('orange', HTML('<style bg="orange" fg="white">Orange</style>')),
        ],
        title=HTML('Radiolist dialog example <reverse>with colors</reverse>'),
        text='Please select a color:')

    print('Result = {}'.format(result))


if __name__ == '__main__':
    main()
