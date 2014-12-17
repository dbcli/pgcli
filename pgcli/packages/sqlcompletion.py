import re
import sqlparse

# Regex for finding "words" in documents. (We consider a group of alnum
# characters a word, but also a group of special characters a word, as long as
# it doesn't contain a space.)
# (This is a 'word' in Vi.)
_FIND_WORD_RE = re.compile(r'(\w+)$')
# Regex for finding "WORDS" in documents.
# (This is a 'WORD in Vi.)
_FIND_BIG_WORD_RE = re.compile(r'([^\s]+)$')

def last_word(text, include_special_chars=False):
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
        regex = _FIND_BIG_WORD_RE if include_special_chars else _FIND_WORD_RE
        result = regex.findall(text)
        if result:
            return result[0]
        else:
            return ''

def suggest_type(full_text, text_before_cursor):
    """Takes the full_text that is typed so far and also the text before the
    cursor to suggest completion type and scope.

    Returns a tuple with a type of entity ('table', 'column' etc) and a scope.
    A scope for a column category will be the table name. Scope is set to None
    if unavailable.
    """

    word_before_cursor = last_word(text_before_cursor,
            include_special_chars=True)

    # If we've partially typed a word then word_before_cursor won't be an
    # empty string. In that case we want to remove the partially typed
    # string before sending it to the sqlparser. Otherwise the last token
    # will always be the partially typed string which renders the smart
    # completion useless because it will always return the list of keywords
    # as completion.
    if word_before_cursor:
        parsed = sqlparse.parse(
                text_before_cursor[:-len(word_before_cursor)])
    else:
        parsed = sqlparse.parse(text_before_cursor)

    last_token = ''
    if parsed:
        last_token = parsed[0].token_prev(len(parsed[0].tokens))
        last_token = last_token.value if last_token else ''

    if last_token.lower() in ('select', 'where', 'having', 'set',
            'order by', 'group by'):
        return ('columns', None)
    elif last_token.lower() in ('from', 'update', 'into', 'describe'):
        return ('tables', None)
    elif last_token in ('d',):  # \d
        return ('tables', None)
    elif last_token.lower() in ('c', 'use'):  # \c
        return ('databases', None)
    else:
        return ('keywords', None)
