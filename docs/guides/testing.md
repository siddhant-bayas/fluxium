# Testing

## respx (Recommended)

`respx` intercepts httpx calls for deterministic, fast tests.

```bash
pip install respx pytest-asyncio
```

## Basic Mocking

```python
import respx
import httpx
import fluxium

@respx.mock
def test_get_user():
    route = respx.get("https://api.example.com/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Alice"})
    )

    r = fluxium.get("https://api.example.com/users/1")
    assert r.status_code == 200
    assert r.json()["name"] == "Alice"
    assert route.called
```

## With Session

```python
@respx.mock
def test_session():
    respx.get("https://api.example.com/").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    with fluxium.Session() as s:
        r = s.get("https://api.example.com/")
        assert r.status_code == 200
```

## Async Testing

```python
import pytest
import respx
import httpx
from fluxium import AsyncSession

@pytest.mark.asyncio
@respx.mock
async def test_async_get():
    respx.get("https://api.example.com/").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    async with AsyncSession() as s:
        r = await s.get("https://api.example.com/")
        assert r.status_code == 200
```

## Dynamic Responses

```python
def test_retry():
    counter = [0]

    def respond(request):
        counter[0] += 1
        if counter[0] == 1:
            return httpx.Response(500)
        return httpx.Response(200, json={"ok": True})

    route = respx.get("https://api.example.com/").mock(side_effect=respond)
    with fluxium.Session(max_retries=1, retry_backoff=0.01) as s:
        r = s.get("https://api.example.com/")
        assert r.status_code == 200
    assert route.call_count == 2
```

## Pytest Fixtures

```python
import pytest
import respx
import httpx
from fluxium import Session, MemoryCache

@pytest.fixture
def mocked():
    with respx.mock:
        yield

@pytest.fixture
def session():
    with Session(cache=MemoryCache()) as s:
        yield s

def test_cached_request(mocked, session):
    respx.get("https://api.example.com/").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    session.get("https://api.example.com/")
    session.get("https://api.example.com/")  # from cache
    assert respx.routes[0].call_count == 1
```
