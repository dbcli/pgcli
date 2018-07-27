from __future__ import unicode_literals
from __future__ import print_function

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='psycopg2')

import os
import re
import sys
import traceback
import logging
import threading
import shutil
import functools
import humanize
import datetime as dt
import itertools
from time import time, sleep
from codecs import open


from cli_helpers.tabular_output import TabularOutputFormatter
from cli_helpers.tabular_output.preprocessors import (align_decimals,
                                                      format_numbers)
import click
try:
    import setproctitle
except ImportError:
    setproctitle = None
from prompt_toolkit import CommandLineInterface, Application, AbortAction
from prompt_toolkit.enums import DEFAULT_BUFFER, EditingMode
from prompt_toolkit.shortcuts import create_prompt_layout, create_eventloop
from prompt_toolkit.buffer import AcceptAction
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Always, HasFocus, IsDone
from prompt_toolkit.layout.lexers import PygmentsLexer
from prompt_toolkit.layout.processors import (ConditionalProcessor,
                                              HighlightMatchingBracketProcessor,
                                              TabsProcessor)
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from pygments.lexers.sql import PostgresLexer
from pygments.token import Token

from pgspecial.main import (PGSpecial, NO_QUERY, PAGER_OFF)
import pgspecial as special
try:
    import keyring
except ImportError:
    keyring = None
from .pgcompleter import PGCompleter
from .pgtoolbar import create_toolbar_tokens_func
from .pgstyle import style_factory, style_factory_output
from .pgexecute import PGExecute
from .pgbuffer import PGBuffer
from .completion_refresher import CompletionRefresher
from .config import (get_casing_file,
    load_config, config_location, ensure_dir_exists, get_config)
from .key_bindings import pgcli_bindings
from .encodingutils import utf8tounicode
from .encodingutils import text_type
from .packages.prompt_utils import confirm_destructive_query
from .__init__ import __version__

click.disable_unicode_literals_warning = True

try:
    from urlparse import urlparse, unquote, parse_qs
except ImportError:
    from urllib.parse import urlparse, unquote, parse_qs

from getpass import getuser
from psycopg2 import OperationalError, InterfaceError
import psycopg2

from collections import namedtuple

from textwrap import dedent

# Query tuples are used for maintaining history
MetaQuery = namedtuple(
    'Query',
    [
        'query',            # The entire text of the command
        'successful',       # True If all subqueries were successful
        'total_time',       # Time elapsed executing the query
        'meta_changed',     # True if any subquery executed create/alter/drop
        'db_changed',       # True if any subquery changed the database
        'path_changed',     # True if any subquery changed the search path
        'mutated',          # True if any subquery executed insert/update/delete
        'is_special',       # True if the query is a special command
    ])
MetaQuery.__new__.__defaults__ = ('', False, 0, False, False, False, False)

OutputSettings = namedtuple(
    'OutputSettings',
    'table_format dcmlfmt floatfmt missingval expanded max_width case_function style_output'
)
OutputSettings.__new__.__defaults__ = (
    None, None, None, '<null>', False, None, lambda x: x, None
)


class PgCliQuitError(Exception):
    pass


class PGCli(object):

    default_prompt = '\\u@\\h:\\d> '
    max_len_prompt = 30

    def set_default_pager(self, config):
        configured_pager = config['main'].get('pager')
        os_environ_pager = os.environ.get('PAGER')

        if configured_pager:
            self.logger.info(
                'Default pager found in config file: "{}"'.format(configured_pager))
            os.environ['PAGER'] = configured_pager
        elif os_environ_pager:
            self.logger.info('Default pager found in PAGER environment variable: "{}"'.format(
                os_environ_pager))
            os.environ['PAGER'] = os_environ_pager
        else:
            self.logger.info(
                'No default pager found in environment. Using os default pager')

        # Set default set of less recommended options, if they are not already set.
        # They are ignored if pager is different than less.
        if not os.environ.get('LESS'):
            os.environ['LESS'] = '-SRXF'

    def __init__(self, force_passwd_prompt=False, never_passwd_prompt=False,
                 pgexecute=None, pgclirc_file=None, row_limit=None,
                 single_connection=False, less_chatty=None, prompt=None, prompt_dsn=None,
                 auto_vertical_output=False, warn=None):

        self.force_passwd_prompt = force_passwd_prompt
        self.never_passwd_prompt = never_passwd_prompt
        self.pgexecute = pgexecute
        self.dsn_alias = None
        self.watch_command = None

        # Load config.
        c = self.config = get_config(pgclirc_file)

        self.logger = logging.getLogger(__name__)
        self.initialize_logging()

        self.set_default_pager(c)
        self.output_file = None
        self.pgspecial = PGSpecial()

        self.multi_line = c['main'].as_bool('multi_line')
        self.multiline_mode = c['main'].get('multi_line_mode', 'psql')
        self.vi_mode = c['main'].as_bool('vi')
        self.auto_expand = auto_vertical_output or c['main'].as_bool(
            'auto_expand')
        self.expanded_output = c['main'].as_bool('expand')
        self.pgspecial.timing_enabled = c['main'].as_bool('timing')
        if row_limit is not None:
            self.row_limit = row_limit
        else:
            self.row_limit = c['main'].as_int('row_limit')

        self.min_num_menu_lines = c['main'].as_int('min_num_menu_lines')
        self.multiline_continuation_char = c['main']['multiline_continuation_char']
        self.table_format = c['main']['table_format']
        self.syntax_style = c['main']['syntax_style']
        self.cli_style = c['colors']
        self.wider_completion_menu = c['main'].as_bool('wider_completion_menu')
        c_dest_warning = c['main'].as_bool('destructive_warning')
        self.destructive_warning = c_dest_warning if warn is None else warn
        self.less_chatty = bool(less_chatty) or c['main'].as_bool('less_chatty')
        self.null_string = c['main'].get('null_string', '<null>')
        self.prompt_format = prompt if prompt is not None else c['main'].get('prompt', self.default_prompt)
        self.prompt_dsn_format = prompt_dsn
        self.on_error = c['main']['on_error'].upper()
        self.decimal_format = c['data_formats']['decimal']
        self.float_format = c['data_formats']['float']
        self.keyring_enabled = c["main"].as_bool("keyring")

        self.pgspecial.pset_pager(self.config['main'].as_bool(
            'enable_pager') and "on" or "off")

        self.style_output = style_factory_output(
            self.syntax_style, c['colors'])

        self.now = dt.datetime.today()

        self.completion_refresher = CompletionRefresher()

        self.query_history = []

        # Initialize completer
        smart_completion = c['main'].as_bool('smart_completion')
        keyword_casing = c['main']['keyword_casing']
        self.settings = {
            'casing_file': get_casing_file(c),
            'generate_casing_file': c['main'].as_bool('generate_casing_file'),
            'generate_aliases': c['main'].as_bool('generate_aliases'),
            'asterisk_column_order': c['main']['asterisk_column_order'],
            'qualify_columns': c['main']['qualify_columns'],
            'case_column_headers': c['main'].as_bool('case_column_headers'),
            'search_path_filter': c['main'].as_bool('search_path_filter'),
            'single_connection': single_connection,
            'less_chatty': less_chatty,
            'keyword_casing': keyword_casing,
        }

        completer = PGCompleter(smart_completion, pgspecial=self.pgspecial,
            settings=self.settings)
        self.completer = completer
        self._completer_lock = threading.Lock()
        self.register_special_commands()

        self.eventloop = create_eventloop()
        self.cli = None

    def quit(self):
        raise PgCliQuitError

    def register_special_commands(self):

        self.pgspecial.register(
            self.change_db, '\\c', '\\c[onnect] database_name',
            'Change to a new database.', aliases=('use', '\\connect', 'USE'))

        refresh_callback = lambda: self.refresh_completions(
            persist_priorities='all')

        self.pgspecial.register(self.quit, '\\q', '\\q',
                                'Quit pgcli.', arg_type=NO_QUERY, case_sensitive=True,
                                aliases=(':q',))
        self.pgspecial.register(self.quit, 'quit', 'quit',
                                'Quit pgcli.', arg_type=NO_QUERY, case_sensitive=False,
                                aliases=('exit',))
        self.pgspecial.register(refresh_callback, '\\#', '\\#',
                                'Refresh auto-completions.', arg_type=NO_QUERY)
        self.pgspecial.register(refresh_callback, '\\refresh', '\\refresh',
                                'Refresh auto-completions.', arg_type=NO_QUERY)
        self.pgspecial.register(self.execute_from_file, '\\i', '\\i filename',
                                'Execute commands from file.')
        self.pgspecial.register(self.write_to_file, '\\o', '\\o [filename]',
                                'Send all query results to file.')
        self.pgspecial.register(self.info_connection, '\\conninfo',
                                '\\conninfo', 'Get connection details')
        self.pgspecial.register(self.change_table_format, '\\T', '\\T [format]',
                                'Change the table format used to output results')

    def change_table_format(self, pattern, **_):
        try:
            if pattern not in TabularOutputFormatter().supported_formats:
                raise ValueError()
            self.table_format = pattern
            yield (None, None, None,
                   'Changed table format to {}'.format(pattern))
        except ValueError:
            msg = 'Table format {} not recognized. Allowed formats:'.format(
                pattern)
            for table_type in TabularOutputFormatter().supported_formats:
                msg += "\n\t{}".format(table_type)
            msg += '\nCurrently set to: %s' % self.table_format
            yield (None, None, None, msg)

    def info_connection(self, **_):
        if self.pgexecute.host.startswith('/'):
            host = 'socket "%s"' % self.pgexecute.host
        else:
            host = 'host "%s"' % self.pgexecute.host

        yield (None, None, None, 'You are connected to database "%s" as user '
               '"%s" on %s at port "%s".' % (self.pgexecute.dbname,
                                             self.pgexecute.user,
                                             host,
                                             self.pgexecute.port))

    def change_db(self, pattern, **_):
        if pattern:
            # Get all the parameters in pattern, handling double quotes if any.
            infos = re.findall(r'"[^"]*"|[^"\'\s]+', pattern)
            # Now removing quotes.
            list(map(lambda s: s.strip('"'), infos))

            infos.extend([None] * (4 - len(infos)))
            db, user, host, port = infos
            try:
                self.pgexecute.connect(database=db, user=user, host=host,
                                       port=port, application_name='pgcli')
            except OperationalError as e:
                click.secho(str(e), err=True, fg='red')
                click.echo("Previous connection kept")
        else:
            self.pgexecute.connect()

        yield (None, None, None, 'You are now connected to database "%s" as '
               'user "%s"' % (self.pgexecute.dbname, self.pgexecute.user))

    def execute_from_file(self, pattern, **_):
        if not pattern:
            message = '\\i: missing required argument'
            return [(None, None, None, message, '', False, True)]
        try:
            with open(os.path.expanduser(pattern), encoding='utf-8') as f:
                query = f.read()
        except IOError as e:
            return [(None, None, None, str(e), '', False, True)]

        if (self.destructive_warning and
                confirm_destructive_query(query) is False):
            message = 'Wise choice. Command execution stopped.'
            return [(None, None, None, message)]

        on_error_resume = (self.on_error == 'RESUME')
        return self.pgexecute.run(
            query, self.pgspecial, on_error_resume=on_error_resume
        )

    def write_to_file(self, pattern, **_):
        if not pattern:
            self.output_file = None
            message = 'File output disabled'
            return [(None, None, None, message, '', True, True)]
        filename = os.path.abspath(os.path.expanduser(pattern))
        if not os.path.isfile(filename):
            try:
                open(filename, 'w').close()
            except IOError as e:
                self.output_file = None
                message = str(e) + '\nFile output disabled'
                return [(None, None, None, message, '', False, True)]
        self.output_file = filename
        message = 'Writing to file "%s"' % self.output_file
        return [(None, None, None, message, '', True, True)]

    def initialize_logging(self):

        log_file = self.config['main']['log_file']
        if log_file == 'default':
            log_file = config_location() + 'log'
        ensure_dir_exists(log_file)
        log_level = self.config['main']['log_level']

        # Disable logging if value is NONE by switching to a no-op handler.
        # Set log level to a high value so it doesn't even waste cycles getting called.
        if log_level.upper() == 'NONE':
            handler = logging.NullHandler()
        else:
            handler = logging.FileHandler(os.path.expanduser(log_file))

        level_map = {'CRITICAL': logging.CRITICAL,
                     'ERROR': logging.ERROR,
                     'WARNING': logging.WARNING,
                     'INFO': logging.INFO,
                     'DEBUG': logging.DEBUG,
                     'NONE': logging.CRITICAL
                     }

        log_level = level_map[log_level.upper()]

        formatter = logging.Formatter(
            '%(asctime)s (%(process)d/%(threadName)s) '
            '%(name)s %(levelname)s - %(message)s')

        handler.setFormatter(formatter)

        root_logger = logging.getLogger('pgcli')
        root_logger.addHandler(handler)
        root_logger.setLevel(log_level)

        root_logger.debug('Initializing pgcli logging.')
        root_logger.debug('Log file %r.', log_file)

        pgspecial_logger = logging.getLogger('pgspecial')
        pgspecial_logger.addHandler(handler)
        pgspecial_logger.setLevel(log_level)

    def connect_dsn(self, dsn):
        self.connect(dsn=dsn)

    def connect_uri(self, uri):
        uri = urlparse(uri)
        database = uri.path[1:]  # ignore the leading fwd slash

        def fixup_possible_percent_encoding(s):
            return unquote(str(s)) if s else s

        arguments = dict(database=fixup_possible_percent_encoding(database),
                         host=fixup_possible_percent_encoding(uri.hostname),
                         user=fixup_possible_percent_encoding(uri.username),
                         port=fixup_possible_percent_encoding(uri.port),
                         passwd=fixup_possible_percent_encoding(uri.password))
        # Deal with extra params e.g. ?sslmode=verify-ca&sslrootcert=/myrootcert
        if uri.query:
            arguments = dict(
                {k: v for k, (v,) in parse_qs(uri.query).items()},
                **arguments)

        # unquote str(each URI part (they may be percent encoded)
        self.connect(**arguments)

    def connect(self, database='', host='', user='', port='', passwd='',
                dsn='', **kwargs):
        # Connect to the database.

        if not user:
            user = getuser()

        if not database:
            database = user

        # If password prompt is not forced but no password is provided, try
        # getting it from environment variable.
        if not self.force_passwd_prompt and not passwd:
            passwd = os.environ.get('PGPASSWORD', '')

        # Find password from store
        key = '%s@%s' % (user, host)
        keyring_error_message = dedent("""\
            {}
            {}
            To remove this message do one of the following:
            - prepare keyring as described at: https://keyring.readthedocs.io/en/stable/
            - uninstall keyring: pip uninstall keyring
            - disable keyring in our configuration: add keyring = False to [main]""")
        if not passwd and keyring and self.keyring_enabled:
            try:
                passwd = keyring.get_password('pgcli', key)
            except (
                RuntimeError,
                keyring.errors.InitError
            ) as e:
                click.secho(
                    keyring_error_message.format(
                        "Load your password from keyring returned:",
                        str(e)
                    ),
                    err=True,
                    fg='red'
                )

        # Prompt for a password immediately if requested via the -W flag. This
        # avoids wasting time trying to connect to the database and catching a
        # no-password exception.
        # If we successfully parsed a password from a URI, there's no need to
        # prompt for it, even with the -W flag
        if self.force_passwd_prompt and not passwd:
            passwd = click.prompt('Password for %s' % user, hide_input=True,
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
                pgexecute = PGExecute(database, user, passwd, host, port, dsn,
                                      application_name='pgcli', **kwargs)
            except (OperationalError, InterfaceError) as e:
                if ('no password supplied' in utf8tounicode(e.args[0]) and
                        auto_passwd_prompt):
                    passwd = click.prompt('Password for %s' % user,
                                          hide_input=True, show_default=False,
                                          type=str)
                    pgexecute = PGExecute(database, user, passwd, host, port,
                                          dsn, application_name='pgcli',
                                          **kwargs)
                else:
                    raise e
            if passwd and keyring and self.keyring_enabled:
                try:
                    keyring.set_password('pgcli', key, passwd)
                except (
                    keyring.errors.InitError,
                    RuntimeError,
                    keyring.errors.KeyringLocked
                ) as e:
                    click.secho(
                        keyring_error_message.format(
                            "Set password in keyring returned:",
                            str(e)
                        ),
                        err=True,
                        fg='red'
                    )

        except Exception as e:  # Connecting to a database could fail.
            self.logger.debug('Database connection failed: %r.', e)
            self.logger.error("traceback: %r", traceback.format_exc())
            click.secho(str(e), err=True, fg='red')
            exit(1)

        self.pgexecute = pgexecute

    def handle_editor_command(self, cli, document):
        r"""
        Editor command is any query that is prefixed or suffixed
        by a '\e'. The reason for a while loop is because a user
        might edit a query multiple times.
        For eg:
        "select * from \e"<enter> to edit it in vim, then come
        back to the prompt with the edited query "select * from
        blah where q = 'abc'\e" to edit it again.
        :param cli: CommandLineInterface
        :param document: Document
        :return: Document
        """
        # FIXME: using application.pre_run_callables like this here is not the best solution.
        # It's internal api of prompt_toolkit that may change. This was added to fix #668.
        # We may find a better way to do it in the future.
        saved_callables = cli.application.pre_run_callables
        try:
            editor_command = special.editor_command(document.text)
            while editor_command:
                if editor_command == '\\e':
                    filename = special.get_filename(document.text)
                    query = (special.get_editor_query(document.text) or
                             self.get_last_query())
                else:  # \ev or \ef
                    filename = None
                    spec = document.text.split()[1]
                    if editor_command == '\\ev':
                        query = self.pgexecute.view_definition(spec)
                    elif editor_command == '\\ef':
                        query = self.pgexecute.function_definition(spec)
                sql, message = special.open_external_editor(
                    filename, sql=query)
                if message:
                    # Something went wrong. Raise an exception and bail.
                    raise RuntimeError(message)
                cli.current_buffer.document = Document(
                    sql, cursor_position=len(sql))
                cli.application.pre_run_callables = []
                document = cli.run()
                editor_command = special.editor_command(document.text)
        finally:
            cli.application.pre_run_callables = saved_callables
        return document

    def execute_command(self, text):
        logger = self.logger

        query = MetaQuery(query=text, successful=False)

        try:
            if (self.destructive_warning):
                destroy = confirm = confirm_destructive_query(text)
                if destroy is False:
                    click.secho('Wise choice!')
                    raise KeyboardInterrupt
                elif destroy:
                    click.secho('Your call!')
            output, query = self._evaluate_command(text)
        except KeyboardInterrupt:
            # Restart connection to the database
            self.pgexecute.connect()
            logger.debug("cancelled query, sql: %r", text)
            click.secho("cancelled query", err=True, fg='red')
        except NotImplementedError:
            click.secho('Not Yet Implemented.', fg="yellow")
        except OperationalError as e:
            logger.error("sql: %r, error: %r", text, e)
            logger.error("traceback: %r", traceback.format_exc())
            self._handle_server_closed_connection()
        except PgCliQuitError as e:
            raise
        except Exception as e:
            logger.error("sql: %r, error: %r", text, e)
            logger.error("traceback: %r", traceback.format_exc())
            click.secho(str(e), err=True, fg='red')
        else:
            try:
                if self.output_file and not text.startswith(('\\o ', '\\? ')):
                    try:
                        with open(self.output_file, 'a', encoding='utf-8') as f:
                            click.echo(text, file=f)
                            click.echo('\n'.join(output), file=f)
                            click.echo('', file=f)  # extra newline
                    except IOError as e:
                        click.secho(str(e), err=True, fg='red')
                else:
                    self.echo_via_pager('\n'.join(output))
            except KeyboardInterrupt:
                pass

            if self.pgspecial.timing_enabled:
                # Only add humanized time display if > 1 second
                if query.total_time > 1:
                    print('Time: %0.03fs (%s)' % (query.total_time,
                          humanize.time.naturaldelta(query.total_time)))
                else:
                    print('Time: %0.03fs' % query.total_time)

            # Check if we need to update completions, in order of most
            # to least drastic changes
            if query.db_changed:
                with self._completer_lock:
                    self.completer.reset_completions()
                self.refresh_completions(persist_priorities='keywords')
            elif query.meta_changed:
                self.refresh_completions(persist_priorities='all')
            elif query.path_changed:
                logger.debug('Refreshing search path')
                with self._completer_lock:
                    self.completer.set_search_path(
                        self.pgexecute.search_path())
                logger.debug('Search path: %r',
                             self.completer.search_path)
        return query

    def run_cli(self):
        logger = self.logger

        history_file = self.config['main']['history_file']
        if history_file == 'default':
            history_file = config_location() + 'history'
        history = FileHistory(os.path.expanduser(history_file))
        self.refresh_completions(history=history,
                                 persist_priorities='none')

        self.cli = self._build_cli(history)

        if not self.less_chatty:
            print('Server: PostgreSQL', self.pgexecute.get_server_version())
            print('Version:', __version__)
            print('Chat: https://gitter.im/dbcli/pgcli')
            print('Mail: https://groups.google.com/forum/#!forum/pgcli')
            print('Home: http://pgcli.com')

        try:
            while True:
                document = self.cli.run()

                try:
                    document = self.handle_editor_command(self.cli, document)
                except RuntimeError as e:
                    logger.error("sql: %r, error: %r", document.text, e)
                    logger.error("traceback: %r", traceback.format_exc())
                    click.secho(str(e), err=True, fg='red')
                    continue

                self.watch_command, timing = special.get_watch_command(
                    document.text)
                if self.watch_command:
                    while self.watch_command:
                        try:
                            query = self.execute_command(self.watch_command)
                            click.echo(
                                'Waiting for {0} seconds before repeating'
                                .format(timing))
                            sleep(timing)
                        except KeyboardInterrupt:
                            self.watch_command = None
                else:
                    query = self.execute_command(document.text)

                self.now = dt.datetime.today()

                # Allow PGCompleter to learn user's preferred keywords, etc.
                with self._completer_lock:
                    self.completer.extend_query_history(document.text)

                self.query_history.append(query)

        except (PgCliQuitError, EOFError):
            if not self.less_chatty:
                print ('Goodbye!')

    def _build_cli(self, history):

        def set_vi_mode(value):
            self.vi_mode = value

        key_binding_manager = pgcli_bindings(
            get_vi_mode_enabled=lambda: self.vi_mode,
            set_vi_mode_enabled=set_vi_mode)

        def prompt_tokens(_):
            if self.dsn_alias and self.prompt_dsn_format is not None:
                prompt_format = self.prompt_dsn_format
            else:
                prompt_format = self.prompt_format

            prompt = self.get_prompt(prompt_format)

            if (prompt_format == self.default_prompt and
                    len(prompt) > self.max_len_prompt):
                prompt = self.get_prompt('\\d> ')

            return [(Token.Prompt, prompt)]

        def get_continuation_tokens(cli, width):
            continuation=self.multiline_continuation_char * (width - 1) + ' '
            return [(Token.Continuation, continuation)]

        get_toolbar_tokens = create_toolbar_tokens_func(
            lambda: self.vi_mode, self.completion_refresher.is_refreshing,
            self.pgexecute.failed_transaction,
            self.pgexecute.valid_transaction)

        layout = create_prompt_layout(
            lexer=PygmentsLexer(PostgresLexer),
            reserve_space_for_menu=self.min_num_menu_lines,
            get_prompt_tokens=prompt_tokens,
            get_continuation_tokens=get_continuation_tokens,
            get_bottom_toolbar_tokens=get_toolbar_tokens,
            display_completions_in_columns=self.wider_completion_menu,
            multiline=True,
            extra_input_processors=[
                # Highlight matching brackets while editing.
                ConditionalProcessor(
                    processor=HighlightMatchingBracketProcessor(
                        chars='[](){}'),
                    filter=HasFocus(DEFAULT_BUFFER) & ~IsDone()),
                # Render \t as 4 spaces instead of "^I"
                TabsProcessor(get_char1=lambda _: ' ',
                              get_char2=lambda _: ' '),
            ])

        with self._completer_lock:
            buf = PGBuffer(
                auto_suggest=AutoSuggestFromHistory(),
                always_multiline=self.multi_line,
                multiline_mode=self.multiline_mode,
                completer=self.completer,
                history=history,
                complete_while_typing=Always(),
                accept_action=AcceptAction.RETURN_DOCUMENT)

            editing_mode = EditingMode.VI if self.vi_mode else EditingMode.EMACS

            application = Application(
                style=style_factory(self.syntax_style, self.cli_style),
                layout=layout,
                buffer=buf,
                key_bindings_registry=key_binding_manager.registry,
                on_exit=AbortAction.RAISE_EXCEPTION,
                on_abort=AbortAction.RETRY,
                ignore_case=True,
                editing_mode=editing_mode)

            cli = CommandLineInterface(application=application,
                                       eventloop=self.eventloop)

            return cli

    def _should_show_limit_prompt(self, status, cur):
        """returns True if limit prompt should be shown, False otherwise."""
        if not is_select(status):
            return False
        return self.row_limit > 0 and cur and cur.rowcount > self.row_limit

    def _evaluate_command(self, text):
        """Used to run a command entered by the user during CLI operation
        (Puts the E in REPL)

        returns (results, MetaQuery)
        """
        logger = self.logger
        logger.debug('sql: %r', text)

        all_success = True
        meta_changed = False  # CREATE, ALTER, DROP, etc
        mutated = False  # INSERT, DELETE, etc
        db_changed = False
        path_changed = False
        output = []
        total = 0

        # Run the query.
        start = time()
        on_error_resume = self.on_error == 'RESUME'
        res = self.pgexecute.run(text, self.pgspecial,
                                 exception_formatter, on_error_resume)

        for title, cur, headers, status, sql, success, is_special in res:
            logger.debug("headers: %r", headers)
            logger.debug("rows: %r", cur)
            logger.debug("status: %r", status)
            threshold = self.row_limit
            if self._should_show_limit_prompt(status, cur):
                click.secho('The result set has more than %s rows.'
                            % threshold, fg='red')
                if not click.confirm('Do you want to continue?'):
                    click.secho("Aborted!", err=True, fg='red')
                    break

            if self.pgspecial.auto_expand or self.auto_expand:
                max_width = self.cli.output.get_size().columns
            else:
                max_width = None

            expanded = self.pgspecial.expanded_output or self.expanded_output
            settings = OutputSettings(
                table_format=self.table_format,
                dcmlfmt=self.decimal_format,
                floatfmt=self.float_format,
                missingval=self.null_string,
                expanded=expanded,
                max_width=max_width,
                case_function=(
                    self.completer.case if self.settings['case_column_headers']
                    else lambda x: x
                ),
                style_output=self.style_output
            )
            formatted = format_output(title, cur, headers, status, settings)

            output.extend(formatted)
            total = time() - start

            # Keep track of whether any of the queries are mutating or changing
            # the database
            if success:
                mutated = mutated or is_mutating(status)
                db_changed = db_changed or has_change_db_cmd(sql)
                meta_changed = meta_changed or has_meta_cmd(sql)
                path_changed = path_changed or has_change_path_cmd(sql)
            else:
                all_success = False

        meta_query = MetaQuery(text, all_success, total, meta_changed,
                               db_changed, path_changed, mutated, is_special)

        return output, meta_query

    def _handle_server_closed_connection(self):
        """Used during CLI execution"""
        reconnect = click.prompt(
            'Connection reset. Reconnect (Y/n)',
            show_default=False, type=bool, default=True)
        if reconnect:
            try:
                self.pgexecute.connect()
                click.secho('Reconnected!\nTry the command again.', fg='green')
            except OperationalError as e:
                click.secho(str(e), err=True, fg='red')

    def refresh_completions(self, history=None, persist_priorities='all'):
        """ Refresh outdated completions

        :param history: A prompt_toolkit.history.FileHistory object. Used to
                        load keyword and identifier preferences

        :param persist_priorities: 'all' or 'keywords'
        """

        callback = functools.partial(self._on_completions_refreshed,
                                     persist_priorities=persist_priorities)
        self.completion_refresher.refresh(self.pgexecute, self.pgspecial,
            callback, history=history, settings=self.settings)
        return [(None, None, None,
                'Auto-completion refresh started in the background.')]

    def _on_completions_refreshed(self, new_completer, persist_priorities):
        self._swap_completer_objects(new_completer, persist_priorities)

        if self.cli:
            # After refreshing, redraw the CLI to clear the statusbar
            # "Refreshing completions..." indicator
            self.cli.request_redraw()

    def _swap_completer_objects(self, new_completer, persist_priorities):
        """Swap the completer object in cli with the newly created completer.

            persist_priorities is a string specifying how the old completer's
            learned prioritizer should be transferred to the new completer.

              'none'     - The new prioritizer is left in a new/clean state

              'all'      - The new prioritizer is updated to exactly reflect
                           the old one

              'keywords' - The new prioritizer is updated with old keyword
                           priorities, but not any other.
        """
        with self._completer_lock:
            old_completer = self.completer
            self.completer = new_completer

            if persist_priorities == 'all':
                # Just swap over the entire prioritizer
                new_completer.prioritizer = old_completer.prioritizer
            elif persist_priorities == 'keywords':
                # Swap over the entire prioritizer, but clear name priorities,
                # leaving learned keyword priorities alone
                new_completer.prioritizer = old_completer.prioritizer
                new_completer.prioritizer.clear_names()
            elif persist_priorities == 'none':
                # Leave the new prioritizer as is
                pass

            # When pgcli is first launched we call refresh_completions before
            # instantiating the cli object. So it is necessary to check if cli
            # exists before trying the replace the completer object in cli.
            if self.cli:
                self.cli.current_buffer.completer = new_completer

    def get_completions(self, text, cursor_positition):
        with self._completer_lock:
            return self.completer.get_completions(
                Document(text=text, cursor_position=cursor_positition), None)

    def get_prompt(self, string):
        # should be before replacing \\d
        string = string.replace('\\dsn_alias', self.dsn_alias or '')
        string = string.replace('\\t', self.now.strftime('%x %X'))
        string = string.replace('\\u', self.pgexecute.user or '(none)')
        host = self.pgexecute.host or '(none)'
        string = string.replace('\\H', host)
        short_host, _, _ = host.partition('.')
        string = string.replace('\\h', short_host)
        string = string.replace('\\d', self.pgexecute.dbname or '(none)')
        string = string.replace('\\p', str(self.pgexecute.port) or '(none)')
        string = string.replace('\\i', str(self.pgexecute.pid) or '(none)')
        string = string.replace('\\#', "#" if (self.pgexecute.superuser) else ">")
        string = string.replace('\\n', "\n")
        return string

    def get_last_query(self):
        """Get the last query executed or None."""
        return self.query_history[-1][0] if self.query_history else None

    def echo_via_pager(self, text, color=None):
        if self.pgspecial.pager_config == PAGER_OFF or self.watch_command:
            click.echo(text, color=color)
        else:
            click.echo_via_pager(text, color)

@click.command()
# Default host is '' so psycopg2 can default to either localhost or unix socket
@click.option('-h', '--host', default='', envvar='PGHOST',
        help='Host address of the postgres database.')
@click.option('-p', '--port', default=5432, help='Port number at which the '
        'postgres instance is listening.', envvar='PGPORT', type=click.INT)
@click.option('-U', '--username', 'username_opt', envvar='PGUSER',
        help='Username to connect to the postgres database.')
@click.option('--user', 'username_opt', envvar='PGUSER',
              help='Username to connect to the postgres database.')
@click.option('-W', '--password', 'prompt_passwd', is_flag=True, default=False,
        help='Force password prompt.')
@click.option('-w', '--no-password', 'never_prompt', is_flag=True,
        default=False, help='Never prompt for password.')
@click.option('--single-connection', 'single_connection', is_flag=True,
        default=False,
        help='Do not use a separate connection for completions.')
@click.option('-v', '--version', is_flag=True, help='Version of pgcli.')
@click.option('-d', '--dbname', default='', envvar='PGDATABASE',
        help='database name to connect to.')
@click.option('--pgclirc', default=config_location() + 'config',
        envvar='PGCLIRC', help='Location of pgclirc file.', type=click.Path(dir_okay=False))
@click.option('-D', '--dsn', default='', envvar='DSN',
        help='Use DSN configured into the [alias_dsn] section of pgclirc file.')
@click.option('--list-dsn', 'list_dsn', is_flag=True,
              help='list of DSN configured into the [alias_dsn] section of pgclirc file.')
@click.option('--row-limit', default=None, envvar='PGROWLIMIT', type=click.INT,
        help='Set threshold for row limit prompt. Use 0 to disable prompt.')
@click.option('--less-chatty', 'less_chatty', is_flag=True,
        default=False,
        help='Skip intro on startup and goodbye on exit.')
@click.option('--prompt', help='Prompt format (Default: "\\u@\\h:\\d> ").')
@click.option('--prompt-dsn', help='Prompt format for connections using DSN aliases (Default: "\\u@\\h:\\d> ").')
@click.option('-l', '--list', 'list_databases', is_flag=True, help='list '
              'available databases, then exit.')
@click.option('--auto-vertical-output', is_flag=True,
              help='Automatically switch to vertical output mode if the result is wider than the terminal width.')
@click.option('--warn/--no-warn', default=None,
              help='Warn before running a destructive query.')
@click.argument('database', default=lambda: None, envvar='PGDATABASE', nargs=1)
@click.argument('username', default=lambda: None, envvar='PGUSER', nargs=1)
def cli(database, username_opt, host, port, prompt_passwd, never_prompt,
        single_connection, dbname, username, version, pgclirc, dsn, row_limit,
        less_chatty, prompt, prompt_dsn, list_databases, auto_vertical_output,
        list_dsn, warn):

    if version:
        print('Version:', __version__)
        sys.exit(0)

    config_dir = os.path.dirname(config_location())
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    # Migrate the config file from old location.
    config_full_path = config_location() + 'config'
    if os.path.exists(os.path.expanduser('~/.pgclirc')):
        if not os.path.exists(config_full_path):
            shutil.move(os.path.expanduser('~/.pgclirc'), config_full_path)
            print ('Config file (~/.pgclirc) moved to new location',
                   config_full_path)
        else:
            print ('Config file is now located at', config_full_path)
            print ('Please move the existing config file ~/.pgclirc to',
                   config_full_path)
    if list_dsn:
        try:
            cfg = load_config(pgclirc, config_full_path)
            for alias in cfg['alias_dsn']:
                click.secho(alias + " : " + cfg['alias_dsn'][alias])
            sys.exit(0)
        except Exception as err:
            click.secho('Invalid DSNs found in the config file. '
                        'Please check the "[alias_dsn]" section in pgclirc.',
                        err=True, fg='red')
            exit(1)

    pgcli = PGCli(prompt_passwd, never_prompt, pgclirc_file=pgclirc,
                  row_limit=row_limit, single_connection=single_connection,
                  less_chatty=less_chatty, prompt=prompt, prompt_dsn=prompt_dsn,
                  auto_vertical_output=auto_vertical_output, warn=warn)

    # Choose which ever one has a valid value.
    database = database or dbname
    user = username_opt or username

    # because option --list or -l are not supposed to have a db name
    if list_databases:
        database = 'postgres'

    if dsn is not '':
        try:
            cfg = load_config(pgclirc, config_full_path)
            dsn_config = cfg['alias_dsn'][dsn]
        except:
            click.secho('Invalid DSNs found in the config file. '\
                'Please check the "[alias_dsn]" section in pgclirc.',
                 err=True, fg='red')
            exit(1)
        pgcli.connect_uri(dsn_config)
        pgcli.dsn_alias = dsn
    elif '://' in database:
        pgcli.connect_uri(database)
    elif "=" in database:
        pgcli.connect_dsn(database)
    elif os.environ.get('PGSERVICE', None):
        pgcli.connect_dsn('service={0}'.format(os.environ['PGSERVICE']))
    else:
        pgcli.connect(database, host, user, port)

    if list_databases:
        cur, headers, status = pgcli.pgexecute.full_databases()

        title = 'List of databases'
        settings = OutputSettings(
            table_format='ascii',
            missingval='<null>'
        )
        formatted = format_output(title, cur, headers, status, settings)
        pgcli.echo_via_pager('\n'.join(formatted))

        sys.exit(0)

    pgcli.logger.debug('Launch Params: \n'
            '\tdatabase: %r'
            '\tuser: %r'
            '\thost: %r'
            '\tport: %r', database, user, host, port)

    if setproctitle:
        obfuscate_process_password()

    pgcli.run_cli()


def obfuscate_process_password():
    process_title = setproctitle.getproctitle()
    if '://' in process_title:
        process_title = re.sub(r":(.*):(.*)@", r":\1:xxxx@", process_title)
    elif "=" in process_title:
        process_title = re.sub(r"password=(.+?)((\s[a-zA-Z]+=)|$)", r"password=xxxx\2", process_title)

    setproctitle.setproctitle(process_title)


def has_meta_cmd(query):
    """Determines if the completion needs a refresh by checking if the sql
    statement is an alter, create, drop, commit or rollback."""
    try:
        first_token = query.split()[0]
        if first_token.lower() in ('alter', 'create', 'drop', 'commit', 'rollback'):
            return True
    except Exception:
        return False

    return False


def has_change_db_cmd(query):
    """Determines if the statement is a database switch such as 'use' or '\\c'"""
    try:
        first_token = query.split()[0]
        if first_token.lower() in ('use', '\\c', '\\connect'):
            return True
    except Exception:
        return False

    return False


def has_change_path_cmd(sql):
    """Determines if the search_path should be refreshed by checking if the
    sql has 'set search_path'."""
    return 'set search_path' in sql.lower()


def is_mutating(status):
    """Determines if the statement is mutating based on the status."""
    if not status:
        return False

    mutating = set(['insert', 'update', 'delete'])
    return status.split(None, 1)[0].lower() in mutating


def is_select(status):
    """Returns true if the first word in status is 'select'."""
    if not status:
        return False
    return status.split(None, 1)[0].lower() == 'select'


def exception_formatter(e):
    return click.style(utf8tounicode(str(e)), fg='red')


def format_output(title, cur, headers, status, settings):
    output = []
    expanded = (settings.expanded or settings.table_format == 'vertical')
    table_format = ('vertical' if settings.expanded else
                    settings.table_format)
    max_width = settings.max_width
    case_function = settings.case_function
    formatter = TabularOutputFormatter(format_name=table_format)

    def format_array(val):
        if val is None:
            return settings.missingval
        if not isinstance(val, list):
            return val
        return '{' + ','.join(text_type(format_array(e)) for e in val) + '}'

    def format_arrays(data, headers, **_):
        data = list(data)
        for row in data:
            row[:] = [
                format_array(val) if isinstance(val, list) else val
                for val in row
            ]

        return data, headers

    output_kwargs = {
        'sep_title': 'RECORD {n}',
        'sep_character': '-',
        'sep_length': (1, 25),
        'missing_value': settings.missingval,
        'integer_format': settings.dcmlfmt,
        'float_format': settings.floatfmt,
        'preprocessors': (format_numbers, format_arrays),
        'disable_numparse': True,
        'preserve_whitespace': True,
        'style': settings.style_output
    }
    if not settings.floatfmt:
        output_kwargs['preprocessors'] = (align_decimals, )

    if title:  # Only print the title if it's not None.
        output.append(title)

    if cur:
        headers = [case_function(utf8tounicode(x)) for x in headers]
        if max_width is not None:
            cur = list(cur)
        column_types = None
        if hasattr(cur, 'description'):
            column_types = []
            for d in cur.description:
                if d[1] in psycopg2.extensions.DECIMAL.values or \
                        d[1] in psycopg2.extensions.FLOAT.values:
                    column_types.append(float)
                if d[1] == psycopg2.extensions.INTEGER.values or \
                        d[1] in psycopg2.extensions.LONGINTEGER.values:
                    column_types.append(int)
                else:
                    column_types.append(text_type)
        formatted = formatter.format_output(cur, headers, **output_kwargs)
        if isinstance(formatted, (text_type)):
            formatted = iter(formatted.splitlines())
        first_line = next(formatted)
        formatted = itertools.chain([first_line], formatted)

        if (not expanded and max_width and len(first_line) > max_width and headers):
            formatted = formatter.format_output(
                cur, headers, format_name='vertical', column_types=None, **output_kwargs)
            if isinstance(formatted, (text_type)):
                formatted = iter(formatted.splitlines())

        output = itertools.chain(output, formatted)

    if status:  # Only print the status if it's not None.
        output = itertools.chain(output, [status])

    return output


if __name__ == "__main__":
    cli()
