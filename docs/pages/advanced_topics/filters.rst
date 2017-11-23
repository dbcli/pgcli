.. _filters:


Filters
-------

Many places in `prompt_toolkit` expect a boolean. For instance, for determining
the visibility of some part of the layout (it can be either hidden or visible),
or a key binding filter (the binding can be active on not) or the
``wrap_lines`` option of
:class:`~prompt_toolkit.layout.controls.BufferControl`, etc.

These booleans however are often dynamic and can change at runtime. For
instance, the search toolbar should only be visible when the user is actually
searching (when the search buffer has the focus). The ``wrap_lines`` option
could be changed with a certain key binding. And that key binding could only
work when the default buffer got the focus.

In `prompt_toolkit`, we decided to reduce the amount of state in the whole
framework, and apply a simple kind of reactive programming to describe the flow
of these booleans as expressions. (It's one-way only: if a key binding needs to
know whether it's active or not, it can follow this flow by evaluating an
expression.)

The base class is :class:`~prompt_toolkit.filters.Filter`, which wraps an
expression that takes no input and evaluates to a boolean.

An example
^^^^^^^^^^

One way to create a :class:`~prompt_toolkit.filters.Filter` instance is by
creating a :class:`~prompt_toolkit.filters.Condition` instance from a function.
For instance, the following condition will evaluate to ``True`` when the user
is searching:

.. code:: python

    from prompt_toolkit.application.current import get_app
    from prompt_toolkit.filters import Condition

    is_searching = Condition(lambda: get_app().is_searching)

A different way of writing this, is by using the decorator syntax:

.. code:: python

    from prompt_toolkit.application.current import get_app
    from prompt_toolkit.filters import Condition

    @Condition
    def is_searching():
        return get_app().is_searching)

This filter can then be used in a key binding, like in the following snippet:

.. code:: python

    from prompt_toolkit.key_binding.key_bindings import KeyBindings

    kb = KeyBindings()

    @kb.add('c-t', filter=is_searching)
    def _(event):
        # Do, something, but only when searching.
        pass

Built-in filters
^^^^^^^^^^^^^^^^^

There are many built-in filters, ready to use. All of them have a lowercase
name, because they represent the wrapped function underneath, and can be called
as a function.

- :class:`~prompt_toolkit.filters.app.has_arg`
- :class:`~prompt_toolkit.filters.app.has_completions`
- :class:`~prompt_toolkit.filters.app.has_focus`
- :class:`~prompt_toolkit.filters.app.buffer_has_focus`
- :class:`~prompt_toolkit.filters.app.has_selection`
- :class:`~prompt_toolkit.filters.app.has_validation_error`
- :class:`~prompt_toolkit.filters.app.is_aborting`
- :class:`~prompt_toolkit.filters.app.is_done`
- :class:`~prompt_toolkit.filters.app.is_read_only`
- :class:`~prompt_toolkit.filters.app.is_multiline`
- :class:`~prompt_toolkit.filters.app.renderer_height_is_known`
- :class:`~prompt_toolkit.filters.app.in_editing_mode`
- :class:`~prompt_toolkit.filters.app.in_paste_mode`

- :class:`~prompt_toolkit.filters.app.vi_mode`
- :class:`~prompt_toolkit.filters.app.vi_navigation_mode`
- :class:`~prompt_toolkit.filters.app.vi_insert_mode`
- :class:`~prompt_toolkit.filters.app.vi_insert_multiple_mode`
- :class:`~prompt_toolkit.filters.app.vi_replace_mode`
- :class:`~prompt_toolkit.filters.app.vi_selection_mode`
- :class:`~prompt_toolkit.filters.app.vi_waiting_for_text_object_mode`
- :class:`~prompt_toolkit.filters.app.vi_digraph_mode`

- :class:`~prompt_toolkit.filters.app.emacs_mode`
- :class:`~prompt_toolkit.filters.app.emacs_insert_mode`
- :class:`~prompt_toolkit.filters.app.emacs_selection_mode`

- :class:`~prompt_toolkit.filters.app.is_searching`
- :class:`~prompt_toolkit.filters.app.control_is_searchable`
- :class:`~prompt_toolkit.filters.app.vi_search_direction_reversed`


Combining filters
^^^^^^^^^^^^^^^^^

Further, these filters can be chained by the ``&`` and ``|`` operators or
negated by the ``~`` operator.

Some examples:

.. code:: python

    from prompt_toolkit.key_binding.key_bindings import KeyBindings
    from prompt_toolkit.filters import has_selection, has_selection

    kb = KeyBindings()

    @kb.add('c-t', filter=~is_searching)
    def _(event):
        " Do something, but not while searching. "
        pass

    @kb.add('c-t', filter=has_search | has_selection)
    def _(event):
        " Do something, but only when searching or when there is a selection. "
        pass
