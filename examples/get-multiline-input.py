#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit import prompt


if __name__ == '__main__':
    print('Press [Meta+Enter] or [Esc] followed by [Enter] to accept input.')
    answer = prompt('Multiline input: ', multiline=True)
    print('You said: %s' % answer)
