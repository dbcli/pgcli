import logging
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.filters import Condition
from .filters import HasSelectedCompletion

_logger = logging.getLogger(__name__)


def pgcli_bindings(get_vi_mode_enabled, set_vi_mode_enabled):
    """
    Custom key bindings for pgcli.
    """
    assert callable(get_vi_mode_enabled)
    assert callable(set_vi_mode_enabled)

    key_binding_manager = KeyBindingManager(
        enable_open_in_editor=True,
        enable_system_bindings=True,
        enable_search=True,
        enable_abort_and_exit_bindings=True)

    @key_binding_manager.registry.add_binding(Keys.F2)
    def _(event):
        """
        Enable/Disable SmartCompletion Mode.
        """
        _logger.debug('Detected F2 key.')
        buf = event.cli.current_buffer
        buf.completer.smart_completion = not buf.completer.smart_completion

    @key_binding_manager.registry.add_binding(Keys.F3)
    def _(event):
        """
        Enable/Disable Multiline Mode.
        """
        _logger.debug('Detected F3 key.')
        buf = event.cli.current_buffer
        buf.always_multiline = not buf.always_multiline

    @key_binding_manager.registry.add_binding(Keys.F4)
    def _(event):
        """
        Toggle between Vi and Emacs mode.
        """
        _logger.debug('Detected F4 key.')
        vi_mode = not get_vi_mode_enabled()
        set_vi_mode_enabled(vi_mode)

        event.cli.editing_mode = EditingMode.VI if vi_mode else EditingMode.EMACS

    @key_binding_manager.registry.add_binding(Keys.Tab)
    def _(event):
        """
        Force autocompletion at cursor.
        """
        _logger.debug('Detected <Tab> key.')
        b = event.cli.current_buffer
        if b.complete_state:
            b.complete_next()
        else:
            event.cli.start_completion(select_first=True)

    @key_binding_manager.registry.add_binding(Keys.ControlSpace)
    def _(event):
        """
        Initialize autocompletion at cursor.

        If the autocompletion menu is not showing, display it with the
        appropriate completions for the context.

        If the menu is showing, select the next completion.
        """
        _logger.debug('Detected <C-Space> key.')

        b = event.cli.current_buffer
        if b.complete_state:
            b.complete_next()
        else:
            event.cli.start_completion(select_first=False)

    @key_binding_manager.registry.add_binding(Keys.ControlJ, filter=HasSelectedCompletion())
    def _(event):
        """
        Makes the enter key work as the tab key only when showing the menu.
        """
        _logger.debug('Detected <C-J> key.')

        event.current_buffer.complete_state = None
        b = event.cli.current_buffer
        b.complete_state = None

    return key_binding_manager
