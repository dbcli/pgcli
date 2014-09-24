#!/usr/bin/env python
"""
Simple example of the layout options.
"""
from __future__ import unicode_literals

from prompt_toolkit import CommandLineInterface
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.toolbars import ValidationToolbar
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.line import Line

from pygments.token import Token
from pygments.style import Style


layout = Layout(
    before_input = DefaultPrompt(text='Give an e-mail address: '),
    bottom_toolbars = [ValidationToolbar()]
)

class EmailValidator(Validator):
    def validate(self, document):
        if not '@' in document.text:
            raise ValidationError(message='Not a valid e-mail address')


class TestLine(Line):
    is_multiline = True


class TestStyle(Style):
    styles = {
        Token.ValidationToolbar:  'bg:#aa0000 #ffbbbb',
    }


def main():
    cli = CommandLineInterface(layout=layout, style=TestStyle, line=Line(validator=EmailValidator()))

    document = cli.read_input()
    print('You said: ' + document.text)


if __name__ == '__main__':
    main()
