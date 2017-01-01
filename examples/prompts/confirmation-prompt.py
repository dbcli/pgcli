#!/usr/bin/env python
"""
Example of a confirmation prompt.
"""
from __future__ import unicode_literals

from prompt_toolkit.shortcuts import confirm

if __name__ == '__main__':
    answer = confirm('Should we do that? (y/n) ')
    print('You said: %s' % answer)
