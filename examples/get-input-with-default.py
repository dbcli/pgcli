#!/usr/bin/env python
"""
Example of a call to `get_input` with a default value.
The input is pre-filled, but the user can still edit the default.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import get_input
import getpass

if __name__ == '__main__':
    answer = get_input('What is your name: ', default=getpass.getuser())
    print('You said: %s' % answer)
