import os
import logging
from collections import namedtuple

from . import export
from .helpcommands import helpcommands

log = logging.getLogger(__name__)

NO_QUERY = 0
PARSED_QUERY = 1
RAW_QUERY = 2

SpecialCommand = namedtuple('SpecialCommand',
        ['handler', 'syntax', 'description', 'arg_type', 'hidden', 'case_sensitive'])

@export
class CommandNotFound(Exception):
    pass


@export
class PGSpecial(object):

    # Default static commands that don't rely on PGSpecial state are registered
    # via the special_command decorator and stored in default_commands
    default_commands = {}

    def __init__(self):
        self.timing_enabled = True

        self.commands = self.default_commands.copy()

        self.timing_enabled = False
        self.expanded_output = False
        self.auto_expand = False
        self.pager = os.environ.get('PAGER', '')

        self.register(self.show_help, '\\?', '\\?', 'Show Help.',
                      arg_type=NO_QUERY)

        self.register(self.toggle_expanded_output, '\\x', '\\x',
                      'Toggle expanded output.', arg_type=PARSED_QUERY)

        self.register(self.show_command_help, '\\h', '\\h',
                      'Help.', arg_type=PARSED_QUERY)

        self.register(self.toggle_timing, '\\timing', '\\timing',
                      'Toggle timing of commands.', arg_type=NO_QUERY)

        self.register(self.set_pager, '\\pager', '\\pager [command]',
                      'Set PAGER. Pring the query results via PAGER.',
                      arg_type=PARSED_QUERY)

    def register(self, *args, **kwargs):
        register_special_command(*args, command_dict=self.commands, **kwargs)

    def execute(self, cur, sql):
        commands = self.commands
        command, verbose, pattern = parse_special_command(sql)

        if (command not in commands) and (command.lower() not in commands):
            raise CommandNotFound

        try:
            special_cmd = commands[command]
        except KeyError:
            special_cmd = commands[command.lower()]
            if special_cmd.case_sensitive:
                raise CommandNotFound('Command not found: %s' % command)

        if special_cmd.arg_type == NO_QUERY:
            return special_cmd.handler()
        elif special_cmd.arg_type == PARSED_QUERY:
            return special_cmd.handler(cur=cur, pattern=pattern, verbose=verbose)
        elif special_cmd.arg_type == RAW_QUERY:
            return special_cmd.handler(cur=cur, query=sql)

    def show_help(self):
        headers = ['Command', 'Description']
        result = []

        for _, value in sorted(self.commands.items()):
            if not value.hidden:
                result.append((value.syntax, value.description))
        return [(None, result, headers, None)]

    def show_command_help_listing(self):
        table = chunks(sorted(helpcommands.keys()), 6)
        return [(None, table, [], None)]

    def show_command_help(self, pattern, **_):
        command = pattern.strip().upper()
        message = ""

        if not command:
            return self.show_command_help_listing()

        if command in helpcommands:
            helpcommand = helpcommands[command]

            if "description" in helpcommand:
                message += helpcommand["description"]
            if "synopsis" in helpcommand:
                message += "\nSyntax:\n"
                message += helpcommand["synopsis"]
        else:
            message = "No help available for \"%s\"" % pattern
            message += "\nTry \h with no arguments to see available help."

        return [(None, None, None, message)]


    def toggle_expanded_output(self, pattern, **_):
        flag = pattern.strip()
        if flag == "auto":
            self.auto_expand = True
            self.expanded_output = False
            return [(None, None, None, u"Expanded display is used automatically.")]
        elif flag == "off":
            self.expanded_output = False
        elif flag == "on":
            self.expanded_output = True
        else:
            self.expanded_output = not (self.expanded_output or self.auto_expand)

        self.auto_expand = self.expanded_output
        message = u"Expanded display is "
        message += u"on." if self.expanded_output else u"off."
        return [(None, None, None, message)]

    def toggle_timing(self):
        self.timing_enabled = not self.timing_enabled
        message = "Timing is "
        message += "on." if self.timing_enabled else "off."
        return [(None, None, None, message)]

    def set_pager(self, pattern, **_):
        if not pattern:
            if not self.pager:
                os.environ.pop('PAGER', None)
                msg = 'Pager reset to system default.'
            else:
                os.environ['PAGER'] = self.pager
                msg = 'Reset pager back to default. Default: %s' % self.pager
        else:
            os.environ['PAGER'] = pattern
            msg = 'PAGER set to %s.' % pattern

        return [(None, None, None, msg)]

@export
def content_exceeds_width(row, width):
    # Account for 3 characters between each column
    separator_space = (len(row)*3)
    # Add 2 columns for a bit of buffer
    line_len = sum([len(x) for x in row]) + separator_space + 2
    return line_len > width

@export
def parse_special_command(sql):
    command, _, arg = sql.partition(' ')
    verbose = '+' in command

    command = command.strip().replace('+', '')
    return (command, verbose, arg.strip())


def special_command(command, syntax, description, arg_type=PARSED_QUERY,
        hidden=False, case_sensitive=True, aliases=()):
    """A decorator used internally for static special commands"""

    def wrapper(wrapped):
        register_special_command(wrapped, command, syntax, description,
                arg_type, hidden, case_sensitive, aliases,
                command_dict=PGSpecial.default_commands)
        return wrapped
    return wrapper


def register_special_command(handler, command, syntax, description,
        arg_type=PARSED_QUERY, hidden=False, case_sensitive=True, aliases=(),
        command_dict=None):

    cmd = command.lower() if not case_sensitive else command
    command_dict[cmd] = SpecialCommand(handler, syntax, description, arg_type,
                                   hidden, case_sensitive)
    for alias in aliases:
        cmd = alias.lower() if not case_sensitive else alias
        command_dict[cmd] = SpecialCommand(handler, syntax, description, arg_type,
                                       case_sensitive=case_sensitive,
                                       hidden=True)
def chunks(l, n):
    n = max(1, n)
    return [l[i:i + n] for i in range(0, len(l), n)]

@special_command('\\e', '\\e [file]', 'Edit the query with external editor.', arg_type=NO_QUERY)
def doc_only():
    raise RuntimeError

@special_command('\\ef', '\\ef [funcname [line]]', 'Edit the contents of the query buffer.', arg_type=NO_QUERY, hidden=True)
@special_command('\\sf', '\\sf[+] FUNCNAME', 'Show a function\'s definition.', arg_type=NO_QUERY, hidden=True)
@special_command('\\do', '\\do[S] [pattern]', 'List operators.', arg_type=NO_QUERY, hidden=True)
@special_command('\\dp', '\\dp [pattern]', 'List table, view, and sequence access privileges.', arg_type=NO_QUERY, hidden=True)
@special_command('\\z', '\\z [pattern]', 'Same as \\dp.', arg_type=NO_QUERY, hidden=True)
def place_holder():
    raise NotImplementedError
