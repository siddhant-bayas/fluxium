"""Module-level convenience functions — one-shot requests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .session import Session

if TYPE_CHECKING:
    from .models import Response


def request(method: str, url: str, **kwargs) -> Response:
    with Session() as s:
        return s.request(method, url, **kwargs)


def get(url, **kw) -> Response:
    return request("GET", url, **kw)


def post(url, **kw) -> Response:
    return request("POST", url, **kw)


def put(url, **kw) -> Response:
    return request("PUT", url, **kw)


def patch(url, **kw) -> Response:
    return request("PATCH", url, **kw)


def delete(url, **kw) -> Response:
    return request("DELETE", url, **kw)


def head(url, **kw) -> Response:
    return request("HEAD", url, **kw)


def options(url, **kw) -> Response:
    return request("OPTIONS", url, **kw)


async def arequest(method: str, url: str, **kwargs) -> Response:
    from .session import AsyncSession

    async with AsyncSession() as s:
        return await s.request(method, url, **kwargs)


async def aget(url, **kw) -> Response:
    return await arequest("GET", url, **kw)


async def apost(url, **kw) -> Response:
    return await arequest("POST", url, **kw)


async def aput(url, **kw) -> Response:
    return await arequest("PUT", url, **kw)


async def apatch(url, **kw) -> Response:
    return await arequest("PATCH", url, **kw)


async def adelete(url, **kw) -> Response:
    return await arequest("DELETE", url, **kw)


async def ahead(url, **kw) -> Response:
    return await arequest("HEAD", url, **kw)


async def aoptions(url, **kw) -> Response:
    return await arequest("OPTIONS", url, **kw)
