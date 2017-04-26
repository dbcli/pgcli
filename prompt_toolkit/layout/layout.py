"""
Wrapper for the layout.
"""
from __future__ import unicode_literals
from .controls import UIControl, BufferControl
from .containers import Window, to_container, to_window
from prompt_toolkit.buffer import Buffer
import six

__all__ = (
    'Layout',
    'InvalidLayoutError',
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

        if focussed_window is None:
            try:
                self._stack.append(next(self.find_all_windows()))
            except StopIteration:
                raise InvalidLayoutError('Invalid layout. The layout does not contain any Window object.')
        else:
            self._stack.append(to_window(focussed_window))

    def __repr__(self):
        return 'Layout(%r, current_control=%r)' % (
            self.container, self.current_control)

    def find_all_windows(self):
        """
        Find all the `UIControl` objects in this layout.
        """
        for item in self.container.walk():
            if isinstance(item, Window):
                yield item

    def find_all_controls(self):
        for container in self.find_all_windows():
            yield container.content

    def focus(self, value):
        """
        Focus the given object.

        :param value: `UIControl` or `Window` instance.
        """
        if isinstance(value, UIControl):
            self.current_control = value
        else:
            value = to_window(value)
            self.current_window = value

    def has_focus(self, value):
        """
        Check whether the given control has the focus.
        :param value: `UIControl` or `Window` instance.
        """
        if isinstance(value, six.text_type):
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

    @property
    def current_buffer(self):
        """
        The currently focussed :class:`~.Buffer` or `None`.
        """
        ui_control = self.current_control
        if isinstance(ui_control, BufferControl):
            return ui_control.buffer

    @property
    def previous_control(self):
        """
        Get the `UIControl` to previously had the focus.
        """
        try:
            return self._stack[-2].content
        except IndexError:
            return self._stack[-1].content

    def pop_focus(self):
        """
        Give the focus to the previously focussed control.
        """
        if len(self._stack) > 1:
            self._stack = self._stack[:-1]

    def walk(self):
        """
        Walk through all the layout nodes (and their children) and yield them.
        """
        return self.container.walk()

    def reset(self):
        return self.container.reset()


class InvalidLayoutError(Exception):
    pass

