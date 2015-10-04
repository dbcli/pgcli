#!/usr/bin/env python
"""
Example of implementing auto correction while typing.

The word "impotr" will be corrected when the user types a space afterwards.
"""
from __future__ import unicode_literals
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit import prompt

# Database of words to be replaced by typing.
corrections = {
    'impotr': 'import',
    'wolrd': 'world',
}


def main():
    # We start with a `KeyBindingManager` instance, because this will already
    # nicely load all the default key bindings.
    key_bindings_manager = KeyBindingManager()

    # We add a custom key binding to space.
    @key_bindings_manager.registry.add_binding(' ')
    def _(event):
        """
        When space is pressed, we check the word before the cursor, and
        autocorrect that.
        """
        b = event.cli.current_buffer
        w = b.document.get_word_before_cursor()

        if w is not None:
            if w in corrections:
                b.delete_before_cursor(count=len(w))
                b.insert_text(corrections[w])

        b.insert_text(' ')

    # Read input.
    text = prompt('Say something: ', key_bindings_registry=key_bindings_manager.registry)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
