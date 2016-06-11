from __future__ import print_function
import re
import sqlparse
from collections import namedtuple
from sqlparse.sql import IdentifierList, Identifier, Function
from sqlparse.tokens import Keyword, DML, Punctuation, Token, Error

cleanup_regex = {
        # This matches only alphanumerics and underscores.
        'alphanum_underscore': re.compile(r'(\w+)$'),
        # This matches everything except spaces, parens, colon, and comma
        'many_punctuations': re.compile(r'([^():,\s]+)$'),
        # This matches everything except spaces, parens, colon, comma, and period
        'most_punctuations': re.compile(r'([^\.():,\s]+)$'),
        # This matches everything except a space.
        'all_punctuations': re.compile('([^\s]+)$'),
        }

def last_word(text, include='alphanum_underscore'):
    """
    Find the last word in a sentence.

    >>> last_word('abc')
    'abc'
    >>> last_word(' abc')
    'abc'
    >>> last_word('')
    ''
    >>> last_word(' ')
    ''
    >>> last_word('abc ')
    ''
    >>> last_word('abc def')
    'def'
    >>> last_word('abc def ')
    ''
    >>> last_word('abc def;')
    ''
    >>> last_word('bac $def')
    'def'
    >>> last_word('bac $def', include='most_punctuations')
    '$def'
    >>> last_word('bac \def', include='most_punctuations')
    '\\\\def'
    >>> last_word('bac \def;', include='most_punctuations')
    '\\\\def;'
    >>> last_word('bac::def', include='most_punctuations')
    'def'
    >>> last_word('"foo*bar', include='most_punctuations')
    '"foo*bar'
    """

    if not text:   # Empty string
        return ''

    if text[-1].isspace():
        return ''
    else:
        regex = cleanup_regex[include]
        matches = regex.search(text)
        if matches:
            return matches.group(0)
        else:
            return ''


TableReference = namedtuple('TableReference', ['schema', 'name', 'alias',
                                               'is_function'])
TableReference.ref = property(lambda self: self.alias or (
  self.name if self.name.islower() or self.name[0] == '"'
  else '"' + self.name + '"'))


# This code is borrowed from sqlparse example script.
# <url>
def is_subselect(parsed):
    if not parsed.is_group():
        return False
    for item in parsed.tokens:
        if item.ttype is DML and item.value.upper() in ('SELECT', 'INSERT',
                'UPDATE', 'CREATE', 'DELETE'):
            return True
    return False


def _identifier_is_function(identifier):
    return any(isinstance(t, Function) for t in identifier.tokens)

def extract_from_part(parsed, stop_at_punctuation=True):
    tbl_prefix_seen = False
    for item in parsed.tokens:
        if tbl_prefix_seen:
            if is_subselect(item):
                for x in extract_from_part(item, stop_at_punctuation):
                    yield x
            elif stop_at_punctuation and item.ttype is Punctuation:
                raise StopIteration
            # An incomplete nested select won't be recognized correctly as a
            # sub-select. eg: 'SELECT * FROM (SELECT id FROM user'. This causes
            # the second FROM to trigger this elif condition resulting in a
            # StopIteration. So we need to ignore the keyword if the keyword
            # FROM.
            # Also 'SELECT * FROM abc JOIN def' will trigger this elif
            # condition. So we need to ignore the keyword JOIN and its variants
            # INNER JOIN, FULL OUTER JOIN, etc.
            elif item.ttype is Keyword and (
                    not item.value.upper() == 'FROM') and (
                    not item.value.upper().endswith('JOIN')):
                tbl_prefix_seen = False
            else:
                yield item
        elif item.ttype is Keyword or item.ttype is Keyword.DML:
            item_val = item.value.upper()
            if (item_val in ('COPY', 'FROM', 'INTO', 'UPDATE', 'TABLE') or
                    item_val.endswith('JOIN')):
                tbl_prefix_seen = True
        # 'SELECT a, FROM abc' will detect FROM as part of the column list.
        # So this check here is necessary.
        elif isinstance(item, IdentifierList):
            for identifier in item.get_identifiers():
                if (identifier.ttype is Keyword and
                        identifier.value.upper() == 'FROM'):
                    tbl_prefix_seen = True
                    break


def extract_table_identifiers(token_stream, allow_functions=True):
    """yields tuples of TableReference namedtuples"""

    # We need to do some massaging of the names because postgres is case-
    # insensitive and '"Foo"' is not the same table as 'Foo' (while 'foo' is)
    def parse_identifier(item):
        name = item.get_real_name()
        schema_name = item.get_parent_name()
        alias = item.get_alias()
        if not name:
            schema_name = None
            name = item.get_name()
            alias = alias or name
        schema_quoted = schema_name and item.value[0] == '"'
        if schema_name and not schema_quoted:
            schema_name = schema_name.lower()
        quote_count = item.value.count('"')
        name_quoted = quote_count > 2 or (quote_count and not schema_quoted)
        alias_quoted = alias and item.value[-1] == '"'
        if alias_quoted or name_quoted and not alias and name.islower():
            alias = '"' + (alias or name) + '"'
        if name and not name_quoted and not name.islower():
            if not alias:
                alias = name
            name = name.lower()
        return schema_name, name, alias


    for item in token_stream:
        if isinstance(item, IdentifierList):
            for identifier in item.get_identifiers():
                # Sometimes Keywords (such as FROM ) are classified as
                # identifiers which don't have the get_real_name() method.
                try:
                    schema_name = identifier.get_parent_name()
                    real_name = identifier.get_real_name()
                    is_function = (allow_functions and
                                   _identifier_is_function(identifier))
                except AttributeError:
                    continue
                if real_name:
                    yield TableReference(schema_name, real_name,
                                         identifier.get_alias(), is_function)
        elif isinstance(item, Identifier):
            schema_name, real_name, alias = parse_identifier(item)
            is_function = allow_functions and _identifier_is_function(item)

            yield TableReference(schema_name, real_name, alias, is_function)
        elif isinstance(item, Function):
            schema_name, real_name, alias = parse_identifier(item)
            yield TableReference(None, real_name, alias, allow_functions)


# extract_tables is inspired from examples in the sqlparse lib.
def extract_tables(sql):
    """Extract the table names from an SQL statment.

    Returns a list of TableReference namedtuples

    """
    parsed = sqlparse.parse(sql)
    if not parsed:
        return ()

    # INSERT statements must stop looking for tables at the sign of first
    # Punctuation. eg: INSERT INTO abc (col1, col2) VALUES (1, 2)
    # abc is the table name, but if we don't stop at the first lparen, then
    # we'll identify abc, col1 and col2 as table names.
    insert_stmt = parsed[0].token_first().value.lower() == 'insert'
    stream = extract_from_part(parsed[0], stop_at_punctuation=insert_stmt)

    # Kludge: sqlparse mistakenly identifies insert statements as
    # function calls due to the parenthesized column list, e.g. interprets
    # "insert into foo (bar, baz)" as a function call to foo with arguments
    # (bar, baz). So don't allow any identifiers in insert statements
    # to have is_function=True
    identifiers = extract_table_identifiers(stream,
                                            allow_functions=not insert_stmt)
    # In the case 'sche.<cursor>', we get an empty TableReference; remove that
    return tuple(i for i in identifiers if i.name)



def find_prev_keyword(sql):
    """ Find the last sql keyword in an SQL statement

    Returns the value of the last keyword, and the text of the query with
    everything after the last keyword stripped
    """
    if not sql.strip():
        return None, ''

    parsed = sqlparse.parse(sql)[0]
    flattened = list(parsed.flatten())

    logical_operators = ('AND', 'OR', 'NOT', 'BETWEEN')

    for t in reversed(flattened):
        if t.value == '(' or (t.is_keyword and (
                              t.value.upper() not in logical_operators)):
            # Find the location of token t in the original parsed statement
            # We can't use parsed.token_index(t) because t may be a child token
            # inside a TokenList, in which case token_index thows an error
            # Minimal example:
            #   p = sqlparse.parse('select * from foo where bar')
            #   t = list(p.flatten())[-3]  # The "Where" token
            #   p.token_index(t)  # Throws ValueError: not in list
            idx = flattened.index(t)

            # Combine the string values of all tokens in the original list
            # up to and including the target keyword token t, to produce a
            # query string with everything after the keyword token removed
            text = ''.join(tok.value for tok in flattened[:idx+1])
            return t, text

    return None, ''


# Postgresql dollar quote signs look like `$$` or `$tag$`
dollar_quote_regex = re.compile(r'^\$[^$]*\$$')


def is_open_quote(sql):
    """Returns true if the query contains an unclosed quote"""

    # parsed can contain one or more semi-colon separated commands
    parsed = sqlparse.parse(sql)
    return any(_parsed_is_open_quote(p) for p in parsed)


def _parsed_is_open_quote(parsed):
    tokens = list(parsed.flatten())

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.match(Token.Error, "'"):
            # An unmatched single quote
            return True
        elif (tok.ttype in Token.Name.Builtin
                and dollar_quote_regex.match(tok.value)):
            # Find the matching closing dollar quote sign
            for (j, tok2) in enumerate(tokens[i+1:], i+1):
                if tok2.match(Token.Name.Builtin, tok.value):
                    # Found the matching closing quote - continue our scan for
                    # open quotes thereafter
                    i = j
                    break
            else:
                # No matching dollar sign quote
                return True

        i += 1

    return False


def parse_partial_identifier(word):
    """Attempt to parse a (partially typed) word as an identifier

    word may include a schema qualification, like `schema_name.partial_name`
    or `schema_name.` There may also be unclosed quotation marks, like
    `"schema`, or `schema."partial_name`

    :param word: string representing a (partially complete) identifier
    :return: sqlparse.sql.Identifier, or None
    """

    p = sqlparse.parse(word)[0]
    n_tok = len(p.tokens)
    if n_tok == 1 and isinstance(p.tokens[0], Identifier):
        return p.tokens[0]
    elif p.token_next_match(0, Error, '"'):
        # An unmatched double quote, e.g. '"foo', 'foo."', or 'foo."bar'
        # Close the double quote, then reparse
        return parse_partial_identifier(word + '"')
    else:
        return None


if __name__ == '__main__':
    sql = 'select * from (select t. from tabl t'
    print (extract_tables(sql))
