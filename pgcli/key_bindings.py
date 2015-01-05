import logging
from prompt_toolkit.keys import Keys
from prompt_toolkit.enums import InputMode

_logger = logging.getLogger(__name__)

def pgcli_bindings(registry, cli_ref):
    """
    Custom key bindings for pgcli.
    """
    line = cli_ref().line
    handle = registry.add_binding

    @handle(Keys.F2)
    def _(event):
        """
        Enable/Disable SmartCompletion Mode.
        """
        _logger.debug('Detected F2 key.')
        line.completer.smart_completion = not line.completer.smart_completion

    @handle(Keys.F3)
    def _(event):
        """
        Enable/Disable Multiline Mode.
        """
        _logger.debug('Detected F3 key.')
        line.always_multiline = not line.always_multiline

    @handle(Keys.ControlSpace, in_mode=InputMode.INSERT)
    def _(event):
        """
        Force autocompletion at cursor.
        """
        _logger.debug('Detected <C-Space> key.')
        line.complete_next()
