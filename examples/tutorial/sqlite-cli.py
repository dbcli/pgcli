#!/usr/bin/env python
import sys
import sqlite3

from prompt_toolkit import CommandLineInterface, AbortAction, Exit
from prompt_toolkit.layout import Layout
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.completion import Completion, Completer

from pygments.lexers import SqlLexer
from pygments.style import Style
from pygments.token import Token
from pygments.styles.default import DefaultStyle


class SqlCompleter(Completer):
    keywords = ['create', 'select', 'insert', 'drop',
                'delete', 'from', 'where', 'table']

    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor()

        for keyword in self.keywords:
            if keyword.startswith(word_before_cursor):
                yield Completion(keyword, -len(word_before_cursor))


class DocumentStyle(Style):
    styles = {
        Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
        Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
        Token.Menu.Completions.ProgressButton: 'bg:#003333',
        Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
    }
    styles.update(DefaultStyle.styles)


def main(database):
    connection = sqlite3.connect(database)
    layout = Layout(before_input=DefaultPrompt('> '),
                    lexer=SqlLexer, menus=[CompletionsMenu()])
    buffer = Buffer(completer=SqlCompleter())
    cli = CommandLineInterface(style=DocumentStyle, layout=layout, buffer=buffer)
    try:
        while True:
            document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
            with connection:
                messages = connection.execute(document.text)
                for message in messages:
                    print message
    except Exit:
        print 'GoodBye!'


if __name__ == '__main__':
    if len(sys.argv) < 2:
        db = ':memory:'
    else:
        db = sys.argv[1]

    main(db)
