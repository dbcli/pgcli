"""
Filters that accept a `Application` as argument.
"""
from __future__ import unicode_literals
from .base import Condition
from prompt_toolkit.cache import memoized
from prompt_toolkit.enums import EditingMode
import six

__all__ = (
    'has_arg',
    'has_completions',
    'has_focus',
    'has_selection',
    'has_validation_error',
    'is_aborting',
    'is_done',
    'is_read_only',
    'is_multiline',
    'renderer_height_is_known',
    'in_editing_mode',
    'in_paste_mode',

    'vi_mode',
    'vi_navigation_mode',
    'vi_insert_mode',
    'vi_insert_multiple_mode',
    'vi_replace_mode',
    'vi_selection_mode',
    'vi_waiting_for_text_object_mode',
    'vi_digraph_mode',

    'emacs_mode',
    'emacs_insert_mode',
    'emacs_selection_mode',

    'is_searching',
    'control_is_searchable',
    'vi_search_direction_reversed',
)


@memoized()
def has_focus(value):
    """
    Enable when this buffer has the focus.
    """
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.layout.controls import UIControl
    from prompt_toolkit.layout.containers import to_window

    if isinstance(value, six.text_type):
        def test(app):
            return app.current_buffer.name == value
    elif isinstance(value, Buffer):
        def test(app):
            return app.current_buffer == value
    elif isinstance(value, UIControl):
        def test(app):
            return app.layout.current_control == value
    else:
        value = to_window(value)

        def test(app):
            return app.layout.current_window == value

    @Condition
    def has_focus_filter(app):
        return test(app)
    return has_focus_filter


@Condition
def has_selection(app):
    """
    Enable when the current buffer has a selection.
    """
    return bool(app.current_buffer.selection_state)


@Condition
def has_completions(app):
    """
    Enable when the current buffer has completions.
    """
    return app.current_buffer.complete_state is not None


@Condition
def is_read_only(app):
    """
    True when the current buffer is read only.
    """
    return app.current_buffer.read_only()


@Condition
def is_multiline(app):
    """
    True when the current buffer has been marked as multiline.
    """
    return app.current_buffer.multiline()


@Condition
def has_validation_error(app):
    " Current buffer has validation error.  "
    return app.current_buffer.validation_error is not None


@Condition
def has_arg(app):
    " Enable when the input processor has an 'arg'. "
    return app.key_processor.arg is not None


@Condition
def is_aborting(app):
    " True when aborting. (E.g. Control-C pressed.) "
    return app.is_aborting


@Condition
def is_exiting(app):
    """
    True when exiting. (E.g. Control-D pressed.)
    """
    return app.is_exiting


@Condition
def is_done(app):
    """
    True when the CLI is returning, aborting or exiting.
    """
    return app.is_done


@Condition
def renderer_height_is_known(app):
    """
    Only True when the renderer knows it's real height.

    (On VT100 terminals, we have to wait for a CPR response, before we can be
    sure of the available height between the cursor position and the bottom of
    the terminal. And usually it's nicer to wait with drawing bottom toolbars
    until we receive the height, in order to avoid flickering -- first drawing
    somewhere in the middle, and then again at the bottom.)
    """
    return app.renderer.height_is_known


@memoized()
def in_editing_mode(editing_mode):
    " Check whether a given editing mode is active. (Vi or Emacs.) "
    @Condition
    def in_editing_mode_filter(app):
        return app.editing_mode == editing_mode
    return in_editing_mode_filter


@Condition
def in_paste_mode(app):
    return app.paste_mode(app)


@Condition
def vi_mode(app):
    return app.editing_mode == EditingMode.VI


@Condition
def vi_navigation_mode(app):
    " Active when the set for Vi navigation key bindings are active. "
    from prompt_toolkit.key_binding.vi_state import InputMode
    if (app.editing_mode != EditingMode.VI
            or app.vi_state.operator_func
            or app.vi_state.waiting_for_digraph
            or app.current_buffer.selection_state):
        return False

    return (app.vi_state.input_mode == InputMode.NAVIGATION or
            app.current_buffer.read_only())


@Condition
def vi_insert_mode(app):
    from prompt_toolkit.key_binding.vi_state import InputMode
    if (app.editing_mode != EditingMode.VI
            or app.vi_state.operator_func
            or app.vi_state.waiting_for_digraph
            or app.current_buffer.selection_state
            or app.current_buffer.read_only()):
        return False

    return app.vi_state.input_mode == InputMode.INSERT


@Condition
def vi_insert_multiple_mode(app):
    from prompt_toolkit.key_binding.vi_state import InputMode
    if (app.editing_mode != EditingMode.VI
            or app.vi_state.operator_func
            or app.vi_state.waiting_for_digraph
            or app.current_buffer.selection_state
            or app.current_buffer.read_only()):
        return False

    return app.vi_state.input_mode == InputMode.INSERT_MULTIPLE


@Condition
def vi_replace_mode(app):
    from prompt_toolkit.key_binding.vi_state import InputMode
    if (app.editing_mode != EditingMode.VI
            or app.vi_state.operator_func
            or app.vi_state.waiting_for_digraph
            or app.current_buffer.selection_state
            or app.current_buffer.read_only()):
        return False

    return app.vi_state.input_mode == InputMode.REPLACE


@Condition
def vi_selection_mode(app):
    if app.editing_mode != EditingMode.VI:
        return False

    return bool(app.current_buffer.selection_state)


@Condition
def vi_waiting_for_text_object_mode(app):
    if app.editing_mode != EditingMode.VI:
        return False

    return app.vi_state.operator_func is not None


@Condition
def vi_digraph_mode(app):
    if app.editing_mode != EditingMode.VI:
        return False

    return app.vi_state.waiting_for_digraph


@Condition
def emacs_mode(app):
    " When the Emacs bindings are active. "
    return app.editing_mode == EditingMode.EMACS


@Condition
def emacs_insert_mode(app):
    if (app.editing_mode != EditingMode.EMACS
            or app.current_buffer.selection_state
            or app.current_buffer.read_only()):
        return False
    return True


@Condition
def emacs_selection_mode(app):
    return (app.editing_mode == EditingMode.EMACS
            and app.current_buffer.selection_state)


@Condition
def is_searching(app):
    " When we are searching. "
    from prompt_toolkit.layout.controls import BufferControl
    control = app.layout.current_control
    prev = app.layout.previous_control

    return (isinstance(prev, BufferControl) and
            isinstance(control, BufferControl) and
            prev.search_buffer_control is not None and
            prev.search_buffer_control == control)


@Condition
def control_is_searchable(app):
    " When the current UIControl is searchable. "
    from prompt_toolkit.layout.controls import BufferControl
    control = app.layout.current_control

    return (isinstance(control, BufferControl) and
            control.search_buffer_control is not None)


@Condition
def vi_search_direction_reversed(app):
    " When the '/' and '?' key bindings for Vi-style searching have been reversed. "
    return app.reverse_vi_search_direction(app)
