"""
"""
from __future__ import unicode_literals

__all__ = (
    'ValidationError',
)


class ValidationError(Exception):
    def __init__(self, line=0, column=0, message=''):
        self.line = line
        self.column = column
        self.message = message


class Validator(object):
    def validate(self, document):
        """
        Validate the input.
        If invalid, this should raise `self.validation_error`.
        """
        pass
