#!/usr/bin/env python
"""
get_password function that displays asterisks instead of the actual characters.
With the addition of a ControlT shortcut to hide/show the input.
"""
from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.filters import Condition


def main():
    hidden = [True] # Nonlocal
    bindings = KeyBindings()

    @bindings.add(Keys.ControlT)
    def _(event):
        ' When ControlT has been pressed, toggle visibility. '
        hidden[0] = not hidden[0]


    print('Type Control-T to toggle password visible.')
    password = prompt('Password: ',
                      is_password=Condition(lambda: hidden[0]),
                      extra_key_bindings=bindings)
    print('You said: %s' % password)


if __name__ == '__main__':
    main()
