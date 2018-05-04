#!/usr/bin/env python
"""
Eample of using the control-space key binding for auto completion.
"""
from __future__ import unicode_literals

from prompt_toolkit import prompt
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.key_binding import KeyBindings


animal_completer = WordCompleter([
    'alligator', 'ant', 'ape', 'bat', 'bear', 'beaver', 'bee', 'bison',
    'butterfly', 'cat', 'chicken', 'crocodile', 'dinosaur', 'dog', 'dolphin',
    'dove', 'duck', 'eagle', 'elephant', 'fish', 'goat', 'gorilla', 'kangaroo',
    'leopard', 'lion', 'mouse', 'rabbit', 'rat', 'snake', 'spider', 'turkey',
    'turtle',
], ignore_case=True)


kb = KeyBindings()


@kb.add('c-space')
def _(event):
    """
    Start auto completion. If the menu is showing already, select the next
    completion.
    """
    b = event.app.current_buffer
    if b.complete_state:
        b.complete_next()
    else:
        b.start_completion(select_first=False)


def main():
    text = prompt('Give some animals: ', completer=animal_completer,
                  complete_while_typing=False, key_bindings=kb)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
