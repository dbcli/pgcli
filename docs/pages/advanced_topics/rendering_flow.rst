.. _rendering_flow:

The rendering flow
------------------

Understanding the rendering flow is important for understanding how
:class:`~prompt_toolkit.layout.Container` and
:class:`~prompt_toolkit.layout.UIControl` objects interact. We will demonstrate
it by explaining the flow around a
:class:`~prompt_toolkit.layout.BufferControl`.

.. note::

    A :class:`~prompt_toolkit.layout.BufferControl` is a
    :class:`~prompt_toolkit.layout.UIControl` for displaying the content of a
    :class:`~prompt_toolkit.buffer.Buffer`. A buffer is the object that holds
    any editable region of text. Like all controls, it has to be wrapped into a
    :class:`~prompt_toolkit.layout.Window`.

Let's take the following code:

.. code:: python

    from prompt_toolkit.enums import DEFAULT_BUFFER
    from prompt_toolkit.layout.containers import Window
    from prompt_toolkit.layout.controls import BufferControl
    from prompt_toolkit.buffer import Buffer

    b = Buffer(name=DEFAULT_BUFFER)
    Window(content=BufferControl(buffer=b))

What happens when a :class:`~prompt_toolkit.renderer.Renderer` objects wants a
:class:`~prompt_toolkit.layout.Container` to be rendered on a certain
:class:`~prompt_toolkit.layout.screen.Screen`?

The visualisation happens in several steps:

1. The :class:`~prompt_toolkit.renderer.Renderer` calls the
   :meth:`~prompt_toolkit.layout.Container.write_to_screen` method
   of a :class:`~prompt_toolkit.layout.Container`.
   This is a request to paint the layout in a rectangle of a certain size.

   The :class:`~prompt_toolkit.layout.Window` object then requests
   the :class:`~prompt_toolkit.layout.UIControl` to create a
   :class:`~prompt_toolkit.layout.UIContent` instance (by calling
   :meth:`~prompt_toolkit.layout.UIControl.create_content`).
   The user control receives the dimensions of the window, but can still
   decide to create more or less content.

   Inside the :meth:`~prompt_toolkit.layout.UIControl.create_content`
   method of :class:`~prompt_toolkit.layout.UIControl`, there are several
   steps:

   2. First, the buffer's text is passed to the
      :meth:`~prompt_toolkit.lexers.Lexer.lex_document` method of a
      :class:`~prompt_toolkit.lexers.Lexer`. This returns a function which
      for a given line number, returns a token list for that line (that's a
      list of ``(Token, text)`` tuples).

   3. The token list is passed through a list of
      :class:`~prompt_toolkit.layout.processors.Processor` objects.
      Each processor can do a transformation for each line.
      (For instance, they can insert or replace some text.)

   4. The :class:`~prompt_toolkit.layout.UIControl` returns a
      :class:`~prompt_toolkit.layout.UIContent` instance which
      generates such a token lists for each lines.

The :class:`~prompt_toolkit.layout.Window` receives the
:class:`~prompt_toolkit.layout.UIContent` and then:

5. It calculates the horizontal and vertical scrolling, if applicable
   (if the content would take more space than what is available).

6. The content is copied to the correct absolute position
   :class:`~prompt_toolkit.layout.screen.Screen`, as requested by the
   :class:`~prompt_toolkit.renderer.Renderer`. While doing this, the
   :class:`~prompt_toolkit.layout.Window` can possible wrap the
   lines, if line wrapping was configured.

Note that this process is lazy: if a certain line is not displayed in the
:class:`~prompt_toolkit.layout.Window`, then it is not requested
from the :class:`~prompt_toolkit.layout.UIContent`. And from there, the line is
not passed through the processors or even asked from the
:class:`~prompt_toolkit.lexers.Lexer`.
