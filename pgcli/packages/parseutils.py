import re
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Function
from sqlparse.tokens import Keyword, DML, Punctuation

cleanup_regex = {
        # This matches only alphanumerics and underscores.
        'alphanum_underscore': re.compile(r'(\w+)$'),
        # This matches everything except spaces, parens and comma.
        'most_punctuations': re.compile(r'([^\.(),\s]+)$'),
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
    >>> last_word('bac $def', True)
    '$def'
    >>> last_word('bac \def', True)
    '\\\\def'
    >>> last_word('bac \def;', True)
    '\\\\def;'
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

def extract_from_part(parsed):
    tbl_prefix_seen = False
    for item in parsed.tokens:
        if tbl_prefix_seen:
            if is_subselect(item):
                for x in extract_from_part(item):
                    yield x
            elif item.ttype is Keyword or item.ttype is Punctuation:
                raise StopIteration
            else:
                yield item
        elif item.ttype is Keyword and item.value.upper() in ('FROM', 'INTO',
                'UPDATE', 'TABLE', ):
            tbl_prefix_seen = True
        # 'SELECT a, FROM abc' will detect FROM as part of the column list.
        # So this check here is necessary.
        elif isinstance(item, IdentifierList):
            for identifier in item.get_identifiers():
                if identifier.ttype is Keyword and identifier.value.upper() == 'FROM':
                    tbl_prefix_seen = True
                    break

def extract_table_identifiers(token_stream):
    for item in token_stream:
        if isinstance(item, IdentifierList):
            for identifier in item.get_identifiers():
                real_name = identifier.get_real_name()
                yield (real_name, identifier.get_alias() or real_name)
        elif isinstance(item, Identifier):
            real_name = item.get_real_name()
            yield (real_name, item.get_alias() or real_name)
        elif isinstance(item, Function):
            yield (item.get_name(), item.get_name())
        # It's a bug to check for Keyword here, but in the example
        # above some tables names are identified as keywords...
        elif item.ttype is Keyword:
            yield (item.value, item.value)

def extract_tables(sql, include_alias=False):
    if not sql:
        return []
    stream = extract_from_part(sqlparse.parse(sql)[0])
    if include_alias:
        return dict((alias, t) for t, alias in extract_table_identifiers(stream))
    else:
        return [x[0] for x in extract_table_identifiers(stream)]
