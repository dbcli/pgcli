from prompt_toolkit.layout.toolbars import Toolbar
from prompt_toolkit.layout.utils import TokenList
from pygments.token import Token

class PGToolbar(Toolbar):
    def __init__(self, token=None):
        token = token or Token.Toolbar.Status
        super(self.__class__, self).__init__(token=token)

    def get_tokens(self, cli, width):
        result = TokenList()
        result.append((self.token, ' '))
        if cli.line.completer.smart_completion:
            result.append((self.token.On, '[F2] Smart Completion (on)'))
        else:
            result.append((self.token.Off, '[F2] Smart Completion (off)'))

        #result.append((self.token, ' ' * (width - len(result))))
        return result
