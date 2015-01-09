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
from .packages.expanded import expanded_table
from .packages.pgspecial import (CASE_SENSITIVE_COMMANDS,
        NON_CASE_SENSITIVE_COMMANDS, is_expanded_output)
from .pgcompleter import PGCompleter
from .pgtoolbar import PGToolbar
from .pgstyle import PGStyle
from .pgexecute import PGExecute
from .pgline import PGLine
from .config import write_default_config, load_config
from .key_bindings import pgcli_bindings

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
from getpass import getuser
from psycopg2 import OperationalError


class PGCli(object):
    def __init__(self, force_passwd_prompt=False, never_passwd_prompt=False,
                 pgexecute=None):

        self.force_passwd_prompt = force_passwd_prompt
        self.never_passwd_prompt = never_passwd_prompt
        self.pgexecute = pgexecute

        from pgcli import __file__ as package_root
        package_root = os.path.dirname(package_root)

        default_config = os.path.join(package_root, 'pgclirc')
        write_default_config(default_config, '~/.pgclirc')

        # Load config.
        c = self.config = load_config('~/.pgclirc', default_config)
        self.smart_completion = c.getboolean('main', 'smart_completion')
        self.multi_line = c.getboolean('main', 'multi_line')

        self.logger = logging.getLogger(__name__)
        self.initialize_logging()

    def initialize_logging(self):

        log_file = self.config.get('main', 'log_file')
        log_level = self.config.get('main', 'log_level')

        level_map = {'CRITICAL': logging.CRITICAL,
                     'ERROR': logging.ERROR,
                     'WARNING': logging.WARNING,
                     'INFO': logging.INFO,
                     'DEBUG': logging.DEBUG
                     }

        handler = logging.FileHandler(os.path.expanduser(log_file))

        formatter = logging.Formatter(
            '%(asctime)s (%(process)d/%(threadName)s) '
            '%(name)s %(levelname)s - %(message)s')

        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        self.logger.setLevel(level_map[log_level.upper()])

        self.logger.debug('Initializing pgcli logging.')
        self.logger.debug('Log file "%s".' % log_file)

    def connect_uri(self, uri):
        uri = urlparse(uri)
        database = uri.path[1:]  # ignore the leading fwd slash
        self.connect(database, uri.hostname, uri.username,
                     uri.port, uri.password)

    def connect(self, database='', host='', user='', port='', passwd=''):
        # Connect to the database.

        if not database:
            #default to current OS username just like psql
            database = user = getuser()

        # Prompt for a password immediately if requested via the -W flag. This
        # avoids wasting time trying to connect to the database and catching a
        # no-password exception.
        # If we successfully parsed a password from a URI, there's no need to
        # prompt for it, even with the -W flag
        if self.force_passwd_prompt and not passwd:
            passwd = click.prompt('Password', hide_input=True,
                                  show_default=False, type=str)

        # Prompt for a password after 1st attempt to connect without a password
        # fails. Don't prompt if the -w flag is supplied
        auto_passwd_prompt = not passwd and not self.never_passwd_prompt

        # Attempt to connect to the database.
        # Note that passwd may be empty on the first attempt. If connection
        # fails because of a missing password, but we're allowed to prompt for a
        # password (no -w flag), prompt for a passwd and try again.
        try:
            try:
                pgexecute = PGExecute(database, user, passwd, host, port)
            except OperationalError as e:
                if 'no password supplied' in e.message and auto_passwd_prompt:
                    passwd = click.prompt('Password', hide_input=True,
                                          show_default=False, type=str)
                    pgexecute = PGExecute(database, user, passwd, host, port)
                else:
                    raise e

        except Exception as e:  # Connecting to a database could fail.
            self.logger.debug('Database connection failed: %r.', e)
            click.secho(str(e), err=True, fg='red')
            exit(1)

        self.pgexecute = pgexecute

    def run_cli(self):
        pgexecute = self.pgexecute
        prompt = '%s> ' % pgexecute.dbname
        logger = self.logger
        original_less_opts = self.adjust_less_opts()

        layout = Layout(before_input=DefaultPrompt(prompt),
            menus=[CompletionsMenu(max_height=10)],
            lexer=SqlLexer, bottom_toolbars=[PGToolbar()])

        completer = PGCompleter(self.smart_completion)
        completer.extend_special_commands(CASE_SENSITIVE_COMMANDS.keys())
        completer.extend_special_commands(NON_CASE_SENSITIVE_COMMANDS.keys())
        refresh_completions(pgexecute, completer)
        line = PGLine(always_multiline=self.multi_line, completer=completer,
                history=FileHistory(os.path.expanduser('~/.pgcli-history')))
        cli = CommandLineInterface(style=PGStyle, layout=layout, line=line,
                key_binding_factories=[emacs_bindings, pgcli_bindings])

        try:
            while True:
                cli.layout.before_input = DefaultPrompt(prompt)
                document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)

            # The reason we check here instead of inside the pgexecute is
            # because we want to raise the Exit exception which will be caught
            # by the try/except block that wraps the pgexecute.run() statement.
                if quit_command(document.text):
                    raise Exit
                try:
                    logger.debug('sql: %r', document.text)
                    res = pgexecute.run(document.text)
                    output = []
                    for rows, headers, status in res:
                        logger.debug("headers: %r", headers)
                        logger.debug("rows: %r", rows)
                        if rows:
                            if is_expanded_output():
                                output.append(expanded_table(rows, headers))
                            else:
                                output.append(tabulate(rows, headers, tablefmt='psql'))
                        if status:  # Only print the status if it's not None.
                            output.append(status)
                        logger.debug("status: %r", status)
                    click.echo_via_pager('\n'.join(output))
                except Exception as e:
                    logger.error("sql: %r, error: %r", document.text, e)
                    logger.error("traceback: %r", traceback.format_exc())
                    click.secho(str(e), err=True, fg='red')

                # Refresh the table names and column names if necessary.
                if need_completion_refresh(document.text):
                    completer.reset_completions()
                    refresh_completions(pgexecute, completer)
        except Exit:
            print ('GoodBye!')
        finally:  # Reset the less opts back to original.
            logger.debug('Restoring env var LESS to %r.', original_less_opts)
            os.environ['LESS'] = original_less_opts

    def adjust_less_opts(self):
        less_opts = os.environ.get('LESS', '')
        self.logger.debug('Original value for LESS env var: %r', less_opts)
        if not less_opts:
            os.environ['LESS'] = '-RXF'

        if 'X' not in less_opts:
            os.environ['LESS'] += 'X'
        if 'F' not in less_opts:
            os.environ['LESS'] += 'F'

        return less_opts

@click.command()

# Default host is '' so psycopg2 can default to either localhost or unix socket
@click.option('-h', '--host', default='', envvar='PGHOST',
        help='Host address of the postgres database.')
@click.option('-p', '--port', default=5432, help='Port number at which the '
        'postgres instance is listening.', envvar='PGPORT')
@click.option('-U', '--user', envvar='PGUSER', help='User name to '
        'connect to the postgres database.')
@click.option('-W', '--password', 'prompt_passwd', is_flag=True, default=False,
              help='Force password prompt.')
@click.option('-w', '--no-password', 'never_prompt', is_flag=True,
              default=False, help='Never issue a password prompt')
@click.argument('database', default='', envvar='PGDATABASE')
def cli(database, user, host, port, prompt_passwd, never_prompt):

    pgcli = PGCli(prompt_passwd, never_prompt)

    if '://' in database:
        pgcli.connect_uri(database)
    else:
        pgcli.connect(database, host, user, port)

    pgcli.logger.debug('Launch Params: \n'
            '\tdatabase: %r'
            '\tuser: %r'
            '\thost: %r'
            '\tport: %r', database, user, host, port)

    pgcli.run_cli()


def format_output(rows, headers, status):
    output = []
    if rows:
        if is_expanded_output():
            output.append(expanded_table(rows, headers))
        else:
            output.append(tabulate(rows, headers, tablefmt='psql'))
    if status:  # Only print the status if it's not None.
        output.append(status)
    return output

def need_completion_refresh(sql):
    try:
        first_token = sql.split()[0]
        return first_token.lower() in ('alter', 'create', 'use', '\c', 'drop')
    except Exception:
        return False

def quit_command(sql):
    return (sql.strip().lower() == 'exit'
            or sql.strip().lower() == 'quit'
            or sql.strip() == '\q'
            or sql.strip() == ':q')

def refresh_completions(pgexecute, completer):
    tables, columns = pgexecute.tables()
    completer.extend_table_names(tables)
    for table in tables:
        table = table[1:-1] if table[0] == '"' and table[-1] == '"' else table
        completer.extend_column_names(table, columns[table])
    completer.extend_database_names(pgexecute.databases())

if __name__ == "__main__":
    cli()
