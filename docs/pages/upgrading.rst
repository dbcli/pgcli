.. _upgrading_2_0:

Upgrading to prompt_toolkit 2.0
===============================

Prompt_toolkit 2.0 is not compatible with 1.0, however you probably want to
upgrade your applications. This page explains why we have these differences and
how to upgrade.

If you experience some difficulties or you feel that some information is
missing from this page, don't hesitate to open a GitHub issue for help.


Why all these breaking changes?
-------------------------------

After more and more custom prompt_toolkit applications were developed, it
became clear that prompt_toolkit 1.0 was not flexible enough for certain use
cases. Mostly, the development of full screen applications was not really
natural. All the important components, like the rendering, key bindings, input
and output handling were present, but the API was in the first place designed
for simple command line prompts. This was mostly notably in the following two
places:

- First, there was the focus which was always pointing to a
  :class:`~prompt_toolkit.buffer.Buffer` (or text input widget), but in full
  screen applications there are other widgets, like menus and buttons which
  can be focused.
- And secondly, it was impossible to make reusable UI components. All the key
  bindings for the entire applications were stored together in one
  ``KeyBindings`` object, and similar, all
  :class:`~prompt_toolkit.buffer.Buffer` objects were stored together in one
  dictionary. This didn't work well. You want reusable components to define
  their own key bindings and everything. It's the idea of encapsulation.

For simple prompts, the changes wouldn't be that invasive, but given that there
would be some, I took the opportunity to fix a couple of other things. For
instance:

- In prompt_toolkit 1.0, we translated `\\r` into `\\n` during the input
  processing. This was not a good idea, because some people wanted to handle
  these keys individually. This makes sense if you keep in mind that they
  correspond to `Control-M` and `Control-J`. However, we couldn't fix this
  without breaking everyone's enter key, which happens to be the most important
  key in prompts.

Given that we were going to break compatibility anyway, we changed a couple of
other important things that both effect both simple prompt applications and
full screen applications. These are the most important:

- We no longer depend on Pygments for styling. While we like Pygments, it was
  not flexible enough to provide all the styling options that we need, and the
  Pygments tokens were not ideal for styling anything besides tokenized text.

  Instead we created something similar to CSS. All UI components can attach
  classnames to themselves, as well as define an inline style. The final style is
  then computed by combining the inline styles, the classnames and the style
  sheet.

  There are still adaptors available for using Pygments lexers as well as for
  Pygments styles.

- The way that key bindings were defined was too complex.
  ``KeyBindingsManager`` was too complex and no longer exists. Every set of key
  bindings is now a
  :class:`~prompt_toolkit.key_binding.KeyBindings` object and multiple of these
  can be merged together at any time. The runtime performance remains the same,
  but it's now easier for users.

- The separation between the ``CommandLineInterface`` and
  :class:`~prompt_toolkit.application.Application` class was confusing and in
  the end, didn't really had an advantage. These two are now merged together in
  one :class:`~prompt_toolkit.application.Application` class.

- We no longer pass around the active ``CommandLineInterface``. This was one of
  the most annoying things. Key bindings need it in order to change anything
  and filters need it in order to evaluate their state. It was pretty annoying,
  especially because there was usually only one application active at a time.
  So, :class:`~prompt_toolkit.application.Application` became a ``TaskLocal``.
  That is like a global variable, but scoped in the current coroutine or
  context. The way this works is still not 100% correct, but good enough for
  the projects that need it (like Pymux), and hopefully Python will get support
  for this in the future thanks to PEP521, PEP550 or PEP555.

All of these changes have been tested for many months, and I can say with
confidence that prompt_toolkit 2.0 is a better prompt_toolkit.


Some new features
-----------------

Apart from the breaking changes above, there are also some exciting new
features.

- We now support vt100 escape codes for Windows consoles on Windows 10. This
  means much faster rendering, and full color support.

- We have a concept of formatted text. This is an object that evaluates to
  styled text. Every input that expects some text, like the message in a
  prompt, or the text in a toolbar, can take any kind of formatted text as input.
  This means you can pass in a plain string, but also a list of `(style,
  text)` tuples (similar to a Pygments tokenized string), or an
  :class:`~prompt_toolkit.formatted_text.HTML` object. This simplifies many
  APIs.

- New utilities were added. We now have function for printing formatted text
  and an experimental module for displaying progress bars.

- Autocompletion, input validation, and auto suggestion can now either be
  asynchronous or synchronous. By default they are synchronous, but by wrapping
  them in :class:`~prompt_toolkit.completion.ThreadedCompleter`,
  :class:`~prompt_toolkit.validation.ThreadedValidator` or
  :class:`~prompt_toolkit.auto_suggest.ThreadedAutoSuggest`, they will become
  asynchronous by running in a background thread.

  Furter, if the autocompletion code runs in a background thread, we will show
  the completions as soon as they arrive. This means that the autocompletion
  algorithm could for instance first yield the most trivial completions and then
  take time to produce the completions that take more time.


Upgrading
---------

More guidelines on how to upgrade will follow.


`AbortAction` has been removed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Prompt_toolkit 1.0 had an argument ``abort_action`` for both the
``Application`` class as well as for the ``prompt`` function. This has been
removed. The recommended way to handle this now is by capturing
``KeyboardInterrupt`` and ``EOFError`` manually.


Calling `create_eventloop` usually not required anymore
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Prompt_toolkit 2.0 will automatically create the appropriate event loop when
it's needed for the first time. There is no need to create one and pass it
around. If you want to run an application on top of asyncio (without using an
executor), it still needs to be activated by calling
:func:`~prompt_toolkit.eventloop.use_asyncio_event_loop` at the beginning.


Pygments styles and tokens
^^^^^^^^^^^^^^^^^^^^^^^^^^

prompt_toolkit 2.0 no longer depends on `Pygments <http://pygments.org/>`_, but
that definitely doesn't mean that you can't use any Pygments functionality
anymore. The only difference is that Pygments stuff needs to be wrapped in an
adaptor to make it compatible with the native prompt_toolkit objects.

- For instance, if you have a list of ``(pygments.Token, text)`` tuples for
  formatting, then this needs to be wrapped in a
  :class:`~prompt_toolkit.formatted_text.PygmentsTokens` object. This is an
  adaptor that turns it into prompt_toolkit "formatted text". Feel free to keep
  using this.

- Pygments lexers need to be wrapped in a
  :class:`~prompt_toolkit.lexers.PygmentsLexer`. This will convert the list of
  Pygments tokens into prompt_toolkit formatted text.

- If you have a Pygments style, then this needs to be converted as well. A
  Pygments style class can be converted in a prompt_toolkit
  :class:`~prompt_toolkit.styles.Style` with the
  :func:`~prompt_toolkit.styles.pygments.style_from_pygments_cls` function
  (which used to be called ``style_from_pygments``). A Pygments style
  dictionary can be converted using
  :func:`~prompt_toolkit.styles.pygments.style_from_pygments_dict`.

  Multiple styles can be merged together using
  :func:`~prompt_toolkit.styles.merge_styles`.

Asynchronous autocompletion
^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, prompt_toolkit 2.0 completion is now synchronous. If you still want
asynchronous auto completion (which is often good thing), then you have to wrap
the completer in a :class:`~prompt_toolkit.completion.ThreadedCompleter`.


Filters
^^^^^^^

We don't distiguish anymore between `CLIFilter` and `SimpleFilter`, because the
application object is no longer passed around. This means that all filters are
a `Filter` from now on.

All filters have been turned into functions. For instance, `IsDone` became
`is_done` and `HasCompletions` became `has_completions`.

This was done because almost all classes were called without any arguments in
the `__init__` causing additional braces everywhere. This means that
`HasCompletions()` has to be replaced by `has_completions` (without
parenthesis).

The few filters that took arguments as input, became functions, but still have
to be called with the given arguments.

For new filters, it is recommended to use the `@Condition` decorator,
rather then inheriting from `Filter`. For instance:

.. code:: python

    from prompt_toolkit.filter import Condition

    @Condition
    def my_filter();
        return True  # Or False

