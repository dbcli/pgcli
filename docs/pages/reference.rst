Reference
=========

Application
-----------

.. automodule:: prompt_toolkit.application
    :members: Application, get_app, set_app, NoRunningApplicationError,
        DummyApplication, run_in_terminal, run_coroutine_in_terminal


Formatted text
--------------

.. automodule:: prompt_toolkit.formatted_text
    :members:


Buffer
------

.. automodule:: prompt_toolkit.buffer
    :members:


Selection
---------

.. automodule:: prompt_toolkit.selection
    :members:


Clipboard
---------

.. automodule:: prompt_toolkit.clipboard
    :members: Clipboard, ClipboardData, DummyClipboard, DynamicClipboard, InMemoryClipboard

.. automodule:: prompt_toolkit.clipboard.pyperclip
    :members:


Auto completion
---------------

.. automodule:: prompt_toolkit.completion
    :members:


Document
--------

.. automodule:: prompt_toolkit.document
    :members:


Enums
-----

.. automodule:: prompt_toolkit.enums
    :members:


History
-------

.. automodule:: prompt_toolkit.history
    :members:


Keys
----

.. automodule:: prompt_toolkit.keys
    :members:


Style
-----

.. automodule:: prompt_toolkit.styles
    :members: Attrs, ANSI_COLOR_NAMES, BaseStyle, DummyStyle, DynamicStyle,
        Style, Priority, merge_styles, style_from_pygments_cls,
        style_from_pygments_dict, pygments_token_to_classname, NAMED_COLORS


Shortcuts
---------

.. automodule:: prompt_toolkit.shortcuts
    :members: prompt, PromptSession, confirm, CompleteStyle,
        create_confirm_session, clear, clear_title, print_formatted_text,
        set_title, ProgressBar, input_dialog, message_dialog, progress_dialog,
        radiolist_dialog, yes_no_dialog, button_dialog

.. automodule:: prompt_toolkit.shortcuts.progress_bar.formatters
    :members:


Validation
----------

.. automodule:: prompt_toolkit.validation
    :members:


Auto suggestion
---------------

.. automodule:: prompt_toolkit.auto_suggest
    :members:


Renderer
--------

.. automodule:: prompt_toolkit.renderer
    :members:

Lexers
------

.. automodule:: prompt_toolkit.lexers
    :members:


Layout
------

The layout class itself
^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: prompt_toolkit.layout
    :members: Layout, InvalidLayoutError, walk


Containers
^^^^^^^^^^

.. automodule:: prompt_toolkit.layout
    :members: Container, HSplit, VSplit, FloatContainer, Float, Window,
        WindowAlign, ConditionalContainer, ScrollOffsets, ColorColumn,
        to_container, to_window, is_container, HorizontalAlign, VerticalAlign


Controls
^^^^^^^^

.. automodule:: prompt_toolkit.layout
    :members: BufferControl, SearchBufferControl, DummyControl,
        FormattedTextControl, UIControl, UIContent


Other
^^^^^

.. automodule:: prompt_toolkit.layout
    :members: Dimension, Margin, NumberedMargin, ScrollbarMargin,
        ConditionalMargin, PromptMargin, CompletionsMenu,
        MultiColumnCompletionsMenu

.. automodule:: prompt_toolkit.layout.processors
    :members:

.. automodule:: prompt_toolkit.layout.utils
    :members:

.. automodule:: prompt_toolkit.layout.screen
    :members:


Widgets
-------

.. automodule:: prompt_toolkit.widgets
    :members: TextArea, Label, Button, Frame, Shadow, Box, VerticalLine,
        HorizontalLine, RadioList, Checkbox, ProgressBar, CompletionsToolbar,
        FormattedTextToolbar, SearchToolbar, SystemToolbar, ValidationToolbar,
        MenuContainer, MenuItem


Filters
-------

.. automodule:: prompt_toolkit.filters
    :members:

.. autoclass:: prompt_toolkit.filters.Filter
    :members:

.. autoclass:: prompt_toolkit.filters.Condition
    :members:

.. automodule:: prompt_toolkit.filters.utils
    :members:

.. automodule:: prompt_toolkit.filters.app
    :members:


Key binding
-----------

.. automodule:: prompt_toolkit.key_binding
    :members: KeyBindingsBase, KeyBindings, ConditionalKeyBindings,
        merge_key_bindings, DynamicKeyBindings

.. automodule:: prompt_toolkit.key_binding.defaults
    :members:

.. automodule:: prompt_toolkit.key_binding.vi_state
    :members:


Eventloop
---------

.. automodule:: prompt_toolkit.eventloop
    :members: EventLoop, get_traceback_from_context, From, Return,
        ensure_future, create_event_loop, create_asyncio_event_loop,
        use_asyncio_event_loop, get_event_loop, set_event_loop,
        run_in_executor, call_from_executor, run_until_complete, Future,
        InvalidStateError

.. automodule:: prompt_toolkit.eventloop.posix
    :members:

.. automodule:: prompt_toolkit.eventloop.win32
    :members:

.. automodule:: prompt_toolkit.eventloop.asyncio_win32
    :members:

.. automodule:: prompt_toolkit.eventloop.asyncio_posix
    :members:


Input
-----

.. automodule:: prompt_toolkit.input
    :members: Input, DummyInput, create_input, get_default_input, set_default_input

.. automodule:: prompt_toolkit.input.vt100
    :members:

.. automodule:: prompt_toolkit.input.win32
    :members:

Output
------

.. automodule:: prompt_toolkit.output
    :members: Output, DummyOutput, ColorDepth, create_output,
        get_default_output, set_default_output

.. automodule:: prompt_toolkit.output.vt100
    :members:

.. automodule:: prompt_toolkit.output.win32
    :members:


Patch stdout
------------

.. automodule:: prompt_toolkit.patch_stdout
    :members: patch_stdout, StdoutProxy
