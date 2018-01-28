#!/usr/bin/env python
"""
A simple application that shows a Pager application.
"""
from __future__ import unicode_literals

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea, SearchField

from pygments.lexers import PythonLexer


# Create one text buffer for the main content.

with open('./pager.py', 'rb') as f:
    text = f.read().decode('utf-8')


def get_statusbar_text():
    return [
        ('class:status', './pager.py - '),
        ('class:status.position', '{}:{}'.format(
            text_area.document.cursor_position_row + 1,
            text_area.document.cursor_position_col + 1)),
        ('class:status', ' - Press '),
        ('class:status.key', 'Ctrl-C'),
        ('class:status', ' to exit, '),
        ('class:status.key', '/'),
        ('class:status', ' for searching.'),
    ]


search_field = SearchField(text_if_not_searching=[
    ('class:not-searching', "Press '/' to start searching.")])


text_area = TextArea(
    text=text,
    read_only=True,
    scrollbar=True,
    line_numbers=True,
    search_field=search_field,
    lexer=PygmentsLexer(PythonLexer))


root_container = HSplit([
    # The top toolbar.
    Window(content=FormattedTextControl(
        get_statusbar_text),
        height=D.exact(1),
        style='class:status'),

    # The main content.
    text_area,
    search_field,
])


# Key bindings.
bindings = KeyBindings()


@bindings.add('c-c')
@bindings.add('q')
def _(event):
    " Quit. "
    event.app.set_result(None)


style = Style.from_dict({
    'status': 'reverse',
    'status.position': '#aaaa00',
    'status.key': '#ffaa00',
    'not-searching': '#888888',
})


# create application.
application = Application(
    layout=Layout(
        root_container,
        focused_element=text_area,
    ),
    key_bindings=bindings,
    enable_page_navigation_bindings=True,
    mouse_support=True,
    style=style,
    full_screen=True)


def run():
    application.run()


if __name__ == '__main__':
    run()
