"""
"""
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod

__all__ = (
    'ValidationError',
)


class ValidationError(Exception):
    def __init__(self, index=0, message=''):
        self.index = index
        self.message = message


class Validator(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def validate(self, document):
        """
        Validate the input.
        If invalid, this should raise `self.validation_error`.
        """
        pass
