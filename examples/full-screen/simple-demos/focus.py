#!/usr/bin/env python
"""
Demonstration of how to programatically focus a certain widget.
"""
from __future__ import unicode_literals

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import VSplit, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document


# 1. The layout
top_text = (
    "Focus example.\n"
    "[q] Quit [a] Focus left top [b] Right top [c] Left bottom [d] Right bottom."
)

LIPSUM = """Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Maecenas quis interdum enim. Nam viverra, mauris et blandit malesuada, ante est
bibendum mauris, ac dignissim dui tellus quis ligula. Aenean condimentum leo at
dignissim placerat. In vel dictum ex, vulputate accumsan mi. Donec ut quam
placerat massa tempor elementum. Sed tristique mauris ac suscipit euismod. Ut
tempus vehicula augue non venenatis. Mauris aliquam velit turpis, nec congue
risus aliquam sit amet. Pellentesque blandit scelerisque felis, faucibus
consequat ante. Curabitur tempor tortor a imperdiet tincidunt. Nam sed justo
sit amet odio bibendum congue. Quisque varius ligula nec ligula gravida, sed
convallis augue faucibus. Nunc ornare pharetra bibendum. Praesent blandit ex
quis sodales maximus. """


left_top = Window(BufferControl(Buffer(document=Document(LIPSUM))))
left_bottom = Window(BufferControl(Buffer(document=Document(LIPSUM))))
right_top = Window(BufferControl(Buffer(document=Document(LIPSUM))))
right_bottom = Window(BufferControl(Buffer(document=Document(LIPSUM))))


body = HSplit([
    Window(FormattedTextControl(top_text), height=2, style='reverse'),
    Window(height=1, char='-'),  # Horizontal line in the middle.
    VSplit([
        left_top,
        Window(width=1, char='|'),
        right_top
    ]),
    Window(height=1, char='-'),  # Horizontal line in the middle.
    VSplit([
        left_bottom,
        Window(width=1, char='|'),
        right_bottom
    ]),
])


# 2. Key bindings
kb = KeyBindings()


@kb.add('q')
def _(event):
    " Quit application. "
    event.app.set_result(None)


@kb.add('a')
def _(event):
    event.app.layout.focus(left_top)


@kb.add('b')
def _(event):
    event.app.layout.focus(right_top)


@kb.add('c')
def _(event):
    event.app.layout.focus(left_bottom)


@kb.add('d')
def _(event):
    event.app.layout.focus(right_bottom)


@kb.add('tab')
def _(event):
    event.app.layout.focus_next()


@kb.add('s-tab')
def _(event):
    event.app.layout.focus_previous()


# 3. The `Application`
application = Application(
    layout=Layout(body),
    key_bindings=kb,
    full_screen=True)


def run():
    application.run()


if __name__ == '__main__':
    run()
