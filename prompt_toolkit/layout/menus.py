from __future__ import unicode_literals

from pygments.token import Token
from ..enums import InputMode

__all__ = (
    'CompletionMenu',
)


class CompletionMenu(object):
    """
    Helper for drawing the complete menu to the screen.
    """
    current_completion_token = Token.CompletionMenu.Completion.Current
    completion_token = Token.CompletionMenu.Completion

    current_meta_token = Token.CompletionMenu.Meta.Current
    meta_token = Token.CompletionMenu.Meta

    progress_button_token = Token.CompletionMenu.ProgressButton
    progress_bar_token = Token.CompletionMenu.ProgressBar

    def __init__(self, max_height=5, line_name='default'):
        self.max_height = max_height
        self.line_name = line_name

    def is_visible(self, cli):
        """
        True when this menu is visible.
        """
        if cli.input_processor.input_mode in (InputMode.SYSTEM, InputMode.INCREMENTAL_SEARCH):
            return False

        return bool(cli.lines[self.line_name].complete_state)

    def get_height(self, complete_state):
        """
        Return the height of the menu. (Number of rows it will use.)
        """
        return min(self.max_height, len(complete_state.current_completions))

    def write(self, screen, complete_cursor_position, complete_state):
        """
        Write the menu to the screen object.
        """
        completions = complete_state.current_completions
        index = complete_state.complete_index  # Can be None!

        # Get position of the menu.
        y, x = complete_cursor_position
        y += 1
        x = max(0, x - 1)  # XXX: Don't draw it in the right margin!!!...

        # Calculate width of completions menu.
        menu_width = self.get_menu_width(screen, complete_state)
        menu_meta_width = self.get_menu_meta_width(screen, complete_state)
        show_meta = self.show_meta(complete_state)

        # Decide which slice of completions to show.
        if len(completions) > self.max_height and (index or 0) > self.max_height / 2:
            slice_from = min(
                (index or 0) - self.max_height // 2,  # In the middle.
                len(completions) - self.max_height  # At the bottom.
            )
        else:
            slice_from = 0

        slice_to = min(slice_from + self.max_height, len(completions))

        # Create a function which decides at which positions the scroll button should be shown.
        def is_scroll_button(row):
            items_per_row = float(len(completions)) / min(len(completions), self.max_height)
            items_on_this_row_from = row * items_per_row
            items_on_this_row_to = (row + 1) * items_per_row
            return items_on_this_row_from <= (index or 0) < items_on_this_row_to

        # Write completions to screen.
        for i, c in enumerate(completions[slice_from:slice_to]):
            is_current_completion = (i + slice_from == index)

            if is_scroll_button(i):
                button_token = self.progress_button_token
            else:
                button_token = self.progress_bar_token

            tokens = ([(Token, ' ')] +
                      self.get_menu_item_tokens(c, is_current_completion, menu_width) +
                      (self.get_menu_item_meta_tokens(c, is_current_completion, menu_meta_width)
                          if show_meta else []) +
                      [(button_token, ' '), (Token, ' ')])

            screen.write_highlighted_at_pos(y+i, x, tokens, z_index=10)

    def show_meta(self, complete_state):
        """
        Return ``True`` if we need to show a column with meta information.
        """
        return any(c.display_meta for c in complete_state.current_completions)

    def get_menu_width(self, screen, complete_state):
        """
        Return the width of the main column.
        """
        max_display = int(screen.size.columns / 2)
        return min(max_display, max(len(c.display) for c in complete_state.current_completions)),

    def get_menu_meta_width(self, screen, complete_state):
        """
        Return the width of the meta column.
        """
        max_display_meta = int(screen.size.columns / 4)
        return min(max_display_meta, max(len(c.display_meta) for c in complete_state.current_completions))

    def get_menu_item_tokens(self, completion, is_current_completion, width):
        if is_current_completion:
            token = self.current_completion_token
        else:
            token = self.completion_token

        return [(token, ' %%-%is ' % width % completion.display)]

    def get_menu_item_meta_tokens(self, completion, is_current_completion, width):
        if is_current_completion:
            token = self.current_meta_token
        else:
            token = self.meta_token

        return [(token, ' %%-%is ' % width % completion.display_meta or 'none')]
