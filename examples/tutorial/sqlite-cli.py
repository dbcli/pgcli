#!/usr/bin/env python
from __future__ import unicode_literals
import sys
import sqlite3

from prompt_toolkit import prompt
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.lexers import PygmentsLexer

from pygments.lexers import SqlLexer

sql_completer = WordCompleter(['create', 'select', 'insert', 'drop',
                               'delete', 'from', 'where', 'table'], ignore_case=True)

style = Style.from_dict({
    'completion-menu.current-completion': 'bg:#00aaaa #000000',
    'completion-menu.completion': 'bg:#008888 #ffffff',
})


def main(database):
    history = InMemoryHistory()
    connection = sqlite3.connect(database)

    while True:
        try:
            text = prompt('> ', lexer=PygmentsLexer(SqlLexer), completer=sql_completer,
                          style=style, history=history)
        except KeyboardInterrupt:
            continue  # Control-C pressed. Try again.
        except EOFError:
            break  # Control-D pressed.

        with connection:
            try:
                messages = connection.execute(text)
            except Exception as e:
                print(repr(e))
            else:
                for message in messages:
                    print(message)
    print('GoodBye!')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        db = ':memory:'
    else:
        db = sys.argv[1]

    main(db)
