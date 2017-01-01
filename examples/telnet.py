#!/usr/bin/env python
from __future__ import unicode_literals

from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.contrib.telnet.application import TelnetApplication
from prompt_toolkit.contrib.telnet.server import TelnetServer
from prompt_toolkit.shortcuts import Prompt
from prompt_toolkit.layout.lexers import PygmentsLexer

from pygments.lexers import HtmlLexer

import logging

# Set up logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


class ExampleApplication(TelnetApplication):
    def client_connected(self, telnet_connection):
        # When a client is connected, erase the screen from the client and say
        # Hello.
        telnet_connection.erase_screen()
        telnet_connection.send('Welcome!\n')

        # Set CommandLineInterface.
        animal_completer = WordCompleter(['alligator', 'ant'])
        telnet_connection.set_application(
            Prompt(message='Say something: ',
                   lexer=PygmentsLexer(HtmlLexer),
                   completer=animal_completer,
                   output=telnet_connection.vt100_output).app,
            self.handle_command)

    def handle_command(self, telnet_connection, text):
        # When the client enters a command, just reply.
        if text == 'exit':
            telnet_connection.close()
        else:
            telnet_connection.send('You said: %s\n\n' % text)

    def client_leaving(self, telnet_connection):
        # Say 'bye' when the client quits.
        telnet_connection.send('Bye.\n')


if __name__ == '__main__':
    TelnetServer(application=ExampleApplication(), port=2323).run()
