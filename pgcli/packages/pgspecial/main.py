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

@export
def register_special_command(handler, command, syntax, description,
        arg_type=PARSED_QUERY, hidden=False, case_sensitive=True, aliases=()):
    cmd = command.lower() if not case_sensitive else command
    COMMANDS[cmd] = SpecialCommand(handler, syntax, description, arg_type,
                                   hidden, case_sensitive)
    for alias in aliases:
        cmd = alias.lower() if not case_sensitive else alias
        COMMANDS[cmd] = SpecialCommand(handler, syntax, description, arg_type,
                                       case_sensitive=case_sensitive,
                                       hidden=True)


@export
def execute(cur, sql):
    command, verbose, pattern = parse_special_command(sql)

    if (command not in COMMANDS) and (command.lower() not in COMMANDS):
        raise CommandNotFound

    try:
        special_cmd = COMMANDS[command]
    except KeyError:
        special_cmd = COMMANDS[command.lower()]
        if special_cmd.case_sensitive:
            raise CommandNotFound('Command not found: %s' % command)

    if special_cmd.arg_type == NO_QUERY:
        return special_cmd.handler()
    elif special_cmd.arg_type == PARSED_QUERY:
        return special_cmd.handler(cur=cur, pattern=pattern, verbose=verbose)
    elif special_cmd.arg_type == RAW_QUERY:
        return special_cmd.handler(cur=cur, query=sql)

@special_command('\\?', '\\?', 'Show Help.', arg_type=NO_QUERY)
def show_help():
    headers = ['Command', 'Description']
    result = []

    for _, value in sorted(COMMANDS.items()):
        if not value.hidden:
            result.append((value.syntax, value.description))
    return [(None, result, headers, None)]

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
