from __future__ import unicode_literals
from prompt_toolkit.eventloop import consume_async_generator
from prompt_toolkit.eventloop import get_event_loop, ensure_future, From, AsyncGeneratorItem, Future, generator_to_async_generator


def _async_generator():
    " Simple asynchronous generator. "

    # await.
    result = yield From(Future.succeed(1))

    # yield
    yield AsyncGeneratorItem(result + 1)

    # await.
    result = yield From(Future.succeed(10))

    # yield
    yield AsyncGeneratorItem(result + 1)


def test_async_generator():
    " Test asynchronous generator. "
    items = []
    f = ensure_future(consume_async_generator(
        _async_generator(), lambda: False, items.append))

    # Run the event loop until all items are collected.
    get_event_loop().run_until_complete(f)
    assert items == [2, 11]

    # Check that `consume_async_generator` didn't fail.
    assert f.result() is None


def _empty_async_generator():
    " Async generator that returns right away. "
    if False:
        yield


def test_empty_async_generator():
    " Test asynchronous generator. "
    items = []
    f = ensure_future(consume_async_generator(
        _empty_async_generator(), lambda: False, items.append))

    # Run the event loop until all items are collected.
    get_event_loop().run_until_complete(f)
    assert items == []

    # Check that `consume_async_generator` didn't fail.
    assert f.result() is None


def _sync_generator():
    yield 1
    yield 10


def test_generator_to_async_generator():
    """
    Test conversion of sync to asycn generator.
    This should run the synchronous parts in a background thread.
    """
    async_gen = generator_to_async_generator(_sync_generator)

    items = []
    f = ensure_future(consume_async_generator(
        async_gen, lambda: False, items.append))

    # Run the event loop until all items are collected.
    get_event_loop().run_until_complete(f)
    assert items == [1, 10]

    # Check that `consume_async_generator` didn't fail.
    assert f.result() is None
