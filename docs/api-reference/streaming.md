# Streaming

`fluxium/streaming.py`

## SSEEvent

```python
class SSEEvent:
    def __init__(
        self,
        event: str = "message",
        data: str = "",
        id: str | None = None,
        retry: int | None = None,
    )
```

### Methods

| Method | Returns | Description |
|---|---|---|
| `json()` | `Any` | Parse `data` as JSON |

## StreamReader

```python
class StreamReader:
    def __init__(self, response: Response, chunk_size: int = 8192)
```

### Properties

| Property | Returns | Description |
|---|---|---|
| `bytes_read` | `int` | Bytes read so far |
| `total` | `int \| None` | Total bytes from Content-Length |
| `progress` | `float \| None` | 0.0 to 1.0 |

### Methods

| Method | Returns | Description |
|---|---|---|
| `iter_chunks()` | `Iterator[bytes]` | Iterate body chunks |
| `iter_text()` | `Iterator[str]` | Iterate decoded text |
| `save_to(path=None)` | `str` | Save to file, return absolute path |

## Functions

| Function | Returns | Description |
|---|---|---|
| `iter_sse(response)` | `Iterator[SSEEvent]` | Parse SSE from sync stream |
| `aiter_sse(response)` | `AsyncIterator[SSEEvent]` | Parse SSE from async stream |
