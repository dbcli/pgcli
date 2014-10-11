from __future__ import unicode_literals
from prompt_toolkit.keys import Keys


def custom_pdb_key_bindings(registry, cli_ref):
    """
    Custom key bindings.
    """
    line = cli_ref().line
    handle = registry.add_binding

    def return_text(text):
        line.text = text
        line.cursor_position = len(text)
        cli_ref().set_return_value(line.document)

    @handle(Keys.F6)
    def _(event):
        # TODO: Open REPL
        pass

    @handle(Keys.F7)
    def _(event):
        return_text('step')

    @handle(Keys.F8)
    def _(event):
        return_text('next')

    @handle(Keys.F9)
    def _(event):
        return_text('continue')
