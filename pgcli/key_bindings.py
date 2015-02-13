import logging
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding.manager import KeyBindingManager

_logger = logging.getLogger(__name__)

def pgcli_bindings(vi_mode=False):
    """
    Custom key bindings for pgcli.
    """
    key_binding_manager = KeyBindingManager(enable_vi_mode=vi_mode)

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
        key_binding_manager.enable_vi_mode = not key_binding_manager.enable_vi_mode

    @key_binding_manager.registry.add_binding(Keys.ControlSpace)
    def _(event):
        """
        Force autocompletion at cursor.
        """
        _logger.debug('Detected <C-Space> key.')
        event.cli.current_buffer.complete_next()

    return key_binding_manager
