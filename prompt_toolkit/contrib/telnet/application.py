"""
Interface for Telnet applications.
"""
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass

__all__ = (
    'TelnetApplication',
)


class TelnetApplication(with_metaclass(ABCMeta, object)):
    """
    The interface which has to be implemented for any telnet application.
    An instance of this class has to be passed to `TelnetServer`.
    """
    @abstractmethod
    def create_cli(self, telnet_connection):
        """
        Return a new CommandLineInterface instance from here. This method is
        called for every new connection.

        Hint: Use the following shortcut: `prompt_toolkit.shortcuts.create_cli`
        """

    @abstractmethod
    def client_connected(self, telnet_connection):
        """
        Called when a new client was connected.
        """

    @abstractmethod
    def handle_command(self, telnet_connection, document):
        """
        Called when the user accepted input on the command line.
        """

    @abstractmethod
    def client_leaving(self, telnet_connection):
        """
        Called when a client quits.
        """
