"""
Search related key bindings.
"""
from __future__ import unicode_literals
from ..key_bindings import key_binding
from prompt_toolkit.application.current import get_app
from prompt_toolkit.enums import SearchDirection
from prompt_toolkit.filters import is_searching, control_is_searchable, Condition
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.layout.controls import BufferControl

__all__ = [
    'abort_search',
    'accept_search',
    'start_reverse_incremental_search',
    'start_forward_incremental_search',
    'reverse_incremental_search',
    'forward_incremental_search',
    'accept_search_and_accept_input',
]


@key_binding(filter=is_searching)
def abort_search(event):
    """
    Abort an incremental search and restore the original
    line.
    (Usually bound to ControlG/ControlC.)
    """
    event.current_buffer.reset()

    target_buffer_control = event.app.layout.search_target_buffer_control
    search_control = event.app.layout.current_control

    # Stop search and focus previous control again.
    event.app.layout.stop_search(target_buffer_control, search_control)

    # If we're in Vi mode, go back to navigation mode.
    event.app.vi_state.input_mode = InputMode.NAVIGATION


@key_binding(filter=is_searching)
def accept_search(event):
    """
    When enter pressed in isearch, quit isearch mode. (Multiline
    isearch would be too complicated.)
    (Usually bound to Enter.)
    """
    search_control = event.app.layout.current_control
    target_buffer_control = event.app.layout.search_target_buffer_control
    search_state = target_buffer_control.search_state

    # Update search state.
    if search_control.buffer.text:
        search_state.text = search_control.buffer.text

    # Apply search.
    target_buffer_control.buffer.apply_search(search_state, include_current_position=True)

    # Add query to history of search line.
    search_control.buffer.append_to_history()
    search_control.buffer.reset()

    # Stop search and focus previous control again.
    event.app.layout.stop_search(target_buffer_control, search_control)

    # If we're in Vi mode, go back to navigation mode.
    event.app.vi_state.input_mode = InputMode.NAVIGATION


@key_binding(filter=control_is_searchable)
def start_reverse_incremental_search(event):
    """
    Enter reverse incremental search.
    (Usually ControlR.)
    """
    control = event.app.layout.current_control
    search_state = control.search_state

    search_state.direction = SearchDirection.BACKWARD

    event.app.layout.start_search(control, control.search_buffer_control)

    # If we're in Vi mode, make sure to go into insert mode.
    event.app.vi_state.input_mode = InputMode.INSERT


@key_binding(filter=control_is_searchable)
def start_forward_incremental_search(event):
    """
    Enter forward incremental search.
    (Usually ControlS.)
    """
    control = event.app.layout.current_control
    search_state = control.search_state

    search_state.direction = SearchDirection.FORWARD

    event.app.layout.start_search(control, control.search_buffer_control)

    # If we're in Vi mode, make sure to go into insert mode.
    event.app.vi_state.input_mode = InputMode.INSERT


def _incremental_search(app, direction, count=1):
    " Apply search, but keep search buffer focused. "
    assert is_searching()

    search_control = app.layout.current_control
    prev_control = app.layout.previous_control
    search_state = prev_control.search_state

    # Update search_state.
    direction_changed = search_state.direction != direction

    search_state.text = search_control.buffer.text
    search_state.direction = direction

    # Apply search to current buffer.
    if not direction_changed:
        prev_control.buffer.apply_search(
            search_state, include_current_position=False, count=count)


@key_binding(filter=is_searching)
def reverse_incremental_search(event):
    """
    Apply reverse incremental search, but keep search buffer focused.
    """
    _incremental_search(
        event.app, SearchDirection.BACKWARD, count=event.arg)


@key_binding(filter=is_searching)
def forward_incremental_search(event):
    """
    Apply forward incremental search, but keep search buffer focused.
    """
    _incremental_search(
        event.app, SearchDirection.FORWARD, count=event.arg)


@Condition
def _previous_buffer_is_returnable():
    """
    True if the previously focused buffer has a return handler.
    """
    prev_control = get_app().layout.previous_control
    if isinstance(prev_control, BufferControl):
        return prev_control.buffer.is_returnable
    return False


@key_binding(filter=is_searching & _previous_buffer_is_returnable)
def accept_search_and_accept_input(event):
    """
    Accept the search operation first, then accept the input.
    """
    accept_search.call(event)
    event.current_buffer.validate_and_handle()
