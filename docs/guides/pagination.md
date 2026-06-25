# Pagination

## Offset-Based Pagination

```python
from fluxium import Session

all_items = []
page = 1

with Session() as s:
    while True:
        r = s.get("https://api.example.com/items", params={"page": page, "per_page": 100})
        data = r.json()
        if not data["items"]:
            break
        all_items.extend(data["items"])
        page += 1
```

## Cursor-Based Pagination

```python
with Session() as s:
    cursor = None
    while True:
        params = {"limit": 100}
        if cursor:
            params["cursor"] = cursor
        r = s.get("https://api.example.com/items", params=params)
        data = r.json()
        process(data["items"])
        cursor = data.get("next_cursor")
        if not cursor:
            break
```

## Async Pagination

```python
import asyncio
from fluxium import AsyncSession

async def fetch_all():
    all_items = []
    cursor = None

    async with AsyncSession() as s:
        while True:
            params = {"limit": 100}
            if cursor:
                params["cursor"] = cursor
            r = await s.get("https://api.example.com/items", params=params)
            data = r.json()
            all_items.extend(data["items"])
            cursor = data.get("next_cursor")
            if not cursor:
                break

    return all_items

items = asyncio.run(fetch_all())
```

## With Cache (Avoid Re-Fetching)

```python
from fluxium import Session, MemoryCache

with Session(cache=MemoryCache()) as s:
    # First pass fetches and caches
    for page in range(1, 11):
        s.get("https://api.example.com/items", params={"page": page})

    # Second pass reads from cache (instant)
    for page in range(1, 11):
        r = s.get("https://api.example.com/items", params={"page": page})
```
