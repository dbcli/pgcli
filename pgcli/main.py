#!/usr/bin/env python
from __future__ import unicode_literals
from __future__ import print_function

import os.path

import click

from prompt_toolkit import CommandLineInterface, AbortAction, Exit
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_bindings.emacs import emacs_bindings
from pygments.lexers.sql import SqlLexer

from .packages.tabulate import tabulate
from .packages.pgspecial import COMMANDS
from .pgcompleter import PGCompleter
from .pgtoolbar import PGToolbar
from .pgstyle import PGStyle
from .pgexecute import PGExecute
from .pgline import PGLine
from .config import write_default_config, load_config
from .key_bindings import pgcli_bindings

@click.command()
@click.option('-h', '--host', default='localhost', help='Host address of the '
        'postgres database.')
@click.option('-p', '--port', default=5432, help='Port number at which the '
        'postgres instance is listening.')
@click.option('-U', '--user', prompt=True, envvar='USER', help='User name to '
        'connect to the postgres database.')
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
    smart_completion = config.getboolean('main', 'smart_completion')

    # Connect to the database.
    try:
        pgexecute = PGExecute(database, user, password, host, port)
    except Exception as e:  # Connecting to a database could fail.
        click.secho(e.message, err=True, fg='red')
        exit(1)
    layout = Layout(before_input=DefaultPrompt('%s> ' % pgexecute.dbname),
            menus=[CompletionsMenu()],
            lexer=SqlLexer,
            bottom_toolbars=[
                PGToolbar()])
    completer = PGCompleter(smart_completion)
    completer.extend_special_commands(COMMANDS.keys())
    completer.extend_table_names(pgexecute.tables())
    completer.extend_column_names(pgexecute.all_columns())
    completer.extend_database_names(pgexecute.databases())
    line = PGLine(completer=completer,
            history=FileHistory(os.path.expanduser('~/.pgcli-history')))
    cli = CommandLineInterface(style=PGStyle, layout=layout, line=line,
            key_binding_factories=[emacs_bindings, pgcli_bindings])

    try:
        while True:
            cli.layout.before_input = DefaultPrompt('%s> ' % pgexecute.dbname)
            document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)

            # The reason we check here instead of inside the pgexecute is
            # because we want to raise the Exit exception which will be caught
            # by the try/except block that wraps the pgexecute.run() statement.
            if (document.text.strip().lower() == 'exit'
                    or document.text.strip().lower() == 'quit'
                    or document.text.strip() == '\q'):
                raise Exit
            try:
                res = pgexecute.run(document.text)
                for rows, headers, status in res:
                    if rows:
                        print(tabulate(rows, headers, tablefmt='psql'))
                    print(status)
            except Exception as e:
                click.secho(e.message, err=True, fg='red')

            # Refresh the table names and column names if necessary.
            if need_completion_refresh(document.text):
                completer.reset_completions()
                completer.extend_table_names(pgexecute.tables())
                completer.extend_column_names(pgexecute.all_columns())
    except Exit:
        print ('GoodBye!')

def need_completion_refresh(sql):
    first_token = sql.split()[0]
    return first_token in ('alter', 'create', 'use', '\c', 'drop')
