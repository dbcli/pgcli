"""
Input validation for a `Buffer`.
(Validators will be called before accepting input.)
"""
from __future__ import unicode_literals
from .filters import to_filter
from .eventloop import Future, run_in_executor

from abc import ABCMeta, abstractmethod
from six import with_metaclass, text_type

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

    A validator is typically created in one of the following two ways:

    - Either by overriding this class and implementing the `validate` method.
    - Or by passing a callable to `Validator.from_callable`.

    If the validation takes some time and needs to happen in a background
    thread, this can be wrapped in a :class:`.ThreadedValidator`.
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

    @classmethod
    def from_callable(cls, validate_func, error_message='Invalid input',
                      move_cursor_to_end=False):
        """
        Create a validator from a simple validate callable. E.g.:

        .. code:: python

            def is_valid(text):
                return text in ['hello', 'world']
            Validator.from_callable(is_valid, error_message='Invalid input')

        :param validate_func: Callable that takes the input string, and returns
            `True` if the input is valid input.
        :param error_message: Message to be displayed if the input is invalid.
        :param move_cursor_to_end: Move the cursor to the end of the input, if
            the input is invalid.
        """
        return _ValidatorFromCallable(
            validate_func, error_message, move_cursor_to_end)


class _ValidatorFromCallable(Validator):
    """
    Validate input from a simple callable.
    """
    def __init__(self, func, error_message, move_cursor_to_end):
        assert callable(func)
        assert isinstance(error_message, text_type)

        self.func = func
        self.error_message = error_message
        self.move_cursor_to_end = move_cursor_to_end

    def __repr__(self):
        return 'Validator.from_callable(%r)' % (self.func, )

    def validate(self, document):
        if not self.func(document.text):
            if self.move_cursor_to_end:
                index = len(document.text)
            else:
                index = 0

            raise ValidationError(cursor_position=index,
                                  message=self.error_message)


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
