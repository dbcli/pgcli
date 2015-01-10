import logging
from prompt_toolkit import filters
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding.registry import Registry
from prompt_toolkit.key_binding.bindings.emacs import load_emacs_bindings

_logger = logging.getLogger(__name__)

def pgcli_bindings():
    """
    Custom key bindings for pgcli.
    """
    registry = Registry()
    load_emacs_bindings(registry)

    handle = registry.add_binding

    @handle(Keys.F2)
    def _(event):
        """
        Enable/Disable SmartCompletion Mode.
        """
        _logger.debug('Detected F2 key.')
        buf = event.cli.current_buffer
        buf.completer.smart_completion = not buf.completer.smart_completion

    @handle(Keys.F3)
    def _(event):
        """
        Enable/Disable Multiline Mode.
        """
        _logger.debug('Detected F3 key.')
        buf = event.cli.current_buffer
        buf.always_multiline = not buf.always_multiline

    @handle(Keys.ControlSpace, filter=~filters.HasSelection())
    def _(event):
        """
        Force autocompletion at cursor.
        """
        _logger.debug('Detected <C-Space> key.')
        event.cli.current_buffer.complete_next()

    return registry
