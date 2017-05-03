#!/usr/bin/env python
"""
A simple application that shows a Pager application.
"""
from __future__ import unicode_literals

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import KeyBindings, merge_key_bindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.lexers import PygmentsLexer
from prompt_toolkit.layout.margins import ScrollbarMargin, NumberredMargin
from prompt_toolkit.styles import Style, merge_styles, default_style

from pygments.lexers import PythonLexer


# Create one text buffer for the main content.

with open('./pager.py', 'rb') as f:
    text = f.read().decode('utf-8')

default_buffer = Buffer(read_only=True, document=Document(text, 0))


def get_statusbar_text(app):
    return [
        ('class:status', './pager.py - '),
        ('class:status.position', '{}:{}'.format(
            default_buffer.document.cursor_position_row + 1,
            default_buffer.document.cursor_position_col + 1)),
        ('class:status', ' - Press Ctrl-C to exit. ')
    ]


buffer_window = Window(
    content=BufferControl(buffer=default_buffer, lexer=PygmentsLexer(PythonLexer)),
    left_margins=[NumberredMargin()],
    right_margins=[ScrollbarMargin()])


root_container = HSplit([
    # The top toolbar.
    Window(content=FormattedTextControl(
        get_statusbar_text),
        height=D.exact(1),
        style='class:status'),

    # The main content.
    buffer_window,

    #SearchToolbar(),
])


# Key bindings.
bindings = KeyBindings()

@bindings.add('c-c')
@bindings.add('q')
def _(event):
    " Quit. "
    event.app.set_return_value(None)


style = merge_styles([
    default_style(),
    Style.from_dict({
        'status': 'bg:#444444 #ffffff',
        'status.position': '#aaaa44',
    })
])

# create application.
application = Application(
    layout=Layout(
        root_container,
        focussed_window=buffer_window,
    ),
    key_bindings=merge_key_bindings([
        load_key_bindings(enable_search=True, enable_extra_page_navigation=True),
        bindings,
    ]),
    mouse_support=True,
    style=style,

    # Using an alternate screen buffer means as much as: "run full screen".
    # It switches the terminal to an alternate screen.
    full_screen=True)


def run():
    application.run()

if __name__ == '__main__':
    run()
