# Streaming

## iter_content

Stream response body in chunks.

```python
with fluxium.Session() as s:
    r = s.get("https://api.example.com/large.zip", stream=True)
    for chunk in r.iter_content(chunk_size=8192):
        process(chunk)
```

## iter_lines

Iterate line-by-line.

```python
with fluxium.Session() as s:
    r = s.get("https://api.example.com/stream", stream=True)
    for line in r.iter_lines():
        print(line)
```

## StreamReader

High-level streaming with progress tracking.

```python
from fluxium import StreamReader

with fluxium.Session() as s:
    r = s.get("https://api.example.com/file.zip", stream=True)
    reader = StreamReader(r, chunk_size=65536)

    print(f"Total: {reader.total} bytes")
    for chunk in reader.iter_chunks():
        print(f"Progress: {reader.progress:.0%}")

    # Or save directly
    path = reader.save_to("file.zip")
    print(f"Saved to {path}")
```

## Async Streaming

```python
async with AsyncSession() as s:
    r = await s.get("https://api.example.com/stream", stream=True)
    async for chunk in r._raw.aiter_bytes(chunk_size=8192):
        process(chunk)
```
