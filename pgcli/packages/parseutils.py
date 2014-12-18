import re

# This matches only alphanumerics and underscores.
_LAST_WORD_RE = re.compile(r'(\w+)$')
# This matches everything except a space.
_LAST_WORD_SPL_RE = re.compile(r'([^\s]+)$')

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
        regex = _LAST_WORD_SPL_RE if include_special_chars else _LAST_WORD_RE
        result = regex.findall(text)
        if result:
            return result[0]
        else:
            return ''

def extract_tables(sql):
    return []

