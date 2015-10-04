#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.filters import Always


if __name__ == '__main__':
    print("You have Vi keybindings here. Press [Esc] to go to navigation mode.")
    answer = prompt('Give me some input: ', multiline=False, vi_mode=Always())
    print('You said: %s' % answer)
