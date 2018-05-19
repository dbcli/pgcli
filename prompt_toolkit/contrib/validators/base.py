from __future__ import unicode_literals
from prompt_toolkit.validation import Validator, ValidationError
from six import string_types


class SentenceValidator(Validator):
    """
    Accept input only when it appears in this list of sentences.

    :param sentences: List of strings.
    :param ignore_case: If True, case-insensitive comparisons.
    """
    def __init__(self, sentences, ignore_case=False, error_message='Invalid input',
                 move_cursor_to_end=False):
        assert all(isinstance(s, string_types) for s in sentences)
        assert isinstance(ignore_case, bool)
        assert isinstance(error_message, string_types)

        self.sentences = sentences
        self.ignore_case = ignore_case
        self.error_message = error_message
        self.move_cursor_to_end = move_cursor_to_end

    def __repr__(self):
        return 'SentenceValidator(%r, ignore_case=%r, error_message=%r)' % (
            self.sentences, self.ignore_case, self.error_message)

    def _is_valid(self, text):
        " Check whether this given text is valid. "
        if self.ignore_case:
            text = text.lower()
            return text in [s.lower() for s in self.sentences]

        return text in self.sentences

    def validate(self, document):
        if self._is_valid(document.text):
            if self.move_cursor_to_end:
                index = len(document.text)
            else:
                index = 0

            raise ValidationError(cursor_position=index,
                                  message=self.error_message)
