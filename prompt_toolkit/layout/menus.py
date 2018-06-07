from __future__ import unicode_literals

from six.moves import zip_longest, range
from prompt_toolkit.application.current import get_app
from prompt_toolkit.filters import has_completions, is_done, Condition, to_filter
from prompt_toolkit.mouse_events import MouseEventType
from prompt_toolkit.utils import get_cwidth

from .containers import Window, HSplit, ConditionalContainer, ScrollOffsets
from .controls import UIControl, UIContent
from .dimension import Dimension
from .margins import ScrollbarMargin
from .screen import Point

import math

__all__ = [
    'CompletionsMenu',
    'MultiColumnCompletionsMenu',
]


class CompletionsMenuControl(UIControl):
    """
    Helper for drawing the complete menu to the screen.

    :param scroll_offset: Number (integer) representing the preferred amount of
        completions to be displayed before and after the current one. When this
        is a very high number, the current completion will be shown in the
        middle most of the time.
    """
    # Preferred minimum size of the menu control.
    # The CompletionsMenu class defines a width of 8, and there is a scrollbar
    # of 1.)
    MIN_WIDTH = 7

    def has_focus(self):
        return False

    def preferred_width(self, max_available_width):
        complete_state = get_app().current_buffer.complete_state
        if complete_state:
            menu_width = self._get_menu_width(500, complete_state)
            menu_meta_width = self._get_menu_meta_width(500, complete_state)

            return menu_width + menu_meta_width
        else:
            return 0

    def preferred_height(self, width, max_available_height, wrap_lines):
        complete_state = get_app().current_buffer.complete_state
        if complete_state:
            return len(complete_state.completions)
        else:
            return 0

    def create_content(self, width, height):
        """
        Create a UIContent object for this control.
        """
        complete_state = get_app().current_buffer.complete_state
        if complete_state:
            completions = complete_state.completions
            index = complete_state.complete_index  # Can be None!

            # Calculate width of completions menu.
            menu_width = self._get_menu_width(width, complete_state)
            menu_meta_width = self._get_menu_meta_width(width - menu_width, complete_state)
            show_meta = self._show_meta(complete_state)

            def get_line(i):
                c = completions[i]
                is_current_completion = (i == index)
                result = self._get_menu_item_fragments(c, is_current_completion, menu_width)

                if show_meta:
                    result += self._get_menu_item_meta_fragments(c, is_current_completion, menu_meta_width)
                return result

            return UIContent(get_line=get_line,
                             cursor_position=Point(x=0, y=index or 0),
                             line_count=len(completions))

        return UIContent()

    def _show_meta(self, complete_state):
        """
        Return ``True`` if we need to show a column with meta information.
        """
        return any(c.display_meta for c in complete_state.completions)

    def _get_menu_width(self, max_width, complete_state):
        """
        Return the width of the main column.
        """
        return min(max_width, max(self.MIN_WIDTH, max(get_cwidth(c.display)
                   for c in complete_state.completions) + 2))

    def _get_menu_meta_width(self, max_width, complete_state):
        """
        Return the width of the meta column.
        """
        if self._show_meta(complete_state):
            return min(max_width, max(get_cwidth(c.display_meta)
                       for c in complete_state.completions) + 2)
        else:
            return 0

    def _get_menu_item_fragments(self, completion, is_current_completion, width):
        if is_current_completion:
            style_str = 'class:completion-menu.completion.current %s %s' % (
                completion.style, completion.selected_style)
        else:
            style_str = 'class:completion-menu.completion ' + completion.style

        text, tw = _trim_text(completion.display, width - 2)
        padding = ' ' * (width - 2 - tw)
        return [(style_str, ' %s%s ' % (text, padding))]

    def _get_menu_item_meta_fragments(self, completion, is_current_completion, width):
        if is_current_completion:
            style_str = 'class:completion-menu.meta.completion.current'
        else:
            style_str = 'class:completion-menu.meta.completion'

        text, tw = _trim_text(completion.display_meta, width - 2)
        padding = ' ' * (width - 2 - tw)
        return [(style_str, ' %s%s ' % (text, padding))]

    def mouse_handler(self, mouse_event):
        """
        Handle mouse events: clicking and scrolling.
        """
        b = get_app().current_buffer

        if mouse_event.event_type == MouseEventType.MOUSE_UP:
            # Select completion.
            b.go_to_completion(mouse_event.position.y)
            b.complete_state = None

        elif mouse_event.event_type == MouseEventType.SCROLL_DOWN:
            # Scroll up.
            b.complete_next(count=3, disable_wrap_around=True)

        elif mouse_event.event_type == MouseEventType.SCROLL_UP:
            # Scroll down.
            b.complete_previous(count=3, disable_wrap_around=True)


def _trim_text(text, max_width):
    """
    Trim the text to `max_width`, append dots when the text is too long.
    Returns (text, width) tuple.
    """
    width = get_cwidth(text)

    # When the text is too wide, trim it.
    if width > max_width:
        # When there are no double width characters, just use slice operation.
        if len(text) == width:
            trimmed_text = (text[:max(1, max_width - 3)] + '...')[:max_width]
            return trimmed_text, len(trimmed_text)

        # Otherwise, loop until we have the desired width. (Rather
        # inefficient, but ok for now.)
        else:
            trimmed_text = ''
            for c in text:
                if get_cwidth(trimmed_text + c) <= max_width - 3:
                    trimmed_text += c
            trimmed_text += '...'

            return (trimmed_text, get_cwidth(trimmed_text))
    else:
        return text, width


class CompletionsMenu(ConditionalContainer):
    # NOTE: We use a pretty big z_index by default. Menus are supposed to be
    #       above anything else. We also want to make sure that the content is
    #       visible at the point where we draw this menu.
    def __init__(self, max_height=None, scroll_offset=0, extra_filter=True,
                 display_arrows=False, z_index=10 ** 8):
        extra_filter = to_filter(extra_filter)
        display_arrows = to_filter(display_arrows)

        super(CompletionsMenu, self).__init__(
            content=Window(
                content=CompletionsMenuControl(),
                width=Dimension(min=8),
                height=Dimension(min=1, max=max_height),
                scroll_offsets=ScrollOffsets(top=scroll_offset, bottom=scroll_offset),
                right_margins=[ScrollbarMargin(display_arrows=display_arrows)],
                dont_extend_width=True,
                style='class:completion-menu',
                z_index=z_index,
            ),
            # Show when there are completions but not at the point we are
            # returning the input.
            filter=has_completions & ~is_done & extra_filter)


class MultiColumnCompletionMenuControl(UIControl):
    """
    Completion menu that displays all the completions in several columns.
    When there are more completions than space for them to be displayed, an
    arrow is shown on the left or right side.

    `min_rows` indicates how many rows will be available in any possible case.
    When this is larger than one, it will try to use less columns and more
    rows until this value is reached.
    Be careful passing in a too big value, if less than the given amount of
    rows are available, more columns would have been required, but
    `preferred_width` doesn't know about that and reports a too small value.
    This results in less completions displayed and additional scrolling.
    (It's a limitation of how the layout engine currently works: first the
    widths are calculated, then the heights.)

    :param suggested_max_column_width: The suggested max width of a column.
        The column can still be bigger than this, but if there is place for two
        columns of this width, we will display two columns. This to avoid that
        if there is one very wide completion, that it doesn't significantly
        reduce the amount of columns.
    """
    _required_margin = 3  # One extra padding on the right + space for arrows.

    def __init__(self, min_rows=3, suggested_max_column_width=30):
        assert isinstance(min_rows, int) and min_rows >= 1

        self.min_rows = min_rows
        self.suggested_max_column_width = suggested_max_column_width
        self.scroll = 0

        # Info of last rendering.
        self._rendered_rows = 0
        self._rendered_columns = 0
        self._total_columns = 0
        self._render_pos_to_completion = {}
        self._render_left_arrow = False
        self._render_right_arrow = False
        self._render_width = 0

    def reset(self):
        self.scroll = 0

    def has_focus(self):
        return False

    def preferred_width(self, max_available_width):
        """
        Preferred width: prefer to use at least min_rows, but otherwise as much
        as possible horizontally.
        """
        complete_state = get_app().current_buffer.complete_state
        column_width = self._get_column_width(complete_state)
        result = int(column_width * math.ceil(len(complete_state.completions) / float(self.min_rows)))

        # When the desired width is still more than the maximum available,
        # reduce by removing columns until we are less than the available
        # width.
        while result > column_width and result > max_available_width - self._required_margin:
            result -= column_width
        return result + self._required_margin

    def preferred_height(self, width, max_available_height, wrap_lines):
        """
        Preferred height: as much as needed in order to display all the completions.
        """
        complete_state = get_app().current_buffer.complete_state
        column_width = self._get_column_width(complete_state)
        column_count = max(1, (width - self._required_margin) // column_width)

        return int(math.ceil(len(complete_state.completions) / float(column_count)))

    def create_content(self, width, height):
        """
        Create a UIContent object for this menu.
        """
        complete_state = get_app().current_buffer.complete_state
        column_width = self._get_column_width(complete_state)
        self._render_pos_to_completion = {}

        def grouper(n, iterable, fillvalue=None):
            " grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx "
            args = [iter(iterable)] * n
            return zip_longest(fillvalue=fillvalue, *args)

        def is_current_completion(completion):
            " Returns True when this completion is the currently selected one. "
            return complete_state.complete_index is not None and c == complete_state.current_completion

        # Space required outside of the regular columns, for displaying the
        # left and right arrow.
        HORIZONTAL_MARGIN_REQUIRED = 3

        if complete_state:
            # There should be at least one column, but it cannot be wider than
            # the available width.
            column_width = min(width - HORIZONTAL_MARGIN_REQUIRED, column_width)

            # However, when the columns tend to be very wide, because there are
            # some very wide entries, shrink it anyway.
            if column_width > self.suggested_max_column_width:
                # `column_width` can still be bigger that `suggested_max_column_width`,
                # but if there is place for two columns, we divide by two.
                column_width //= (column_width // self.suggested_max_column_width)

            visible_columns = max(1, (width - self._required_margin) // column_width)

            columns_ = list(grouper(height, complete_state.completions))
            rows_ = list(zip(*columns_))

            # Make sure the current completion is always visible: update scroll offset.
            selected_column = (complete_state.complete_index or 0) // height
            self.scroll = min(selected_column, max(self.scroll, selected_column - visible_columns + 1))

            render_left_arrow = self.scroll > 0
            render_right_arrow = self.scroll < len(rows_[0]) - visible_columns

            # Write completions to screen.
            fragments_for_line = []

            for row_index, row in enumerate(rows_):
                fragments = []
                middle_row = row_index == len(rows_) // 2

                # Draw left arrow if we have hidden completions on the left.
                if render_left_arrow:
                    fragments += [('class:scrollbar', '<' if middle_row else ' ')]

                # Draw row content.
                for column_index, c in enumerate(row[self.scroll:][:visible_columns]):
                    if c is not None:
                        fragments += self._get_menu_item_fragments(c, is_current_completion(c), column_width)

                        # Remember render position for mouse click handler.
                        for x in range(column_width):
                            self._render_pos_to_completion[(column_index * column_width + x, row_index)] = c
                    else:
                        fragments += [('class:completion', ' ' * column_width)]

                # Draw trailing padding. (_get_menu_item_fragments only returns padding on the left.)
                fragments += [('class:completion', ' ')]

                # Draw right arrow if we have hidden completions on the right.
                if render_right_arrow:
                    fragments += [('class:scrollbar', '>' if middle_row else ' ')]

                # Newline.
                fragments_for_line.append(fragments)

        else:
            fragments = []

        self._rendered_rows = height
        self._rendered_columns = visible_columns
        self._total_columns = len(columns_)
        self._render_left_arrow = render_left_arrow
        self._render_right_arrow = render_right_arrow
        self._render_width = column_width * visible_columns + render_left_arrow + render_right_arrow + 1

        def get_line(i):
            return fragments_for_line[i]

        return UIContent(get_line=get_line, line_count=len(rows_))

    def _get_column_width(self, complete_state):
        """
        Return the width of each column.
        """
        return max(get_cwidth(c.display) for c in complete_state.completions) + 1

    def _get_menu_item_fragments(self, completion, is_current_completion, width):
        if is_current_completion:
            style_str = 'class:completion-menu.completion.current %s %s' % (
                completion.style, completion.selected_style)
        else:
            style_str = 'class:completion-menu.completion ' + completion.style

        text, tw = _trim_text(completion.display, width)
        padding = ' ' * (width - tw - 1)

        return [(style_str, ' %s%s' % (text, padding))]

    def mouse_handler(self, mouse_event):
        """
        Handle scroll and click events.
        """
        b = get_app().current_buffer

        def scroll_left():
            b.complete_previous(count=self._rendered_rows, disable_wrap_around=True)
            self.scroll = max(0, self.scroll - 1)

        def scroll_right():
            b.complete_next(count=self._rendered_rows, disable_wrap_around=True)
            self.scroll = min(self._total_columns - self._rendered_columns, self.scroll + 1)

        if mouse_event.event_type == MouseEventType.SCROLL_DOWN:
            scroll_right()

        elif mouse_event.event_type == MouseEventType.SCROLL_UP:
            scroll_left()

        elif mouse_event.event_type == MouseEventType.MOUSE_UP:
            x = mouse_event.position.x
            y = mouse_event.position.y

            # Mouse click on left arrow.
            if x == 0:
                if self._render_left_arrow:
                    scroll_left()

            # Mouse click on right arrow.
            elif x == self._render_width - 1:
                if self._render_right_arrow:
                    scroll_right()

            # Mouse click on completion.
            else:
                completion = self._render_pos_to_completion.get((x, y))
                if completion:
                    b.apply_completion(completion)

    def get_key_bindings(self):
        """
        Expose key bindings that handle the left/right arrow keys when the menu
        is displayed.
        """
        from prompt_toolkit.key_binding.key_bindings import KeyBindings
        kb = KeyBindings()

        @Condition
        def filter():
            " Only handle key bindings if this menu is visible. "
            app = get_app()
            complete_state = app.current_buffer.complete_state

            # There need to be completions, and one needs to be selected.
            if complete_state is None or complete_state.complete_index is None:
                return False

            # This menu needs to be visible.
            return any(
                window.content == self
                for window in app.layout.visible_windows)

        def move(right=False):
            buff = get_app().current_buffer
            complete_state = buff.complete_state

            if complete_state is not None and \
                    buff.complete_state.complete_index is not None:
                # Calculate new complete index.
                new_index = buff.complete_state.complete_index
                if right:
                    new_index += self._rendered_rows
                else:
                    new_index -= self._rendered_rows

                if 0 <= new_index < len(complete_state.completions):
                    buff.go_to_completion(new_index)

        # NOTE: the is_global is required because the completion menu will
        #       never be focussed.

        @kb.add('left', is_global=True, filter=filter)
        def _(event):
            move()

        @kb.add('right', is_global=True, filter=filter)
        def _(event):
            move(True)

        return kb


class MultiColumnCompletionsMenu(HSplit):
    """
    Container that displays the completions in several columns.
    When `show_meta` (a :class:`~prompt_toolkit.filters.Filter`) evaluates
    to True, it shows the meta information at the bottom.
    """
    def __init__(self, min_rows=3, suggested_max_column_width=30,
                 show_meta=True, extra_filter=True, z_index=10 ** 8):
        show_meta = to_filter(show_meta)
        extra_filter = to_filter(extra_filter)

        # Display filter: show when there are completions but not at the point
        # we are returning the input.
        full_filter = has_completions & ~is_done & extra_filter

        @Condition
        def any_completion_has_meta():
            return any(c.display_meta for c in get_app().current_buffer.complete_state.completions)

        # Create child windows.
        completions_window = ConditionalContainer(
            content=Window(
                content=MultiColumnCompletionMenuControl(
                    min_rows=min_rows, suggested_max_column_width=suggested_max_column_width),
                width=Dimension(min=8),
                height=Dimension(min=1),
                style='class:completion-menu'),
            filter=full_filter)

        meta_window = ConditionalContainer(
            content=Window(content=_SelectedCompletionMetaControl()),
            filter=show_meta & full_filter & any_completion_has_meta)

        # Initialise split.
        super(MultiColumnCompletionsMenu, self).__init__([
            completions_window,
            meta_window
        ], z_index=z_index)


class _SelectedCompletionMetaControl(UIControl):
    """
    Control that shows the meta information of the selected completion.
    """
    def preferred_width(self, max_available_width):
        """
        Report the width of the longest meta text as the preferred width of this control.

        It could be that we use less width, but this way, we're sure that the
        layout doesn't change when we select another completion (E.g. that
        completions are suddenly shown in more or fewer columns.)
        """
        app = get_app()
        if app.current_buffer.complete_state:
            state = app.current_buffer.complete_state
            return 2 + max(get_cwidth(c.display_meta) for c in state.completions)
        else:
            return 0

    def preferred_height(self, width, max_available_height, wrap_lines):
        return 1

    def create_content(self, width, height):
        fragments = self._get_text_fragments()

        def get_line(i):
            return fragments

        return UIContent(get_line=get_line, line_count=1 if fragments else 0)

    def _get_text_fragments(self):
        style = 'class:completion-menu.multi-column-meta'
        state = get_app().current_buffer.complete_state

        if state and state.current_completion and state.current_completion.display_meta:
            return [(style, ' %s ' % state.current_completion.display_meta)]

        return []
