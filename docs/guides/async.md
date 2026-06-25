# Async

## AsyncSession

```python
from fluxium import AsyncSession

async with AsyncSession() as s:
    r = await s.get("https://api.example.com")
    print(r.json())
```

## Concurrent Requests

```python
import asyncio
from fluxium import AsyncSession

async def main():
    async with AsyncSession() as s:
        tasks = [s.get(f"https://api.example.com/item/{i}") for i in range(100)]
        results = await asyncio.gather(*tasks)
        print(f"Fetched {len(results)} items")

asyncio.run(main())
```

## uvloop

Fluxium auto-installs `uvloop` when available (Linux/macOS). Install it:

```bash
pip install "fluxium[uvloop]"
```

No code changes needed — detected on import.

## Sequential Requests

```python
async with AsyncSession() as s:
    r1 = await s.get("https://api.example.com/users/1")
    r2 = await s.post("https://api.example.com/items", json={"from": r1.json()["id"]})
```

## Concurrency Limiting

```python
sem = asyncio.Semaphore(10)

async def fetch(s, url):
    async with sem:
        return await s.get(url)

async with AsyncSession() as s:
    tasks = [fetch(s, f"https://api.example.com/item/{i}") for i in range(1000)]
    results = await asyncio.gather(*tasks)
```

## Async Streaming

```python
async with AsyncSession() as s:
    r = await s.get("https://api.example.com/stream", stream=True)
    async for line in r._raw.aiter_lines():
        print(line)
```

## Async + Cache

```python
from fluxium import AsyncSession, MemoryCache

async with AsyncSession(cache=MemoryCache()) as s:
    await s.get("https://api.example.com")  # network
    await s.get("https://api.example.com")  # cache
```
