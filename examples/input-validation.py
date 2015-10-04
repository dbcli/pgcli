#!/usr/bin/env python
"""
Simple example of input validation.
"""
from __future__ import unicode_literals

from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit import prompt


class EmailValidator(Validator):
    def validate(self, document):
        if '@' not in document.text:
            raise ValidationError(message='Not a valid e-mail address (Does not contain an @).',
                                  cursor_position=len(document.text))  # Move cursor to end of input.


def main():
    text = prompt('Enter e-mail address: ', validator=EmailValidator())
    print('You said: %s' % text)

if __name__ == '__main__':
    main()
