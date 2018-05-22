#!/usr/bin/env python
"""
A simple example of a a text area displaying "Hello World!".
"""
from __future__ import unicode_literals
from prompt_toolkit.application import Application
from prompt_toolkit.eventloop import use_asyncio_event_loop
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.widgets import Box, Frame, TextArea
import asyncio

# Layout for displaying hello world.
# (The frame creates the border, the box takes care of the margin/padding.)
root_container = Box(
    Frame(TextArea(
        text='Hello world!\nPress control-c to quit.',
        width=40,
        height=10,
    )),
)
layout = Layout(container=root_container)


# Key bindings.
kb = KeyBindings()

@kb.add('c-c')
def _(event):
    " Quit when control-c is pressed. "
    event.app.exit()


# Build a main application object.
application = Application(
    layout=layout,
    key_bindings=kb,
    full_screen=True)


def main():
    # Tell prompt_toolkit to use asyncio.
    use_asyncio_event_loop()

    # Run application async.
    asyncio.get_event_loop().run_until_complete(
        application.run_async().to_asyncio_future())


if __name__ == '__main__':
    main()
