from inspect import trace
from textwrap import dedent
import sys

import pytest

from aeval import __version__, aeval


def test_version():
    assert __version__ == '0.1.1'


@pytest.mark.asyncio
async def test_simple_value():
    scope = dict(items=[])
    value = await aeval(dedent('''
    10
    '''), scope, None)
    assert value == 10


@pytest.mark.asyncio
async def test_sync_for():
    scope = dict(items=[])
    await aeval(dedent('''
    for i in range(3):
        items.append(i)
    '''), scope, None)
    assert scope['items'] == [0, 1, 2]


@pytest.mark.asyncio
async def test_async_def():
    scope = dict()
    await aeval(dedent('''
    async def foo():
        await sleep(1)
    '''), scope, None)

    assert callable(scope['foo'])


@pytest.mark.asyncio
async def test_simple_await():
    scope = dict()
    await aeval(dedent('''
    import asyncio
    await asyncio.sleep(0)
    '''), scope, None)


@pytest.mark.asyncio
async def test_async_for():
    items = []
    async def gen():
        import asyncio
        for i in range(3):
            await asyncio.sleep(0)
            yield i

    scope = dict(items=items, gen=gen)
    await aeval(dedent('''
    async for i in gen():
        items.append(i)
    '''), scope, None)

    assert items == [0, 1, 2]


@pytest.mark.asyncio
async def test_async_with():
    import contextlib

    @contextlib.asynccontextmanager
    async def mgr():
        import asyncio
        await asyncio.sleep(0)
        yield 7

    scope = dict(mgr=mgr)

    await aeval(dedent('''
    async with mgr() as num:
        x = num
    '''), scope, None)

    assert scope['x'] == 7


@pytest.mark.asyncio
async def test_await_in_for():
    async def foo():
        return 3

    scope = dict(foo=foo)
    await aeval(dedent('''
    for _ in range(1):
        x = await foo()
    '''), scope, None)

    assert scope['x'] == 3

@pytest.mark.asyncio
async def test_await_in_for():
    import contextlib

    @contextlib.contextmanager
    def foo():
        yield 1

    scope = dict(foo=foo)
    await aeval(dedent('''
    with foo() as f:
        import asyncio
        await asyncio.sleep(0)
        x = f
    '''), scope, None)

    assert scope['x'] == 1


@pytest.mark.asyncio
async def test_del():
    scope = dict(x=1)
    await aeval(dedent('''
    del x
    '''), scope, None)

    assert 'x' not in scope


@pytest.mark.asyncio
async def test_exposed_annotated_name():
    scope = dict()
    await aeval(dedent('''
    foo: int
    foo = 7
    '''), scope, None)

    assert scope['foo'] == 7


@pytest.mark.asyncio
async def test_exposed_annotated_assign():
    scope = dict()
    await aeval(dedent('''
    foo: int = 10
    '''), scope, None)

    assert scope['foo'] == 10


@pytest.mark.asyncio
async def test_exposed_aug_assign():
    scope = dict(foo=1)
    await aeval(dedent('''
    foo += 10
    '''), scope, None)

    assert scope['foo'] == 11


@pytest.mark.asyncio
async def test_exposed_class():
    scope = dict()
    await aeval(dedent('''
    class Foo():
        ...
    '''), scope, None)

    assert isinstance(scope['Foo'], type)


@pytest.mark.asyncio
async def test_unexposed_class_annotated_assign():
    scope = dict()
    await aeval(dedent('''
    class Foo():
        x: int
        y: str = 'abc'
        ...
    '''), scope, None)

    assert scope['Foo'].__annotations__['x'] is int
    assert scope['Foo'].__annotations__['y'] is str
    assert scope['Foo'].y == 'abc'


@pytest.mark.asyncio
async def test_raise():
    with pytest.raises(Exception):
        await aeval(dedent('''
        raise Exception('ha')
        '''), dict(), None)
