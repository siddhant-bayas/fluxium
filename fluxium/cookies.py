"""Dict-like CookieJar with full http.cookiejar integration."""
from http.cookiejar import CookieJar as _CJ, Cookie


class CookieJar(_CJ):
    """Dict-like cookie jar backed by :class:`http.cookiejar.CookieJar`.

    Supports standard dict operations (``[]``, ``in``, ``del``) plus
    :meth:`to_header` for the ``Cookie`` header value and :meth:`to_dict`
    for a plain ``{name: value}`` mapping.
    """

    __slots__ = ()

    def __init__(self, cookies=None):
        super().__init__()
        if cookies:
            self.update(cookies)

    def __setitem__(self, name: str, value: str) -> None:
        self.set(name, value)

    def __getitem__(self, name: str) -> str:
        for c in self:
            if c.name == name:
                return c.value
        raise KeyError(name)

    def __delitem__(self, name: str) -> None:
        for d in self._cookies.values():
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
        return [(c.name, c.value) for c in self]

    def keys(self) -> list[str]:
        return [c.name for c in self]

    def values(self) -> list[str]:
        return [c.value for c in self]

    def update(self, cookies) -> None:
        if isinstance(cookies, dict):
            for k, v in cookies.items():
                self.set(k, v)
        elif isinstance(cookies, CookieJar):
            for c in cookies:
                domain = c.domain or ""
                path = c.path or "/"
                self._cookies.setdefault(domain, {}).setdefault(path, {})[c.name] = c

    def set(self, name: str, value: str, domain: str = "", path: str = "/") -> None:
        cookie = Cookie(
            version=0, name=name, value=value,
            port=None, port_specified=False,
            domain=domain, domain_specified=bool(domain),
            domain_initial_dot=domain.startswith(".") if domain else False,
            path=path, path_specified=bool(path),
            secure=False, expires=None, discard=True,
            comment=None, comment_url=None, rest={},
        )
        self._cookies.setdefault(domain, {}).setdefault(path, {})[name] = cookie

    def to_dict(self) -> dict[str, str]:
        return {c.name: c.value for c in self}

    def to_header(self) -> str:
        return "; ".join(f"{c.name}={c.value}" for c in self)
