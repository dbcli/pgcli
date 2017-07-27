"""
Telnet server.
"""
from __future__ import unicode_literals

import inspect
import socket
import sys

from six import int2byte, text_type, binary_type

from prompt_toolkit.application.current import get_app, NoRunningApplicationError
from prompt_toolkit.eventloop import get_event_loop, ensure_future, Future, From
from prompt_toolkit.eventloop.context import context
from prompt_toolkit.input.vt100 import PipeInput
from prompt_toolkit.layout.formatted_text import to_formatted_text
from prompt_toolkit.layout.screen import Size
from prompt_toolkit.output.vt100 import Vt100_Output
from prompt_toolkit.renderer import print_formatted_text as renderer_print_formatted_text
from prompt_toolkit.shortcuts import Prompt
from prompt_toolkit.styles import default_style, BaseStyle

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
            logger.error("Couldn't send data over socket: %s" % e)

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
        assert isinstance(style, BaseStyle)

        self.conn = conn
        self.addr = addr
        self.interact = interact
        self.server = server
        self.encoding = encoding
        self.style = style
        self.callback = None  # Function that handles the CLI result.

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
        def run():
            with context() as ctx_id:
                self._context_id = ctx_id
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
                    self.conn.close()

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
        self.vt100_input.close()

    def send(self, data):
        """
        Send text to the client.
        """
        assert isinstance(data, text_type)

        def write():
            # When data is send back to the client, we should replace the line
            # endings. (We didn't allocate a real pseudo terminal, and the
            # telnet connection is raw, so we are responsible for inserting \r.)
            self.stdout.write(data.replace('\n', '\r\n'))
            self.stdout.flush()

        self._run_in_terminal(write)

    def send_formatted_text(self, formatted_text):
        """
        Send a piece of formatted text to the client.
        """
        formatted_text = to_formatted_text(formatted_text)

        def write():
            renderer_print_formatted_text(self.vt100_output, formatted_text, self.style)
        self._run_in_terminal(write)

    def _run_in_terminal(self, func):
        # Make sure that when an application was active for this connection,
        # that we print the text above the application.
        with context(self._context_id):
            try:
                app = get_app(raise_exception=True)
            except NoRunningApplicationError:
                func()
            else:
                app.run_in_terminal(func)

    def erase_screen(self):
        """
        Erase the screen and move the cursor to the top.
        """
        self.vt100_output.erase_screen()
        self.vt100_output.cursor_goto(0, 0)
        self.vt100_output.flush()

    def prompt_async(self, *a, **kw):
        """
        Like the `prompt_toolkit.shortcuts.prompt` function.
        Ask for input.
        """
        p = Prompt(input=self.vt100_input, output=self.vt100_output)
        return p.prompt_async(*a, **kw)


class TelnetServer(object):
    """
    Telnet server implementation.
    """
    def __init__(self, host='127.0.0.1', port=23, interact=None, encoding='utf-8', style=None):
        assert isinstance(host, text_type)
        assert isinstance(port, int)
        assert callable(interact)
        assert isinstance(encoding, text_type)

        if style is None:
            style = default_style()
        assert isinstance(style, BaseStyle)

        self.host = host
        self.port = port
        self.interact = interact
        self.encoding = encoding
        self.style = style

        self.connections = set()

    @classmethod
    def create_socket(cls, host, port):
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
        listen_socket = self.create_socket(self.host, self.port)
        logger.info('Listening for telnet connections on %s port %r', self.host, self.port)

        get_event_loop().add_reader(listen_socket, lambda: self._accept(listen_socket))

        #listen_socket.close()  # TODO

    def _accept(self, listen_socket):
        """
        Accept new incoming connection.
        """
        loop = get_event_loop()

        conn, addr = listen_socket.accept()
        logger.info('New connection %r %r', *addr)

        connection = TelnetConnection(
            conn, addr, self.interact, self,
            encoding=self.encoding, style=self.style)
        self.connections.add(connection)

        def handle_incoming_data():
            " Handle incoming data on socket. "
            connection = [c for c in self.connections if c.conn == conn][0]
            data = conn.recv(1024)
            if data:
                connection.feed(data)
            else:
                # Connection closed by client.
                connection.close()

        loop.add_reader(conn, handle_incoming_data)

        # Run application for this connection.
        def run():
            try:
                yield From(connection.run_application())
            except Exception as e:
                print(e)
            finally:
                self.connections.remove(connection)
                loop.remove_reader(conn)

        ensure_future(run())
