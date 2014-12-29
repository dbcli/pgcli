#!/usr/bin/env python
"""
Simple example of input validation.
"""
from __future__ import unicode_literals

from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.contrib.shortcuts import get_input

from pygments.token import Token
from pygments.style import Style


class EmailValidator(Validator):
    def validate(self, document):
        if '@' not in document.text:
            raise ValidationError(message='Not a valid e-mail address')


class TestStyle(Style):
    styles = {
        Token.Toolbar.Validation:  'bg:#aa0000 #ffbbbb',
    }


def main():
    text = get_input('Enter e-mail address: ', validator=EmailValidator(), style=TestStyle)
    print('You said: %s' % text)

if __name__ == '__main__':
    main()
