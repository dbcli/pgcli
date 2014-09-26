from .rules import TokenStream
from .lexer import lex_document


__all__ = (
    'get_parse_info',
    'InvalidCommandException',
)


class InvalidCommandException(Exception):
    def __init__(self):
        super(InvalidCommandException, self).__init__('Invalid command.')


def get_parse_info(grammar, document):
    parts, last_part_token = lex_document(document, only_before_cursor=True)
    stream = TokenStream(parts + [last_part_token.unescaped_text])  # TODO: raise error when this last token is not finished.

    trees = list(grammar.parse(stream))

    if len(trees) == 1:
        return(trees[0])
    else:
        raise InvalidCommandException()
