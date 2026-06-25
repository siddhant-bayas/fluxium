# v1 to v2 Migration Guide

## Breaking Changes

### 1. `setup.py` Removed

`setup.py` is gone. Use `pyproject.toml` only. No action needed unless you were importing from `setup.py`.

### 2. Retry Bug Fix (behavioral change)

In v1, **retries did not work** due to a bug where `if response:` evaluated to `False` for 4xx/5xx status codes. In v2, retries work correctly.

If you were working around this bug (e.g., catching HTTPError manually), your code will still work — it just won't retry unnecessarily anymore.

### 3. Version Bump

Version is now `2.0.0`. No API changes beyond the retry fix.

## Upgrade Steps

```bash
pip install --upgrade fluxium
```

Then verify:

```python
import fluxium
print(fluxium.__version__)  # 2.0.0
```

## New Features to Try

1. **Caching** — wrap your session with `MemoryCache()`:
   ```python
   from fluxium import Session, MemoryCache
   with Session(cache=MemoryCache()) as s:
       s.get("https://api.example.com")  # cached!
   ```

2. **Pre-warming** — eliminate first-request latency:
   ```python
   with Session() as s:
       s.prewarm("https://api.example.com")
   ```

3. **uvloop** — install for faster async:
   ```bash
   pip install "fluxium[uvloop]"
   ```
