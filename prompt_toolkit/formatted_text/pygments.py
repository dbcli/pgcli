from __future__ import unicode_literals
from prompt_toolkit.styles.pygments import pygments_token_to_classname

__all__ = [
    'PygmentsTokens',
]


class PygmentsTokens(object):
    """
    Turn a pygments token list into a list of prompt_toolkit text fragments
    (``(style_str, text)`` tuples).
    """
    def __init__(self, token_list):
        assert isinstance(token_list, list), 'Got %r' % (token_list, )
        self.token_list = token_list

    def __pt_formatted_text__(self):
        result = []

        for token, text in self.token_list:
            result.append(('class:' + pygments_token_to_classname(token), text))

        return result
