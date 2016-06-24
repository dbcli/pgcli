from __future__ import print_function
import sys
import re
import sqlparse
from collections import namedtuple
from sqlparse.sql import Comparison, Identifier, Where
from .parseutils import (
    last_word, extract_tables, find_prev_keyword, parse_partial_identifier)
from pgspecial.main import parse_special_command

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str
else:
    string_types = basestring


Special = namedtuple('Special', [])
Database = namedtuple('Database', [])
Schema = namedtuple('Schema', [])
Table = namedtuple('Table', ['schema'])
# JoinConditions are suggested after ON, e.g. 'foo.barid = bar.barid'
JoinCondition = namedtuple('JoinCondition', ['tables', 'parent'])
# Joins are suggested after JOIN, e.g. 'foo ON foo.barid = bar.barid'
Join = namedtuple('Join', ['tables', 'schema'])

Function = namedtuple('Function', ['schema', 'filter'])
# For convenience, don't require the `filter` argument in Function constructor
Function.__new__.__defaults__ = (None, None)

Column = namedtuple('Column', ['tables', 'require_last_table'])
Column.__new__.__defaults__ = (None, None)

View = namedtuple('View', ['schema'])
Keyword = namedtuple('Keyword', [])
NamedQuery = namedtuple('NamedQuery', [])
Datatype = namedtuple('Datatype', ['schema'])
Alias = namedtuple('Alias', ['aliases'])

Path = namedtuple('Path', [])


class SqlStatement(object):
    def __init__(self, full_text, text_before_cursor):
        self.identifier = None
        self.word_before_cursor = word_before_cursor = last_word(
            text_before_cursor, include='many_punctuations')
        full_text = _strip_named_query(full_text)
        text_before_cursor = _strip_named_query(text_before_cursor)
        self.text_before_cursor_including_last_word = text_before_cursor

        # If we've partially typed a word then word_before_cursor won't be an
        # empty string. In that case we want to remove the partially typed
        # string before sending it to the sqlparser. Otherwise the last token
        # will always be the partially typed string which renders the smart
        # completion useless because it will always return the list of
        # keywords as completion.
        if self.word_before_cursor:
            if word_before_cursor[-1] == '(' or word_before_cursor[0] == '\\':
                parsed = sqlparse.parse(text_before_cursor)
            else:
                text_before_cursor = text_before_cursor[:-len(word_before_cursor)]
                parsed = sqlparse.parse(text_before_cursor)
                self.identifier = parse_partial_identifier(word_before_cursor)
        else:
            parsed = sqlparse.parse(text_before_cursor)

        full_text, text_before_cursor, parsed = \
            _split_multiple_statements(full_text, text_before_cursor, parsed)

        self.full_text = full_text
        self.text_before_cursor = text_before_cursor
        self.parsed = parsed

        self.last_token = parsed and parsed.token_prev(len(parsed.tokens)) or ''

    def get_identifier_schema(self):
        schema = (self.identifier and self.identifier.get_parent_name()) or None
        # If schema name is unquoted, lower-case it
        if schema and self.identifier.value[0] != '"':
            schema = schema.lower()

        return schema

    def reduce_to_prev_keyword(self):
        prev_keyword, self.text_before_cursor = \
            find_prev_keyword(self.text_before_cursor)
        return prev_keyword


def suggest_type(full_text, text_before_cursor):
    """Takes the full_text that is typed so far and also the text before the
    cursor to suggest completion type and scope.

    Returns a tuple with a type of entity ('table', 'column' etc) and a scope.
    A scope for a column category will be a list of tables.
    """

    if full_text.startswith('\\i '):
        return (Path(),)

    stmt = SqlStatement(full_text, text_before_cursor)

    # Check for special commands and handle those separately
    if stmt.parsed:
        # Be careful here because trivial whitespace is parsed as a
        # statement, but the statement won't have a first token
        tok1 = stmt.parsed.token_first()
        if tok1 and tok1.value == '\\':
            text = stmt.text_before_cursor + stmt.word_before_cursor
            return suggest_special(text)

    return suggest_based_on_last_token(stmt.last_token, stmt)


named_query_regex = re.compile(r'^\s*\\ns\s+[A-z0-9\-_]+\s+')


def _strip_named_query(txt):
    """
    This will strip "save named query" command in the beginning of the line:
    '\ns zzz SELECT * FROM abc'   -> 'SELECT * FROM abc'
    '  \ns zzz SELECT * FROM abc' -> 'SELECT * FROM abc'
    """

    if named_query_regex.match(txt):
        txt = named_query_regex.sub('', txt)
    return txt


def _split_multiple_statements(full_text, text_before_cursor, parsed):
    if len(parsed) > 1:
        # Multiple statements being edited -- isolate the current one by
        # cumulatively summing statement lengths to find the one that bounds
        # the current position
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

    return full_text, text_before_cursor, statement


def suggest_special(text):
    text = text.lstrip()
    cmd, _, arg = parse_special_command(text)

    if cmd == text:
        # Trying to complete the special command itself
        return (Special(),)

    if cmd in ('\\c', '\\connect'):
        return (Database(),)

    if cmd == '\\dn':
        return (Schema(),)

    if arg:
        # Try to distinguish "\d name" from "\d schema.name"
        # Note that this will fail to obtain a schema name if wildcards are
        # used, e.g. "\d schema???.name"
        parsed = sqlparse.parse(arg)[0].tokens[0]
        try:
            schema = parsed.get_parent_name()
        except AttributeError:
            schema = None
    else:
        schema = None

    if cmd[1:] == 'd':
        # \d can descibe tables or views
        if schema:
            return (Table(schema=schema),
                    View(schema=schema),)
        else:
            return (Schema(),
                    Table(schema=None),
                    View(schema=None),)
    elif cmd[1:] in ('dt', 'dv', 'df', 'dT'):
        rel_type = {'dt': Table,
                    'dv': View,
                    'df': Function,
                    'dT': Datatype,
                    }[cmd[1:]]
        if schema:
            return (rel_type(schema=schema),)
        else:
            return (Schema(), rel_type(schema=None))

    if cmd in ['\\n', '\\ns', '\\nd']:
        return (NamedQuery(),)

    return (Keyword(), Special())


def suggest_based_on_last_token(token, stmt):

    if isinstance(token, string_types):
        token_v = token.lower()
    elif isinstance(token, Comparison):
        # If 'token' is a Comparison type such as
        # 'select * FROM abc a JOIN def d ON a.id = d.'. Then calling
        # token.value on the comparison type will only return the lhs of the
        # comparison. In this case a.id. So we need to do token.tokens to get
        # both sides of the comparison and pick the last token out of that
        # list.
        token_v = token.tokens[-1].value.lower()
    elif isinstance(token, Where):
        # sqlparse groups all tokens from the where clause into a single token
        # list. This means that token.value may be something like
        # 'where foo > 5 and '. We need to look "inside" token.tokens to handle
        # suggestions in complicated where clauses correctly
        prev_keyword = stmt.reduce_to_prev_keyword()
        return suggest_based_on_last_token(prev_keyword, stmt)
    elif isinstance(token, Identifier):
        # If the previous token is an identifier, we can suggest datatypes if
        # we're in a parenthesized column/field list, e.g.:
        #       CREATE TABLE foo (Identifier <CURSOR>
        #       CREATE FUNCTION foo (Identifier <CURSOR>
        # If we're not in a parenthesized list, the most likely scenario is the
        # user is about to specify an alias, e.g.:
        #       SELECT Identifier <CURSOR>
        #       SELECT foo FROM Identifier <CURSOR>
        prev_keyword, _ = find_prev_keyword(stmt.text_before_cursor)
        if prev_keyword and prev_keyword.value == '(':
            # Suggest datatypes
            return suggest_based_on_last_token('type', stmt)
        else:
            return (Keyword(),)
    else:
        token_v = token.value.lower()

    if not token:
        return (Keyword(), Special())
    elif token_v.endswith('('):
        p = sqlparse.parse(stmt.text_before_cursor)[0]

        if p.tokens and isinstance(p.tokens[-1], Where):
            # Four possibilities:
            #  1 - Parenthesized clause like "WHERE foo AND ("
            #        Suggest columns/functions
            #  2 - Function call like "WHERE foo("
            #        Suggest columns/functions
            #  3 - Subquery expression like "WHERE EXISTS ("
            #        Suggest keywords, in order to do a subquery
            #  4 - Subquery OR array comparison like "WHERE foo = ANY("
            #        Suggest columns/functions AND keywords. (If we wanted to be
            #        really fancy, we could suggest only array-typed columns)

            column_suggestions = suggest_based_on_last_token('where', stmt)

            # Check for a subquery expression (cases 3 & 4)
            where = p.tokens[-1]
            prev_tok = where.token_prev(len(where.tokens) - 1)

            if isinstance(prev_tok, Comparison):
                # e.g. "SELECT foo FROM bar WHERE foo = ANY("
                prev_tok = prev_tok.tokens[-1]

            prev_tok = prev_tok.value.lower()
            if prev_tok == 'exists':
                return (Keyword(),)
            else:
                return column_suggestions

        # Get the token before the parens
        prev_tok = p.token_prev(len(p.tokens) - 1)

        if (prev_tok and prev_tok.value
          and prev_tok.value.lower().split(' ')[-1] == 'using'):
            # tbl1 INNER JOIN tbl2 USING (col1, col2)
            tables = extract_tables(stmt.text_before_cursor)

            # suggest columns that are present in more than one table
            return (Column(tables=tables, require_last_table=True),)

        elif p.token_first().value.lower() == 'select':
            # If the lparen is preceeded by a space chances are we're about to
            # do a sub-select.
            if last_word(stmt.text_before_cursor,
                         'all_punctuations').startswith('('):
                return (Keyword(),)
        # We're probably in a function argument list
        return (Column(tables=extract_tables(stmt.full_text)),)
    elif token_v in ('set', 'by', 'distinct'):
        return (Column(tables=extract_tables(stmt.full_text)),)
    elif token_v in ('select', 'where', 'having'):
        # Check for a table alias or schema qualification
        parent = (stmt.identifier and stmt.identifier.get_parent_name()) or []

        if parent:
            tables = extract_tables(stmt.full_text)
            tables = tuple(t for t in tables if identifies(parent, t))
            return (Column(tables=tables),
                    Table(schema=parent),
                    View(schema=parent),
                    Function(schema=parent),)
        else:
            return (Column(tables=extract_tables(stmt.full_text)),
                    Function(schema=None),
                    Keyword(),)

    elif (token_v.endswith('join') and token.is_keyword) or (token_v in
            ('copy', 'from', 'update', 'into', 'describe', 'truncate')):

        schema = stmt.get_identifier_schema()

        # Suggest tables from either the currently-selected schema or the
        # public schema if no schema has been specified
        suggest = [Table(schema=schema)]

        if not schema:
            # Suggest schemas
            suggest.insert(0, Schema())

        # Only tables can be TRUNCATED, otherwise suggest views
        if token_v != 'truncate':
            suggest.append(View(schema=schema))

        # Suggest set-returning functions in the FROM clause
        if token_v == 'from' or (token_v.endswith('join') and token.is_keyword):
            suggest.append(Function(schema=schema, filter='for_from_clause'))

        if (token_v.endswith('join') and token.is_keyword
          and _allow_join(stmt.parsed)):
            tables = extract_tables(stmt.text_before_cursor)
            suggest.append(Join(tables=tables, schema=schema))

        return tuple(suggest)

    elif token_v in ('table', 'view', 'function'):
        # E.g. 'DROP FUNCTION <funcname>', 'ALTER TABLE <tablname>'
        rel_type = {'table': Table, 'view': View, 'function': Function}[token_v]
        schema = stmt.get_identifier_schema()
        if schema:
            return (rel_type(schema=schema),)
        else:
            return (Schema(), rel_type(schema=schema))

    elif token_v == 'column':
        # E.g. 'ALTER TABLE foo ALTER COLUMN bar
        return (Column(tables=extract_tables(stmt.text_before_cursor)),)

    elif token_v == 'on':
        tables = extract_tables(stmt.text_before_cursor)  # [(schema, table, alias), ...]
        parent = (stmt.identifier and stmt.identifier.get_parent_name()) or None
        if parent:
            # "ON parent.<suggestion>"
            # parent can be either a schema name or table alias
            filteredtables = tuple(t for t in tables if identifies(parent, t))
            sugs = [Column(tables=filteredtables),
                    Table(schema=parent),
                    View(schema=parent),
                    Function(schema=parent)]
            if filteredtables and _allow_join_condition(stmt.parsed):
                sugs.append(JoinCondition(tables=tables,
                                          parent=filteredtables[-1]))
            return tuple(sugs)
        else:
            # ON <suggestion>
            # Use table alias if there is one, otherwise the table name
            aliases = tuple(t.ref for t in tables)
            if _allow_join_condition(stmt.parsed):
                return (Alias(aliases=aliases), JoinCondition(
                    tables=tables, parent=None))
            else:
                return (Alias(aliases=aliases),)

    elif token_v in ('c', 'use', 'database', 'template'):
        # "\c <db", "use <db>", "DROP DATABASE <db>",
        # "CREATE DATABASE <newdb> WITH TEMPLATE <db>"
        return (Database(),)
    elif token_v == 'schema':
        # DROP SCHEMA schema_name
        return (Schema(),)
    elif token_v.endswith(',') or token_v in ('=', 'and', 'or'):
        prev_keyword = stmt.reduce_to_prev_keyword()
        if prev_keyword:
            return suggest_based_on_last_token(prev_keyword, stmt)
        else:
            return ()
    elif token_v in ('type', '::'):
        #   ALTER TABLE foo SET DATA TYPE bar
        #   SELECT foo::bar
        # Note that tables are a form of composite type in postgresql, so
        # they're suggested here as well
        schema = stmt.get_identifier_schema()
        suggestions = [Datatype(schema=schema),
                       Table(schema=schema)]
        if not schema:
            suggestions.append(Schema())
        return tuple(suggestions)
    else:
        return (Keyword(),)


def identifies(id, ref):
    """Returns true if string `id` matches TableReference `ref`"""

    return id == ref.alias or id == ref.name or (
        ref.schema and (id == ref.schema + '.' + ref.name))


def _allow_join_condition(statement):
    """
    Tests if a join condition should be suggested

    We need this to avoid bad suggestions when entering e.g.
        select * from tbl1 a join tbl2 b on a.id = <cursor>
    So check that the preceding token is a ON, AND, or OR keyword, instead of
    e.g. an equals sign.

    :param statement: an sqlparse.sql.Statement
    :return: boolean
    """

    if not statement or not statement.tokens:
        return False

    last_tok = statement.token_prev(len(statement.tokens))
    return last_tok.value.lower() in ('on', 'and', 'or')


def _allow_join(statement):
    """
    Tests if a join should be suggested

    We need this to avoid bad suggestions when entering e.g.
        select * from tbl1 a join tbl2 b <cursor>
    So check that the preceding token is a JOIN keyword

    :param statement: an sqlparse.sql.Statement
    :return: boolean
    """

    if not statement or not statement.tokens:
        return False

    last_tok = statement.token_prev(len(statement.tokens))
    return (last_tok.value.lower().endswith('join')
        and last_tok.value.lower() not in('cross join', 'natural join'))
