#!/usr/bin/env python
"""
Demonstration of how the input can be indented.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import get_input


if __name__ == '__main__':
    answer = get_input('Give me some input:\n > ', multiline=True)
    print('You said: %s' % answer)
