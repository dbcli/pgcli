Upgrading to prompt_toolkit 2.0
===============================

Prompt_toolkit 2.0 is not compatible with 1.0, however you want to upgrade your
applications. This page explains why we have these differences and how to
upgrade.


Why all these breaking changes?
-------------------------------

We had a problem, which is that prompt_toolkit 1.0 is not flexible enough for
certain use cases. It was mostly the development of full screen applications
that was not really natural. All the important components, like the rendering,
key bindings, input and output handling were present, but the API was in the
first place designed for simple command line prompts. This was mostly notably
in the following two places:

- First, there was the focus which was always pointing to a
  :class:`~prompt_toolkit.buffer.Buffer` (or text input widget), but in full
  screen applications there are other widgets, like menus and buttons  which
  can be focussed.
- And secondly, it was impossible to make reusable UI components. All the key
  bindings for the entire applications were stored together in one
  ``KeyBindings`` object, and similar, all
  :class:`~prompt_toolkit.buffer.Buffer` objects were stored together in one
  dictionary. This didn't work well. You want reusable components to define
  their own key bindings and everything. It's the idea of encapsulation.

For simple prompts, the changes wouldn't be that invasive, but given that there
would be some changes, I took the opportunity to fix a couple of other things.
For instance, in prompt_toolkit 1.0, we translated `\\r` into `\\n` during the
input processing. This was not a good idea, because some people wanted to
handle these keys individually. This makes sense if you keep in mind that they
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
  classnames to themself, as well as define an inline style. The final style is
  then computed by combining the inline styles, the classnames and the style
  sheet.

  There are still adaptors available for using Pygments lexers as well as for
  Pygments styles.

- The way that key bindings were defined was too complex.
  ``KeyBindingsManager`` was too complex and no longer exists. Every set of key
  bindings is now a
  :class:`~prompt_toolkit.key_binding.key_bindings.KeyBindings` object and
  multiple of these can be merged together at any time. The runtime performance
  remains the same, but it's now easier for users.

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


Upgrading
---------

More guidelines on how to upgrade will follow.
