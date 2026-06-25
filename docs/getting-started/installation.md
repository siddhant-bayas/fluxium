# Installation

## Basic

```bash
pip install fluxium
```

## Optional Extras

```bash
# SOCKS proxy support (requires httpx-socks)
pip install "fluxium[socks]"

# uvloop for 20-40% faster async (Linux/macOS)
pip install "fluxium[uvloop]"

# Hishel RFC 7234 cache backend
pip install "fluxium[cache]"

# Everything
pip install "fluxium[all]"
```

## Development Install

```bash
git clone https://github.com/siddhant-bayas/fluxium.git
cd fluxium
pip install -e ".[dev]"
```

## Verify

```python
import fluxium
print(fluxium.__version__)  # 2.0.0
```

## Dependencies

| Package | Required | Purpose |
|---|---|---|
| `httpx[http2]` | Yes | HTTP client with HTTP/2 |
| `idna` | Yes | International domain names |
| `chardet` | Yes | Encoding detection |
| `brotli` | Yes | Brotli decompression |
| `httpx-socks` | No | SOCKS proxy |
| `uvloop` | No | Faster async event loop |
| `hishel` | No | RFC 7234 cache backend |
