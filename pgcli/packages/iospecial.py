from __future__ import print_function

import re
import logging
import click

_logger = logging.getLogger(__name__)


def editor_command(command):
    """
    Is this an external editor command?
    :param command: string
    """
    # It is possible to have `\e filename` or `SELECT * FROM \e`. So we check
    # for both conditions.
    return command.strip().endswith('\\e') or command.strip().startswith('\\e')

def get_filename(sql):
    if sql.strip().startswith('\\e'):
        command, _, filename = sql.partition(' ')
        return filename.strip() or None

def open_external_editor(filename=None, sql=''):
    """
    Open external editor, wait for the user to type in his query,
    return the query.
    :return: list with one tuple, query as first element.
    """

    sql = sql.strip()

    # The reason we can't simply do .strip('\e') is that it strips characters,
    # not a substring. So it'll strip "e" in the end of the sql also!
    # Ex: "select * from style\e" -> "select * from styl".
    pattern = re.compile('(^\\\e|\\\e$)')
    while pattern.search(sql):
        sql = pattern.sub('', sql)

    message = None
    filename = filename.strip().split(' ', 1)[0] if filename else None

    MARKER = '# Type your query above this line.\n'

    # Populate the editor buffer with the partial sql (if available) and a
    # placeholder comment.
    query = click.edit(sql + '\n\n' + MARKER,
            filename=filename)

    if filename:
        try:
            with open(filename, "r") as f:
                query = f.read()
        except IOError:
            message = 'Error reading file: %s.' % filename

    if query is not None:
        query = query.split(MARKER, 1)[0].rstrip('\n')
    else:
        # Don't return None for the caller to deal with.
        # Empty string is ok.
        query = sql

    return (query, message)
