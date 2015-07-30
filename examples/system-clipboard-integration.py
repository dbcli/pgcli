#!/usr/bin/env python
"""
Demonstration of a custom clipboard class.
This requires the 'pyperclip' library to be installed.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import get_input
from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard


if __name__ == '__main__':
    print('Emacs shortcuts:')
    print('    Press Control-Y to paste from the system clipboard.')
    print('    Press Control-Space or Control-@ to enter selection mode.')
    print('    Press Control-W to cut to clipboard.')
    print('')

    answer = get_input('Give me some input: ', clipboard=PyperclipClipboard())
    print('You said: %s' % answer)
