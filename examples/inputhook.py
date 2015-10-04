#!/usr/bin/env python
"""
An example that demonstrates how inputhooks can be used in prompt-toolkit.

An inputhook is a callback that an eventloop calls when it's idle. For
instance, readline calls `PyOS_InputHook`. This allows us to do other work in
the same thread, while waiting for input. Important however is that we give the
control back to prompt-toolkit when some input is ready to be processed.

There are two ways to know when input is ready. One way is to poll
`InputHookContext.input_is_ready()`. Another way is to check for
`InputHookContext.fileno()` to be ready. In this example we do the latter.
"""
from __future__ import unicode_literals

from prompt_toolkit.shortcuts import prompt, create_eventloop
from pygments.lexers import PythonLexer

import gtk, gobject


def hello_world_window():
    """
    Create a GTK window with one 'Hello world' button.
    """
    # Create a new window.
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_border_width(50)

    # Create a new button with the label "Hello World".
    button = gtk.Button("Hello World")
    window.add(button)

    # Clicking the button prints some text.
    def clicked(data):
        print('Button clicked!')

    button.connect("clicked", clicked)

    # Display the window.
    button.show()
    window.show()


def inputhook(context):
    """
    When the eventloop of prompt-toolkit is idle, call this inputhook.

    This will run the GTK main loop until the file descriptor
    `context.fileno()` becomes ready.

    :param context: An `InputHookContext` instance.
    """
    def _main_quit(*a, **kw):
        gtk.main_quit()
        return False

    gobject.io_add_watch(context.fileno(), gobject.IO_IN, _main_quit)
    gtk.main()


def main():
    # Create user interface.
    hello_world_window()

    # Enable threading in GTK. (Otherwise, GTK will keep the GIL.)
    gtk.gdk.threads_init()

    # Read input from the command line, using an event loop with this hook.
    # We say `patch_stdout=True`, because clicking the button will print
    # something; and that should print nicely 'above' the input line.
    result = prompt('Python >>> ',
                    eventloop=create_eventloop(inputhook=inputhook),
                    lexer=PythonLexer,
                    patch_stdout=True)
    print('You said: %s' % result)


if __name__ == '__main__':
    main()
