.. _full_screen_applications:

Building full screen applications
=================================

`prompt_toolkit` can be used to create complex full screen terminal
applications. Typically, an application consists of a layout (to describe the
graphical part) and a set of key bindings.

The sections below describe the components required for full screen
applications (or custom, non full screen applications), and how to assemble
them together.

.. warning:: This is going to change.

    The information below is still up to date, but we are planning to
    refactor some of the internal architecture of prompt_toolkit, to make it
    easier to build full screen applications. This will however be
    backwards-incompatible. The refactoring should probably be complete
    somewhere around half 2017.

A simple application
--------------------

Every prompt_toolkit application is an instance of an
:class:`~prompt_toolkit.application.application.Application` object. The
simplest example would look like this:

.. code:: python

    from prompt_toolkit import Application

    app = Application()
    app.run()

This will display a dummy application that says "No layout specified. Press
ENTER to quit.". We are discussing full screen applications in this section, so
we may as well set the ``full_screen`` flag so that the application runs in
full screen mode (in the alternate screen buffer).

.. code:: python

    from prompt_toolkit import Application

    app = Application(full_screen=True)
    app.run()

An application consists of several components. The most important are:

- I/O objects: the event loop, the input and output device.
- The layout: this defines the graphical structure of the application. For
  instance, a text box on the left side, and a button on the right side.
- A style: this defines what colors and underline/bold/italic styles are used
  everywhere.
- Key bindings.

We will discuss all of these in more detail them below.

Three I/O objects
-----------------

An :class:`~prompt_toolkit.application.application.Application` instance requires three I/O
objects:

    - An :class:`~prompt_toolkit.eventloop.base.EventLoop` instance. This is
      basically a while-true loop that waits for user input, and when it
      receives something (like a key press), it will send that to the the
      appropriate handler, like for instance, a key binding.
    - An :class:`~prompt_toolkit.input.base.Input` instance. This is an abstraction
      of the input stream (stdin).
    - An :class:`~prompt_toolkit.output.base.Output` instance. This is an
      abstraction of the output stream, and is called by the renderer.

All of these three objects are optional, and a default value will be used when
they are absent. Usually, the default works fine.

The layout
----------

A layered layout architecture
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are several ways to create a prompt_toolkit layout, depending on how
customizable you want things to be. In fact, there are several layers of
abstraction.

- The most low-level way of creating a layout is by combining
  :class:`~prompt_toolkit.layout.containers.Container` and
  :class:`~prompt_toolkit.layout.controls.UIControl` objects.

  Examples of :class:`~prompt_toolkit.layout.containers.Container` objects are
  :class:`~prompt_toolkit.layout.containers.VSplit` (vertical split),
  :class:`~prompt_toolkit.layout.containers.HSplit` (horizontal split) and
  :class:`~prompt_toolkit.layout.containers.FloatContainer`. These containers
  arrange the layout and can split it in multiple regions. Each container can
  recursively contain multiple other containers. They can be combined in any
  way to define the "shape" of the layout.

  The :class:`~prompt_toolkit.layout.containers.Window` object is a special
  kind of container that can contain
  :class:`~prompt_toolkit.layout.controls.UIControl` object. The
  :class:`~prompt_toolkit.layout.controls.UIControl` object is responsible for
  the actual content. The :class:`~prompt_toolkit.layout.containers.Window`
  object acts as an adaptor between the
  :class:`~prompt_toolkit.layout.controls.UIControl` and other containers, but
  it's also responsible for the scrolling and line wrapping of the content.

  Examples of :class:`~prompt_toolkit.layout.controls.UIControl` objects are
  :class:`~prompt_toolkit.layout.controls.BufferControl` for showing the
  content of an editable/scrollable buffer, and
  :class:`~prompt_toolkit.layout.controls.FormattedTextControl` for displaying static
  static (:ref:`formatted <formatted_text>`) text.

- A higher level abstraction of building a layout is by using "widgets". A
  widget is a reusable layout component that can contain multiple containers
  and controls. It should have a ``__pt__container__`` function, which is
  supposed to return the root container for this widget.

- The highest level abstractions are in the ``shortcuts`` module. There we
  don't have to think about the layout, controls and containers at all. This is
  the simplest way to use prompt_toolkit, but is only meant for certain use
  cases.

Containers and controls
^^^^^^^^^^^^^^^^^^^^^^^

The biggest difference between containers and controls is that containers
arrange the layout by splitting the screen in many regions, while controls are
responsible for generating the actual content.

.. note::

   Under the hood, the difference is:

   - containers use *absolute coordinates*, and paint on a
     :class:`~prompt_toolkit.layout.screen.Screen` instance.
   - user controls create a :class:`~prompt_toolkit.layout.controls.UIContent`
     instance. This is a collection of lines that represent the actual
     content. A :class:`~prompt_toolkit.layout.controls.UIControl` is not aware
     of the screen.

+------------------------------------------------------+-----------------------------------------------------------+
| Abstract base class                                  | Examples                                                  |
+======================================================+===========================================================+
| :class:`~prompt_toolkit.layout.containers.Container` | :class:`~prompt_toolkit.layout.containers.HSplit`         |
|                                                      | :class:`~prompt_toolkit.layout.containers.VSplit`         |
|                                                      | :class:`~prompt_toolkit.layout.containers.FloatContainer` |
|                                                      | :class:`~prompt_toolkit.layout.containers.Window`         |
+------------------------------------------------------+-----------------------------------------------------------+
| :class:`~prompt_toolkit.layout.controls.UIControl`   | :class:`~prompt_toolkit.layout.controls.BufferControl`    |
|                                                      | :class:`~prompt_toolkit.layout.controls.TokenListControl` |
|                                                      | :class:`~prompt_toolkit.layout.controls.FillControl`      |
+------------------------------------------------------+-----------------------------------------------------------+

The :class:`~prompt_toolkit.layout.containers.Window` class itself is
particular: it is a :class:`~prompt_toolkit.layout.containers.Container` that
can contain a :class:`~prompt_toolkit.layout.controls.UIControl`. Thus, it's
the adaptor between the two.

The :class:`~prompt_toolkit.layout.containers.Window` class also takes care of
scrolling the content if needed.

Here is an example of a layout that displays the content of the default buffer
on the left, and displays ``"Hello world"`` on the right. In between it shows a
vertical line:

.. code:: python

    from prompt_toolkit import Application
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.layout.containers import VSplit, Window
    from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl

    buffer1 = Buffer()

    root_container = VSplit([
        # One window that holds the BufferControl with the default buffer on the
        # left.
        Window(content=BufferControl(buffer=buffer1)),

        # A vertical line in the middle. We explicitely specify the width, to make
        # sure that the layout engine will not try to divide the whole width by
        # three for all these windows. The window will simply fill its content
        # by repeating this character.
        Window(width=1, char='|', style='class:line'),

        # Display the text 'Hello world' on the right.
        Window(content=FormattedTextControl('Hello world')),
    ])

    layout = Layout(root_container)

    app = Application(layout=layout, full_screen=True)
    app.run()


Key bindings
------------

In order to react to user actions, we need to create a
:class:`~prompt_toolkit.key_binding.key_bindings.KeyBindings` object and pass
that to our :class:`~prompt_toolkit.application.application.Application`.

There are two kinds of key bindings:

- Global key bindings, which are always active.
- Key bindings that belong to a certain
  :class:`~prompt_toolkit.layout.controls.UIControl` and are only active when
  this control is focussed.

Global key bindings
^^^^^^^^^^^^^^^^^^^

.. code:: python

    from prompt_toolkit import Application
    from prompt_toolkit.key_binding.key_bindings import KeyBindings

    kb = KeyBindings()
    app = Application(key_bindings=kb)
    app.run()

To register a new keyboard shortcut, we can use the
:meth:`~prompt_toolkit.key_binding.key_bindings.KeyBindings.add` method as a
decorator of the key handler:

.. code:: python

    from prompt_toolkit import Application
    from prompt_toolkit.key_binding.key_bindings import KeyBindings

    kb = KeyBindings()

    @kb.add('c-q')
    def exit_(event):
        """
        Pressing Ctrl-Q will exit the user interface.

        Setting a return value means: quit the event loop that drives the user
        interface and return this value from the `CommandLineInterface.run()` call.
        """
        event.app.set_return_value(None)

    app = Application(key_bindings=kb, full_screen=True)
    app.run()

The callback function is named ``exit_`` for clarity, but it could have been
named ``_`` (underscore) as well, because the we won't refer to this name.


Input processors
----------------

An :class:`~prompt_toolkit.layout.processors.Processor` is an object that
processes the tokens of a line in a
:class:`~prompt_toolkit.layout.controls.BufferControl` before it's passed to a
:class:`~prompt_toolkit.layout.controls.UIContent` instance.

Some build-in processors:

+----------------------------------------------------------------------------+-----------------------------------------------------------+
| Processor                                                                  | Usage:                                                    |
+============================================================================+===========================================================+
| :class:`~prompt_toolkit.layout.processors.HighlightSearchProcessor`        | Highlight the current search results.                     |
+----------------------------------------------------------------------------+-----------------------------------------------------------+
| :class:`~prompt_toolkit.layout.processors.HighlightSelectionProcessor`     | Highlight the selection.                                  |
+----------------------------------------------------------------------------+-----------------------------------------------------------+
| :class:`~prompt_toolkit.layout.processors.PasswordProcessor`               | Display input as asterisks. (``*`` characters).           |
+----------------------------------------------------------------------------+-----------------------------------------------------------+
| :class:`~prompt_toolkit.layout.processors.BracketsMismatchProcessor`       | Highlight open/close mismatches for brackets.             |
+----------------------------------------------------------------------------+-----------------------------------------------------------+
| :class:`~prompt_toolkit.layout.processors.BeforeInput`                     | Insert some text before.                                  |
+----------------------------------------------------------------------------+-----------------------------------------------------------+
| :class:`~prompt_toolkit.layout.processors.AfterInput`                      | Insert some text after.                                   |
+----------------------------------------------------------------------------+-----------------------------------------------------------+
| :class:`~prompt_toolkit.layout.processors.AppendAutoSuggestion`            | Append auto suggestion text.                              |
+----------------------------------------------------------------------------+-----------------------------------------------------------+
| :class:`~prompt_toolkit.layout.processors.ShowLeadingWhiteSpaceProcessor`  | Visualise leading whitespace.                             |
+----------------------------------------------------------------------------+-----------------------------------------------------------+
| :class:`~prompt_toolkit.layout.processors.ShowTrailingWhiteSpaceProcessor` | Visualise trailing whitespace.                            |
+----------------------------------------------------------------------------+-----------------------------------------------------------+
| :class:`~prompt_toolkit.layout.processors.TabsProcessor`                   | Visualise tabs as `n` spaces, or some symbols.            |
+----------------------------------------------------------------------------+-----------------------------------------------------------+



Custom user controls
--------------------

The Window class
----------------

The :class:`~prompt_toolkit.layout.containers.Window` class exposes many
interesting functionality that influences the behaviour of user controls.




Buffers
-------


The focus stack
---------------


Input hooks
-----------


Running on the ``asyncio`` event loop
-------------------------------------
