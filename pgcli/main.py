#!/usr/bin/env python
from __future__ import unicode_literals
from __future__ import print_function

import os.path

import click

from prompt_toolkit import CommandLineInterface, AbortAction, Exit
from .pgcompleter import PGCompleter
from .pgstyle import PGStyle
from .pgexecute import PGExecute
from .config import write_default_config, load_config
from prompt_toolkit.line import Line
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.history import FileHistory

from pygments.lexers.sql import SqlLexer
from tabulate import tabulate

@click.command()
@click.option('-h', '--host', default='localhost')
@click.option('-p', '--port', default=5432)
@click.option('-U', '--user', prompt=True, envvar='USER')
@click.password_option('-W', '--password', default='',
        confirmation_prompt=False)
@click.argument('database', envvar='USER')
def cli(database, user, password, host, port):

    from pgcli import __file__ as package_root
    package_root = os.path.dirname(package_root)

    default_config = os.path.join(package_root, 'pgclirc')
    # Write default config.
    write_default_config(default_config, '~/.pgclirc')

    # Load config.
    config = load_config('~/.pgclirc')

    # Connect to the database.
    try:
        pgexecute = PGExecute(database, user, password, host, port)
    except Exception as e:
        click.secho(e.message, err=True, fg='red')
        exit(1)
    layout = Layout(before_input=DefaultPrompt('%s> ' % database),
            menus=[CompletionsMenu()],
            lexer=SqlLexer)
    completer = PGCompleter(config.getboolean('main', 'smart_completion'))
    completer.extend_special_commands(pgexecute.special_commands.keys())
    completer.extend_table_names(pgexecute.tables())
    completer.extend_column_names(pgexecute.all_columns())
    line = Line(completer=completer,
            history=FileHistory(os.path.expanduser('~/.pgcli-history')))
    cli = CommandLineInterface(style=PGStyle, layout=layout, line=line)

    try:
        while True:
            document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
            try:
                rows, headers, status = pgexecute.run(document.text)
                if rows:
                    print(tabulate(rows, headers, tablefmt='psql'))
                print(status)
            except Exception as e:
                click.secho(e.message, err=True, fg='red')
    except Exit:
        print ('GoodBye!')
