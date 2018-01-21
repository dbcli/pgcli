"""
Wrapper for the layout.
"""
from __future__ import unicode_literals
from .controls import UIControl, BufferControl
from .containers import Window, to_container, to_window, ConditionalContainer
from prompt_toolkit.buffer import Buffer
import six

__all__ = (
    'Layout',
    'InvalidLayoutError',
    'walk',
)


class Layout(object):
    """
    The layout for a prompt_toolkit
    :class:`~prompt_toolkit.application.Application`.
    This also keeps track of which user control is focussed.

    :param container: The "root" container for the layout.
    :param focussed_window: The `Window` to be focused initially.
    """
    def __init__(self, container, focussed_window=None):
        self.container = to_container(container)
        self._stack = []

        # Map search BufferControl back to the original BufferControl.
        # This is used to keep track of when exactly we are searching, and for
        # applying the search.
        self.search_links = {}

        # Mapping that maps the children in the layout to their parent.
        # This relationship is calculated dynamically, each time when the UI
        # is rendered.  (UI elements have only references to their children.)
        self._child_to_parent = {}

        if focussed_window is None:
            try:
                self._stack.append(next(self.find_all_windows()))
            except StopIteration:
                raise InvalidLayoutError('Invalid layout. The layout does not contain any Window object.')
        else:
            self._stack.append(to_window(focussed_window))

        # List of visible windows.
        self.visible_windows = []  # type: List[Window]

    def __repr__(self):
        return 'Layout(%r, current_window=%r)' % (
            self.container, self.current_window)

    def find_all_windows(self):
        """
        Find all the `UIControl` objects in this layout.
        """
        for item in self.walk():
            if isinstance(item, Window):
                yield item

    def find_all_controls(self):
        for container in self.find_all_windows():
            yield container.content

    def focus(self, value):
        """
        Focus the given UI element.

        `value` can be either:
        - a `UIControl`
        - a `Buffer` instance or the name of a `Buffer`
        - a `Window`
        - Any container object. In this case we will focus the `Window` from
          this container that was focussed most recent, or the very first
          focussable `Window` of the container.
        """
        # BufferControl by buffer name.
        if isinstance(value, six.text_type):
            for control in self.find_all_controls():
                if isinstance(control, BufferControl) and control.buffer.name == value:
                    self.focus(control)
                    return
            raise ValueError("Couldn't find Buffer in the current layout: %r." % (value, ))

        # BufferControl by buffer object.
        elif isinstance(value, Buffer):
            for control in self.find_all_controls():
                if isinstance(control, BufferControl) and control.buffer == value:
                    self.focus(control)
                    return
            raise ValueError("Couldn't find Buffer in the current layout: %r." % (value, ))

        # Focus UIControl.
        elif isinstance(value, UIControl):
            if value not in self.find_all_controls():
                raise ValueError('Invalid value. Container does not appear in the layout.')
            if not value.is_focussable():
                raise ValueError('Invalid value. UIControl is not focussable.')

            self.current_control = value

        # Otherwise, expecting any Container object.
        else:
            value = to_container(value)

            if isinstance(value, Window):
                # This is a `Window`: focus that.
                if value not in self.find_all_windows():
                    raise ValueError('Invalid value. Window does not appear in the layout: %r' %
                            (value, ))

                self.current_window = value
            else:
                # Focus a window in this container.
                # If we have many windows as part of this container, and some
                # of them have been focussed before, take the last focused
                # item. (This is very useful when the UI is composed of more
                # complex sub components.)
                windows = []
                for c in walk(value, skip_hidden=True):
                    if isinstance(c, Window) and c.content.is_focussable():
                        windows.append(c)

                # Take the first one that was focussed before.
                for w in reversed(self._stack):
                    if w in windows:
                        self.current_window = w
                        return

                # None was focussed before: take the very first focussable window.
                if windows:
                    self.current_window = windows[0]
                    return

                raise ValueError('Invalid value. Container cannot be focussed: %r' % (value, ))

    def has_focus(self, value):
        """
        Check whether the given control has the focus.
        :param value: `UIControl` or `Window` instance.
        """
        if isinstance(value, six.text_type):
            if self.current_buffer is None:
                return False
            return self.current_buffer.name == value
        if isinstance(value, Buffer):
            return self.current_buffer == value
        if isinstance(value, UIControl):
            return self.current_control == value
        else:
            value = to_window(value)
            return self.current_window == value

    @property
    def current_control(self):
        """
        Get the `UIControl` to currently has the  focus.
        """
        return self._stack[-1].content

    @current_control.setter
    def current_control(self, control):
        """
        Set the `UIControl` to receive the focus.
        """
        assert isinstance(control, UIControl)

        for window in self.find_all_windows():
            if window.content == control:
                self.current_window = window
                return

        raise ValueError('Control not found in the user interface.')

    @property
    def current_window(self):
        " Return the `Window` object that is currently focussed. "
        return self._stack[-1]

    @current_window.setter
    def current_window(self, value):
        " Set the `Window` object to be currently focussed. "
        assert isinstance(value, Window)
        self._stack.append(value)

    def start_search(self, control, search_buffer_control):
        # Make sure to focus the search BufferControl
        self.focus(search_buffer_control)

        # Remember search link.
        self.search_links[search_buffer_control] = control

    @property
    def is_searching(self):
        " True if we are searching right now. "
        return self.current_control in self.search_links

    @property
    def search_target_buffer_control(self):
        " Return the `BufferControl` in which we are searching or `None`. "
        return self.search_links.get(self.current_control)

    def get_focussable_windows(self):
        """
        Return all the `Window` objects which are focussable (in the 'modal'
        area).
        """
        for w in self.walk_through_modal_area():
            if isinstance(w, Window) and w.content.is_focussable():
                yield w

    def get_visible_focussable_windows(self):
        """
        Return a list of `Window` objects that are focussable.
        """
        # Focussable windows are windows that are visible, but also part of the
        # modal container. Make sure to keep the ordering.
        visible_windows = self.visible_windows
        return [w for w in self.get_focussable_windows() if w in visible_windows]

    @property
    def current_buffer(self):
        """
        The currently focussed :class:`~.Buffer` or `None`.
        """
        ui_control = self.current_control
        if isinstance(ui_control, BufferControl):
            return ui_control.buffer

    def get_buffer_by_name(self, buffer_name):
        """
        Look in the layout for a buffer with the given name.
        Return `None` when nothing was found.
        """
        for w in self.walk():
            if isinstance(w, Window) and isinstance(w.content, BufferControl):
                if w.content.buffer.name == buffer_name:
                    return w.content.buffer

    @property
    def buffer_has_focus(self):
        """
        Return `True` if the currently foccussed control is a `BufferControl`.
        (For instance, used to determine whether the default key bindings
        should be active or not.)
        """
        ui_control = self.current_control
        return isinstance(ui_control, BufferControl)

    @property
    def previous_control(self):
        """
        Get the `UIControl` to previously had the focus.
        """
        try:
            return self._stack[-2].content
        except IndexError:
            return self._stack[-1].content

    def focus_last(self):
        """
        Give the focus to the last focussed control.
        """
        if len(self._stack) > 1:
            self._stack = self._stack[:-1]

    def focus_next(self):
        """
        Focus the next visible/focussable Window.
        """
        windows = self.get_visible_focussable_windows()

        if len(windows) > 0:
            try:
                index = windows.index(self.current_window)
            except ValueError:
                index = 0
            else:
                index = (index + 1) % len(windows)

            self.focus(windows[index])

    def focus_previous(self):
        """
        Focus the previous visible/focussable Window.
        """
        windows = self.get_visible_focussable_windows()

        if len(windows) > 0:
            try:
                index = windows.index(self.current_window)
            except ValueError:
                index = 0
            else:
                index = (index - 1) % len(windows)

            self.focus(windows[index])

    def walk(self):
        """
        Walk through all the layout nodes (and their children) and yield them.
        """
        for i in walk(self.container):
            yield i

    def walk_through_modal_area(self):
        """
        Walk through all the containers which are in the current 'modal' part
        of the layout.
        """
        # Go up in the tree, and find the root. (it will be a part of the
        # layout, if the focus is in a modal part.)
        root = self.current_window
        while not root.is_modal() and root in self._child_to_parent:
            root = self._child_to_parent[root]

        for container in walk(root):
            yield container

    def update_parents_relations(self):
        """
        Update child->parent relationships mapping.
        """
        parents = {}

        def walk(e):
            for c in e.get_children():
                parents[c] = e
                walk(c)

        walk(self.container)

        self._child_to_parent = parents

    def reset(self):
        return self.container.reset()

    def get_parent(self, container):
        """
        Return the parent container for the given container, or ``None``, if it
        wasn't found.
        """
        try:
            return self._child_to_parent[container]
        except KeyError:
            return


class InvalidLayoutError(Exception):
    pass


def walk(container, skip_hidden=False):
    """
    Walk through layout, starting at this container.
    """
    # When `skip_hidden` is set, don't go into disabled ConditionalContainer containers.
    if skip_hidden and isinstance(container, ConditionalContainer) and not container.filter():
        return

    yield container

    for c in container.get_children():
        # yield from walk(c)
        for i in walk(c, skip_hidden=skip_hidden):
            yield i
