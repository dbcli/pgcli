from __future__ import print_function
import sqlparse
from parseutils import last_word, extract_tables


def suggest_type(full_text, text_before_cursor):
    """Takes the full_text that is typed so far and also the text before the
    cursor to suggest completion type and scope.

    Returns a tuple with a type of entity ('table', 'column' etc) and a scope.
    A scope for a column category will be a list of tables.
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

    def is_function_word(word):
        return word and len(word) > 1 and word[-1] == '('

    if is_function_word(word_before_cursor):
        return ('columns', extract_tables(full_text))
    elif last_token.lower() in ('set', 'by', 'distinct'):
        return ('columns', extract_tables(full_text))
    elif last_token.lower() in ('select', 'where', 'having'):
        return ('columns-and-functions', extract_tables(full_text))
    elif last_token.lower() in ('from', 'update', 'into', 'describe'):
        return ('tables', [])
    elif last_token in ('d',):  # \d
        return ('tables', [])
    elif last_token.lower() in ('c', 'use'):  # \c
        return ('databases', [])
    else:
        return ('keywords', [])
