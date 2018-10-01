from __future__ import unicode_literals

from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import Condition
from prompt_toolkit.application import get_app
from .packages.parseutils.utils import is_open_quote


def pg_is_multiline(pgcli):
    @Condition
    def cond():
        doc = get_app().layout.get_buffer_by_name(DEFAULT_BUFFER).document

        if not pgcli.multi_line:
            return False
        if pgcli.multiline_mode == 'safe':
            return True
        else:
            return not _multiline_exception(doc.text)
    return cond


def _is_complete(sql):
    # A complete command is an sql statement that ends with a semicolon, unless
    # there's an open quote surrounding it, as is common when writing a
    # CREATE FUNCTION command
    return sql.endswith(';') and not is_open_quote(sql)


def _multiline_exception(text):
    text = text.strip()
    return (
        text.startswith('\\') or  # Special Command
        text.endswith(r'\e') or  # Ended with \e which should launch the editor
        _is_complete(text) or  # A complete SQL command
        (text == 'exit') or  # Exit doesn't need semi-colon
        (text == 'quit') or  # Quit doesn't need semi-colon
        (text == ':q') or  # To all the vim fans out there
        (text == '')  # Just a plain enter without any text
    )
