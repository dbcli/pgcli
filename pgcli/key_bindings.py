from prompt_toolkit.keys import Keys
from prompt_toolkit.enums import InputMode

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
        line.completer.smart_completion = not line.completer.smart_completion

    @handle(Keys.F3)
    def _(event):
        """
        Enable/Disable Multiline Mode.
        """
        #import pdb; pdb.set_trace()
        line.always_multiline = not line.always_multiline

    @handle(Keys.ControlSpace, in_mode=InputMode.INSERT)
    @handle(Keys.ControlSpace, in_mode=InputMode.SELECTION)
    def _(event):
        """
        Force autocompletion at cursor
        """
        line.complete_next()
