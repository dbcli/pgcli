"""
Container for the layout.
(Containers can contain other containers or user interface controls.)
"""
from __future__ import unicode_literals

from six import with_metaclass
from abc import ABCMeta, abstractmethod
from pygments.token import Token

from .screen import Point, WritePosition
from .dimension import LayoutDimension, sum_layout_dimensions, max_layout_dimensions
from .controls import UIControl, TokenListControl
from .margins import Margin
from prompt_toolkit.filters import to_cli_filter
from prompt_toolkit.mouse_events import MouseEvent, MouseEventTypes

__all__ = (
    'HSplit',
    'VSplit',
    'FloatContainer',
    'Float',
    'Window',
    'ConditionalContainer',
    'ScrollOffsets'
)

Transparent = Token.Transparent


class Layout(with_metaclass(ABCMeta, object)):
    """
    Base class for user interface layout.
    """
    @abstractmethod
    def reset(self):
        """
        Reset the state of this container and all the children.
        (E.g. reset scroll offsets, etc...)
        """

    @abstractmethod
    def preferred_width(self, cli, max_available_width):
        """
        Return a `LayoutDimension` that represents the desired width for this
        container.
        """

    @abstractmethod
    def preferred_height(self, cli, width):
        """
        Return a `LayoutDimension` that represents the desired height for this
        container.
        """

    @abstractmethod
    def write_to_screen(self, cli, screen, mouse_handlers, write_position):
        """
        Write the actual content to the screen.
        """

    @abstractmethod
    def walk(self):
        """
        Walk through all the layout nodes (and their children) and yield them.
        """


class HSplit(Layout):
    """
    Several layouts, one stacked above/under the other.
    """
    def __init__(self, children):
        assert all(isinstance(c, Layout) for c in children)
        self.children = children

    def preferred_width(self, cli, max_available_width):
        dimensions = [c.preferred_width(cli, max_available_width) for c in self.children]
        return max_layout_dimensions(dimensions)

    def preferred_height(self, cli, width):
        dimensions = [c.preferred_height(cli, width) for c in self.children]
        return sum_layout_dimensions(dimensions)

    def reset(self):
        for c in self.children:
            c.reset()

    def write_to_screen(self, cli, screen, mouse_handlers, write_position):
        """
        Render the prompt to a `Screen` instance.

        :param screen: The :class:`Screen` class into which we write the output.
        """
        # Calculate heights.
        dimensions = [c.preferred_height(cli, write_position.width) for c in self.children]
        sum_dimensions = sum_layout_dimensions(dimensions)

        # If there is not enough space for both.
        # Don't do anything. (TODO: show window too small message.)
        if sum_dimensions.min > write_position.extended_height:
            return

        # Find optimal sizes. (Start with minimal size, increase until we cover
        # the whole height.)
        sizes = [d.min for d in dimensions]

        i = 0
        while sum(sizes) < min(write_position.extended_height, sum_dimensions.preferred):
            # Increase until we meet at least the 'preferred' size.
            if sizes[i] < dimensions[i].preferred:
                sizes[i] += 1
            i = (i + 1) % len(sizes)

        if not any([cli.is_returning, cli.is_exiting, cli.is_aborting]):
            while sum(sizes) < min(write_position.height, sum_dimensions.max):
                # Increase until we use all the available space. (or until "max")
                if sizes[i] < dimensions[i].max:
                    sizes[i] += 1
                i = (i + 1) % len(sizes)

        # Draw child panes.
        ypos = write_position.ypos
        xpos = write_position.xpos
        width = write_position.width

        for s, c in zip(sizes, self.children):
            c.write_to_screen(cli, screen, mouse_handlers, WritePosition(xpos, ypos, width, s))
            ypos += s

    def walk(self):
        """ Walk through children. """
        yield self
        for c in self.children:
            for i in c.walk():
                yield i


class VSplit(Layout):
    """
    Several layouts, one stacked left/right of the other.
    """
    def __init__(self, children):
        assert all(isinstance(c, Layout) for c in children)
        self.children = children

    def preferred_width(self, cli, max_available_width):
        dimensions = [c.preferred_width(cli, max_available_width) for c in self.children]
        return sum_layout_dimensions(dimensions)

    def preferred_height(self, cli, width):
        sizes = self._divide_widths(cli, width)
        if sizes is None:
            return LayoutDimension()
        else:
            dimensions = [c.preferred_height(cli, s)
                          for s, c in zip(sizes, self.children)]
            return max_layout_dimensions(dimensions)

    def reset(self):
        for c in self.children:
            c.reset()

    def _divide_widths(self, cli, width):
        """
        Return the widths for all columns.
        Or None when there is not enough space.
        """
        # Calculate widths.
        dimensions = [c.preferred_width(cli, width) for c in self.children]
        sum_dimensions = sum_layout_dimensions(dimensions)

        # If there is not enough space for both.
        # Don't do anything. (TODO: show window too small message.)
        if sum_dimensions.min > width:
            return

        # TODO: like HSplit, first increase until the "preferred" size.

        # Find optimal sizes. (Start with minimal size, increase until we cover
        # the whole height.)
        sizes = [d.min for d in dimensions]
        i = 0
        while sum(sizes) < min(width, sum_dimensions.max):
            if sizes[i] < dimensions[i].max:
                sizes[i] += 1
            i = (i + 1) % len(sizes)

        return sizes

    def write_to_screen(self, cli, screen, mouse_handlers, write_position):
        """
        Render the prompt to a `Screen` instance.

        :param screen: The :class:`Screen` class into which we write the output.
        """
        if not self.children:
            return

        sizes = self._divide_widths(cli, write_position.width)

        if sizes is None:
            return

        # Calculate heights, take the largest possible, but not larger than write_position.extended_height.
        heights = [child.preferred_height(cli, width).preferred
                   for width, child in zip(sizes, self.children)]
        height = max(write_position.height, min(write_position.extended_height, max(heights)))

        # Draw child panes.
        ypos = write_position.ypos
        xpos = write_position.xpos

        for s, c in zip(sizes, self.children):
            c.write_to_screen(cli, screen, mouse_handlers, WritePosition(xpos, ypos, s, height))
            xpos += s

    def walk(self):
        """ Walk through children. """
        yield self
        for c in self.children:
            for i in c.walk():
                yield i


class FloatContainer(Layout):
    """
    Container which can contain another container for the background, as well
    as a list of floating containers on top of it.

    Example Usage::

        FloatContainer(content=Window(...),
                       floats=[
                           Float(xcursor=True,
                                ycursor=True,
                                layout=CompletionMenu(...))
                       ])
    """
    def __init__(self, content, floats):
        assert isinstance(content, Layout)
        assert all(isinstance(f, Float) for f in floats)

        self.content = content
        self.floats = floats

    def reset(self):
        self.content.reset()

        for f in self.floats:
            f.content.reset()

    def preferred_width(self, cli, write_position):
        return self.content.preferred_width(cli, write_position)

    def preferred_height(self, cli, width):
        """
        Return the preferred height of the float container.
        (We don't care about the height of the floats, they should always fit
        into the dimensions provided by the container.)
        """
        return self.content.preferred_height(cli, width)

    def write_to_screen(self, cli, screen, mouse_handlers, write_position):
        self.content.write_to_screen(cli, screen, mouse_handlers, write_position)

        # When a menu_position was given, use this instead of the cursor
        # position. (These cursor positions are absolute, translate again
        # relative to the write_position.)
        cursor_position = screen.menu_position or screen.cursor_position
        cursor_position = Point(x=cursor_position.x - write_position.xpos,
                                y=cursor_position.y - write_position.ypos)

        for fl in self.floats:
            # Left & width given.
            if fl.left is not None and fl.width is not None:
                xpos = fl.left
                width = fl.width
            # Left & right given -> calculate width.
            elif fl.left is not None and fl.right is not None:
                xpos = fl.left
                width = write_position.width - fl.left - fl.right
            # Width & right given -> calculate left.
            elif fl.width is not None and fl.right is not None:
                xpos = write_position.width - fl.right - fl.width
                width = fl.width
            elif fl.xcursor:
                width = fl.width
                if width is None:
                    width = fl.content.preferred_width(cli, write_position.width).preferred
                    width = min(write_position.width, width)

                xpos = cursor_position.x
                if xpos + width > write_position.width:
                    xpos = max(0, write_position.width - width)
            # Only width given -> center horizontally.
            elif fl.width:
                xpos = int((write_position.width - fl.width) / 2)
                width = fl.width
            # Otherwise, take preferred width from float content.
            else:
                width = fl.content.preferred_width(cli, write_position.width).preferred

                if fl.left is not None:
                    xpos = fl.left
                elif fl.right is not None:
                    xpos = max(0, write_position.width - width - fl.right)
                else:  # Center horizontally.
                    xpos = max(0, int((write_position.width - width) / 2))

                # Trim.
                width = min(width, write_position.width - xpos)

            # Top & height given.
            if fl.top is not None and fl.height is not None:
                ypos = fl.top
                height = fl.height
            # Top & bottom given -> calculate height.
            elif fl.top is not None and fl.bottom is not None:
                ypos = fl.top
                height = write_position.height - fl.top - fl.bottom
            # Height & bottom given -> calculate top.
            elif fl.height is not None and fl.bottom is not None:
                ypos = write_position.height - fl.height - fl.bottom
                height = fl.height
            # Near cursor
            elif fl.ycursor:
                ypos = cursor_position.y + 1

                height = fl.height
                if height is None:
                    height = fl.content.preferred_height(cli, width).preferred

                # Reduce height if not enough space. (We can use the
                # extended_height when the content requires it.)
                if height > write_position.extended_height - ypos:
                    if write_position.extended_height - ypos + 1 >= ypos:
                        # When the space below the cursor is more than
                        # the space above, just reduce the height.
                        height = write_position.extended_height - ypos
                    else:
                        # Otherwise, fit the float above the cursor.
                        height = min(height, cursor_position.y)
                        ypos = cursor_position.y - height

            # Only height given -> center vertically.
            elif fl.width:
                ypos = int((write_position.height - fl.height) / 2)
                height = fl.height
            # Otherwise, take preferred height from content.
            else:
                height = fl.content.preferred_height(cli, width).preferred

                if fl.top is not None:
                    ypos = fl.top
                elif fl.bottom is not None:
                    ypos = max(0, write_position.height - height - fl.bottom)
                else:  # Center vertically.
                    ypos = max(0, int((write_position.height - height) / 2))

                # Trim.
                height = min(height, write_position.height - ypos)

            # Write float.
            if xpos >= 0 and ypos >= 0 and height > 0 and width > 0:
                wp = WritePosition(xpos=xpos + write_position.xpos,
                                   ypos=ypos + write_position.ypos,
                                   width=width, height=height)
                fl.content.write_to_screen(cli, screen, mouse_handlers, wp)

    def walk(self):
        """ Walk through children. """
        yield self

        for i in self.content.walk():
            yield i

        for f in self.floats:
            for i in f.content.walk():
                yield i


class Float(object):
    def __init__(self, top=None, right=None, bottom=None, left=None,
                 width=None, height=None,
                 xcursor=False, ycursor=False, content=None):
        assert isinstance(content, Layout)

        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom

        self.width = width
        self.height = height

        self.xcursor = xcursor
        self.ycursor = ycursor

        self.content = content

    def __repr__(self):
        return 'Float(content=%r)' % self.content


class WindowRenderInfo(object):
    """
    Render information, for the last render time of this control.
    It stores mapping information between the input buffers (in case of a
    BufferControl) and the actual render position on the output screen.

    (Could be used for implementation of the Vi 'H' and 'L' key bindings as
    well as implementing mouse support.)

    :param original_screen: The original full screen instance that contains the
                            whole input, without clipping. (temp_screen)
    :param horizontal_scroll: The horizontal scroll of the `Window` instance.
    :param vertical_scroll: The vertical scroll of the `Window` instance.
    :param height: The height that was used for the rendering.
    :param cursor_position: `Point` instance. Where the cursor is currently
                            shown, relative to the window.
    """
    def __init__(self, original_screen, horizontal_scroll, vertical_scroll,
                 window_width, window_height, cursor_position,
                 configured_scroll_offsets, applied_scroll_offsets):
        self.original_screen = original_screen
        self.vertical_scroll = vertical_scroll
        self.window_width = window_width
        self.window_height = window_height
        self.cursor_position = cursor_position
        self.configured_scroll_offsets = configured_scroll_offsets
        self.applied_scroll_offsets = applied_scroll_offsets

    @property
    def input_line_to_screen_line(self):
        """
        Return a dictionary mapping the line numbers of the screen to the one
        of the input buffer.
        """
        return dict((v, k) for k, v in
                    self.original_screen.screen_line_to_input_line.items())

    @property
    def screen_line_to_input_line(self):
        """
        Return the dictionary mapping the line numbers of the input buffer to
        the lines of the screen.
        """
        return self.original_screen.screen_line_to_input_line

    @property
    def visible_line_to_input_line(self):
        """
        Return a dictionary mapping the visible rows to the line numbers of the
        input.
        """
        return dict((k - self.vertical_scroll, v) for
                    k, v in self.original_screen.screen_line_to_input_line.items())

    def first_visible_line(self, after_scroll_offset=False):
        """
        Return the line number (0 based) of the input document that corresponds
        with the first visible line.
        """
        # Note that we can't just do vertical_scroll+height because some input
        # lines could be wrapped and span several lines in the screen.
        screen = self.original_screen
        height = self.window_height

        start = self.vertical_scroll
        if after_scroll_offset:
            start += self.applied_scroll_offsets.top

        for y in range(start, self.vertical_scroll + height):
            if y in screen.screen_line_to_input_line:
                return screen.screen_line_to_input_line[y]

        return 0

    def last_visible_line(self, before_scroll_offset=False):
        """
        Like `first_visible_line`, but for the last visible line.
        """
        screen = self.original_screen
        height = self.window_height

        start = self.vertical_scroll + height - 1
        if before_scroll_offset:
            start -= self.applied_scroll_offsets.bottom

        for y in range(start, self.vertical_scroll, -1):
            if y in screen.screen_line_to_input_line:
                return screen.screen_line_to_input_line[y]

        return 0

    def center_visible_line(self, before_scroll_offset=False,
                            after_scroll_offset=False):
        """
        Like `first_visible_line`, but for the center visible line.
        """
        return (self.first_visible_line(after_scroll_offset) +
                (self.last_visible_line(before_scroll_offset) -
                    self.first_visible_line(after_scroll_offset))/2
                )

    @property
    def content_height(self):
        """
        The full height of the user control.
        """
        return self.original_screen.height

    @property
    def full_height_visible(self):
        """
        True when the full height is visible (There is no vertical scroll.)
        """
        return self.window_height >= self.original_screen.height

    @property
    def top_visible(self):
        """
        True when the top of the buffer is visible.
        """
        return self.vertical_scroll == 0

    @property
    def bottom_visible(self):
        """
        True when the bottom of the buffer is visible.
        """
        return self.vertical_scroll >= \
            self.original_screen.height - self.window_height

    @property
    def vertical_scroll_percentage(self):
        """
        Vertical scroll as a percentage. (0 means: the top is visible,
        100 means: the bottom is visible.)
        """
        return (100 * self.vertical_scroll //
                (self.original_screen.height - self.window_height))


class ScrollOffsets(object):
    """
    Scroll offsets for the `Window` class.

    Note that left/rigth offsets only make sense if line wrapping is disabled.
    """
    def __init__(self, top=0, bottom=0, left=0, right=0):
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right

    def __repr__(self):
        return 'ScrollOffsets(top=%r, bottom=%r, left=%r, right=%r)' % (
            self.top, self.bottom, self.left, self.right)


class Window(Layout):
    """
    Layout that holds a control.

    :param content: User interface control.
    :param width: `LayoutDimension` instance.
    :param height: `LayoutDimension` instance.
    :param get_width: callable which takes a `CommandLineInterface` and returns a `LayoutDimension`.
    :param get_height: callable which takes a `CommandLineInterface` and returns a `LayoutDimension`.
    :param dont_extend_width: When `True`, don't take up more width then the
                              preferred width reported by the control.
    :param dont_extend_height: When `True`, don't take up more width then the
                               preferred height reported by the control.
    :param left_margins: A list of `Margin` instance to be displayed on the left.
        For instance: `NumberredMargin` can be one of them in order to show line numbers.
    :param right_margins: Like `left_margins`, but on the other side.
    :param scroll_offsets: `ScrollOffsets` instance, representing the preferred
        amount of lines/columns to be always visible before/after the cursor.
        When both top and bottom are a very high number, the cursor will be
        centered vertically most of the time.
    :param allow_scroll_beyond_bottom: A `bool` or `Filter` instance. When
         True, allow scrolling so far, that the top part of the content is not
         visible anymore, while there is still empty space available at the
         bottom of the window. In the Vi editor for instance, this is possible.
         You will see tildes while the top part of the body is hidden.
    """
    def __init__(self, content, width=None, height=None, get_width=None,
                 get_height=None, dont_extend_width=False, dont_extend_height=False,
                 left_margins=None, right_margins=None, scroll_offsets=None,
                 allow_scroll_beyond_bottom=False):
        assert isinstance(content, UIControl)
        assert width is None or isinstance(width, LayoutDimension)
        assert height is None or isinstance(height, LayoutDimension)
        assert get_width is None or callable(get_width)
        assert get_height is None or callable(get_height)
        assert width is None or get_width is None
        assert height is None or get_height is None
        assert scroll_offsets is None or isinstance(scroll_offsets, ScrollOffsets)
        assert left_margins is None or all(isinstance(m, Margin) for m in left_margins)
        assert right_margins is None or all(isinstance(m, Margin) for m in right_margins)

        self.allow_scroll_beyond_bottom = to_cli_filter(allow_scroll_beyond_bottom)

        self.content = content
        self.dont_extend_width = dont_extend_width
        self.dont_extend_height = dont_extend_height
        self.left_margins = left_margins or []
        self.right_margins = right_margins or []
        self.scroll_offsets = scroll_offsets or ScrollOffsets()
        self._width = get_width or (lambda cli: width)
        self._height = get_height or (lambda cli: height)

        self.reset()

    def __repr__(self):
        return 'Window(content=%r)' % self.content

    def reset(self):
        self.content.reset()

        #: Scrolling position of the main content.
        self.vertical_scroll = 0
        self.horizontal_scroll = 0

        #: Keep render information (mappings between buffer input and render
        #: output.)
        self.render_info = None

    def preferred_width(self, cli, max_available_width):
        # Width of the margins.
        total_margin_width = sum(m.get_width(cli) for m in
                                 self.left_margins + self.right_margins)

        # Window of the content.
        preferred_width = self.content.preferred_width(
                cli, max_available_width - total_margin_width)

        if preferred_width is not None:
            preferred_width += total_margin_width

        # Merge.
        return self._merge_dimensions(
            dimension=self._width(cli),
            preferred=preferred_width,
            dont_extend=self.dont_extend_width)

    def preferred_height(self, cli, width):
        return self._merge_dimensions(
            dimension=self._height(cli),
            preferred=self.content.preferred_height(cli, width),
            dont_extend=self.dont_extend_height)

    @staticmethod
    def _merge_dimensions(dimension, preferred=None, dont_extend=False):
        """
        Take the LayoutDimension from this `Window` class and the received
        preferred size from the `UIControl` and return a `LayoutDimension` to
        report to the parent container.
        """
        dimension = dimension or LayoutDimension()

        # When a preferred dimension was explicitely given to the Window,
        # ignore the UIControl.
        if dimension.preferred_specified:
            preferred = dimension.preferred

        # When a 'preferred' dimension is given by the UIControl, make sure
        # that it stays within the bounds of the Window.
        if preferred is not None:
            if dimension.max:
                preferred = min(preferred, dimension.max)

            if dimension.min:
                preferred = max(preferred, dimension.min)

        # When a `dont_extend` flag has been given, use the preferred dimension
        # also as the max demension.
        if dont_extend and preferred is not None:
            max_ = min(dimension.max, preferred)
        else:
            max_ = dimension.max

        return LayoutDimension(min=dimension.min, max=max_, preferred=preferred)

    def write_to_screen(self, cli, screen, mouse_handlers, write_position):
        """
        Write window to screen. This renders the user control, the margins and
        copies everything over to the absolute position at the given screen.
        """
        # Render margins.
        left_margin_widths = [m.get_width(cli) for m in self.left_margins]
        right_margin_widths = [m.get_width(cli) for m in self.right_margins]
        total_margin_width = sum(left_margin_widths + right_margin_widths)

        # Render UserControl.
        temp_screen = self.content.create_screen(
            cli, write_position.width - total_margin_width, write_position.height)

        # Scroll content.
        applied_scroll_offsets = self._scroll(
            temp_screen, write_position.width - total_margin_width, write_position.height, cli)

        # Write body to screen.
        self._copy_body(cli, temp_screen, screen, write_position,
                        sum(left_margin_widths), write_position.width - total_margin_width,
                        applied_scroll_offsets)

        # Remember render info. (Set before generating the margins. They need this.)
        self.render_info = WindowRenderInfo(
            original_screen=temp_screen,
            horizontal_scroll=self.horizontal_scroll,
            vertical_scroll=self.vertical_scroll,
            window_width=write_position.width,
            window_height=write_position.height,
            cursor_position=Point(y=temp_screen.cursor_position.y - self.vertical_scroll,
                                  x=temp_screen.cursor_position.x - self.horizontal_scroll),
            configured_scroll_offsets=self.scroll_offsets,
            applied_scroll_offsets=applied_scroll_offsets)

        # Set mouse handlers.
        def mouse_handler(cli, mouse_event):
            """ Wrapper around the mouse_handler of the `UIControl` that turns
            absolute coordinates into relative coordinates. """
            position = mouse_event.position

            # Call the mouse handler of the UIControl first.
            result = self.content.mouse_handler(
                cli, MouseEvent(
                    position=Point(x=position.x - write_position.xpos - sum(left_margin_widths),
                                   y=position.y - write_position.ypos + self.vertical_scroll),
                    event_type=mouse_event.event_type))

            # If it returns NotImplemented, handle it here.
            if result == NotImplemented:
                return self._mouse_handler(cli, mouse_event)

            return result

        mouse_handlers.set_mouse_handler_for_range(
                x_min=write_position.xpos + sum(left_margin_widths),
                x_max=write_position.xpos + write_position.width - total_margin_width,
                y_min=write_position.ypos,
                y_max=write_position.ypos + write_position.height,
                handler=mouse_handler)

        # Render and copy margins.
        move_x = 0

        def render_margin(m, width):
            " Render margin. return `Screen`. "
            control = TokenListControl(
                lambda _: m.create_margin(cli, self.render_info, width, write_position.height))
            return control.create_screen(cli, width + 1, write_position.height)

        for m, width in zip(self.left_margins, left_margin_widths):
            # Create screen for margin.
            margin_screen = render_margin(m, width)

            # Copy and shift X.
            self._copy_margin(margin_screen, screen, write_position, move_x, width)
            move_x += width

        move_x = write_position.width - sum(right_margin_widths)

        for m, width in zip(self.right_margins, right_margin_widths):
            # Create screen for margin.
            margin_screen = render_margin(m, width)

            # Copy and shift X.
            self._copy_margin(margin_screen, screen, write_position, move_x, width)
            move_x += width

    def _copy_body(self, cli, temp_screen, new_screen, write_position, move_x, width, applied_scroll_offsets):
        """
        Copy characters from the temp screen that we got from the `UIControl`
        to the real screen.
        """
        xpos = write_position.xpos + move_x
        ypos = write_position.ypos
        height = write_position.height

        temp_buffer = temp_screen._buffer
        new_buffer = new_screen._buffer
        temp_screen_height = temp_screen.height
        y = 0

        # Now copy the region we need to the real screen.
        for y in range(0, height):
            # We keep local row variables. (Don't look up the row in the dict
            # for each iteration of the nested loop.)
            new_row = new_buffer[y + ypos]

            if y >= temp_screen_height and y >= write_position.height:
                # Break out of for loop when we pass after the last row of the
                # temp screen. (We use the 'y' position for calculation of new
                # screen's height.)
                break
            else:
                temp_row = temp_buffer[y + self.vertical_scroll]

                # Copy row content, except for transparent tokens.
                # (This is useful in case of floats.)
                for x in range(0, width):
                    cell = temp_row[x + self.horizontal_scroll]
                    if cell.token != Transparent:
                        new_row[x + xpos] = cell

        if self.content.has_focus(cli):
            new_screen.cursor_position = Point(y=temp_screen.cursor_position.y + ypos - self.vertical_scroll,
                                               x=temp_screen.cursor_position.x + xpos - self.horizontal_scroll)

        if not new_screen.menu_position and temp_screen.menu_position:
            new_screen.menu_position = Point(y=temp_screen.menu_position.y + ypos - self.vertical_scroll,
                                             x=temp_screen.menu_position.x + xpos - self.horizontal_scroll)

        # Update height of the output screen. (new_screen.write_data is not
        # called, so the screen is not aware of its height.)
        new_screen.height = max(new_screen.height, ypos + y + 1)

    def _copy_margin(self, temp_screen, new_screen, write_position, move_x, width):
        """
        Copy characters from the margin screen to the real screen.
        """
        xpos = write_position.xpos + move_x
        ypos = write_position.ypos

        temp_buffer = temp_screen._buffer
        new_buffer = new_screen._buffer

        # Now copy the region we need to the real screen.
        for y in range(0, write_position.height):
            new_row = new_buffer[y + ypos]
            temp_row = temp_buffer[y]

            # Copy row content, except for transparent tokens.
            # (This is useful in case of floats.)
            for x in range(0, width):
                cell = temp_row[x]
                if cell.token != Transparent:
                    new_row[x + xpos] = cell

    def _scroll(self, temp_screen, width, height, cli):
        """
        Scroll to make sure the cursor position is visible and that we maintain the
        requested scroll offset.
        Return the applied scroll offsets.
        """
        def do_scroll(current_scroll, scroll_offset_start, scroll_offset_end, cursor_pos, window_size, content_size):
            " Scrolling algorithm. Used for both horizontal and vertical scrolling. "
            # Calculate the scroll offset to apply.
            # This can obviously never be more than have the screen size. Also, when the
            # cursor appears at the top or bottom, we don't apply the offset.
            scroll_offset_start = int(min(scroll_offset_start, window_size / 2, cursor_pos))
            scroll_offset_end = int(min(scroll_offset_end, window_size / 2,
                                           content_size - 1 - cursor_pos))

            # Prevent negative scroll offsets.
            if current_scroll < 0:
                current_scroll = 0

            # Scroll back if we scrolled to much and there's still space to show more of the document.
            if (not self.allow_scroll_beyond_bottom(cli) and
                    current_scroll > content_size - window_size):
                current_scroll = max(0, content_size - window_size)

            # Scroll up if cursor is before visible part.
            if current_scroll > cursor_pos - scroll_offset_start:
                current_scroll = max(0, cursor_pos - scroll_offset_start)

            # Scroll down if cursor is after visible part.
            if current_scroll < (cursor_pos + 1) - window_size + scroll_offset_end:
                current_scroll = (cursor_pos + 1) - window_size + scroll_offset_end

            # Calculate the applied scroll offset. This value can be lower than what we had.
            scroll_offset_start = max(0, min(current_scroll, scroll_offset_start))
            scroll_offset_end = max(0, min(content_size - current_scroll - window_size, scroll_offset_end))

            return current_scroll, scroll_offset_start, scroll_offset_end

        offsets = self.scroll_offsets

        self.vertical_scroll, scroll_offset_top, scroll_offset_bottom  = do_scroll(
            current_scroll=self.vertical_scroll,
            scroll_offset_start=offsets.top,
            scroll_offset_end=offsets.bottom,
            cursor_pos=temp_screen.cursor_position.y,
            window_size=height,
            content_size=temp_screen.height)

        self.horizontal_scroll, scroll_offset_left, scroll_offset_right = do_scroll(
            current_scroll=self.horizontal_scroll,
            scroll_offset_start=offsets.left,
            scroll_offset_end=offsets.right,
            cursor_pos=temp_screen.cursor_position.x,
            window_size=width,
            content_size=temp_screen.width)

        applied_scroll_offsets = ScrollOffsets(
            top=scroll_offset_top,
            bottom=scroll_offset_bottom,
            left=scroll_offset_left,
            right=scroll_offset_right)

        return applied_scroll_offsets

    def _mouse_handler(self, cli, mouse_event):
        """
        Mouse handler. Called when the UI control doesn't handle this
        particular event.
        """
        if mouse_event.event_type == MouseEventTypes.SCROLL_DOWN:
            self._scroll_down(cli)
        elif mouse_event.event_type == MouseEventTypes.SCROLL_UP:
            self._scroll_up(cli)

    def _scroll_down(self, cli):
        " Scroll window down. "
        info = self.render_info

        if self.vertical_scroll < info.content_height - info.window_height:
            if info.cursor_position.y <= info.configured_scroll_offsets.top:
                self.content.move_cursor_down(cli)

            self.vertical_scroll += 1

    def _scroll_up(self, cli):
        " Scroll window up. "
        info = self.render_info

        if info.vertical_scroll > 0:
            if info.cursor_position.y >= info.window_height - 1 - info.configured_scroll_offsets.bottom:
                self.content.move_cursor_up(cli)

            self.vertical_scroll -= 1

    def walk(self):
        # Only yield self. A window doesn't have children.
        yield self


class ConditionalContainer(Layout):
    """
    Wrapper around any other container that can change the visibility. The
    received `filter` determines whether the given container should be
    displayed or not.

    :param content: `Container` instance.
    :param filter: `CLIFilter` instance.
    """
    def __init__(self, content, filter):
        assert isinstance(content, Layout)

        self.content = content
        self.filter = to_cli_filter(filter)

    def reset(self):
        self.content.reset()

    def preferred_width(self, cli, max_available_width):
        if self.filter(cli):
            return self.content.preferred_width(cli, max_available_width)
        else:
            return LayoutDimension.exact(0)

    def preferred_height(self, cli, width):
        if self.filter(cli):
            return self.content.preferred_height(cli, width)
        else:
            return LayoutDimension.exact(0)

    def write_to_screen(self, cli, screen, mouse_handlers, write_position):
        if self.filter(cli):
            return self.content.write_to_screen(cli, screen, mouse_handlers, write_position)

    def walk(self):
        return self.content.walk()
