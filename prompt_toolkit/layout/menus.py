from __future__ import unicode_literals

from pygments.token import Token
from prompt_toolkit.filters import HasCompletions, IsDone, Always
from prompt_toolkit.utils import get_cwidth

from .controls import UIControl
from .containers import Window
from .dimension import LayoutDimension
from .screen import Screen

__all__ = (
    'CompletionsMenu',
)


class CompletionsMenuControl(UIControl):
    """
    Helper for drawing the complete menu to the screen.
    """
    def __init__(self):
        self.token = Token.Menu.Completions

    def has_focus(self, cli):
        return False

    def preferred_width(self, cli):
        complete_state = cli.current_buffer.complete_state
        if complete_state:
            menu_width = self._get_menu_width(500, complete_state)
            menu_meta_width = self._get_menu_meta_width(500, complete_state)

            return menu_width + menu_meta_width + 1
        else:
            return 0

    def preferred_height(self, cli, width):
        complete_state = cli.current_buffer.complete_state
        if complete_state:
            return len(complete_state.current_completions)
        else:
            return 0

    def create_screen(self, cli, width, height):
        """
        Write the menu to the screen object.
        """
        screen = Screen(width)

        complete_state = cli.current_buffer.complete_state
        if complete_state:
            completions = complete_state.current_completions
            index = complete_state.complete_index  # Can be None!

            # Calculate width of completions menu.
            menu_width = self._get_menu_width(width - 1, complete_state)
            menu_meta_width = self._get_menu_meta_width(width - 1 - menu_width, complete_state)
            show_meta = self._show_meta(complete_state)

            if menu_width + menu_meta_width + 1 < width:
                menu_width += width - (menu_width + menu_meta_width + 1)

            # Decide which slice of completions to show.
            if len(completions) > height and (index or 0) > height / 2:
                slice_from = min(
                    (index or 0) - height // 2,  # In the middle.
                    len(completions) - height  # At the bottom.
                )
            else:
                slice_from = 0

            slice_to = min(slice_from + height, len(completions))

            # Create a function which decides at which positions the scroll button should be shown.
            def is_scroll_button(row):
                items_per_row = float(len(completions)) / min(len(completions), height)
                items_on_this_row_from = row * items_per_row
                items_on_this_row_to = (row + 1) * items_per_row
                return items_on_this_row_from <= (index or 0) < items_on_this_row_to

            # Write completions to screen.
            tokens = []

            for i, c in enumerate(completions[slice_from:slice_to]):
                is_current_completion = (i + slice_from == index)

                if is_scroll_button(i):
                    button_token = self.token.ProgressButton
                else:
                    button_token = self.token.ProgressBar

                if tokens:
                    tokens += [(Token, '\n')]
                tokens += (self._get_menu_item_tokens(c, is_current_completion, menu_width) +
                           (self._get_menu_item_meta_tokens(c, is_current_completion, menu_meta_width)
                               if show_meta else []) +
                           [(button_token, ' '), ])

            screen.write_data(tokens, width)

        return screen

    def _show_meta(self, complete_state):
        """
        Return ``True`` if we need to show a column with meta information.
        """
        return any(c.display_meta for c in complete_state.current_completions)

    def _get_menu_width(self, max_width, complete_state):
        """
        Return the width of the main column.
        """
        return min(max_width, max(get_cwidth(c.display)
                   for c in complete_state.current_completions) + 2)

    def _get_menu_meta_width(self, max_width, complete_state):
        """
        Return the width of the meta column.
        """
        if self._show_meta(complete_state):
            return min(max_width, max(get_cwidth(c.display_meta)
                       for c in complete_state.current_completions) + 2)
        else:
            return 0

    def _get_menu_item_tokens(self, completion, is_current_completion, width):
        if is_current_completion:
            token = self.token.Completion.Current
        else:
            token = self.token.Completion

        text, tw = self._trim_text(completion.display, width - 2)
        padding = ' ' * (width - 2 - tw)
        return [(token, ' %s%s ' % (text, padding))]

    def _get_menu_item_meta_tokens(self, completion, is_current_completion, width):
        if is_current_completion:
            token = self.token.Meta.Current
        else:
            token = self.token.Meta

        text, tw = self._trim_text(completion.display_meta, width - 2)
        padding = ' ' * (width - 2 - tw)
        return [(token, ' %s%s ' % (text, padding))]

    def _trim_text(self, text, max_width):
        """
        Trim the text to `max_width`, append dots when the text is too long.
        Returns (text, width) tuple.
        """
        width = get_cwidth(text)

        # When the text is too wide, trim it.
        if width > max_width:
            # When there are no double width characters, just use slice operation.
            if len(text) == width:
                trimmed_text = (text[:max(1, max_width-3)] + '...')[:max_width]
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


class CompletionsMenu(Window):
    def __init__(self, max_height=None, extra_filter=Always()):
        super(CompletionsMenu, self).__init__(
            content=CompletionsMenuControl(),
            width=LayoutDimension(min=8),
            height=LayoutDimension(min=1, max=max_height),
            # Show when there are completions but not at the point we are
            # returning the input.
            filter=HasCompletions() & ~IsDone() & extra_filter)
