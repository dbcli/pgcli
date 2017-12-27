#!/usr/bin/env python
"""
Example of Window margins.

This is mainly used for displaying line numbers and scroll bars, but it could
be used to display any other kind of information as well.
"""
from __future__ import unicode_literals

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.margins import NumberredMargin, ScrollbarMargin


LIPSUM = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit.  Maecenas
quis interdum enim. Nam viverra, mauris et blandit malesuada, ante est bibendum
mauris, ac dignissim dui tellus quis ligula. Aenean condimentum leo at
dignissim placerat. In vel dictum ex, vulputate accumsan mi. Donec ut quam
placerat massa tempor elementum. Sed tristique mauris ac suscipit euismod. Ut
tempus vehicula augue non venenatis. Mauris aliquam velit turpis, nec congue
risus aliquam sit amet. Pellentesque blandit scelerisque felis, faucibus
consequat ante. Curabitur tempor tortor a imperdiet tincidunt. Nam sed justo
sit amet odio bibendum congue. Quisque varius ligula nec ligula gravida, sed
convallis augue faucibus. Nunc ornare pharetra bibendum. Praesent blandit ex
quis sodales maximus.""" * 40

# Create text buffers. The margins will update if you scroll up or down.

buff = Buffer()
buff.text = LIPSUM

# 1. The layout
body = HSplit([
    Window(FormattedTextControl('Press "q" to quit.'), height=1, style='reverse'),
    Window(
        BufferControl(buffer=buff),

        # Add margins.
        left_margins=[NumberredMargin(), ScrollbarMargin()],
        right_margins=[ScrollbarMargin(), ScrollbarMargin()],
    ),
])


# 2. Key bindings
kb = KeyBindings()


@kb.add('q')
@kb.add('c-c')
def _(event):
    " Quit application. "
    event.app.set_result(None)


# 3. The `Application`
application = Application(
    layout=Layout(body),
    key_bindings=kb,
    full_screen=True)


def run():
    application.run()


if __name__ == '__main__':
    run()
