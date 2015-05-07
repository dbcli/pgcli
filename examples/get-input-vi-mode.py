#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import get_input


if __name__ == '__main__':
    print("You have Vi keybindings here. Press [Esc] to go to navigation mode.")
    answer = get_input('Give me some input: ', multiline=False, vi_mode=True)
    print('You said: %s' % answer)
