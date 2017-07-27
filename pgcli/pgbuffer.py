from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from .packages.parseutils.utils import is_open_quote


class PGBuffer(Buffer):
    def __init__(self, always_multiline, multiline_mode, *args, **kwargs):
        self.always_multiline = always_multiline
        self.multiline_mode = multiline_mode

        @Condition
        def is_multiline():
            doc = self.document
            if not self.always_multiline:
                return False
            if self.multiline_mode == 'safe':
                return True
            else:
                return not _multiline_exception(doc.text)

        super(self.__class__, self).__init__(*args, is_multiline=is_multiline,
                                             tempfile_suffix='.sql', **kwargs)


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
