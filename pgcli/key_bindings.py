import logging
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition, completion_is_selected

_logger = logging.getLogger(__name__)


def pgcli_bindings(pgcli):
    """
    Custom key bindings for pgcli.
    """
    kb = KeyBindings()

    @kb.add('f2')
    def _(event):
        """
        Enable/Disable SmartCompletion Mode.
        """
        _logger.debug('Detected F2 key.')
        buf = event.app.current_buffer
        buf.completer.smart_completion = not buf.completer.smart_completion

    @kb.add('f3')
    def _(event):
        """
        Enable/Disable Multiline Mode.
        """
        _logger.debug('Detected F3 key.')
        buf = event.app.current_buffer
        pgcli.multi_line = not pgcli.multi_line

    @kb.add('f4')
    def _(event):
        """
        Toggle between Vi and Emacs mode.
        """
        _logger.debug('Detected F4 key.')
        pgcli.vi_mode = not pgcli.vi_mode
        event.app.editing_mode = EditingMode.VI if pgcli.vi_mode else EditingMode.EMACS

    @kb.add('tab')
    def _(event):
        """
        Force autocompletion at cursor.
        """
        _logger.debug('Detected <Tab> key.')
        b = event.app.current_buffer
        if b.complete_state:
            b.complete_next()
        else:
            b.start_completion(select_first=True)

    @kb.add('c-space')
    def _(event):
        """
        Initialize autocompletion at cursor.

        If the autocompletion menu is not showing, display it with the
        appropriate completions for the context.

        If the menu is showing, select the next completion.
        """
        _logger.debug('Detected <C-Space> key.')

        b = event.app.current_buffer
        if b.complete_state:
            b.complete_next()
        else:
            b.start_completion(select_first=False)

    @kb.add('enter', filter=completion_is_selected)
    def _(event):
        """
        Makes the enter key work as the tab key only when showing the menu.
        """
        _logger.debug('Detected <C-J> key.')

        event.current_buffer.complete_state = None
        b = event.app.current_buffer
        b.complete_state = None

    return kb
