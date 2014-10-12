#!/usr/bin/env python
from __future__ import unicode_literals
import sys

import click
import psycopg2

from prompt_toolkit import CommandLineInterface, AbortAction, Exit
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.line import Line
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.menus import CompletionMenu

from pygments.token import Token
from pygments.style import Style
from pygments.lexers.sql import SqlLexer
from pygments.styles.default import DefaultStyle


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


class DocumentStyle(Style):
    styles = {
            Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
            Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
            Token.Menu.Completions.ProgressButton: 'bg:#003333',
            Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
            Token.SelectedText: '#ffffff bg:#6666aa',
            Token.IncrementalSearchMatch: '#ffffff bg:#4444aa',
            Token.IncrementalSearchMatch.Current: '#ffffff bg:#44aa44',
            }
    styles.update(DefaultStyle.styles)


@click.command()
def pgcli():
    layout = Layout(before_input=DefaultPrompt('> '),
            menus=[CompletionMenu()],
            lexer=SqlLexer)
    line = Line(completer=SqlCompleter())
    cli = CommandLineInterface(style=DocumentStyle, layout=layout, line=line)

    try:
        while True:
            document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
            print 'You entered:', document.text
    except Exit:
        print 'GoodBye!'


