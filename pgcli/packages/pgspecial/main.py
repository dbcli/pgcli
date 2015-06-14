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
def parse_special_command(sql):
    command, _, arg = sql.partition(' ')
    verbose = '+' in command

    command = command.strip().replace('+', '')
    return (command, verbose, arg.strip())

def special_command(command, syntax, description, arg_type=PARSED_QUERY,
        hidden=False, case_sensitive=True):
    def wrapper(wrapped):
        register_special_command(wrapped, command, syntax, description,
                arg_type, hidden, case_sensitive)
        return wrapped
    return wrapper

@export
def register_special_command(handler, command, syntax, description,
        arg_type=PARSED_QUERY, hidden=False, case_sensitive=True):
    global COMMANDS
    cmd = command.lower() if not case_sensitive else command
    COMMANDS[cmd] = SpecialCommand(handler, syntax, description, arg_type,
                                   hidden, case_sensitive)

@export
def execute(cur, sql):
    command, verbose, pattern = parse_special_command(sql)
    try:
        special_cmd = COMMANDS[command]
    except KeyError:
        special_cmd = COMMANDS[command.lower()]
        if special_cmd.case_sensitive:
            raise KeyError('Command not found: %s' % command)

    if special_cmd.arg_type == NO_QUERY:
        return special_cmd.handler()
    elif special_cmd.arg_type == PARSED_QUERY:
        return special_cmd.handler(cur=cur, pattern=pattern, verbose=verbose)
    elif special_cmd.arg_type == RAW_QUERY:
        return special_cmd.handler(cur=cur, query=sql)

@special_command('\?', '\?', 'Show Help.', arg_type=NO_QUERY)
def show_help():
    headers = ['Command', 'Description']
    result = []

    for _, value in sorted(COMMANDS.items()):
        if not value.hidden:
            result.append((value.syntax, value.description))
    return [(None, result, headers, None)]

#COMMANDS = {
#            '\?': (show_help, ['\?', 'Help on pgcli commands.']),
#            '\l': ('''SELECT datname FROM pg_database;''', ['\l', 'List databases.']),
#            '\d': (describe_table_details, ['\d [pattern]', 'List or describe tables, views and sequences.']),
#            '\dn': (list_schemas, ['\dn[+] [pattern]', 'List schemas.']),
#            '\du': (list_roles, ['\du[+] [pattern]', 'List roles.']),
#            '\\x': (toggle_expanded_output, ['\\x', 'Toggle expanded output.']),
#            '\\timing': (toggle_timing, ['\\timing', 'Toggle timing of commands.']),
#            '\\dt': (list_tables, ['\\dt[+] [pattern]', 'List tables.']),
#            '\\di': (list_indexes, ['\\di[+] [pattern]', 'List indexes.']),
#            '\\dv': (list_views, ['\\dv[+] [pattern]', 'List views.']),
#            '\\ds': (list_sequences, ['\\ds[+] [pattern]', 'List sequences.']),
#            '\\df': (list_functions, ['\\df[+] [pattern]', 'List functions.']),
#            '\\dT': (list_datatypes, ['\dT[S+] [pattern]', 'List data types']),
#            '\e': (dummy_command, ['\e [file]', 'Edit the query buffer (or file) with external editor.']),
#            '\ef': (in_progress, ['\ef [funcname [line]]', 'Not yet implemented.']),
#            '\sf': (in_progress, ['\sf[+] funcname', 'Not yet implemented.']),
#            '\z': (in_progress, ['\z [pattern]', 'Not yet implemented.']),
#            '\do': (in_progress, ['\do[S] [pattern]', 'Not yet implemented.']),
#            '\\n': (execute_named_query, ['\\n[+] [name]', 'List or execute named queries.']),
#            '\\ns': (save_named_query, ['\\ns [name [query]]', 'Save a named query.']),
#            '\\nd': (delete_named_query, ['\\nd [name]', 'Delete a named query.']),
#            }

## Commands not shown via help.
#HIDDEN_COMMANDS = {
#            'describe': (describe_table_details, ['DESCRIBE [pattern]', '']),
#            }
