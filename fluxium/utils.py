"""URL utilities: IDNA encoding, param serialization, netrc."""
from __future__ import annotations

import hashlib
from urllib.parse import urlencode, urlparse, urlunparse

import idna

_netrc_cache = None
_netrc_creds_cache: dict[str, tuple | None] = {}


def _get_netrc():
    """Read and cache the netrc file."""
    import netrc as _netrc_mod
    global _netrc_cache
    if _netrc_cache is None:
        try:
            _netrc_cache = _netrc_mod.netrc()
        except (FileNotFoundError, _netrc_mod.NetrcParseError, PermissionError):
            _netrc_cache = False
    return _netrc_cache


def encode_url(url: str, params: dict | None = None) -> str:
    """Encode URL with IDNA host support and optional query params.

    When *params* is given they are appended to the query string.
    International (non-ASCII) hostnames are IDNA 2008-encoded automatically.
    """
    if params:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        try:
            encoded_host = idna.encode(host).decode("ascii")
        except Exception:
            encoded_host = host
        netloc = parsed.netloc
        if host and encoded_host != host:
            netloc = netloc.replace(host, encoded_host)
        query = parsed.query
        extra = urlencode(params, doseq=True)
        query = f"{query}&{extra}" if query else extra
        return urlunparse(parsed._replace(netloc=netloc, query=query))

    # Fast path: pure ASCII URLs need no processing
    try:
        url.encode("ascii")
        return url
    except UnicodeEncodeError:
        pass

    # Non-ASCII: IDNA-encode the hostname
    parsed = urlparse(url)
    host = parsed.hostname or ""
    try:
        encoded_host = idna.encode(host).decode("ascii")
    except Exception:
        return url
    if encoded_host == host:
        return url
    netloc = parsed.netloc.replace(host, encoded_host)
    return urlunparse(parsed._replace(netloc=netloc))


def netrc_credentials(host: str) -> tuple[str, str] | None:
    """Return ``(user, password)`` from ``~/.netrc`` for *host*, or ``None``.

    Results are cached per host so the netrc file is read at most once.
    """
    cached = _netrc_creds_cache.get(host)
    if cached is not None:
        return cached
    rc = _get_netrc()
    if not rc:
        _netrc_creds_cache[host] = None
        return None
    try:
        auth = rc.authenticators(host)
        result = (auth[0], auth[2]) if auth else None
    except Exception:
        result = None
    _netrc_creds_cache[host] = result
    return result


def merge_headers(*dicts: dict | None) -> dict:
    """Merge one or more header dicts. Later dicts override earlier ones.
    All keys are lowercased."""
    result: dict[str, str] = {}
    for d in dicts:
        if d:
            result.update({k.lower(): v for k, v in d.items()})
    return result
