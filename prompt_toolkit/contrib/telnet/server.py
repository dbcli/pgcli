"""
Telnet server.
"""
from __future__ import unicode_literals

import socket

from six import int2byte, text_type, binary_type

from prompt_toolkit.application.current import get_app
from prompt_toolkit.eventloop import get_event_loop, ensure_future, Future, From
from prompt_toolkit.eventloop.context import context
from prompt_toolkit.input.vt100 import PipeInput
from prompt_toolkit.layout.screen import Size
from prompt_toolkit.output.vt100 import Vt100_Output
from prompt_toolkit.shortcuts import Prompt

from .log import logger
from .protocol import IAC, DO, LINEMODE, SB, MODE, SE, WILL, ECHO, NAWS, SUPPRESS_GO_AHEAD
from .protocol import TelnetProtocolParser

__all__ = (
    'TelnetServer',
)


def _initialize_telnet(connection):
    logger.info('Initializing telnet connection')

    # Iac Do Linemode
    connection.send(IAC + DO + LINEMODE)

    # Suppress Go Ahead. (This seems important for Putty to do correct echoing.)
    # This will allow bi-directional operation.
    connection.send(IAC + WILL + SUPPRESS_GO_AHEAD)

    # Iac sb
    connection.send(IAC + SB + LINEMODE + MODE + int2byte(0) + IAC + SE)

    # IAC Will Echo
    connection.send(IAC + WILL + ECHO)

    # Negotiate window size
    connection.send(IAC + DO + NAWS)


class _ConnectionStdout(object):
    """
    Wrapper around socket which provides `write` and `flush` methods for the
    Vt100_Output output.
    """
    def __init__(self, connection, encoding):
        self._encoding = encoding
        self._connection = connection
        self._buffer = []

    def write(self, data):
        assert isinstance(data, text_type)
        self._buffer.append(data.encode(self._encoding))
        self.flush()

    def flush(self):
        try:
            self._connection.send(b''.join(self._buffer))
        except socket.error as e:
            logger.error("Couldn't send data over socket: %s" % e)

        self._buffer = []


class TelnetConnection(object):
    """
    Class that represents one Telnet connection.
    """
    def __init__(self, conn, addr, interact, server, encoding):
        assert isinstance(addr, tuple)  # (addr, port) tuple
        assert callable(interact)
        assert isinstance(server, TelnetServer)
        assert isinstance(encoding, text_type)  # e.g. 'utf-8'

        self.conn = conn
        self.addr = addr
        self.interact = interact
        self.server = server
        self.encoding = encoding
        self.callback = None  # Function that handles the CLI result.

        # Create "Output" object.
        self.size = Size(rows=40, columns=79)

        # Initialize.
        _initialize_telnet(conn)

        # Create input.
        self.vt100_input = PipeInput()

        # Create output.
        def get_size():
            return self.size
        self.stdout = _ConnectionStdout(conn, encoding=encoding)
        self.vt100_output = Vt100_Output(
            self.stdout, get_size, write_binary=False)

        def data_received(data):
            """ TelnetProtocolParser 'data_received' callback """
            assert isinstance(data, binary_type)
            self.vt100_input.send_bytes(data)

        def size_received(rows, columns):
            """ TelnetProtocolParser 'size_received' callback """
            self.size = Size(rows=rows, columns=columns)
            get_app()._on_resize()

        self.parser = TelnetProtocolParser(data_received, size_received)

    def run_application(self):
        """
        Run application.
        """
        def run():
            with context():
                try:
                    yield From(self.interact(self))
                except Exception as e:
                    print('Got exception', e)
                    raise
                finally:
                    get_event_loop().remove_reader(self.conn)
                    self.conn.close()

        return ensure_future(run())

    def feed(self, data):
        """
        Handler for incoming data. (Called by TelnetServer.)
        """
        assert isinstance(data, binary_type)
        self.parser.feed(data)

    def send(self, data):
        """
        Send text to the client.
        """
        assert isinstance(data, text_type)

        # When data is send back to the client, we should replace the line
        # endings. (We didn't allocate a real pseudo terminal, and the telnet
        # connection is raw, so we are responsible for inserting \r.)
        self.stdout.write(data.replace('\n', '\r\n'))
        self.stdout.flush()

    def erase_screen(self):
        self.vt100_output.erase_screen()
        self.vt100_output.cursor_goto(0, 0)
        self.vt100_output.flush()

    def prompt_async(self, *a, **kw):
        p = Prompt(input=self.vt100_input, output=self.vt100_output)
        return p.prompt_async(*a, **kw)


class TelnetServer(object):
    """
    Telnet server implementation.
    """
    def __init__(self, host='127.0.0.1', port=23, interact=None, encoding='utf-8'):
        assert isinstance(host, text_type)
        assert isinstance(port, int)
        assert callable(interact)
        assert isinstance(encoding, text_type)

        self.host = host
        self.port = port
        self.interact = interact
        self.encoding = encoding

        self.connections = set()

    @classmethod
    def create_socket(cls, host, port):
        # Create and bind socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))

        s.listen(4)
        return s

    def run(self):
        """
        Run the eventloop for the telnet server.
        """
        listen_socket = self.create_socket(self.host, self.port)
        logger.info('Listening for telnet connections on %s port %r', self.host, self.port)

        get_event_loop().add_reader(listen_socket, lambda: self._accept(listen_socket))

        f = Future()
        get_event_loop().run_until_complete(f)

        #listen_socket.close()  # TODO

    def _accept(self, listen_socket):
        """
        Accept new incoming connection.
        """
        loop = get_event_loop()

        conn, addr = listen_socket.accept()
        logger.info('New connection %r %r', *addr)

        connection = TelnetConnection(conn, addr, self.interact, self, encoding=self.encoding)
        self.connections.add(connection)

        def handle_incoming_data():
            " Handle incoming data on socket. "
            connection = [c for c in self.connections if c.conn == conn][0]
            data = conn.recv(1024)
            if data:
                connection.feed(data)
            else:
                # Connection closed by client.
                self.connections.remove(connection)
                loop.remove_reader(conn)

        loop.add_reader(conn, handle_incoming_data)

        # Run application for this connection.
        def run():
            try:
                yield From(connection.run_application())
            except Exception as e:
                print(e)
            finally:
                loop.remove_reader(conn)

        ensure_future(run())
