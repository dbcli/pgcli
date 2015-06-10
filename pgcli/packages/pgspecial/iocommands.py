from __future__ import print_function

import re
import logging
from codecs import open
import click
from .namedqueries import namedqueries
from . import export

_logger = logging.getLogger(__name__)

TIMING_ENABLED = True
use_expanded_output = False

@export
def is_expanded_output():
    return use_expanded_output

def toggle_expanded_output(**_):
    global use_expanded_output
    use_expanded_output = not use_expanded_output
    message = u"Expanded display is "
    message += u"on." if use_expanded_output else u"off."
    return [(None, None, None, message)]

def toggle_timing(**_):
    global TIMING_ENABLED
    TIMING_ENABLED = not TIMING_ENABLED
    message = "Timing is "
    message += "on." if TIMING_ENABLED else "off."
    return [(None, None, None, message)]

@export
def editor_command(command):
    """
    Is this an external editor command?
    :param command: string
    """
    # It is possible to have `\e filename` or `SELECT * FROM \e`. So we check
    # for both conditions.
    return command.strip().endswith('\\e') or command.strip().startswith('\\e')

@export
def get_filename(sql):
    if sql.strip().startswith('\\e'):
        command, _, filename = sql.partition(' ')
        return filename.strip() or None

@export
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
    query = click.edit(sql + '\n\n' + MARKER, filename=filename,
            extension='.sql')

    if filename:
        try:
            with open(filename, encoding='utf-8') as f:
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

def execute_named_query(cur, pattern, verbose):
    """Returns (title, rows, headers, status)"""
    if pattern == '':
        return list_named_queries(verbose)

    query = namedqueries.get(pattern)
    title = '> {}'.format(query)
    if query is None:
        message = "No named query: {}".format(pattern)
        return [(None, None, None, message)]
    cur.execute(query)
    if cur.description:
        headers = [x[0] for x in cur.description]
        return [(title, cur, headers, cur.statusmessage)]
    else:
        return [(title, None, None, cur.statusmessage)]

def list_named_queries(verbose):
    """List of all named queries.
    Returns (title, rows, headers, status)"""
    if not verbose:
        rows = [[r] for r in namedqueries.list()]
        headers = ["Name"]
    else:
        headers = ["Name", "Query"]
        rows = [[r, namedqueries.get(r)] for r in namedqueries.list()]
    return [('', rows, headers, "")]

def save_named_query(pattern, **_):
    """Save a new named query.
    Returns (title, rows, headers, status)"""
    if ' ' not in pattern:
        return [(None, None, None, "Invalid argument.")]
    name, query = pattern.split(' ', 1)
    namedqueries.save(name, query)
    return [(None, None, None, "Saved.")]

def delete_named_query(pattern, **_):
    """Delete an existing named query.
    """
    if len(pattern) == 0:
        return [(None, None, None, "Invalid argument.")]
    namedqueries.delete(pattern)
    return [(None, None, None, "Deleted.")]
