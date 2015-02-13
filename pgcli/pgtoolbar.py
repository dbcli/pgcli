from prompt_toolkit.layout.toolbars import Toolbar
from prompt_toolkit.layout.utils import TokenList
from pygments.token import Token

class PGToolbar(Toolbar):
    def __init__(self, key_binding_manager, token=None):
        self.key_binding_manager = key_binding_manager
        token = token or Token.Toolbar.Status
        super(self.__class__, self).__init__(token=token)

    def get_tokens(self, cli, width):
        result = TokenList()
        result.append((self.token, ' '))

        if cli.buffers['default'].completer.smart_completion:
            result.append((self.token.On, '[F2] Smart Completion: ON  '))
        else:
            result.append((self.token.Off, '[F2] Smart Completion: OFF  '))

        if cli.buffers['default'].always_multiline:
            result.append((self.token.On, '[F3] Multiline: ON  '))
        else:
            result.append((self.token.Off, '[F3] Multiline: OFF  '))

        if cli.buffers['default'].always_multiline:
            result.append((self.token,
                ' (Semi-colon [;] will end the line)'))

        if self.key_binding_manager.enable_vi_mode:
            result.append((self.token.On, '[F4] Vi-mode'))
        else:
            result.append((self.token.On, '[F4] Emacs-mode'))

        return result
