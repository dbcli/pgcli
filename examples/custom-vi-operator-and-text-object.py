#!/usr/bin/env python
"""
Example of adding a custom Vi operator and text object.
(Note that this API is not guaranteed to remain stable.)
"""
from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.key_binding.defaults import load_key_bindings_for_prompt
from prompt_toolkit.key_binding.bindings.vi import create_operator_decorator, create_text_object_decorator, TextObject
from prompt_toolkit.enums import EditingMode


def main():
    # We start with a `Registry` of default key bindings.
    registry = load_key_bindings_for_prompt()

    # Create the decorators to be used for registering text objects and
    # operators in this registry.
    operator = create_operator_decorator(registry)
    text_object = create_text_object_decorator(registry)

    # Create a custom operator.

    @operator('R')
    def _(event, text_object):
        " Custom operator that reverses text. "
        buff = event.current_buffer

        # Get relative start/end coordinates.
        start, end = text_object.operator_range(buff.document)
        start += buff.cursor_position
        end += buff.cursor_position

        text = buff.text[start:end]
        text = ''.join(reversed(text))

        event.cli.current_buffer.text = buff.text[:start] + text + buff.text[end:]

    # Create a text object.

    @text_object('A')
    def _(event):
        " A custom text object that involves everything. "
        # Note that a `TextObject` has coordinatens, relative to the cursor position.
        buff = event.current_buffer
        return TextObject(
                -buff.document.cursor_position,  # The start.
                len(buff.text) - buff.document.cursor_position)  # The end.

    # Read input.
    print('There is a custom text object "A" that applies to everything')
    print('and a custom operator "r" that reverses the text object.\n')

    print('Things that are possible:')
    print('-  Riw    - reverse inner word.')
    print('-  yA     - yank everything.')
    print('-  RA     - reverse everything.')

    text = prompt('> ', default='hello world', key_bindings_registry=registry, editing_mode=EditingMode.VI)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
