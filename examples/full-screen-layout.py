#!/usr/bin/env python
"""
Simple example of a full screen application with a vertical split.

This will show a window on the left for user input. When the user types, the
reversed input is shown on the right. Pressing Ctrl-Q will quit the application.
"""
from __future__ import unicode_literals

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import VSplit, HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FillControl, TokenListControl
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.shortcuts import create_eventloop

from pygments.token import Token


# 1. First we create the layout
#    --------------------------

# There are two types of classes that have to be combined to contruct a layout.
# We have containers and user controls. Simply said, containers are used for
# arranging the layout, we have for instance `HSplit` and `VSplit`. And on the
# other hand user controls paint the actual content. We have for instance
# `BufferControl` and `TokenListControl`. An important interal difference is that
# containers use absolute coordinates, while user controls paint on their own
# `Screen` with a relative coordinates.

# The Window class itself is a container that can contain a user control, so
# that's the adaptor between the two. The Window class also takes care of
# scrolling the content if the user control is painting on a screen that is
# larger than what was available to the window.

# So, for this example, we create a layout that shows the content of the
# default buffer on the left, shows a line in the middle and another buffer
# (called 'RESULT') on the right.

layout = VSplit([
    # One window that holds the BufferControl with the default buffer on the
    # left.
    Window(content=BufferControl(buffer_name=DEFAULT_BUFFER)),

    # A vertical line in the middle. We explicitely specify the width, to make
    # sure that the layout engine will not try to divide the whole width by
    # three for all these windows. The `FillControl` will simply fill the whole
    # window by repeating this character.
    Window(width=D.exact(1),
           content=FillControl('|', token=Token.Line)),

    # Display the Result buffer on the right.
    Window(content=BufferControl(buffer_name='RESULT')),
])

# As a demonstration. Let's add a title bar to the top, displaying "Hello world".

# somewhere, because usually the default key bindings include searching. (Press
# Ctrl-R.) It would be really annoying if the search key bindings are handled,
# but the user doesn't see any feedback. We will add the search toolbar to the
# bottom by using an HSplit.

def get_titlebar_tokens(cli):
    return [
        (Token.Title, ' Hello world '),
        (Token.Title, ' (Press [Ctrl-Q] to quit.)'),
    ]


layout = HSplit([
    # The titlebar.
    Window(height=D.exact(1),
           content=TokenListControl(get_titlebar_tokens, align_center=True)),

    # Horizontal separator.
    Window(height=D.exact(1),
           content=FillControl('-', token=Token.Line)),

    # The 'body', like defined above.
    layout,
])


# 2. Adding key bindings
#   --------------------

# As a demonstration, we will add just a ControlQ key binding to exit the
# application.  Key bindings are registered in a
# `prompt_toolkit.key_bindings.registry.Registry` instance. However instead of
# starting with an empty `Registry` instance, usually you'd use a
# `KeyBindingmanager`, because it prefills the registry with all of the key
# bindings that are required for basic text editing.

manager = KeyBindingManager()  # Start with the `KeyBindingManager`.

# Now add the Ctrl-Q binding. We have to pass `eager=True` here. The reason is
# that there is another key *sequence* that starts with Ctrl-Q as well. Yes, a
# key binding is linked to a sequence of keys, not necessarily one key. So,
# what happens if there is a key binding for the letter 'a' and a key binding
# for 'ab'. When 'a' has been pressed, nothing will happen yet. Because the
# next key could be a 'b', but it could as well be anything else. If it's a 'c'
# for instance, we'll handle the key binding for 'a' and then look for a key
# binding for 'c'. So, when there's a common prefix in a key binding sequence,
# prompt-toolkit will wait calling a handler, until we have enough information.

# Now, There is an Emacs key binding for the [Ctrl-Q Any] sequence by default.
# Pressing Ctrl-Q followed by any other key will do a quoted insert. So to be
# sure that we won't wait for that key binding to match, but instead execute
# Ctrl-Q immediately, we can pass eager=True. (Don't make a habbit of adding
# `eager=True` to all key bindings, but do it when it conflicts with another
# existing key binding, and you definitely want to override that behaviour.

@manager.registry.add_binding(Keys.ControlQ, eager=True)
def _(event):
    """
    Pressing Ctrl-Q will exit the user interface.

    Setting a return value means: quit the event loop that drives the user
    interface and return this value from the `CommandLineInterface.run()` call.
    """
    event.cli.set_return_value(None)

# 3. Create the buffers
#    ------------------

# Buffers are the objects that keep track of the user input. In our example, we
# have two buffer instances, both are multiline.

buffers={
    DEFAULT_BUFFER: Buffer(is_multiline=True),
    'RESULT': Buffer(is_multiline=True),
}

# Now we add an event handler that captures change events to the buffer on the
# left. If the text changes over there, we'll update the buffer on the right.

def default_buffer_changed():
    """
    When the buffer on the left (DEFAULT_BUFFER) changes, update the buffer on
    the right. We just reverse the text.
    """
    buffers['RESULT'].text = buffers[DEFAULT_BUFFER].text[::-1]


buffers[DEFAULT_BUFFER].on_text_changed += default_buffer_changed


# 3. Creating an `Application` instance
#    ----------------------------------

# This glues everything together.

application = Application(
    layout=layout,
    buffers=buffers,
    key_bindings_registry=manager.registry,

    # Let's add mouse support!
    mouse_support=True,

    # Using an alternate screen buffer means as much as: "run full screen".
    # It switches the terminal to an alternate screen.
    use_alternate_screen=True)


# 4. Run the application
#    -------------------

def run():
    # We need to create an eventloop for this application. An eventloop is
    # basically a while-true loop that waits for user input, and when it
    # receives something (like a key press), it will send that to the
    # application. Usually, you want to use this `create_eventloop` shortcut,
    # which -- according to the environment (Windows/posix) -- returns
    # something that will work there. If you want to run your application
    # inside an "asyncio" environment, you'd have to pass another eventloop.
    eventloop = create_eventloop()

    try:
        # Create a `CommandLineInterface` instance. This is a wrapper around
        # `Application`, but includes all I/O: eventloops, terminal input and output.
        cli = CommandLineInterface(application=application, eventloop=eventloop)

        # Run the interface. (This runs the event loop until Ctrl-Q is pressed.)
        cli.run()

    finally:
        # Clean up. An eventloop creates a posix pipe. This is used internally
        # for scheduling callables, created in other threads into the main
        # eventloop. Calling `close` will close this pipe.
        eventloop.close()

if __name__ == '__main__':
    run()


# Some possible improvements.

# a) Probably you want to add syntax highlighting to one of these buffers. This
#    is possible by passing a lexer to the BufferControl. E.g.:

#    from pygments.lexers import HtmlLexer
#    from prompt_toolkit.layout.lexers import PygmentsLexer
#    BufferControl(lexer=PygmentsLexer(HtmlLexer))


# b) Add search functionality.

# c) Add additional key bindings to move the focus between the buffers.

# d) Add autocompletion.
