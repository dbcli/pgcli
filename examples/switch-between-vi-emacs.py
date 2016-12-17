#!/usr/bin/env python
"""
Example that displays how to switch between Emacs and Vi input mode.

"""
from prompt_toolkit import prompt
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding.defaults import load_key_bindings_for_prompt
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token

def run():
    # Create a `Registry` that contains the default key bindings.
    registry = load_key_bindings_for_prompt()

    # Add an additional key binding for toggling this flag.
    @registry.add_binding(Keys.F4)
    def _(event):
        " Toggle between Emacs and Vi mode. "
        if event.cli.editing_mode == EditingMode.VI:
            event.cli.editing_mode = EditingMode.EMACS
        else:
            event.cli.editing_mode = EditingMode.VI

    # Add a bottom toolbar to display the status.
    style = style_from_dict({
        Token.Toolbar: 'reverse',
    })

    def get_bottom_toolbar_tokens(cli):
        " Display the current input mode. "
        text = 'Vi' if cli.editing_mode == EditingMode.VI else 'Emacs'
        return [
            (Token.Toolbar, ' [F4] %s ' % text)
        ]

    prompt('> ', key_bindings_registry=registry,
           get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
           style=style)


if __name__ == '__main__':
    run()
