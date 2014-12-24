from __future__ import print_function
import sqlparse
from parseutils import last_word, extract_tables


def suggest_type(full_text, text_before_cursor):
    """Takes the full_text that is typed so far and also the text before the
    cursor to suggest completion type and scope.

    Returns a tuple with a type of entity ('table', 'column' etc) and a scope.
    A scope for a column category will be a list of tables.
    """

    tables = extract_tables(full_text)

    word_before_cursor = last_word(text_before_cursor,
            include='all_punctuations')

    # If we've partially typed a word then word_before_cursor won't be an empty
    # string. In that case we want to remove the partially typed string before
    # sending it to the sqlparser. Otherwise the last token will always be the
    # partially typed string which renders the smart completion useless because
    # it will always return the list of keywords as completion.
    if word_before_cursor:
        parsed = sqlparse.parse(
                text_before_cursor[:-len(word_before_cursor)])
    else:
        parsed = sqlparse.parse(text_before_cursor)

    # Need to check if `p` is not empty, since an empty string will result in
    # an empty tuple.
    p = parsed[0] if parsed else None
    n = p and len(p.tokens) or 0
    last_token = p and p.token_prev(n) or ''
    last_token_v = last_token.value if last_token else ''

    def is_function_word(word):
        return word and len(word) > 1 and word[-1] == '('

    if is_function_word(word_before_cursor):
        return ('columns', extract_tables(full_text))
    elif last_token_v.lower().endswith('('):
        return ('columns', tables)
    if last_token_v.lower() in ('set', 'by', 'distinct'):
        return ('columns', tables)
    elif last_token_v.lower() in ('select', 'where', 'having'):
        return ('columns-and-functions', tables)
    elif last_token_v.lower() in ('from', 'update', 'into', 'describe'):
        return ('tables', tables)
    elif last_token_v in ('d',):  # \d
        return ('tables', tables)
    elif last_token_v.lower() in ('c', 'use'):  # \c
        return ('databases', tables)
    elif last_token_v == ',':
        prev_keyword = find_prev_keyword(text_before_cursor)
        if prev_keyword in('select', 'where', 'having'):
            return ('columns-and-functions', tables)
        return ('keywords', tables)
    else:
        return ('keywords', tables)

def find_prev_keyword(sql):
    if not sql.strip():
        return None

    for t in sqlparse.parse(sql)[0].flatten():
        if t.is_keyword:
            return t.value.lower()
