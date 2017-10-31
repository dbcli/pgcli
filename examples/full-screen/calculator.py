#!/usr/bin/env python
"""
A simple example of a calculator program.
This could be used as inspiration for a REPL.
"""
from __future__ import unicode_literals

from prompt_toolkit.application import Application
from prompt_toolkit.document import Document
from prompt_toolkit.filters import has_focus
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import KeyBindings, merge_key_bindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.widgets import TextArea
from prompt_toolkit.styles import Style

help_text = """
Type any expression (e.g. "4 + 4") followed by enter to execute.
Press Control-C to exit.
"""

def main():
    # The layout.
    output_field = TextArea(style='class:output-field', text=help_text)
    input_field = TextArea(height=1, prompt='>>> ', style='class:input-field')

    container = HSplit([
        output_field,
        Window(height=1, char='-', style='class:line'),
        input_field
    ])

    # The key bindings.
    kb = KeyBindings()

    @kb.add('c-c')
    @kb.add('c-q')
    def _(event):
        " Pressing Ctrl-Q or Ctrl-C will exit the user interface. "
        event.app.set_result(None)

    @kb.add('enter', filter=has_focus(input_field))
    def _(event):
        try:
            output = '\n\nIn:  {}\nOut: {}'.format(
                input_field.text,
                eval(input_field.text))  # Don't do 'eval' in real code!
        except BaseException as e:
            output = '\n\n{}'.format(e)
        new_text = output_field.text + output

        output_field.buffer.document = Document(
            text=new_text, cursor_position=len(new_text))
        input_field.text = ''

    all_bindings = merge_key_bindings([
        load_key_bindings(),  # Start from the basic bindings.
        kb,  # But override it with the following.
    ])

    # Style.
    style = Style([
        ('output-field', 'bg:#000044 #ffffff'),
        ('input-field', 'bg:#000000 #ffffff'),
        ('line',        '#004400'),
    ])

    # Run application.
    application = Application(
        layout=Layout(container, focussed_window=input_field),
        key_bindings=all_bindings,
        style=style,
        mouse_support=True,
        full_screen=True)

    application.run()


if __name__ == '__main__':
    main()
