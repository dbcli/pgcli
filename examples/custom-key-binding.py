#!/usr/bin/env python
"""
Example of adding a custom key binding to a prompt.
"""
from prompt_toolkit import CommandLineInterface
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys


def main():
    # We start with a `KeyBindingManager` instance, because this will already
    # nicely load all the default key bindings.
    key_bindings_manager = KeyBindingManager()

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

    # Create a CLI with the key bindings registry of this manager.
    cli = CommandLineInterface(key_bindings_registry=key_bindings_manager.registry)

    # Read input.
    print('Press F4 to insert "hello world", type "xy" to insert "z":')
    code_obj = cli.read_input()
    print('You said: ' + code_obj.text)


if __name__ == '__main__':
    main()
