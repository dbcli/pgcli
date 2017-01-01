#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit import prompt


if __name__ == '__main__':
    password = prompt('Password: ', is_password=True)
    print('You said: %s' % password)
