"""
Input validation for a `Buffer`.
(Validators will be called before accepting input.)
"""
from __future__ import unicode_literals
from .filters import SimpleFilter, Always

from abc import ABCMeta, abstractmethod
from six import with_metaclass

__all__ = (
    'SwitchableValidator',
    'ValidationError',
    'Validator',
)


class ValidationError(Exception):
    def __init__(self, index=0, message=''):
        super(ValidationError, self).__init__(message)
        self.index = index
        self.message = message

    def __repr__(self):
        return '%s(index=%r, message=%r)' % (
            self.__class__.__name__, self.index, self.message)


class Validator(with_metaclass(ABCMeta, object)):
    @abstractmethod
    def validate(self, document):
        """
        Validate the input.
        If invalid, this should raise `self.validation_error`.
        """
        pass


class SwitchableValidator(Validator):
    """
    Validator that can be switched on/off according to
    a filter. (This wraps around another validator.)
    """
    def __init__(self, validator, enabled=Always()):
        assert isinstance(validator, Validator)
        assert isinstance(enabled, SimpleFilter)

        self.validator = validator
        self.enabled = enabled

    def validate(self, document):
        # Call the validator only if the filter is active.
        if self.enabled():
            self.validator.validate(document)
