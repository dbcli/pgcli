#!/usr/bin/env python
from __future__ import unicode_literals
from __future__ import print_function

import os
import traceback
import logging
from time import time

import click
import sqlparse
from prompt_toolkit import CommandLineInterface, AbortAction, Exit
from prompt_toolkit.document import Document
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.history import FileHistory
from pygments.lexers.sql import SqlLexer

from .packages.tabulate import tabulate
from .packages.expanded import expanded_table
from .packages.pgspecial import (CASE_SENSITIVE_COMMANDS,
        NON_CASE_SENSITIVE_COMMANDS, is_expanded_output)
import pgcli.packages.pgspecial as pgspecial
from .pgcompleter import PGCompleter
from .pgtoolbar import PGToolbar
from .pgstyle import style_factory
from .pgexecute import PGExecute
from .pgbuffer import PGBuffer
from .config import write_default_config, load_config
from .key_bindings import pgcli_bindings
from .encodingutils import utf8tounicode


try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
from getpass import getuser
from psycopg2 import OperationalError

from collections import namedtuple

# Query tuples are used for maintaining history
Query = namedtuple('Query', ['query', 'successful', 'mutating'])

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
        self.multi_line = c.getboolean('main', 'multi_line')
        pgspecial.TIMING_ENABLED = c.getboolean('main', 'timing')
        self.table_format = c.get('main', 'table_format')
        self.syntax_style = c.get('main', 'syntax_style')

        self.logger = logging.getLogger(__name__)
        self.initialize_logging()

        self.query_history = []

        # Initialize completer
        smart_completion = c.getboolean('main', 'smart_completion')
        completer = PGCompleter(smart_completion)
        completer.extend_special_commands(CASE_SENSITIVE_COMMANDS.keys())
        completer.extend_special_commands(NON_CASE_SENSITIVE_COMMANDS.keys())
        self.completer = completer

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

        root_logger = logging.getLogger('pgcli')
        root_logger.addHandler(handler)
        root_logger.setLevel(level_map[log_level.upper()])

        root_logger.debug('Initializing pgcli logging.')
        root_logger.debug('Log file %r.', log_file)

    def connect_uri(self, uri):
        uri = urlparse(uri)
        database = uri.path[1:]  # ignore the leading fwd slash
        self.connect(database, uri.hostname, uri.username,
                     uri.port, uri.password)

    def connect(self, database='', host='', user='', port='', passwd=''):
        # Connect to the database.

        if not database:
            if user:
                database = user
            else:
                # default to current OS username just like psql
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
        # fails because of a missing password, but we're allowed to prompt for
        # a password (no -w flag), prompt for a passwd and try again.
        try:
            try:
                pgexecute = PGExecute(database, user, passwd, host, port)
            except OperationalError as e:
                if ('no password supplied' in utf8tounicode(e.args[0]) and
                        auto_passwd_prompt):
                    passwd = click.prompt('Password', hide_input=True,
                                          show_default=False, type=str)
                    pgexecute = PGExecute(database, user, passwd, host, port)
                else:
                    raise e

        except Exception as e:  # Connecting to a database could fail.
            self.logger.debug('Database connection failed: %r.', e)
            self.logger.error("traceback: %r", traceback.format_exc())
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

        completer = self.completer
        self.refresh_completions()

        buf = PGBuffer(always_multiline=self.multi_line, completer=completer,
                history=FileHistory(os.path.expanduser('~/.pgcli-history')))
        cli = CommandLineInterface(style=style_factory(self.syntax_style),
                layout=layout, buffer=buf,
                key_bindings_registry=pgcli_bindings())

        try:
            while True:
                cli.layout.before_input = DefaultPrompt(prompt)
                document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)

                # The reason we check here instead of inside the pgexecute is
                # because we want to raise the Exit exception which will be
                # caught by the try/except block that wraps the pgexecute.run()
                # statement.
                if quit_command(document.text):
                    raise Exit

                # Keep track of whether or not the query is mutating. In case
                # of a multi-statement query, the overall query is considered
                # mutating if any one of the component statements is mutating
                mutating = False

                try:
                    logger.debug('sql: %r', document.text)
                    successful = False
                    # Initialized to [] because res might never get initialized
                    # if an exception occurs in pgexecute.run(). Which causes
                    # finally clause to fail.
                    res = []
                    start = time()
                    # Run the query.
                    res = pgexecute.run(document.text)
                    duration = time() - start
                    successful = True
                    output = []
                    total = 0
                    for cur, headers, status in res:
                        logger.debug("headers: %r", headers)
                        logger.debug("rows: %r", cur)
                        logger.debug("status: %r", status)
                        start = time()
                        threshold = 1000
                        if (is_select(status) and
                                cur and cur.rowcount > threshold):
                            click.secho('The result set has more than %s rows.'
                                    % threshold, fg='red')
                            if not click.confirm('Do you want to continue?'):
                                click.secho("Aborted!", err=True, fg='red')
                                break
                        output.extend(format_output(cur, headers, status, self.table_format))
                        end = time()
                        total += end - start
                        mutating = mutating or is_mutating(status)

                except KeyboardInterrupt:
                    # Restart connection to the database
                    pgexecute.connect()
                    logger.debug("cancelled query, sql: %r", document.text)
                    click.secho("cancelled query", err=True, fg='red')
                except Exception as e:
                    logger.error("sql: %r, error: %r", document.text, e)
                    logger.error("traceback: %r", traceback.format_exc())
                    click.secho(str(e), err=True, fg='red')
                else:
                    click.echo_via_pager('\n'.join(output))
                    if pgspecial.TIMING_ENABLED:
                        print('Command Time:', duration)
                        print('Format Time:', total)
                finally:
                    for cur, _, _ in res:
                        if hasattr(cur, 'close'):
                            cur.close()

                # Refresh the table names and column names if necessary.
                if need_completion_refresh(document.text):
                    prompt = '%s> ' % pgexecute.dbname
                    self.refresh_completions()

                # Refresh search_path to set default schema.
                if need_search_path_refresh(document.text):
                    logger.debug('Refreshing search path')
                    completer.set_search_path(pgexecute.search_path())
                    logger.debug('Search path: %r', completer.search_path)

                query = Query(document.text, successful, mutating)
                self.query_history.append(query)

        except Exit:
            print ('GoodBye!')
        finally:  # Reset the less opts back to original.
            logger.debug('Restoring env var LESS to %r.', original_less_opts)
            os.environ['LESS'] = original_less_opts

    def adjust_less_opts(self):
        less_opts = os.environ.get('LESS', '')
        self.logger.debug('Original value for LESS env var: %r', less_opts)
        os.environ['LESS'] = '-RXF'

        #if 'X' not in less_opts:
            #os.environ['LESS'] += 'X'
        #if 'F' not in less_opts:
            #os.environ['LESS'] += 'F'

        return less_opts

    def refresh_completions(self):
        completer = self.completer
        completer.reset_completions()

        pgexecute = self.pgexecute

        completer.set_search_path(pgexecute.search_path())
        completer.extend_schemata(pgexecute.schemata())
        completer.extend_tables(pgexecute.tables())
        completer.extend_columns(pgexecute.columns())
        completer.extend_database_names(pgexecute.databases())

    def get_completions(self, text, cursor_positition):
        return self.completer.get_completions(
            Document(text=text, cursor_position=cursor_positition), None)

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
        default=False, help='Never prompt for password.')
@click.option('-d', '--dbname', default='', envvar='PGDATABASE',
        help='database name to connect to.')
@click.argument('database', default=lambda: None, envvar='PGDATABASE', nargs=1)
@click.argument('username', default=lambda: None, envvar='PGUSER', nargs=1)
def cli(database, user, host, port, prompt_passwd, never_prompt, dbname,
        username):
    pgcli = PGCli(prompt_passwd, never_prompt)

    # Choose which ever one has a valid value.
    database = database or dbname
    user = username or user

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

def format_output(cur, headers, status, table_format):
    output = []
    if cur:
        headers = [utf8tounicode(x) for x in headers]
        if is_expanded_output():
            output.append(expanded_table(cur, headers))
        else:
            output.append(tabulate(cur, headers, tablefmt=table_format))
    if status:  # Only print the status if it's not None.
        output.append(status)
    return output

def need_completion_refresh(queries):
    """Determines if the completion needs a refresh by checking if the sql
    statement is an alter, create, drop or change db."""
    for query in sqlparse.split(queries):
        try:
            first_token = query.split()[0]
            return first_token.lower() in ('alter', 'create', 'use', '\c',
                    'drop')
        except Exception:
            return False

def need_search_path_refresh(sql):
    """Determines if the search_path should be refreshed by checking if the
    sql has 'set search_path'."""
    return 'set search_path' in sql.lower()

def is_mutating(status):
    """Determines if the statement is mutating based on the status."""
    if not status:
        return False

    mutating = set(['insert', 'update', 'delete', 'alter', 'create', 'drop'])
    return status.split(None, 1)[0].lower() in mutating

def is_select(status):
    """Returns true if the first word in status is 'select'."""
    if not status:
        return False
    return status.split(None, 1)[0].lower() == 'select'

def quit_command(sql):
    return (sql.strip().lower() == 'exit'
            or sql.strip().lower() == 'quit'
            or sql.strip() == '\q'
            or sql.strip() == ':q')

if __name__ == "__main__":
    cli()
