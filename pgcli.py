#!/usr/bin/env python
from __future__ import unicode_literals
from __future__ import print_function

import click

from prompt_toolkit import CommandLineInterface, AbortAction, Exit
from pgcompleter import PGCompleter
from pgstyle import PGStyle
from pgexecute import PGExecute
from prompt_toolkit.line import Line
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.menus import CompletionsMenu

from pygments.lexers import SqlLexer

@click.command()
@click.option('-h', '--host', default='localhost')
@click.option('-p', '--port', default=5432)
@click.option('-U', '--user', prompt=True, envvar='USER')
@click.password_option('-P', '--password', default='',
        confirmation_prompt=False)
@click.argument('database', envvar='USER')
def pgcli(database, user, password, host, port):
    print('database: %s host: %s user: %s password: %s' % (database, host, user, password))
    pgexecute = PGExecute(database, user, password, host, port)
    layout = Layout(before_input=DefaultPrompt('%s> ' % database),
            menus=[CompletionsMenu()],
            lexer=SqlLexer)
    line = Line(completer=PGCompleter())
    cli = CommandLineInterface(style=PGStyle, layout=layout, line=line)

    try:
        while True:
            document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
            print (pgexecute.run(document.text))
    except Exit:
        print ('GoodBye!')
