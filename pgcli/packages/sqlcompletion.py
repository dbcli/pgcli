from __future__ import print_function
import sqlparse
from sqlparse.sql import Comparison
from parseutils import last_word, extract_tables, find_prev_keyword


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

    # Need to check if `p` is not empty, since an empty string will result in
    # an empty tuple.
    p = parsed[0] if parsed else None
    last_token = p and p.token_prev(len(p.tokens)) or ''

    return suggest_based_on_last_token(last_token, text_before_cursor, full_text)

def suggest_based_on_last_token(token, text_before_cursor, full_text):
    if isinstance(token, basestring):
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
            if last_word(text_before_cursor, 'all_punctuations').startswith('('):
                return 'keywords', []
        return 'columns', extract_tables(full_text)
    if token_v.lower() in ('set', 'by', 'distinct'):
        return 'columns', extract_tables(full_text)
    elif token_v.lower() in ('select', 'where', 'having'):
        return 'columns-and-functions', extract_tables(full_text)
    elif token_v.lower() in ('from', 'update', 'into', 'describe', 'join'):
        return 'tables', []
    elif token_v in ('d',):  # \d
        return 'tables', []
    elif token_v.lower() in ('c', 'use'):  # \c
        return 'databases', []
    elif token_v.endswith(','):
        prev_keyword = find_prev_keyword(text_before_cursor)
        return suggest_based_on_last_token(prev_keyword, text_before_cursor, full_text)
    elif token_v.endswith('.'):
        current_alias = last_word(token_v[:-1])
        tables = extract_tables(full_text, include_alias=True)
        return 'columns', [tables.get(current_alias) or current_alias]
    else:
        return 'keywords', []
