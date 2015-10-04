#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit import prompt


if __name__ == '__main__':
    print('This is multiline input. press [Meta+Enter] or [Esc] followed by [Enter] to accept input.')
    print('You can click with the mouse in order to select text.')
    answer = prompt('Multiline input: ', multiline=True, mouse_support=True)
    print('You said: %s' % answer)
