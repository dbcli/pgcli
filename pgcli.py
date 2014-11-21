#!/usr/bin/env python
from __future__ import unicode_literals
from __future__ import print_function

import click
import psycopg2

from prompt_toolkit import CommandLineInterface, AbortAction, Exit
from pgcompleter import PGCompleter
from pgstyle import PGStyle
from prompt_toolkit.line import Line
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.menus import CompletionsMenu

from pygments.lexers import SqlLexer

@click.command()
@click.option('-h', '--host', default='localhost')
@click.option('-U', '--user', prompt=True, envvar='USER')
@click.password_option('-P', '--password', default='',
        confirmation_prompt=False)
@click.argument('database', envvar='USER')
def pgcli(database, host, user, password):
    print('database: %s host: %s user: %s password: %s' % (database, host, user, password))
    layout = Layout(before_input=DefaultPrompt('> '),
            menus=[CompletionsMenu()],
            lexer=SqlLexer)
    line = Line(completer=PGCompleter())
    cli = CommandLineInterface(style=PGStyle, layout=layout, line=line)

    try:
        while True:
            document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
            print ('You entered:', document.text)
    except Exit:
        print ('GoodBye!')
