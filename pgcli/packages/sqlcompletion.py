from __future__ import print_function
import sys
import sqlparse
from sqlparse.sql import Comparison
from .parseutils import last_word, extract_tables, find_prev_keyword

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str
else:
    string_types = basestring


def suggest_type(full_text, text_before_cursor):
    """Takes the full_text that is typed so far and also the text before the
    cursor to suggest completion type and scope.

    Returns a tuple with a type of entity ('table', 'column' etc) and a scope.
    A scope for a column category will be a list of tables.
    """

    word_before_cursor = last_word(text_before_cursor,
            include='most_punctuations')

    # If we've partially typed a word then word_before_cursor won't be an empty
    # string. In that case we want to remove the partially typed string before
    # sending it to the sqlparser. Otherwise the last token will always be the
    # partially typed string which renders the smart completion useless because
    # it will always return the list of keywords as completion.
    if word_before_cursor:
        if word_before_cursor[-1] in ('(', '.'):
            parsed = sqlparse.parse(text_before_cursor)
        else:
            parsed = sqlparse.parse(
                    text_before_cursor[:-len(word_before_cursor)])
    else:
        parsed = sqlparse.parse(text_before_cursor)

    if len(parsed) > 1:
        # Multiple statements being edited -- isolate the current one by
        # cumulatively summing statement lengths to find the one that bounds the
        # current position
        current_pos = len(text_before_cursor)
        stmt_start, stmt_end = 0, 0

        for statement in parsed:
            stmt_len = len(statement.to_unicode())
            stmt_start, stmt_end = stmt_end, stmt_end + stmt_len

            if stmt_end >= current_pos:
                text_before_cursor = full_text[stmt_start:current_pos]
                full_text = full_text[stmt_start:]
                break

    elif parsed:
        # A single statement
        statement = parsed[0]
    else:
        # The empty string
        statement = None

    last_token = statement and statement.token_prev(len(statement.tokens)) or ''

    return suggest_based_on_last_token(last_token, text_before_cursor, full_text)

def suggest_based_on_last_token(token, text_before_cursor, full_text):
    if isinstance(token, string_types):
        token_v = token
    else:
        # If 'token' is a Comparison type such as
        # 'select * FROM abc a JOIN def d ON a.id = d.'. Then calling
        # token.value on the comparison type will only return the lhs of the
        # comparison. In this case a.id. So we need to do token.tokens to get
        # both sides of the comparison and pick the last token out of that
        # list.
        if isinstance(token, Comparison):
            token_v = token.tokens[-1].value
        else:
            token_v = token.value

    if token_v.lower().endswith('('):
        p = sqlparse.parse(text_before_cursor)[0]
        if p.token_first().value.lower() == 'select':
            # If the lparen is preceeded by a space chances are we're about to
            # do a sub-select.
            if last_word(text_before_cursor,
                    'all_punctuations').startswith('('):
                return [{'type': 'keyword'}]

        return [{'type': 'column', 'tables': extract_tables(full_text)}]

    if token_v.lower() in ('set', 'by', 'distinct'):
        return [{'type': 'column', 'tables': extract_tables(full_text)}]
    elif token_v.lower() in ('select', 'where', 'having'):
        return [{'type': 'column', 'tables': extract_tables(full_text)},
                {'type': 'function'}]
    elif token_v.lower() in ('copy', 'from', 'update', 'into', 'describe',
            'join', 'table'):
        return [{'type': 'schema'}, {'type': 'table', 'schema': []}]
    elif token_v.lower() == 'on':
        tables = extract_tables(full_text)  # [(schema, table, alias), ...]

        # Use table alias if there is one, otherwise the table name
        alias = [t[2] or t[1] for t in tables]

        return [{'type': 'alias', 'aliases': alias}]

    elif token_v in ('d',):  # \d
        # Apparently "\d <other>" is parsed by sqlparse as
        # Identifer('d', Whitespace, '<other>')
        if len(token.tokens) > 2:
            other = token.tokens[-1].value
            identifiers = other.split('.')
            if len(identifiers) == 1:
                # "\d table" or "\d schema"
                return [{'type': 'schema'}, {'type': 'table', 'schema': []}]
            elif len(identifiers) == 2:
                # \d schema.table
                return [{'type': 'table', 'schema': identifiers[0]}]
        else:
            return [{'type': 'schema'}, {'type': 'table', 'schema': []}]
    elif token_v.lower() in ('c', 'use'):  # \c
        return [{'type': 'database'}]
    elif token_v.endswith(',') or token_v == '=':
        prev_keyword = find_prev_keyword(text_before_cursor)
        if prev_keyword:
            return suggest_based_on_last_token(
                prev_keyword, text_before_cursor, full_text)
    elif token_v.endswith('.'):

        suggestions = []

        identifier = last_word(token_v[:-1], 'all_punctuations')

        # TABLE.<suggestion> or SCHEMA.TABLE.<suggestion>
        tables = extract_tables(full_text)
        tables = [t for t in tables if identifies(identifier, *t)]
        suggestions.append({'type': 'column', 'tables': tables})

        # SCHEMA.<suggestion>
        suggestions.append({'type': 'table', 'schema': identifier})

        return suggestions

    return [{'type': 'keyword'}]


def identifies(id, schema, table, alias):
    return id == alias or id == table or (
        schema and (id == schema + '.' + table))
