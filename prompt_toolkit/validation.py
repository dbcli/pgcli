"""
Input validation for a `Buffer`.
(Validators will be called before accepting input.)
"""
from __future__ import unicode_literals
from .filters import to_filter
from .eventloop import Future, run_in_executor

from abc import ABCMeta, abstractmethod
from six import with_metaclass

__all__ = [
    'ConditionalValidator',
    'ValidationError',
    'Validator',
    'ThreadedValidator',
    'DummyValidator',
    'DynamicValidator',
]


class ValidationError(Exception):
    """
    Error raised by :meth:`.Validator.validate`.

    :param cursor_position: The cursor position where the error occurred.
    :param message: Text.
    """
    def __init__(self, cursor_position=0, message=''):
        super(ValidationError, self).__init__(message)
        self.cursor_position = cursor_position
        self.message = message

    def __repr__(self):
        return '%s(cursor_position=%r, message=%r)' % (
            self.__class__.__name__, self.cursor_position, self.message)


class Validator(with_metaclass(ABCMeta, object)):
    """
    Abstract base class for an input validator.
    """
    @abstractmethod
    def validate(self, document):
        """
        Validate the input.
        If invalid, this should raise a :class:`.ValidationError`.

        :param document: :class:`~prompt_toolkit.document.Document` instance.
        """
        pass

    def get_validate_future(self, document):
        """
        Return a `Future` which is set when the validation is ready.
        This function can be overloaded in order to provide an asynchronous
        implementation.
        """
        try:
            self.validate(document)
        except ValidationError as e:
            return Future.fail(e)
        else:
            return Future.succeed(None)


class ThreadedValidator(Validator):
    """
    Wrapper that runs input validation in a thread.
    (Use this to prevent the user interface from becoming unresponsive if the
    input validation takes too much time.)
    """
    def __init__(self, validator):
        assert isinstance(validator, Validator)
        self.validator = validator

    def validate(self, document):
        return self.validator.validate(document)

    def get_validate_future(self, document):
        """
        Run the `validate` function in a thread.
        """
        def run_validation_thread():
            return self.validate(document)
        f = run_in_executor(run_validation_thread)
        return f


class DummyValidator(Validator):
    """
    Validator class that accepts any input.
    """
    def validate(self, document):
        pass  # Don't raise any exception.


class ConditionalValidator(Validator):
    """
    Validator that can be switched on/off according to
    a filter. (This wraps around another validator.)
    """
    def __init__(self, validator, filter):
        assert isinstance(validator, Validator)

        self.validator = validator
        self.filter = to_filter(filter)

    def validate(self, document):
        # Call the validator only if the filter is active.
        if self.filter():
            self.validator.validate(document)


class DynamicValidator(Validator):
    """
    Validator class that can dynamically returns any Validator.

    :param get_validator: Callable that returns a :class:`.Validator` instance.
    """
    def __init__(self, get_validator):
        assert callable(get_validator)
        self.get_validator = get_validator

    def validate(self, document):
        validator = self.get_validator() or DummyValidator()
        assert isinstance(validator, Validator)
        return validator.validate(document)

    def get_validate_future(self, document):
        validator = self.get_validator() or DummyValidator()
        assert isinstance(validator, Validator)
        return validator.get_validate_future(document)
