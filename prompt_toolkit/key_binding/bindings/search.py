"""
Search related key bindings.
"""
from __future__ import unicode_literals
from ..key_bindings import key_binding
from prompt_toolkit.application.current import get_app
from prompt_toolkit.filters import is_searching, control_is_searchable, Condition
from prompt_toolkit import search

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
    search.stop_search()


@key_binding(filter=is_searching)
def accept_search(event):
    """
    When enter pressed in isearch, quit isearch mode. (Multiline
    isearch would be too complicated.)
    (Usually bound to Enter.)
    """
    search.accept_search()


@key_binding(filter=control_is_searchable)
def start_reverse_incremental_search(event):
    """
    Enter reverse incremental search.
    (Usually ControlR.)
    """
    search.start_search(direction=search.SearchDirection.BACKWARD)


@key_binding(filter=control_is_searchable)
def start_forward_incremental_search(event):
    """
    Enter forward incremental search.
    (Usually ControlS.)
    """
    search.start_search(direction=search.SearchDirection.FORWARD)


@key_binding(filter=is_searching)
def reverse_incremental_search(event):
    """
    Apply reverse incremental search, but keep search buffer focused.
    """
    search.do_incremental_search(
        search.SearchDirection.BACKWARD, count=event.arg)


@key_binding(filter=is_searching)
def forward_incremental_search(event):
    """
    Apply forward incremental search, but keep search buffer focused.
    """
    search.do_incremental_search(
        search.SearchDirection.FORWARD, count=event.arg)


@Condition
def _previous_buffer_is_returnable():
    """
    True if the previously focused buffer has a return handler.
    """
    prev_control = get_app().layout.search_target_buffer_control
    return prev_control and prev_control.buffer.is_returnable


@key_binding(filter=is_searching & _previous_buffer_is_returnable)
def accept_search_and_accept_input(event):
    """
    Accept the search operation first, then accept the input.
    """
    search.accept_search()
    event.current_buffer.validate_and_handle()
