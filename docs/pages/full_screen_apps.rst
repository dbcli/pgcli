.. _full_screen_applications:

Building full screen applications
=================================

`prompt_toolkit` can be used to create complex full screen terminal
applications. Typically, an application consists of a layout (to describe the
graphical part) and a set of key bindings.

The sections below describe the components required for full screen
applications (or custom, non full screen apps), and how to assemble them
together.


Creating a layout
-----------------

There are two types of classes that have to be combined to contruct a layout.
We have containers (:class:`~prompt_toolkit.layout.containers.Layout`
instances) and user controls
(:class:`~prompt_toolkit.layout.controls.UIControl` instances).

Simply said, containers are used for arranging the layout, while user controls
paint the actual content. An important interal difference is that containers
use absolute coordinates, while user controls create their own
:class:`~prompt_toolkit.layout.screen.Screen` with a relative coordinates.

+-----------------------------------------------------+-----------------------------------------------------------+
| Abstract base class                                 | Examples                                                  |
+=====================================================+===========================================================+
| :class:`~prompt_toolkit.layout.containers.Layout`   | :class:`~prompt_toolkit.layout.containers.HSplit`         |
| (Container)                                         | :class:`~prompt_toolkit.layout.containers.VSplit`         |
|                                                     | :class:`~prompt_toolkit.layout.containers.FloatContainer` |
|                                                     | :class:`~prompt_toolkit.layout.containers.Window`         |
+-----------------------------------------------------+-----------------------------------------------------------+
| :class:`~prompt_toolkit.layout.controls.UIControl`  | :class:`~prompt_toolkit.layout.controls.BufferControl`    |
|                                                     | :class:`~prompt_toolkit.layout.controls.TokenListControl` |
|                                                     | :class:`~prompt_toolkit.layout.controls.FillControl`      |
+-----------------------------------------------------+-----------------------------------------------------------+


The :class:`~prompt_toolkit.layout.containers.Window` class itself is a
container that can contain a
:class:`~prompt_toolkit.layout.controls.UIControl`, so that's the adaptor
between the two. The Window class also takes care of scrolling the content if
the user control created a :class:`~prompt_toolkit.layout.screen.Screen` that
is larger than what was available to the window.

This is an example of a layout that displays the content of the default buffer
on the left, and displays "Hello world" on the right. In between it shows a
vertical line:

.. code:: python

    from prompt_toolkit.layout.containers import VSplit, HSplit, Window
    from prompt_toolkit.layout.dimension import LayoutDimension as D
    from prompt_toolkit.layout.controls import BufferControl, FillControl, TokenListControl

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

        # Display the text 'Hello world' on the right.
        Window(content=TokenListControl(
            get_tokens=lambda cli: [(Token, 'Hello world')])),
    ])

The BufferControl
^^^^^^^^^^^^^^^^^

Input processors
^^^^^^^^^^^^^^^^

The TokenListControl
^^^^^^^^^^^^^^^^^^^^^

Custom user controls
^^^^^^^^^^^^^^^^^^^^

The Window class
^^^^^^^^^^^^^^^^

The :class:`~prompt_toolkit.layout.containers.Window` class exposes many
interesting functionality that influences the behaviour of user controls.


Key bindings
------------


Buffers
-------


The focus stack
---------------


The ``Application`` instance
----------------------------

The :class:`~prompt_toolkit.application.Application` instance is where all the
components for a prompt_toolkit applicaition come together.

.. note:: Actually, not "all" the components, but everything that is not
    dependent on I/O, so all components except for the eventloop and the
    input/output objects.

    This way, it's possible to create an
    :class:`~prompt_toolkit.application.Application` instance and later decide
    to run it on an asyncio eventloop or in a telnet server.

.. code:: python

    from prompt_toolkit.application import Application

    application = Application(
        layout=layout,
        key_bindings_registry=registry,

        # Let's add mouse support as well.
        mouse_support=True,

        # For fullscreen:
        use_alternate_screen=True)

We are talking about full screen applications, so it's important to pass
``use_alternate_screen=True``. This switches the terminal buffer.


Running the application
-----------------------

We need three I/O objects to run an application. These are passed as arguments
to :class:`~prompt_toolkit.interface.CommandLineInterface`.

- An :class:`~prompt_toolkit.eventloop.base.EventLoop` instance. This is
  basically a while-true loop that waits for user input, and when it receives
  something (like a key press), it will send that to the application.
- An :class:`~prompt_toolkit.input.Input` instance. This is an abstraction on
  the input stream (stdin).
- An :class:`~prompt_toolkit.output.Output` instance. This is an abstraction on
  the output stream, and is called by the renderer.

However, all three of the I/O objects are optional, and prompt_toolkit uses the
obvious default.

So, the only thing we actually need in order to run an application is this:

.. code:: python

    from prompt_toolkit.interface import CommandLineInterface

    cli = CommandLineInterface(application=application)
    cli.run()


Filters
-------




Input hooks
-----------
