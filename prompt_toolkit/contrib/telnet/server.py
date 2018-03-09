"""
Telnet server.
"""
from __future__ import unicode_literals

import inspect
import socket
import sys

from six import int2byte, text_type, binary_type

from prompt_toolkit.application.current import get_app
from prompt_toolkit.application.run_in_terminal import run_in_terminal
from prompt_toolkit.eventloop import get_event_loop, ensure_future, Future, From
from prompt_toolkit.eventloop.context import context
from prompt_toolkit.formatted_text import to_formatted_text
from prompt_toolkit.input.defaults import set_default_input
from prompt_toolkit.input.vt100 import PipeInput
from prompt_toolkit.layout.screen import Size
from prompt_toolkit.output.defaults import set_default_output
from prompt_toolkit.output.vt100 import Vt100_Output
from prompt_toolkit.renderer import print_formatted_text as print_formatted_text
from prompt_toolkit.styles import DummyStyle

from .log import logger
from .protocol import IAC, DO, LINEMODE, SB, MODE, SE, WILL, ECHO, NAWS, SUPPRESS_GO_AHEAD
from .protocol import TelnetProtocolParser

__all__ = [
    'TelnetServer',
]


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


def _is_coroutine(func):
    if sys.version_info > (3, 5, 0):
        return inspect.iscoroutine(func)
    return False


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
            logger.warning("Couldn't send data over socket: %s" % e)

        self._buffer = []


class TelnetConnection(object):
    """
    Class that represents one Telnet connection.
    """
    def __init__(self, conn, addr, interact, server, encoding, style):
        assert isinstance(addr, tuple)  # (addr, port) tuple
        assert callable(interact)
        assert isinstance(server, TelnetServer)
        assert isinstance(encoding, text_type)  # e.g. 'utf-8'

        self.conn = conn
        self.addr = addr
        self.interact = interact
        self.server = server
        self.encoding = encoding
        self.style = style
        self._closed = False

        # Execution context.
        self._context_id = None

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
        def handle_incoming_data():
            data = self.conn.recv(1024)
            if data:
                self.feed(data)
            else:
                # Connection closed by client.
                logger.info('Connection closed by client. %r %r' % self.addr)
                self.close()

        def run():
            with context() as ctx_id:
                self._context_id = ctx_id

                # Set input/output for all application running in this context.
                set_default_input(self.vt100_input)
                set_default_output(self.vt100_output)

                # Add reader.
                loop = get_event_loop()
                loop.add_reader(self.conn, handle_incoming_data)

                try:
                    obj = self.interact(self)
                    if _is_coroutine(obj):
                        # Got an asyncio coroutine.
                        import asyncio
                        f = asyncio.ensure_future(obj)
                        yield From(Future.from_asyncio_future(f))
                    else:
                        # Got a prompt_toolkit coroutine.
                        yield From(obj)
                except Exception as e:
                    print('Got %s' % type(e).__name__, e)
                    import traceback; traceback.print_exc()
                    raise
                finally:
                    self.close()

        return ensure_future(run())

    def feed(self, data):
        """
        Handler for incoming data. (Called by TelnetServer.)
        """
        assert isinstance(data, binary_type)
        self.parser.feed(data)

    def close(self):
        """
        Closed by client.
        """
        if not self._closed:
            self._closed = True

            self.vt100_input.close()
            get_event_loop().remove_reader(self.conn)
            self.conn.close()

    def send(self, formatted_text):
        """
        Send text to the client.
        """
        formatted_text = to_formatted_text(formatted_text)
        print_formatted_text(self.vt100_output, formatted_text, self.style or DummyStyle())

    def send_above_prompt(self, formatted_text):
        """
        Send text to the client.
        This is asynchronous, returns a `Future`.
        """
        formatted_text = to_formatted_text(formatted_text)
        return self._run_in_terminal(lambda: self.send(formatted_text))

    def _run_in_terminal(self, func):
        # Make sure that when an application was active for this connection,
        # that we print the text above the application.
        with context(self._context_id):
            return run_in_terminal(func)

    def erase_screen(self):
        """
        Erase the screen and move the cursor to the top.
        """
        self.vt100_output.erase_screen()
        self.vt100_output.cursor_goto(0, 0)
        self.vt100_output.flush()


class TelnetServer(object):
    """
    Telnet server implementation.
    """
    def __init__(self, host='127.0.0.1', port=23, interact=None,
                 encoding='utf-8', style=None):
        assert isinstance(host, text_type)
        assert isinstance(port, int)
        assert callable(interact)
        assert isinstance(encoding, text_type)

        self.host = host
        self.port = port
        self.interact = interact
        self.encoding = encoding
        self.style = style

        self.connections = set()
        self._listen_socket = None

    @classmethod
    def _create_socket(cls, host, port):
        # Create and bind socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))

        s.listen(4)
        return s

    def start(self):
        """
        Start the telnet server.
        Don't forget to call `loop.run_forever()` after doing this.
        """
        self._listen_socket = self._create_socket(self.host, self.port)
        logger.info('Listening for telnet connections on %s port %r', self.host, self.port)

        get_event_loop().add_reader(self._listen_socket, self._accept)

    def stop(self):
        if self._listen_socket:
            self._listen_socket.close()

    def _accept(self):
        """
        Accept new incoming connection.
        """
        conn, addr = self._listen_socket.accept()
        logger.info('New connection %r %r', *addr)

        connection = TelnetConnection(
            conn, addr, self.interact, self,
            encoding=self.encoding, style=self.style)
        self.connections.add(connection)

        # Run application for this connection.
        def run():
            logger.info('Starting interaction %r %r', *addr)
            try:
                yield From(connection.run_application())
            except Exception as e:
                print(e)
            finally:
                self.connections.remove(connection)
                logger.info('Stopping interaction %r %r', *addr)

        ensure_future(run())
