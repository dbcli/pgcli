#!/usr/bin/env python
"""
Simple example of a layout with a horizontal split.
"""
from __future__ import unicode_literals
from prompt_toolkit import CommandLineInterface
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import Completion, Completer
from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.filters import Always
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.layout import Window, VSplit, HSplit, Float, FloatContainer
from prompt_toolkit.layout.controls import TokenListControl, FillControl, BufferControl
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import AfterInput
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.toolbars import SystemToolbar, ArgToolbar, CompletionsToolbar, SearchToolbar

from pygments.style import Style
from pygments.styles.default import DefaultStyle
from pygments.lexers import PythonLexer
from pygments.token import Token

lipsum = """This is the input:

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer blandit
elementum ante, vel fermentum massa fermentum vitae. Nulla ornare egestas
metus, ut molestie lacus sodales lacinia. Vivamus lacinia, lectus at laoreet
fermentum, quam ligula hendrerit massa, in vulputate velit lacus eu tortor. Sed
mi dui, iaculis nec odio iaculis, iaculis pellentesque velit. Duis consequat,
felis vitae hendrerit accumsan, lectus massa volutpat quam, quis scelerisque ex
urna eu neque. Phasellus vitae pharetra tellus, dapibus viverra lectus. Quisque
ornare risus sit amet auctor convallis. Ut vestibulum tincidunt orci vitae
tincidunt. Quisque ornare consectetur elementum.""".replace('\n', '')


class TestCompleter(Completer):
    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor()

        for i in range(0, 20):
            yield Completion('Completion %i' % i, -len(word_before_cursor))


class TestStyle(Style):
    styles = {
        Token.A: '#000000 bg:#ff0000',
        Token.B: '#000000 bg:#00ff00',
        Token.C: '#000000 bg:#0000ff',
        Token.D: '#000000 bg:#ff00ff',
        Token.E: '#000000 bg:#00ffff',
        Token.F: '#000000 bg:#ffff00',
        Token.HelloWorld: 'bg:#ff00ff',
        Token.Line: 'bg:#000000 #ffffff',

        Token.LineNumber:  'bg:#ffffaa #000000',
        Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
        Token.Menu.Completions.Completion:         'bg:#008888 #ffffff',
        Token.Menu.Completions.ProgressButton:     'bg:#003333',
        Token.Menu.Completions.ProgressBar:        'bg:#00aaaa',

        Token.Toolbar.Completions:  'bg:#888800 #000000',
        Token.Toolbar.Completions.Arrow: 'bg:#888800 #000000',
        Token.Toolbar.Completions.Completion:  'bg:#aaaa00 #000000',
        Token.Toolbar.Completions.Completion.Current:  'bg:#ffffaa #000000 bold',

        Token.Prompt: 'bg:#00ffff #000000',
        Token.AfterInput: 'bg:#ff44ff #000000',

    }
    styles.update(DefaultStyle.styles)


def main():
    manager = KeyBindingManager(enable_system_prompt=True)

    D = LayoutDimension
    layout = HSplit([
        VSplit([
            Window(width=D(min=15, max=30, preferred=30),
                   content=FillControl('a', token=Token.A)),
            Window(width=D.exact(1),
                   content=FillControl('|', token=Token.Line)),
            Window(content=TokenListControl.static([(Token.HelloWorld, lipsum)])),
            Window(width=D.exact(1),
                   content=FillControl('|', token=Token.Line)),
            Window(content=BufferControl(lexer=PythonLexer,
                                         show_line_numbers=Always(),
                                         input_processors=[
                                                DefaultPrompt.from_message('python> '),
                                                AfterInput.static(' <python', token=Token.AfterInput),
                                         ]),
            ),
            Window(width=D.exact(1),
                   content=FillControl('|', token=Token.Line)),
            HSplit([
                Window(width=D(max=40),
                      height=D.exact(4),
                      content=FillControl('b', token=Token.B)),
                Window(width=D(max=40),
                      content=FillControl('f', token=Token.F)),
                Window(width=D.exact(30),
                      height=D.exact(2),
                      content=FillControl('c', token=Token.C)),
            ]),
            #CompletionsMenu(),
        ]),
        Window(height=D.exact(1),
              content=FillControl('-', token=Token.Line)),
        Window(height=D.exact(3),
              content=FillControl('d', token=Token.D)),
        SystemToolbar(),
        ArgToolbar(),
        CompletionsToolbar(),
        SearchToolbar(),
    ])

    layout = FloatContainer(
        content=layout,
        floats=[
            Float(xcursor=True,
                  ycursor=True,
                  content=VSplit([
                      Window(width=D.exact(5),
                             content=FillControl('f', token=Token.F)),
                      CompletionsMenu(),
                  ])
            ),
        ]
    )

    eventloop = create_eventloop()
    cli = CommandLineInterface(eventloop=eventloop,
                               layout=layout,
                               style=TestStyle,
                               key_bindings_registry=manager.registry,
                               buffer=Buffer(is_multiline=Always(), completer=TestCompleter()))
    cli.read_input()
    eventloop.close()


if __name__ == '__main__':
    main()
