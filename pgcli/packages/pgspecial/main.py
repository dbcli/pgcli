import logging
from collections import namedtuple

from . import export

log = logging.getLogger(__name__)

NO_QUERY = 0
PARSED_QUERY = 1
RAW_QUERY = 2

SpecialCommand = namedtuple('SpecialCommand',
        ['handler', 'syntax', 'description', 'arg_type', 'hidden', 'case_sensitive'])

COMMANDS = {}

@export
class CommandNotFound(Exception):
    pass


@export
class PGSpecial(object):
    def __init__(self):
        self.timing_enabled = True

        self.commands = COMMANDS.copy()

        self.timing_enabled = False
        self.expanded_output = False

        self.register(self.show_help, '\\?', '\\?', 'Show Help.',
                      arg_type=NO_QUERY)

        self.register(self.toggle_expanded_output, '\\x', '\\x',
                      'Toggle expanded output.', arg_type=NO_QUERY)

        self.register(self.toggle_timing, '\\timing', '\\timing',
                      'Toggle timing of commands.', arg_type=NO_QUERY)

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

    def toggle_expanded_output(self):
        self.expanded_output = not self.expanded_output
        message = u"Expanded display is "
        message += u"on." if self.expanded_output else u"off."
        return [(None, None, None, message)]

    def toggle_timing(self):
        self.timing_enabled = not self.timing_enabled
        message = "Timing is "
        message += "on." if self.timing_enabled else "off."
        return [(None, None, None, message)]


@export
def parse_special_command(sql):
    command, _, arg = sql.partition(' ')
    verbose = '+' in command

    command = command.strip().replace('+', '')
    return (command, verbose, arg.strip())


@export
def special_command(command, syntax, description, arg_type=PARSED_QUERY,
        hidden=False, case_sensitive=True, aliases=()):
    def wrapper(wrapped):
        register_special_command(wrapped, command, syntax, description,
                arg_type, hidden, case_sensitive, aliases)
        return wrapped
    return wrapper


def register_special_command(handler, command, syntax, description,
        arg_type=PARSED_QUERY, hidden=False, case_sensitive=True, aliases=(),
        command_dict=None):

    command_dict = command_dict or COMMANDS

    cmd = command.lower() if not case_sensitive else command
    command_dict[cmd] = SpecialCommand(handler, syntax, description, arg_type,
                                   hidden, case_sensitive)
    for alias in aliases:
        cmd = alias.lower() if not case_sensitive else alias
        command_dict[cmd] = SpecialCommand(handler, syntax, description, arg_type,
                                       case_sensitive=case_sensitive,
                                       hidden=True)


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
