#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit.contrib.shortcuts import get_input


if __name__ == '__main__':
    password = get_input('Give me some input: ', is_password=True)
    print('You said: %s' % password)
