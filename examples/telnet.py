#!/usr/bin/env python
from __future__ import unicode_literals

from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.contrib.telnet.application import TelnetApplication
from prompt_toolkit.contrib.telnet.server import TelnetServer
from prompt_toolkit.shortcuts import create_default_application
from prompt_toolkit.application import AbortAction

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
            create_default_application(
                       message='Say something: ',
                       lexer=HtmlLexer,
                       completer=animal_completer,
                       on_abort=AbortAction.RETRY),
            self.handle_command)

    def handle_command(self, telnet_connection, document):
        # When the client enters a command, just reply.
        if document.text == 'exit':
            telnet_connection.close()
        else:
            telnet_connection.send('You said: %s\n\n' % document.text)

    def client_leaving(self, telnet_connection):
        # Say 'bye' when the client quits.
        telnet_connection.send('Bye.\n')


if __name__ == '__main__':
    TelnetServer(application=ExampleApplication(), port=2323).run()
