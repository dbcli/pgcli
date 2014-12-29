from __future__ import unicode_literals
from prompt_toolkit.keys import Keys


def load_custom_pdb_key_bindings(registry):
    """
    Custom key bindings.
    """
    handle = registry.add_binding

    def return_text(event, text):
        buffer = event.cli.buffers['default']  # XXX: only if the current buffer is a Python buffer.
        buffer.text = text
        buffer.cursor_position = len(text)
        event.cli.set_return_value(buffer.document)

    @handle(Keys.F8)
    def _(event):
        return_text(event, 'step')

    @handle(Keys.F9)
    def _(event):
        return_text(event, 'next')

    @handle(Keys.F10)
    def _(event):
        return_text(event, 'continue')
