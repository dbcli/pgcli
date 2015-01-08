#!/usr/bin/env python
from __future__ import unicode_literals
from __future__ import print_function

import os
import traceback
import logging

import click

from prompt_toolkit import CommandLineInterface, AbortAction, Exit
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_bindings.emacs import emacs_bindings
from pygments.lexers.sql import SqlLexer

from .packages.tabulate import tabulate
from .packages.pgspecial import (CASE_SENSITIVE_COMMANDS,
        NON_CASE_SENSITIVE_COMMANDS)
from .pgcompleter import PGCompleter
from .pgtoolbar import PGToolbar
from .pgstyle import PGStyle
from .pgexecute import PGExecute
from .pgline import PGLine
from .config import write_default_config, load_config
from .key_bindings import pgcli_bindings

_logger = logging.getLogger(__name__)

@click.command()
@click.option('-h', '--host', default='', help='Host address of the '
        'postgres database.')
@click.option('-p', '--port', default=5432, help='Port number at which the '
        'postgres instance is listening.')
@click.option('-U', '--user', prompt=True, envvar='USER', help='User name to '
        'connect to the postgres database.')
@click.option('-W', '--password', is_flag=True, help='Force password prompt.')
@click.argument('database', envvar='USER')
def cli(database, user, password, host, port):
    if password:
        passwd = click.prompt('Password', hide_input=True, show_default=False,
                type=str)
    else:
        passwd = ''

    from pgcli import __file__ as package_root
    package_root = os.path.dirname(package_root)

    default_config = os.path.join(package_root, 'pgclirc')
    write_default_config(default_config, '~/.pgclirc')

    # Load config.
    config = load_config('~/.pgclirc', default_config)
    smart_completion = config.getboolean('main', 'smart_completion')
    multi_line = config.getboolean('main', 'multi_line')
    log_file = config.get('main', 'log_file')
    log_level = config.get('main', 'log_level')

    initialize_logging(log_file, log_level)

    original_less_opts = adjust_less_opts()

    _logger.debug('Launch Params: \n'
            '\tdatabase: %r'
            '\tuser: %r'
            '\tpassword: %r'
            '\thost: %r'
            '\tport: %r', database, user, passwd, host, port)

    # Connect to the database.
    try:
        pgexecute = PGExecute(database, user, passwd, host, port)
    except Exception as e:  # Connecting to a database could fail.
        _logger.debug('Database connection failed: %r.', e)
        click.secho(str(e), err=True, fg='red')
        exit(1)
    layout = Layout(before_input=DefaultPrompt('%s> ' % pgexecute.dbname),
            menus=[CompletionsMenu(max_height=10)],
            lexer=SqlLexer,
            bottom_toolbars=[
                PGToolbar()])
    completer = PGCompleter(smart_completion)
    completer.extend_special_commands(CASE_SENSITIVE_COMMANDS.keys())
    completer.extend_special_commands(NON_CASE_SENSITIVE_COMMANDS.keys())
    refresh_completions(pgexecute, completer)
    line = PGLine(always_multiline=multi_line, completer=completer,
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
            if quit_command(document.text):
                raise Exit
            try:
                _logger.debug('sql: %r', document.text)
                res = pgexecute.run(document.text)

                output = []
                for rows, headers, status in res:
                    _logger.debug("headers: %r", headers)
                    _logger.debug("rows: %r", rows)
                    _logger.debug("status: %r", status)
                    output.extend(format_output(rows, headers, status))
                click.echo_via_pager('\n'.join(output))
            except Exception as e:
                _logger.error("sql: %r, error: %r", document.text, e)
                _logger.error("traceback: %r", traceback.format_exc())
                click.secho(str(e), err=True, fg='red')

            # Refresh the table names and column names if necessary.
            if need_completion_refresh(document.text):
                completer.reset_completions()
                refresh_completions(pgexecute, completer)
    except Exit:
        print ('GoodBye!')
    finally:  # Reset the less opts back to original.
        _logger.debug('Restoring env var LESS to %r.', original_less_opts)
        os.environ['LESS'] = original_less_opts

def format_output(rows, headers, status):
    output = []
    if rows:
        output.append(tabulate(rows, headers, tablefmt='psql'))
    if status:  # Only print the status if it's not None.
        output.append(status)
    return output

def need_completion_refresh(sql):
    try:
        first_token = sql.split()[0]
        return first_token in ('alter', 'create', 'use', '\c', 'drop')
    except Exception:
        return False

def initialize_logging(log_file, log_level):
    level_map = {'CRITICAL': logging.CRITICAL,
                 'ERROR': logging.ERROR,
                 'WARNING': logging.WARNING,
                 'INFO': logging.INFO,
                 'DEBUG': logging.DEBUG
                 }

    handler = logging.FileHandler(os.path.expanduser(log_file))

    formatter = logging.Formatter('%(asctime)s (%(process)d/%(threadName)s) '
              '%(name)s %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    _logger.addHandler(handler)
    _logger.setLevel(level_map[log_level.upper()])

    _logger.debug('Initializing pgcli logging.')
    _logger.debug('Log file "%s".' % log_file)

def adjust_less_opts():
    less_opts = os.environ.get('LESS', '')
    _logger.debug('Original value for LESS env var: %r', less_opts)
    if not less_opts:
        os.environ['LESS'] = '-RXF'

    if 'X' not in less_opts:
        os.environ['LESS'] += 'X'
    if 'F' not in less_opts:
        os.environ['LESS'] += 'F'

    return less_opts

def quit_command(sql):
    return (sql.strip().lower() == 'exit'
            or sql.strip().lower() == 'quit'
            or sql.strip() == '\q'
            or sql.strip() == ':q')

def refresh_completions(pgexecute, completer):
    tables = pgexecute.tables()
    completer.extend_table_names(tables)
    for table in tables:
        completer.extend_column_names(table, pgexecute.columns(table))
    completer.extend_database_names(pgexecute.databases())

if __name__ == "__main__":
    cli()
