import re
import sqlparse
from sqlparse.sql import Identifier
from sqlparse.tokens import Token, Error

cleanup_regex = {
    # This matches only alphanumerics and underscores.
    "alphanum_underscore": re.compile(r"(\w+)$"),
    # This matches everything except spaces, parens, colon, and comma
    "many_punctuations": re.compile(r"([^():,\s]+)$"),
    # This matches everything except spaces, parens, colon, comma, and period
    "most_punctuations": re.compile(r"([^\.():,\s]+)$"),
    # This matches everything except a space.
    "all_punctuations": re.compile(r"([^\s]+)$"),
}


def last_word(text, include="alphanum_underscore"):
    r"""
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

    if not text:  # Empty string
        return ""

    if text[-1].isspace():
        return ""
    else:
        regex = cleanup_regex[include]
        matches = regex.search(text)
        if matches:
            return matches.group(0)
        else:
            return ""


def find_prev_keyword(sql, n_skip=0):
    """Find the last sql keyword in an SQL statement

    Returns the value of the last keyword, and the text of the query with
    everything after the last keyword stripped
    """
    if not sql.strip():
        return None, ""

    parsed = sqlparse.parse(sql)[0]
    flattened = list(parsed.flatten())
    flattened = flattened[: len(flattened) - n_skip]

    logical_operators = ("AND", "OR", "NOT", "BETWEEN")

    for t in reversed(flattened):
        if t.value == "(" or (
            t.is_keyword and (t.value.upper() not in logical_operators)
        ):
            # Find the location of token t in the original parsed statement
            # We can't use parsed.token_index(t) because t may be a child token
            # inside a TokenList, in which case token_index throws an error
            # Minimal example:
            #   p = sqlparse.parse('select * from foo where bar')
            #   t = list(p.flatten())[-3]  # The "Where" token
            #   p.token_index(t)  # Throws ValueError: not in list
            idx = flattened.index(t)

            # Combine the string values of all tokens in the original list
            # up to and including the target keyword token t, to produce a
            # query string with everything after the keyword token removed
            text = "".join(tok.value for tok in flattened[: idx + 1])
            return t, text

    return None, ""


# Postgresql dollar quote signs look like `$$` or `$tag$`
dollar_quote_regex = re.compile(r"^\$[^$]*\$$")


def is_open_quote(sql):
    """Returns true if the query contains an unclosed quote"""

    # parsed can contain one or more semi-colon separated commands
    parsed = sqlparse.parse(sql)
    return any(_parsed_is_open_quote(p) for p in parsed)


def _parsed_is_open_quote(parsed):
    # Look for unmatched single quotes, or unmatched dollar sign quotes
    return any(tok.match(Token.Error, ("'", "$")) for tok in parsed.flatten())


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
    elif p.token_next_by(m=(Error, '"'))[1]:
        # An unmatched double quote, e.g. '"foo', 'foo."', or 'foo."bar'
        # Close the double quote, then reparse
        return parse_partial_identifier(word + '"')
    else:
        return None
