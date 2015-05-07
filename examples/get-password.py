#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import get_input


if __name__ == '__main__':
    password = get_input('Password: ', is_password=True)
    print('You said: %s' % password)
