from __future__ import unicode_literals

from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import Condition
from prompt_toolkit.application import get_app
from .packages.parseutils.utils import is_open_quote


def _is_complete(sql):
    # A complete command is an sql statement that ends with a semicolon, unless
    # there's an open quote surrounding it, as is common when writing a
    # CREATE FUNCTION command
    return sql.endswith(";") and not is_open_quote(sql)


"""
Returns True if the input mode is multi-line using psql mode, and the main
buffer's contents indicate that it should be handled, False otherwise. This
method is required since by default prompt_toolkit would not handle a buffer on
Enter keypress when in multi-line mode.
"""


def multi_line_buffer_should_be_handled(pgcli):
    @Condition
    def cond():
        if not pgcli.multi_line or pgcli.multiline_mode == "safe":
            return False

        doc = get_app().layout.get_buffer_by_name(DEFAULT_BUFFER).document
        text = doc.text.strip()

        return (
            text.startswith("\\")  # Special Command
            or text.endswith(r"\e")  # Special Command
            or text.endswith(r"\G")  # Ended with \e which should launch the editor
            or _is_complete(text)  # A complete SQL command
            or (text == "exit")  # Exit doesn't need semi-colon
            or (text == "quit")  # Quit doesn't need semi-colon
            or (text == ":q")  # To all the vim fans out there
            or (text == "")  # Just a plain enter without any text
        )

    return cond
