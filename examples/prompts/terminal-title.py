#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import set_title


if __name__ == '__main__':
    set_title('This is the terminal title')
    answer = prompt('Give me some input: ')
    set_title('')

    print('You said: %s' % answer)
