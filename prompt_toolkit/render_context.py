from __future__ import unicode_literals

class RenderContext(object):
    """
    :attr prompt: :class:`~prompt_toolkit.prompt.Prompt` instance.
    :attr code_obj: :class:`~prompt_toolkit.code.Code` instance.
    :param accept: True when the user accepts the input, by pressing enter.
                   (In that case we don't highlight the current line, and
                   set the mouse cursor at the end.)
    :param abort: True after Ctrl-C abort.
    :param highlighted_characters: `None` or list of (start,len) tuples of the
                              characters to highlight.
    """
    def __init__(self, line, code_obj, accept=False, abort=False,
                highlighted_characters=None, complete_state=None,
                validation_error=None):
        assert not (accept and abort)

        self.line = line
        self.code_obj = code_obj
        self.accept = accept
        self.abort = abort
        self.highlighted_characters = highlighted_characters
        self.complete_state = complete_state
        self.validation_error = validation_error
