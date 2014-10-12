#!/usr/bin/env python
from __future__ import unicode_literals

from prompt_toolkit import CommandLineInterface
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.line import Line
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.menus import CompletionMenu

from pygments.token import Token
from pygments.style import Style
from pygments.lexers.sql import SqlLexer


class SqlCompleter(Completer):
    keywords = [
        'SELECT',
        'INSERT',
        'ALTER',
        'DROP',
        'DELETE',
        'FROM',
        'WHERE',
    ]

    def get_completions(self, document):
        word_before_cursor = document.get_word_before_cursor()

        for keyword in self.keywords:
            if (keyword.startswith(word_before_cursor) or
                    keyword.startswith(word_before_cursor.upper())):
                yield Completion(keyword, -len(word_before_cursor))


class SyntaxStyle(Style):
    styles = {
        Token.CompletionMenu.Completion.Current: 'bg:#00aaaa #000000',
        Token.CompletionMenu.Completion:         'bg:#008888 #ffffff',
        Token.CompletionMenu.ProgressButton:     'bg:#003333',
        Token.CompletionMenu.ProgressBar:        'bg:#00aaaa',
        Token.SelectedText:            '#ffffff bg:#6666aa',
        Token.IncrementalSearchMatch:         '#ffffff bg:#4444aa',
        Token.IncrementalSearchMatch.Current: '#ffffff bg:#44aa44',
    }


def main():
    cli = CommandLineInterface(style=SyntaxStyle,
            layout=Layout(before_input=DefaultPrompt('> '),
                menus=[CompletionMenu()],
                lexer=SqlLexer),
            line=Line(completer=SqlCompleter())
            )

    print('Press tab to complete')
    code_obj = cli.read_input()
    print('You said: ' + code_obj.text)


if __name__ == '__main__':
    main()
