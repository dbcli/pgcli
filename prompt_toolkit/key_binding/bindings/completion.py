"""
Key binding handlers for displaying completions.
"""
from __future__ import unicode_literals
from prompt_toolkit.application.run_in_terminal import run_coroutine_in_terminal
from prompt_toolkit.completion import CompleteEvent, get_common_complete_suffix
from prompt_toolkit.utils import get_cwidth
from prompt_toolkit.keys import Keys
from prompt_toolkit.key_binding.key_bindings import KeyBindings

import math

__all__ = [
    'generate_completions',
    'display_completions_like_readline',
]


def generate_completions(event):
    r"""
    Tab-completion: where the first tab completes the common suffix and the
    second tab lists all the completions.
    """
    b = event.current_buffer

    # When already navigating through completions, select the next one.
    if b.complete_state:
        b.complete_next()
    else:
        b.start_completion(insert_common_part=True)


def display_completions_like_readline(event):
    """
    Key binding handler for readline-style tab completion.
    This is meant to be as similar as possible to the way how readline displays
    completions.

    Generate the completions immediately (blocking) and display them above the
    prompt in columns.

    Usage::

        # Call this handler when 'Tab' has been pressed.
        key_bindings.add(Keys.ControlI)(display_completions_like_readline)
    """
    # Request completions.
    b = event.current_buffer
    if b.completer is None:
        return
    complete_event = CompleteEvent(completion_requested=True)
    completions = list(b.completer.get_completions(b.document, complete_event))

    # Calculate the common suffix.
    common_suffix = get_common_complete_suffix(b.document, completions)

    # One completion: insert it.
    if len(completions) == 1:
        b.delete_before_cursor(-completions[0].start_position)
        b.insert_text(completions[0].text)
    # Multiple completions with common part.
    elif common_suffix:
        b.insert_text(common_suffix)
    # Otherwise: display all completions.
    elif completions:
        _display_completions_like_readline(event.app, completions)


def _display_completions_like_readline(app, completions):
    """
    Display the list of completions in columns above the prompt.
    This will ask for a confirmation if there are too many completions to fit
    on a single page and provide a paginator to walk through them.
    """
    from prompt_toolkit.shortcuts.prompt import create_confirm_session
    assert isinstance(completions, list)

    # Get terminal dimensions.
    term_size = app.output.get_size()
    term_width = term_size.columns
    term_height = term_size.rows

    # Calculate amount of required columns/rows for displaying the
    # completions. (Keep in mind that completions are displayed
    # alphabetically column-wise.)
    max_compl_width = min(term_width,
        max(get_cwidth(c.text) for c in completions) + 1)
    column_count = max(1, term_width // max_compl_width)
    completions_per_page = column_count * (term_height - 1)
    page_count = int(math.ceil(len(completions) / float(completions_per_page)))
        # Note: math.ceil can return float on Python2.

    def display(page):
        # Display completions.
        page_completions = completions[page * completions_per_page:
                                       (page + 1) * completions_per_page]

        page_row_count = int(math.ceil(len(page_completions) / float(column_count)))
        page_columns = [page_completions[i * page_row_count:(i + 1) * page_row_count]
                   for i in range(column_count)]

        result = []
        for r in range(page_row_count):
            for c in range(column_count):
                try:
                    result.append(page_columns[c][r].text.ljust(max_compl_width))
                except IndexError:
                    pass
            result.append('\n')

        app.output.write(''.join(result))
        app.output.flush()

    # User interaction through an application generator function.
    def run_compl():
        " Coroutine. "
        if len(completions) > completions_per_page:
            # Ask confirmation if it doesn't fit on the screen.
            confirm = yield create_confirm_session(
                'Display all {} possibilities?'.format(len(completions)),
                ).prompt(async_=True)

            if confirm:
                # Display pages.
                for page in range(page_count):
                    display(page)

                    if page != page_count - 1:
                        # Display --MORE-- and go to the next page.
                        show_more = yield _create_more_session('--MORE--').prompt(async_=True)

                        if not show_more:
                            return
            else:
                app.output.flush()
        else:
            # Display all completions.
            display(0)

    run_coroutine_in_terminal(run_compl, render_cli_done=True)


def _create_more_session(message='--MORE--'):
    """
    Create a `PromptSession` object for displaying the "--MORE--".
    """
    from prompt_toolkit.shortcuts import PromptSession
    bindings = KeyBindings()

    @bindings.add(' ')
    @bindings.add('y')
    @bindings.add('Y')
    @bindings.add(Keys.ControlJ)
    @bindings.add(Keys.ControlM)
    @bindings.add(Keys.ControlI)  # Tab.
    def _(event):
        event.app.exit(result=True)

    @bindings.add('n')
    @bindings.add('N')
    @bindings.add('q')
    @bindings.add('Q')
    @bindings.add(Keys.ControlC)
    def _(event):
        event.app.exit(result=False)

    @bindings.add(Keys.Any)
    def _(event):
        " Disable inserting of text. "

    session = PromptSession(message,
        key_bindings=bindings,
        erase_when_done=True)
    return session
