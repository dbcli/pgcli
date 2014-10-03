#!/usr/bin/env python
"""
Simple example of the layout options.
"""
from __future__ import unicode_literals

from prompt_toolkit import CommandLineInterface
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt, Prompt
from prompt_toolkit.layout.margins import LeftMarginWithLineNumbers
from prompt_toolkit.layout.menus import CompletionMenu
from prompt_toolkit.layout.toolbars import TextToolbar, ArgToolbar, SearchToolbar, CompletionToolbar
from prompt_toolkit.line import Line
from prompt_toolkit.completion import Completion, Completer

from pygments.token import Token
from pygments.style import Style


lipsum = """This is the input:

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer blandit
elementum ante, vel fermentum massa fermentum vitae. Nulla ornare egestas
metus, ut molestie lacus sodales lacinia. Vivamus lacinia, lectus at laoreet
fermentum, quam ligula hendrerit massa, in vulputate velit lacus eu tortor. Sed
mi dui, iaculis nec odio iaculis, iaculis pellentesque velit. Duis consequat,
felis vitae hendrerit accumsan, lectus massa volutpat quam, quis scelerisque ex
urna eu neque. Phasellus vitae pharetra tellus, dapibus viverra lectus. Quisque
ornare risus sit amet auctor convallis. Ut vestibulum tincidunt orci vitae
tincidunt. Quisque ornare consectetur elementum."""


class TestCompleter(Completer):
    def get_completions(self, document):
        word_before_cursor = document.get_word_before_cursor()

        for i in range(0, 20):
            yield Completion('Completion %i' % i, -len(word_before_cursor))


class TestStyle(Style):
    styles = {
        Token.Layout.LeftMargin: 'bg:#00aaaa #000000',
        Token.Prompt.BeforeInput: 'bg:#aa2266 #ffffff',
        Token.AfterInput:         'bg:#aa2266 #ffffff',
        Token.BottomToolbar1: 'bg:#440044 #ffffff',
        Token.BottomToolbar2: 'bg:#aa0088 #222222',
        Token.TopToolbar1: 'bg:#aa0088 #222222',
        Token.TopToolbar2: 'bg:#440044 #ffffff',

        Token.Layout.Toolbar.Arg: 'bg:#aaaaff #000088',
        Token.Layout.Toolbar.Arg.Text: 'bg:#aaaaff #000088 bold',

        Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
        Token.Menu.Completions.Completion:         'bg:#008888 #ffffff',
        Token.Menu.Completions.ProgressButton:     'bg:#003333',
        Token.Menu.Completions.ProgressBar:        'bg:#00aaaa',

        Token.Toolbar.Completions:  'bg:#888800 #000000',
        Token.Toolbar.Completions.Arrow: 'bg:#888800 #000000',
        Token.Toolbar.Completions.Completion:  'bg:#aaaa00 #000000',
        Token.Toolbar.Completions.Completion.Current:  'bg:#ffffaa #000000 bold',

        Token.SelectedText: 'bg:#000088 #ffffff',
    }


def main():
    layout = Layout(
        left_margin=LeftMarginWithLineNumbers(),
        before_input=DefaultPrompt(text='Before input >> '),
        after_input=Prompt(' << after input'),
        top_toolbars=[
            TextToolbar('This is a top toolbar', token=Token.TopToolbar1),
            TextToolbar('This is another top toolbar', token=Token.TopToolbar2),
        ],
        bottom_toolbars=[
            ArgToolbar(),
            SearchToolbar(),
            CompletionToolbar(),
            TextToolbar('This is a bottom toolbar', token=Token.BottomToolbar1),
            TextToolbar('This is another bottom toolbar', token=Token.BottomToolbar2),
        ],
        show_tildes=True,
        menus=[CompletionMenu()])

    cli = CommandLineInterface(layout=layout,
                               style=TestStyle,
                               line=Line(is_multiline=True, completer=TestCompleter()))

    code_obj = cli.read_input(initial_value=lipsum)
    print('You said: ' + code_obj.text)


if __name__ == '__main__':
    main()
