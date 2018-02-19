#!/usr/bin/env python
"""
Example that displays how to switch between Emacs and Vi input mode.

"""
from prompt_toolkit import prompt
from prompt_toolkit.application.current import get_app
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding import KeyBindings


def run():
    # Create a `KeyBindings` that contains the default key bindings.
    bindings = KeyBindings()

    # Add an additional key binding for toggling this flag.
    @bindings.add('f4')
    def _(event):
        " Toggle between Emacs and Vi mode. "
        if event.app.editing_mode == EditingMode.VI:
            event.app.editing_mode = EditingMode.EMACS
        else:
            event.app.editing_mode = EditingMode.VI

    def bottom_toolbar():
        " Display the current input mode. "
        if get_app().editing_mode == EditingMode.VI:
            return ' [F4] Vi '
        else:
            return ' [F4] Emacs '

    prompt('> ', key_bindings=bindings, bottom_toolbar=bottom_toolbar)


if __name__ == '__main__':
    run()
