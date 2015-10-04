#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.filters import Always


if __name__ == '__main__':
    print('If you press meta-! or esc-! at the following prompt, you can enter system commands.')
    answer = prompt('Give me some input: ', enable_system_bindings=Always())
    print('You said: %s' % answer)
