"""
Telnet server.

Example usage::

    class MyTelnetApplication(TelnetApplication):
        def create_cli(self, eventloop, telnet_connection):
            # Create simple prompt.
            return create_cli(eventloop, message='$ ')

        def handle_command(self, telnet_connection, document):
            # When the client enters a command, just reply.
            telnet_connection.send('You said: %r\n\n' % document.text)

        ...

    a = MyTelnetApplication()
    TelnetServer(application=a, host='127.0.0.1', port=23).run()
"""
from __future__ import unicode_literals

import socket
import select

import threading
import os
import fcntl

from six import int2byte, string_types, binary_type
from codecs import getincrementaldecoder

from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.eventloop.base import EventLoop
from prompt_toolkit.layout.screen import Size
from prompt_toolkit.renderer import Renderer
from prompt_toolkit.terminal.vt100_input import InputStream
from prompt_toolkit.terminal.vt100_output import Vt100_Output

from .log import logger
from .protocol import IAC, DO, LINEMODE, SB, MODE, SE, WILL, ECHO, NAWS
from .protocol import TelnetProtocolParser
from .application import TelnetApplication

__all__ = (
    'TelnetServer',
)


def _initialize_telnet(connection):
    # Iac Do Linemode
    connection.send(IAC + DO + LINEMODE)

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
        assert isinstance(data, string_types)
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
    def __init__(self, conn, addr, application, server, encoding):
        assert isinstance(addr, tuple)  # (addr, port) tuple
        assert isinstance(application, TelnetApplication)
        assert isinstance(server, TelnetServer)
        assert isinstance(encoding, string_types)  # e.g. 'utf-8'

        self.conn = conn
        self.addr = addr
        self.application = application
        self.closed = False
        self.encoding = encoding

        # Create "Output" object.
        self.size = Size(rows=40, columns=79)

        # Initialize.
        _initialize_telnet(conn)

        # Create output.
        def get_size():
            return self.size
        self.stdout = _ConnectionStdout(conn, encoding=encoding)
        self.vt100_output = Vt100_Output(self.stdout, get_size)

        # Create an eventloop (adaptor) for the CommandLineInterface.
        eventloop = _TelnetEventLoopInterface(server)

        # Create CommandLineInterface instance.
        self.cli = application.create_cli(eventloop, self)

        # Replace the renderer by a renderer that outputs over the telnet
        # connection.
        self.cli.renderer = Renderer(output=self.vt100_output)

        # Input decoder for stdin. (Required when working with multibyte
        # characters, like chinese input.)
        stdin_decoder_cls = getincrementaldecoder(encoding)
        self._stdin_decoder = stdin_decoder_cls()

        # Create a parser, and parser callbacks.
        cb = self.cli.create_eventloop_callbacks()
        inputstream = InputStream(cb.feed_key)

        def data_received(data):
            """ TelnetProtocolParser 'data_received' callback """
            assert isinstance(data, binary_type)

            try:
                result = self._stdin_decoder.decode(data)
                inputstream.feed(result)
            except UnicodeDecodeError:
                self._stdin_decoder = stdin_decoder_cls()
                return ''

        def size_received(rows, columns):
            """ TelnetProtocolParser 'size_received' callback """
            self.size = Size(rows=rows, columns=columns)
            cb.terminal_size_changed()

        self.parser = TelnetProtocolParser(data_received, size_received)

        # Call client_connected
        application.client_connected(self)

        # Render again.
        self.cli._redraw()

    def feed(self, data):
        """
        Handler for incoming data. (Called by TelnetServer.)
        """
        assert isinstance(data, binary_type)

        self.parser.feed(data)

        # Render again.
        self.cli._redraw()

        # When a return value has been set (enter was pressed), handle command.
        if self.cli.is_returning:
            try:
                return_value = self.cli.return_value()
            except (EOFError, KeyboardInterrupt) as e:
                # Control-D or Control-C was pressed.
                logger.info('%s, closing connection.', type(e).__name__)
                self.close()
                return

            # Handle CLI command
            logger.info('Handle command %r', return_value)
            self.application.handle_command(self, return_value)

            # Reset state and draw again. (If the connection is still open --
            # the application could have called TelnetConnection.close()
            if not self.closed:
                self.cli.reset()
                self.cli.buffers[DEFAULT_BUFFER].reset()
                self.cli._redraw()

    def send(self, data):
        """
        Send text to the client.
        """
        assert isinstance(data, string_types)

        # When data is send back to the client, we should replace the line
        # endings. (We didn't allocate a real pseudo terminal, and the telnet
        # connection is raw, so we are responsible for inserting \r.)
        self.stdout.write(data.replace('\n', '\r\n'))
        self.stdout.flush()

    def close(self):
        """
        Close the connection.
        """
        self.application.client_leaving(self)

        self.conn.close()
        self.closed = True


class _TelnetEventLoopInterface(EventLoop):
    """
    Eventloop object to be assigned to `CommandLineInterface`.
    """
    def __init__(self, server):
        self._server = server

    def close(self):
        " Ignore. "

    def stop(self):
        " Ignore. "

    def run_in_executor(self, callback):
        self._server.run_in_executor(callback)

    def call_from_executor(self, callback):
        self._server.call_from_executor(callback)


class TelnetServer(object):
    """
    Telnet server implementation.
    """
    def __init__(self, host='127.0.0.1', port=23, application=None, encoding='utf-8'):
        assert isinstance(host, string_types)
        assert isinstance(port, int)
        assert isinstance(application, TelnetApplication)
        assert isinstance(encoding, string_types)

        self.host = host
        self.port = port
        self.application = application
        self.encoding = encoding

        self.connections = set()

        self._calls_from_executor = []

        # Create a pipe for inter thread communication.
        self._schedule_pipe = os.pipe()
        fcntl.fcntl(self._schedule_pipe[0], fcntl.F_SETFL, os.O_NONBLOCK)

    @classmethod
    def create_socket(cls, host, port):
        # Create and bind socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))

        s.listen(4)
        return s

    def run_in_executor(self, callback):
        threading.Thread(target=callback).start()

    def call_from_executor(self, callback):
        self._calls_from_executor.append(callback)

        if self._schedule_pipe:
            os.write(self._schedule_pipe[1], b'x')

    def _process_callbacks(self):
        """
        Process callbacks from `call_from_executor` in eventloop.
        """
        # Flush all the pipe content.
        os.read(self._schedule_pipe[0], 1024)

        # Process calls from executor.
        calls_from_executor, self._calls_from_executor = self._calls_from_executor, []
        for c in calls_from_executor:
            c()

    def run(self):
        """
        Run the eventloop for the telnet server.
        """
        listen_socket = self.create_socket(self.host, self.port)
        logger.info('Listening for telnet connections on %s port %r', self.host, self.port)

        try:
            while True:
                # Removed closed connections.
                self.connections = {c for c in self.connections if not c.closed}

                # Wait for next event.
                read_list = (
                    [listen_socket, self._schedule_pipe[0]] +
                    [c.conn for c in self.connections])

                read, _, _ = select.select(read_list, [], [])

                for s in read:
                    # When the socket itself is ready, accept a new connection.
                    if s == listen_socket:
                        self._accept(listen_socket)

                    # If we receive something on our "call_from_executor" pipe, process
                    # these callbacks in a thread safe way.
                    elif s == self._schedule_pipe[0]:
                        self._process_callbacks()

                    # Handle incoming data on socket.
                    else:
                        self._handle_incoming_data(s)
        finally:
            listen_socket.close()

    def _accept(self, listen_socket):
        """
        Accept new incoming connection.
        """
        conn, addr = listen_socket.accept()
        connection = TelnetConnection(conn, addr, self.application, self, encoding=self.encoding)
        self.connections.add(connection)

        logger.info('New connection %r %r', *addr)

    def _handle_incoming_data(self, conn):
        """
        Handle incoming data on socket.
        """
        connection = [c for c in self.connections if c.conn == conn][0]
        data = conn.recv(1024)
        if data:
            connection.feed(data)
        else:
            self.connections.remove(connection)
