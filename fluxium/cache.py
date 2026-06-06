"""Built-in caching layer for Fluxium.

Supports in-memory and disk-based caching with TTL.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .models import Response


class CacheBackend:
    """Abstract cache backend."""

    def get(self, key: str) -> dict | None:
        raise NotImplementedError

    def set(self, key: str, value: dict, ttl: int) -> None:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class MemoryCache(CacheBackend):
    """In-memory LRU cache with TTL."""

    def __init__(self, max_size: int = 1000):
        self._store: dict[str, tuple[dict, float]] = {}
        self._max_size = max_size

    def get(self, key: str) -> dict | None:
        if key in self._store:
            value, expires = self._store[key]
            if time.time() < expires:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value: dict, ttl: int) -> None:
        if len(self._store) >= self._max_size:
            now = time.time()
            expired = [k for k, (_, exp) in self._store.items() if exp < now]
            for k in expired:
                del self._store[k]
            if len(self._store) >= self._max_size:
                oldest = next(iter(self._store))
                del self._store[oldest]
        self._store[key] = (value, time.time() + ttl)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


class DiskCache(CacheBackend):
    """Disk-based cache with TTL."""

    def __init__(self, cache_dir: str | Path = ".fluxium_cache"):
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _key_to_path(self, key: str) -> Path:
        safe = hashlib.sha256(key.encode()).hexdigest()[:32]
        return self._dir / f"{safe}.json"

    def get(self, key: str) -> dict | None:
        path = self._key_to_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            if time.time() < data["expires"]:
                return data["value"]
            path.unlink(missing_ok=True)
        except (json.JSONDecodeError, KeyError, OSError):
            path.unlink(missing_ok=True)
        return None

    def set(self, key: str, value: dict, ttl: int) -> None:
        path = self._key_to_path(key)
        path.write_text(json.dumps({"expires": time.time() + ttl, "value": value}))

    def delete(self, key: str) -> None:
        self._key_to_path(key).unlink(missing_ok=True)

    def clear(self) -> None:
        for f in self._dir.glob("*.json"):
            f.unlink(missing_ok=True)


def _make_cache_key(method: str, url: str, headers: dict | None = None) -> str:
    """Create a cache key from request parameters."""
    parts = [method.upper(), url]
    if headers:
        for k in sorted(headers):
            if k.lower() not in ("authorization", "cookie", "x-request-id"):
                parts.append(f"{k}={headers[k]}")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def _response_to_cache(resp: Response) -> dict:
    """Serialize a response for caching."""
    return {
        "status_code": resp.status_code,
        "url": resp.url,
        "headers": resp.headers,
        "content": resp.content.hex(),
        "encoding": resp.encoding,
    }


def _cache_to_response(data: dict) -> Response:
    """Deserialize a cached response."""
    from .cookies import CookieJar

    resp = Response()
    resp.status_code = data["status_code"]
    resp.url = data["url"]
    resp.headers = data["headers"]
    resp._content = bytes.fromhex(data["content"])
    resp.encoding = data.get("encoding", "utf-8")
    resp.cookies = CookieJar()
    return resp
