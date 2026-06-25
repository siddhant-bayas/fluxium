# Making Requests

Fluxium provides module-level functions for one-shot requests and `Session` for connection pooling.

## Module-Level Functions

```python
import fluxium

# GET
r = fluxium.get("https://api.example.com")

# POST
r = fluxium.post("https://api.example.com", json={"key": "value"})

# PUT
r = fluxium.put("https://api.example.com", json={"key": "updated"})

# PATCH
r = fluxium.patch("https://api.example.com", json={"key": "patched"})

# DELETE
r = fluxium.delete("https://api.example.com/item/1")

# HEAD
r = fluxium.head("https://api.example.com")

# OPTIONS
r = fluxium.options("https://api.example.com")

# Custom method
r = fluxium.request("CUSTOM", "https://api.example.com")
```

Each creates a short-lived `Session` internally. For repeated requests to the same host, use a `Session` directly.

## Query Parameters

```python
r = fluxium.get("https://api.example.com/search", params={"q": "python", "page": 1})
# URL: https://api.example.com/search?q=python&page=1
```

## Custom Headers

```python
r = fluxium.get("https://api.example.com", headers={"X-Custom": "value"})
```

## Timeout

```python
# Single timeout for all components
r = fluxium.get("https://api.example.com", timeout=10.0)

# (connect, read) tuple
r = fluxium.get("https://api.example.com", timeout=(5.0, 30.0))
```

## Redirects

```python
# Follow redirects (default)
r = fluxium.get("https://api.example.com/redirect")

# Don't follow
r = fluxium.get("https://api.example.com/redirect", allow_redirects=False)
```

## Streaming

```python
r = fluxium.get("https://api.example.com/large", stream=True)
for chunk in r.iter_content(chunk_size=8192):
    process(chunk)
```

## Async

```python
import asyncio

async def main():
    r = await fluxium.aget("https://api.example.com")
    print(r.json())

asyncio.run(main())
```
