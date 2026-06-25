# Compatibility

## Python

| Version | Status |
|---|---|
| 3.9 | Supported |
| 3.10 | Supported |
| 3.11 | Supported |
| 3.12 | Supported |
| 3.13 | Supported |
| 3.14 | Supported |

## Operating System

| OS | Status |
|---|---|
| Linux | Supported |
| macOS | Supported |
| Windows | Supported |
| WSL | Supported |

## uvloop

Fluxium auto-installs `uvloop` when available on Linux/macOS. On Windows, it falls back to the default asyncio event loop.

```bash
pip install "fluxium[uvloop]"
```

No code changes needed — uvloop is detected and enabled automatically on import.

## Async Backends

Fluxium uses `asyncio` exclusively. It does not currently support trio or other async runtimes.

## httpx Compatibility

Fluxium wraps `httpx[http2]`. If your project already uses httpx, you can use fluxium alongside it — they share the same async event loop.

```python
import httpx
import fluxium

# Both work on the same event loop
async with fluxium.AsyncSession() as s:
    r = await s.get("https://api.example.com")
```
