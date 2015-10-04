#!/usr/bin/env python
"""
Example of adding a custom key binding to a prompt.
"""
from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys


def main():
    # We start with a `KeyBindingManager` instance, because this will already
    # nicely load all the default key bindings.
    key_bindings_manager = KeyBindingManager.for_prompt()

    # Add our own key binding to the registry of the key bindings manager.
    @key_bindings_manager.registry.add_binding(Keys.F4)
    def _(event):
        """
        When F4 has been pressed. Insert "hello world" as text.
        """
        event.cli.current_buffer.insert_text('hello world')

    @key_bindings_manager.registry.add_binding('x', 'y')
    def _(event):
        """
        (Useless, but for demoing.)
        Typing 'xy' will insert 'z'.

        Note that when you type for instance 'xa', the insertion of 'x' is
        postponed until the 'a' is typed. because we don't know earlier whether
        or not a 'y' will follow.
        """
        event.cli.current_buffer.insert_text('z')

    @key_bindings_manager.registry.add_binding(Keys.ControlT)
    def _(event):
        """
        Print 'hello world' in the terminal when ControlT is pressed.

        We use ``run_in_terminal``, because that ensures that the prompt is
        hidden right before ``print_hello`` gets executed and it's drawn again
        after it. (Otherwise this would destroy the output.)
        """
        def print_hello():
            print('hello world')
        event.cli.run_in_terminal(print_hello)


    # Read input.
    print('Press F4 to insert "hello world", type "xy" to insert "z":')
    text = prompt('> ', key_bindings_registry=key_bindings_manager.registry)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
