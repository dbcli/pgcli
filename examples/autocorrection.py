#!/usr/bin/env python
"""
Example of implementing auto correction while typing.

The word "impotr" will be corrected when the user types a space afterwards.
"""
from __future__ import unicode_literals
from prompt_toolkit.key_binding.defaults import load_key_bindings_for_prompt
from prompt_toolkit import prompt

# Database of words to be replaced by typing.
corrections = {
    'impotr': 'import',
    'wolrd': 'world',
}


def main():
    # We start with a `Registry` that contains the default key bindings.
    registry = load_key_bindings_for_prompt()

    # We add a custom key binding to space.
    @registry.add_binding(' ')
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
    text = prompt('Say something: ', key_bindings_registry=registry)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
