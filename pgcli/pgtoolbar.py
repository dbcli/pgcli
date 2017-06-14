from pygments.token import Token
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.key_binding.vi_state import InputMode


def _get_vi_mode(cli):
    return {
        InputMode.INSERT: 'I',
        InputMode.NAVIGATION: 'N',
        InputMode.REPLACE: 'R',
        InputMode.INSERT_MULTIPLE: 'M',
    }[cli.vi_state.input_mode]


def create_toolbar_tokens_func(get_vi_mode_enabled, get_is_refreshing,
                               failed_transaction, valid_transaction):
    """
    Return a function that generates the toolbar tokens.
    """
    assert callable(get_vi_mode_enabled)

    token = Token.Toolbar

    def get_toolbar_tokens(cli):
        result = []
        result.append((token, ' '))

        if cli.buffers[DEFAULT_BUFFER].completer.smart_completion:
            result.append((token.On, '[F2] Smart Completion: ON  '))
        else:
            result.append((token.Off, '[F2] Smart Completion: OFF  '))

        if cli.buffers[DEFAULT_BUFFER].always_multiline:
            result.append((token.On, '[F3] Multiline: ON  '))
        else:
            result.append((token.Off, '[F3] Multiline: OFF  '))

        if cli.buffers[DEFAULT_BUFFER].always_multiline:
            if cli.buffers[DEFAULT_BUFFER].multiline_mode == 'safe':
                result.append((token,' ([Esc] [Enter] to execute]) '))
            else:
                result.append((token,' (Semi-colon [;] will end the line) '))

        if get_vi_mode_enabled():
            result.append((token.On, '[F4] Vi-mode (' + _get_vi_mode(cli) + ')'))
        else:
            result.append((token.On, '[F4] Emacs-mode'))

        if failed_transaction():
            result.append((token.Transaction.Failed, '     Failed transaction'))

        if valid_transaction():
            result.append((token.Transaction.Valid, '     Transaction'))

        if get_is_refreshing():
            result.append((token, '     Refreshing completions...'))

        return result
    return get_toolbar_tokens
