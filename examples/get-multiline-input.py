#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit.contrib.shortcuts import get_input


if __name__ == '__main__':
    print('Press [Meta+Enter] or [Esc] followed by [Enter] to accept input.')
    answer = get_input('Give me some multiline input: ', multiline=True)
    print('You said: %s' % answer)
