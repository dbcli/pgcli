#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit.contrib.shortcuts import get_input


if __name__ == '__main__':
    answer = get_input('Give me some input: ')
    print('You said: %s' % answer)
