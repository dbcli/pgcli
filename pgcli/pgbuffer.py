import logging

from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import Condition
from prompt_toolkit.application import get_app
from .packages.parseutils.utils import is_open_quote

_logger = logging.getLogger(__name__)


def _is_complete(sql):
    # A complete command is an sql statement that ends with a semicolon, unless
    # there's an open quote surrounding it, as is common when writing a
    # CREATE FUNCTION command
    return sql.endswith(";") and not is_open_quote(sql)


"""
Returns True if the buffer contents should be handled (i.e. the query/command
executed) immediately. This is necessary as we use prompt_toolkit in multiline
mode, which by default will insert new lines on Enter.
"""


def safe_multi_line_mode(pgcli):
    @Condition
    def cond():
        _logger.debug(
            'Multi-line mode state: "%s" / "%s"', pgcli.multi_line, pgcli.multiline_mode
        )
        return pgcli.multi_line and (pgcli.multiline_mode == "safe")

    return cond


def buffer_should_be_handled(pgcli):
    @Condition
    def cond():
        if not pgcli.multi_line:
            _logger.debug("Not in multi-line mode. Handle the buffer.")
            return True

        if pgcli.multiline_mode == "safe":
            _logger.debug("Multi-line mode is set to 'safe'. Do NOT handle the buffer.")
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
