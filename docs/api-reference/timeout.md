# Timeout

`fluxium/timeout.py`

## Signature

```python
class Timeout:
    def __init__(
        self,
        connect: float | tuple | None = 30.0,
        read: float | None = None,
        write: float | None = None,
        pool: float | None = None,
    )
```

## Description

Structured timeout configuration. Can be created from a single value or per-component.

## Examples

```python
from fluxium import Timeout

# All components: 30s
Timeout(30.0)

# Connect 5s, read 30s
Timeout(connect=5.0, read=30.0)

# From tuple (connect, read)
Timeout((5.0, 30.0))

# No timeout
Timeout(None)
```

## Methods

| Method | Returns | Description |
|---|---|---|
| `to_httpx()` | `httpx.Timeout` | Convert to httpx Timeout object |

## Conversion to httpx

```python
t = Timeout(connect=5.0, read=30.0)
httpx_timeout = t.to_httpx()
# httpx.Timeout(connect=5.0, read=30.0, write=None, pool=None)
```

## Usage

```python
from fluxium import Session, Timeout

# Session default
s = Session(timeout=Timeout(connect=5.0, read=30.0))

# Per-request
s.get("https://api.example.com", timeout=Timeout(10.0))
```
