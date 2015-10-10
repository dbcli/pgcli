from prompt_toolkit.filters import Filter

class HasSelectedCompletion(Filter):
    """Enable when the current buffer has a selected completion."""

    def __call__(self, cli):
        complete_state = cli.current_buffer.complete_state
        return (complete_state is not None and
                complete_state.current_completion is not None)

    def __repr__(self):
        return "HasSelectedCompletion()"
