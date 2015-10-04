#!/usr/bin/env python
"""
get_password function that displays asterisks instead of the actual characters.
With the addition of a ControlT shortcut to hide/show the input.
"""
from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys
from prompt_toolkit.filters import Condition


def main():
    hidden = [True] # Nonlocal
    key_bindings_manager = KeyBindingManager()

    @key_bindings_manager.registry.add_binding(Keys.ControlT)
    def _(event):
        ' When ControlT has been pressed, toggle visibility. '
        hidden[0] = not hidden[0]


    print('Type Control-T to toggle password visible.')
    password = prompt('Password: ',
                      is_password=Condition(lambda cli: hidden[0]),
                      key_bindings_registry=key_bindings_manager.registry)
    print('You said: %s' % password)


if __name__ == '__main__':
    main()
