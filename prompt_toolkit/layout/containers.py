"""
Container for the layout.
(Containers can contain other containers or user interface controls.)
"""
from __future__ import unicode_literals

from six import with_metaclass
from abc import ABCMeta, abstractmethod

from .screen import Point, WritePosition
from .dimension import LayoutDimension, sum_layout_dimensions, max_layout_dimensions
from .controls import UIControl
from prompt_toolkit.reactive import Integer
from prompt_toolkit.filters import CLIFilter, Always, Never

__all__ = (
    'HSplit',
    'VSplit',
    'FloatContainer',
    'Float',
    'Window',
)


class Layout(with_metaclass(ABCMeta, object)):
    """
    Base class for user interface layout.
    """
    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def width(self, cli):  # XXX: rename to preferred_width
        # Should return a LayoutDimension
        pass

    @abstractmethod  # XXX: rename to preferred_height
    def height(self, cli, width):
        # Should return a LayoutDimension
        pass

    @abstractmethod
    def write_to_screen(self, cli, screen, write_position):
        pass

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

    def width(self, cli):
        dimensions = [c.width(cli) for c in self.children]
        return max_layout_dimensions(dimensions)

    def height(self, cli, width):
        dimensions = [c.height(cli, width) for c in self.children]
        return sum_layout_dimensions(dimensions)

    def reset(self):
        for c in self.children:
            c.reset()

    def write_to_screen(self, cli, screen, write_position):
        """
        Render the prompt to a `Screen` instance.

        :param screen: The :class:`Screen` class into which we write the output.
        """
        # Calculate heights.
        dimensions = [c.height(cli, write_position.width) for c in self.children]
        sum_dimensions = sum_layout_dimensions(dimensions)

        # If there is not enough space for both.
        # Don't do anything. (TODO: show window to small message.)
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
            c.write_to_screen(cli, screen, WritePosition(xpos, ypos, width, s))
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

    def width(self, cli):
        dimensions = [c.width(cli) for c in self.children]
        return sum_layout_dimensions(dimensions)

    def height(self, cli, width):
        sizes = self._divide_widths(cli, width)
        if sizes is None:
            return LayoutDimension()
        else:
            dimensions = [c.height(cli, s) for s, c in zip(sizes, self.children)]
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
        dimensions = [c.width(cli) for c in self.children]
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

    def write_to_screen(self, cli, screen, write_position):
        """
        Render the prompt to a `Screen` instance.

        :param screen: The :class:`Screen` class into which we write the output.
        """
        sizes = self._divide_widths(cli, write_position.width)

        if sizes is None:
            return

        # Calculate heights, take the largest possible, but not larger than write_position.extended_height.
        heights = [child.height(cli, width).preferred for width, child in zip(sizes, self.children)]
        height = max(write_position.height, min(write_position.extended_height, max(heights)))

        # Draw child panes.
        ypos = write_position.ypos
        xpos = write_position.xpos

        for s, c in zip(sizes, self.children):
            c.write_to_screen(cli, screen, WritePosition(xpos, ypos, s, height))
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

    def width(self, cli):
        return self.content.width(cli)

    def height(self, cli, width):
        """
        Return the preferred height of the float container.
        (We don't care about the height of the floats, they should always fit
        into the dimensions provided by the container.)
        """
        return self.content.height(cli, width)

    def write_to_screen(self, cli, screen, write_position):
        self.content.write_to_screen(cli, screen, write_position)

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
                    width = fl.content.width(cli).preferred
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
                width = fl.content.width(cli).preferred

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
                    height = fl.content.height(cli, width).preferred

                # Reduce height if not enough space. (We can use the
                # extended_height when the content requires it.)
                if height > write_position.extended_height - ypos:
                    if write_position.extended_height - ypos > ypos:
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
                height = fl.content.height(cli, width).preferred

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
                fl.content.write_to_screen(cli, screen, wp)

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
    :param vertical_scroll: The vertical scroll of the `Window` instance.
    :param rendered_height: The height that was used for the rendering.
    :param cursor_position: `Point` instance. Where the cursor is currently shown.
    """
    def __init__(self, original_screen, vertical_scroll, rendered_height, cursor_position,
                 configured_scroll_offset, scroll_offset_top, scroll_offset_bottom):
        self.original_screen = original_screen
        self.vertical_scroll = vertical_scroll
        self.rendered_height = rendered_height
        self.cursor_position = cursor_position
        self.configured_scroll_offset = configured_scroll_offset
        self.scroll_offset_top = scroll_offset_top
        self.scroll_offset_bottom = scroll_offset_bottom

    def input_line_to_screen_line(self, lineno):
        """
        Return the line number on the screen, for this line of the input.
        Setting the `vertical_scroll` to this number should make sure that
        `lineno` appears at the top.
        """
        input_to_screen = dict((v, k) for k, v in
                               self.original_screen.screen_line_to_input_line.items())
        try:
            return input_to_screen[lineno]
        except KeyError:
            return None

    @property
    def screen_line_to_input_line(self):
        """
        Return the dictionary mapping the line numbers of the input buffer to
        the lines of the screen.
        """
        return self.original_screen.screen_line_to_input_line

    def first_visible_line(self, after_scroll_offset=False):
        """
        Return the line number (0 based) of the input document that corresponds
        with the first visible line.
        """
        # Note that we can't just do vertical_scroll+height because some input
        # lines could be wrapped and span several lines in the screen.
        screen = self.original_screen
        height = self.rendered_height

        start = self.vertical_scroll
        if after_scroll_offset:
            start += self.scroll_offset_top

        for y in range(start, self.vertical_scroll + height):
            if y in screen.screen_line_to_input_line:
                return screen.screen_line_to_input_line[y]

        return 0

    def last_visible_line(self, before_scroll_offset=False):
        """
        Like `first_visible_line`, but for the last visible line.
        """
        screen = self.original_screen
        height = self.rendered_height

        start = self.vertical_scroll + height - 1
        if before_scroll_offset:
            start -= self.scroll_offset_bottom

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
    def full_height_visible(self):
        """
        True when the full height is visible (There is no vertical scroll.
        """
        return self.rendered_height >= self.original_screen.current_height

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
            self.original_screen.current_height - self.rendered_height

    @property
    def vertical_scroll_percentage(self):
        """
        Vertical scroll as a percentage. (0 means: the top is visible,
        100 means: the bottom is visible.)
        """
        return (100 * self.vertical_scroll //
                (self.original_screen.current_height - self.rendered_height))


class Window(Layout):
    """
    Layout that holds a control.

    :param content: User interface control.
    :param width: `LayoutDimension` instance.
    :param height: `LayoutDimension` instance.
    :param get_width: callable which takes a `CommandLineInterface` and returns a `LayoutDimension`.
    :param get_height: callable which takes a `CommandLineInterface` and returns a `LayoutDimension`.
    :param filter: `Filter` which decides about the visibility.
    :param dont_extend_width: When `True`, don't take up more width then the
                              preferred width reported by the control.
    :param dont_extend_height: When `True`, don't take up more width then the
                               preferred height reported by the control.
    :param scroll_offset: Number (integer) representing the preferred amount of lines to be
                          always visible before and after the cursor. When this is a very high
                          number, the cursor will be centered vertically most of the time.
    :param allow_scroll_beyond_bottom: A `Filter` instance. When True, allow scrolling so far,
                          that the top part of the content is not visible anymore, while there
                          is still empty space available at the bottom of the window. In the Vi
                          editor for instance, this is possible. You will see tildes while the
                          top part of the body is hidden.
    """
    def __init__(self, content, width=None, height=None, get_width=None,
                 get_height=None, filter=Always(), dont_extend_width=False,
                 dont_extend_height=False, scroll_offset=0, allow_scroll_beyond_bottom=Never()):
        assert isinstance(content, UIControl)
        assert width is None or isinstance(width, LayoutDimension)
        assert height is None or isinstance(height, LayoutDimension)
        assert get_width is None or callable(get_width)
        assert get_height is None or callable(get_height)
        assert width is None or get_width is None
        assert height is None or get_height is None
        assert isinstance(filter, CLIFilter)
        assert isinstance(scroll_offset, Integer)
        assert isinstance(allow_scroll_beyond_bottom, CLIFilter)

        self.content = content
        self.filter = filter
        self.dont_extend_width = dont_extend_width
        self.dont_extend_height = dont_extend_height
        self.scroll_offset = scroll_offset
        self.allow_scroll_beyond_bottom = allow_scroll_beyond_bottom
        self._width = get_width or (lambda cli: width)
        self._height = get_height or (lambda cli: height)

        self.reset()

    def __repr__(self):
        return 'Window(content=%r)' % self.content

    def reset(self):
        self.content.reset()

        #: Vertical scrolling position of the main content.
        self.vertical_scroll = 0

        #: Keep render information (mappings between buffer input and render
        #: output.)
        self.render_info = None

    def _visible(self, cli):
        return self.filter(cli)

    def width(self, cli):
        if self._visible(cli):
            width = self._width(cli) or LayoutDimension()
            preferred_width = self.content.preferred_width(cli)

            if preferred_width is None:
                return width
            else:
                # When 'dont_extend_width' has been given. Don't use more than
                # the preferred width of the control. (But also don't go below
                # the minimum.)
                if self.dont_extend_width:
                    max_width = max(width.min, min(preferred_width, width.max))
                else:
                    max_width = width.max
                return LayoutDimension(min=width.min, max=max_width, preferred=preferred_width)
        else:
            return LayoutDimension.exact(0)

    def height(self, cli, width):
        if self._visible(cli):
            height = self._height(cli) or LayoutDimension()
            preferred_height = self.content.preferred_height(cli, width)

            if preferred_height is None:
                return height
            else:
                # When 'dont_extend_height' has been given. Don't use more than
                # the preferred height of the control. (But also don't go below
                # the minimum.)
                if self.dont_extend_height:
                    max_height = max(height.min, min(preferred_height, height.max))
                else:
                    max_height = height.max
                return LayoutDimension(min=height.min, max=max_height, preferred=preferred_height)
        else:
            return LayoutDimension.exact(0)

    def write_to_screen(self, cli, screen, write_position):
                        # XXX: Show window too small messsage...

        # Only write when visible.
        if self._visible(cli):
            # Set position.
            temp_screen = self.content.create_screen(cli, write_position.width, write_position.height)
            applied_scroll_offsets = self._scroll(temp_screen, write_position.height, cli)
            self._copy(cli, temp_screen, screen, write_position, applied_scroll_offsets)

    def _copy(self, cli, temp_screen, new_screen, write_position, applied_scroll_offsets):
        """
        Copy characters from the temp screen that we got from the `UIControl`
        to the real screen.
        """
        xpos = write_position.xpos
        ypos = write_position.ypos
        height = write_position.height

        columns = temp_screen.width

        temp_buffer = temp_screen._buffer
        new_buffer = new_screen._buffer
        temp_screen_height = temp_screen.current_height
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
                for x in range(0, columns):
                    new_row[x + xpos] = temp_row[x]

        if self.content.has_focus(cli):
            new_screen.cursor_position = Point(y=temp_screen.cursor_position.y + ypos - self.vertical_scroll,
                                               x=temp_screen.cursor_position.x + xpos)

        if not new_screen.menu_position and temp_screen.menu_position:
            new_screen.menu_position = Point(y=temp_screen.menu_position.y + ypos - self.vertical_scroll,
                                             x=temp_screen.menu_position.x + xpos)

        # Update height of the output screen.
        new_screen.current_height = max(new_screen.current_height, ypos + y + 1)

        # Remember render info.
        self.render_info = WindowRenderInfo(temp_screen, self.vertical_scroll, height,
                                            new_screen.cursor_position,
                                            applied_scroll_offsets[0],
                                            applied_scroll_offsets[1], applied_scroll_offsets[2])

    def _scroll(self, temp_screen, height, cli):
        """
        Scroll to make sure the cursor position is visible and that we maintain the
        requested scroll offset.
        Return the applied scroll offsets.
        """
        scroll_offset = int(self.scroll_offset)  # Resolve int-value. (In case this is reactive.)

        # Calculate the scroll offset to apply.
        # This can obviously never be more than have the screen size. Also, when the
        # cursor appears at the top or bottom, we don't apply the offset.
        scroll_offset_top = int(min(scroll_offset, height / 2, temp_screen.cursor_position.y))
        scroll_offset_bottom = int(min(scroll_offset, height / 2,
                                       temp_screen.current_height - 1 - temp_screen.cursor_position.y))

        # Prevent negative scroll offsets.
        if self.vertical_scroll < 0:
            self.vertical_scroll = 0

        # Scroll back if we scrolled to much and there's still space to show more of the document.
        if (not self.allow_scroll_beyond_bottom(cli) and
                self.vertical_scroll > temp_screen.current_height - height):
            self.vertical_scroll = max(0, temp_screen.current_height - height)

        # Scroll up if cursor is before visible part.
        if self.vertical_scroll > temp_screen.cursor_position.y - scroll_offset_top:
            self.vertical_scroll = max(0, temp_screen.cursor_position.y - scroll_offset_top)

        # Scroll down if cursor is after visible part.
        if self.vertical_scroll < (temp_screen.cursor_position.y + 1) - height + scroll_offset_bottom:
            self.vertical_scroll = (temp_screen.cursor_position.y + 1) - height + scroll_offset_bottom

        # Calculate the applied scroll offset. This value can be lower than what we had.
        scroll_offset_top = max(0, min(self.vertical_scroll, scroll_offset_top))
        scroll_offset_bottom = max(0, min(temp_screen.current_height - self.vertical_scroll - height, scroll_offset_bottom))

        return scroll_offset, scroll_offset_top, scroll_offset_bottom

    def walk(self):
        # Only yield self. A window doesn't have children.
        yield self
