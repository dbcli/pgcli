#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit import prompt


if __name__ == '__main__':
    # System prompt.
    print('(1/3) If you press meta-! or esc-! at the following prompt, you can enter system commands.')
    answer = prompt('Give me some input: ', enable_system_prompt=True)
    print('You said: %s' % answer)

    # Enable suspend.
    print('(2/3) If you press Control-Z, the application will suspend.')
    answer = prompt('Give me some input: ', enable_suspend=True)
    print('You said: %s' % answer)

    # Enable open_in_editor
    print('(3/3) If you press Control-X Control-E, the prompt will open in $EDITOR.')
    answer = prompt('Give me some input: ', enable_open_in_editor=True)
    print('You said: %s' % answer)
