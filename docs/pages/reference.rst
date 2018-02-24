Reference
=========

Application
-----------

.. automodule:: prompt_toolkit.application
    :members: Application

.. automodule:: prompt_toolkit.application
    :members: get_app, set_app, NoRunningApplicationError

.. automodule:: prompt_toolkit.application
    :members: DummyApplication

.. automodule:: prompt_toolkit.application
    :members: run_in_terminal, run_coroutine_in_terminal


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
    :members: Clipboard, ClipboardData, DummyClipboard, DynamicClipboard

.. automodule:: prompt_toolkit.clipboard
    :members: InMemoryClipboard

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
    :members: BaseStyle, DummyStyle, DynamicStyle

.. automodule:: prompt_toolkit.styles
    :members: Style, merge_styles

.. automodule:: prompt_toolkit.styles
    :members: style_from_pygments_cls, style_from_pygments_dict, pygments_token_to_classname

.. automodule:: prompt_toolkit.styles.named_colors
    :members: NAMED_COLORS


Reactive
--------

.. automodule:: prompt_toolkit.reactive
    :members:


Shortcuts
---------

.. automodule:: prompt_toolkit.shortcuts
    :members: prompt, Prompt

.. automodule:: prompt_toolkit.shortcuts.dialogs
    :members:

.. automodule:: prompt_toolkit.shortcuts.utils
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
    :members: Container, HSplit, VSplit, FloatContainer, Float, Window, ConditionalContainer, ScrollOffsets, ColorColumn, to_container, to_window, is_container


Controls
^^^^^^^^

.. automodule:: prompt_toolkit.layout
    :members: BufferControl, SearchBufferControl, DummyControl, FormattedTextControl, UIControl, UIContent


Other
^^^^^

.. automodule:: prompt_toolkit.layout
    :members: Dimension

.. automodule:: prompt_toolkit.layout
    :members: Margin, NumberredMargin, ScrollbarMargin, ConditionalMargin, PromptMargin

.. automodule:: prompt_toolkit.layout
    :members: CompletionsMenu, MultiColumnCompletionsMenu

.. automodule:: prompt_toolkit.layout.processors
    :members:

.. automodule:: prompt_toolkit.layout.utils
    :members:

.. automodule:: prompt_toolkit.layout.screen
    :members:


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

.. automodule:: prompt_toolkit.eventloop.base
    :members:

.. automodule:: prompt_toolkit.eventloop.posix
    :members:

.. automodule:: prompt_toolkit.eventloop.win32
    :members:

.. automodule:: prompt_toolkit.eventloop.asyncio_base
    :members:

.. automodule:: prompt_toolkit.eventloop.asyncio_win32
    :members:

.. automodule:: prompt_toolkit.eventloop.asyncio_posix
    :members:

.. automodule:: prompt_toolkit.eventloop.callbacks
    :members:


Input
-----

.. automodule:: prompt_toolkit.input
    :members:

.. automodule:: prompt_toolkit.input.defaults
    :members:

.. automodule:: prompt_toolkit.input.vt100
    :members:

.. automodule:: prompt_toolkit.input.win32
    :members:

Output
------

.. automodule:: prompt_toolkit.output
    :members:

.. automodule:: prompt_toolkit.output.defaults
    :members:

.. automodule:: prompt_toolkit.output.base
    :members:

.. automodule:: prompt_toolkit.output.vt100
    :members:

.. automodule:: prompt_toolkit.output.win32
    :members:

.. automodule:: prompt_toolkit.output.color_depth
    :members:
