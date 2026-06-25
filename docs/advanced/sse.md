# SSE (Server-Sent Events)

Deep-dive into SSE with `streaming.py`.

## Basic Usage

```python
with fluxium.Session() as s:
    r = s.get("https://api.example.com/events", stream=True)
    for event in fluxium.iter_sse(r):
        print(f"[{event.event}] {event.data}")
```

## SSEEvent Fields

| Field | Type | Default | Description |
|---|---|---|
| `event` | `str` | `"message"` | Event type |
| `data` | `str` | `""` | Event data |
| `id` | `str \| None` | `None` | Event ID |
| `retry` | `int \| None` | `None` | Reconnect time (ms) |

## Event Types

```python
for event in fluxium.iter_sse(r):
    match event.event:
        case "message":
            handle_message(event.json())
        case "update":
            handle_update(event.json())
        case "delete":
            handle_delete(event.id)
```

## Async SSE

```python
async with AsyncSession() as s:
    r = await s.get("https://api.example.com/events", stream=True)
    async for event in fluxium.aiter_sse(r):
        print(f"[{event.event}] {event.data}")
```

## Reconnection

SSE spec supports reconnection via `retry` field and `Last-Event-ID`.

```python
last_id = None

while True:
    with Session() as s:
        headers = {}
        if last_id:
            headers["Last-Event-ID"] = last_id
        r = s.get("https://api.example.com/events", stream=True, headers=headers)
        try:
            for event in fluxium.iter_sse(r):
                last_id = event.id
                process(event)
        except ConnectionError:
            pass  # auto-reconnect (httpx handles retry field)
```

## Parsing JSON from Events

```python
for event in fluxium.iter_sse(r):
    if event.data:
        data = event.json()
        process(data)
```

## Comments

SSE comments (lines starting with `:`) are silently ignored by `iter_sse` and `aiter_sse`.

## Error Handling

```python
try:
    for event in fluxium.iter_sse(r):
        process(event)
except ConnectionError:
    print("Connection lost, reconnect...")
```

## StreamReader vs iter_sse

- `StreamReader`: binary streaming with progress tracking
- `iter_sse` / `aiter_sse`: SSE-specific event parsing

Use `StreamReader` for raw streaming, `iter_sse` for SSE protocols.
