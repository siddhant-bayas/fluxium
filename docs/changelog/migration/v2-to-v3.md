# v2 to v3 Migration Guide

## Breaking Changes

**None.** v3 is a full performance and quality-of-life release with zero API changes.

## Upgrade Steps

```bash
pip install --upgrade fluxium
```

Then verify:

```python
import fluxium
print(fluxium.__version__)  # 3.0.0
```

## What Changed

v3 is a **performance overhaul** — fluxium now matches or exceeds httpx throughput:

- **~1.9× faster** vs v2 (from 1.70× slower than httpx down to 0.91× — now **9% faster** than httpx)
- Lazy header merging, single-pass request construction, direct transport path
- Empty middleware/hooks/cookies guards to minimize function call overhead
- CookieJar header cache eliminates repeated serialization

### Fixes

- **uvloop on Windows** — installing `fluxium[uvloop]` no longer fails on Windows (platform marker added)
- **CookieJar always truthy** — empty cookie jars no longer force a full header dict copy on every request
