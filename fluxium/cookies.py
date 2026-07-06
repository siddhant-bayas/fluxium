"""Dict-like CookieJar with full http.cookiejar integration."""

from __future__ import annotations

from http.cookiejar import Cookie
from http.cookiejar import CookieJar as _CJ


class CookieJar(_CJ):
    """Dict-like cookie jar backed by :class:`http.cookiejar.CookieJar`.

    Supports standard dict operations (``[]``, ``in``, ``del``) plus
    :meth:`to_header` for the ``Cookie`` header value and :meth:`to_dict`
    for a plain ``{name: value}`` mapping.
    """

    __slots__ = ("_dirty", "_header_cache")

    def __init__(self, cookies=None):
        super().__init__()
        self._dirty = True
        self._header_cache: str | None = None
        if cookies:
            self.update(cookies)

    def __setitem__(self, name: str, value: str) -> None:
        self.set(name, value)

    def __getitem__(self, name: str) -> str:
        for c in self:
            if c.name == name:
                return c.value or ""
        raise KeyError(name)

    def __delitem__(self, name: str) -> None:
        self._dirty = True
        _cookies: dict = object.__getattribute__(self, "_cookies")
        for d in _cookies.values():
            for p in d.values():
                p.pop(name, None)

    def __contains__(self, name: str) -> bool:
        return any(c.name == name for c in self)

    def __repr__(self) -> str:
        items = ", ".join(f"{c.name}={c.value}" for c in self)
        return f"<CookieJar [{items}]>"

    def get(self, name: str, default: str | None = None) -> str | None:
        try:
            return self[name]
        except KeyError:
            return default

    def items(self) -> list[tuple[str, str]]:
        return [(c.name, c.value or "") for c in self]

    def keys(self) -> list[str]:
        return [c.name for c in self]

    def values(self) -> list[str]:
        return [c.value or "" for c in self]

    def update(self, cookies) -> None:
        self._dirty = True
        if isinstance(cookies, dict):
            for k, v in cookies.items():
                self.set(k, v)
        elif isinstance(cookies, CookieJar):
            for c in cookies:
                domain = c.domain or ""
                path = c.path or "/"
                _cookies: dict = object.__getattribute__(self, "_cookies")
                _cookies.setdefault(domain, {}).setdefault(path, {})[c.name] = c

    def set(self, name: str, value: str, domain: str = "", path: str = "/") -> None:
        self._dirty = True
        cookie = Cookie(
            version=0,
            name=name,
            value=value,
            port=None,
            port_specified=False,
            domain=domain,
            domain_specified=bool(domain),
            domain_initial_dot=domain.startswith(".") if domain else False,
            path=path,
            path_specified=bool(path),
            secure=False,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={},
        )
        _cookies: dict = object.__getattribute__(self, "_cookies")
        _cookies.setdefault(domain, {}).setdefault(path, {})[name] = cookie

    def clear(self) -> None:
        self._dirty = True
        super().clear()

    def to_dict(self) -> dict[str, str]:
        return {c.name: c.value or "" for c in self}

    def to_header(self) -> str:
        if not self._dirty and self._header_cache is not None:
            return self._header_cache
        header = "; ".join(f"{c.name}={c.value}" for c in self)
        self._header_cache = header
        self._dirty = False
        return header
