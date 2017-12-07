.. _asyncio:

Running on top of the ``asyncio`` event loop
--------------------------------------------

Prompt_toolkit has a built-in event loop of its own. However, in modern
applications, you probably want to use asyncio for everything. With just one
line of code, it is possible to run prompt_toolkit on top of asyncio:

.. code::

    from prompt_toolkit.eventloop.defaults import use_asyncio_event_loop

    use_asyncio_event_loop()

This will create an adaptor between the asyncio event loop and prompt_toolkit,
and register it as the default event loop.

.. warning::

        If you want to use coroutines in your application, then using asyncio
        is the preferred way. It's better to avoid the built-in coroutines,
        because they make debugging the application much more difficult. Unless
        of course Python 2 support is still required.
