from pygments.token import Token
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.application import get_app
from prompt_toolkit.formatted_text import PygmentsTokens


def _get_vi_mode():
    return {
        InputMode.INSERT: 'I',
        InputMode.NAVIGATION: 'N',
        InputMode.REPLACE: 'R',
        InputMode.INSERT_MULTIPLE: 'M',
    }[get_app().vi_state.input_mode]


def create_toolbar_tokens_func(pgcli):
    """
    Return a function that generates the toolbar tokens.
    """
    token = Token.Toolbar

    def get_toolbar_tokens():
        layout = get_app().layout

        result = []
        result.append((token, ' '))

        if pgcli.completer.smart_completion:
            result.append((token.On, '[F2] Smart Completion: ON  '))
        else:
            result.append((token.Off, '[F2] Smart Completion: OFF  '))

        if pgcli.multi_line:
            result.append((token.On, '[F3] Multiline: ON  '))
        else:
            result.append((token.Off, '[F3] Multiline: OFF  '))

        if pgcli.multi_line:
            if pgcli.multiline_mode == 'safe':
                result.append((token,' ([Esc] [Enter] to execute]) '))
            else:
                result.append((token,' (Semi-colon [;] will end the line) '))

        if pgcli.vi_mode:
            result.append((token.On, '[F4] Vi-mode (' + _get_vi_mode() + ')'))
        else:
            result.append((token.On, '[F4] Emacs-mode'))

        if pgcli.pgexecute.failed_transaction():
            result.append((token.Transaction.Failed, '     Failed transaction'))

        if pgcli.pgexecute.valid_transaction():
            result.append((token.Transaction.Valid, '     Transaction'))

        if pgcli.completion_refresher.is_refreshing():
            result.append((token, '     Refreshing completions...'))

        return PygmentsTokens(result)
    return get_toolbar_tokens
