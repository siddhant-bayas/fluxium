# Async Client (AsyncSession)

`fluxium/session.py`

## Signature

```python
class AsyncSession:
    def __init__(
        self,
        *,
        headers: dict | None = None,
        cookies: dict | CookieJar | None = None,
        auth: AuthBase | None = None,
        verify: bool | str = True,
        proxies: dict | str | None = None,
        timeout: float | tuple = 30.0,
        http2: bool = True,
        max_redirects: int = 30,
        trust_env: bool = True,
        cache: CacheBackend | None = None,
        max_retries: int = 0,
        retry_backoff: float = 0.5,
    )
```

## Methods

```python
async def request(method: str, url: str, **kwargs) -> Response
async def get(url: str, **kwargs) -> Response
async def post(url: str, **kwargs) -> Response
async def put(url: str, **kwargs) -> Response
async def patch(url: str, **kwargs) -> Response
async def delete(url: str, **kwargs) -> Response
async def head(url: str, **kwargs) -> Response
async def options(url: str, **kwargs) -> Response
async def close() -> None
async def prewarm(url: str) -> None
def add_middleware(mw: Middleware) -> None
async def __aenter__() -> AsyncSession
async def __aexit__(exc_type, exc_val, exc_tb) -> None
```

## Example

```python
import asyncio
from fluxium import AsyncSession

async def main():
    async with AsyncSession(timeout=30.0, http2=True) as s:
        r = await s.get("https://api.example.com")
        print(r.json())

asyncio.run(main())
```
