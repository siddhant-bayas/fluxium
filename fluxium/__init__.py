"""
Fluxium — A fast, versatile HTTP library.
Author: Siddhant Bayas
"""

from .api import (
    get, post, put, patch, delete, head, options, request,
    aget, apost, aput, apatch, adelete, ahead, aoptions, arequest,
)
from .session import Session, AsyncSession
from .models import Response, Request
from .auth import BasicAuth, DigestAuth
from .oauth2 import BearerAuth, OAuth2Auth
from .exceptions import (
    FluxiumError, ConnectionError, TimeoutError, HTTPError,
    SSLError, ProxyError, TooManyRedirects,
)
from .cookies import CookieJar
from .cache import MemoryCache, DiskCache
from .middleware import Middleware, LoggingMiddleware, RetryMiddleware
from .streaming import SSEEvent, StreamReader, iter_sse, aiter_sse
from .__version__ import __version__, __author__

__all__ = [
    # Core
    "get", "post", "put", "patch", "delete", "head", "options", "request",
    "aget", "apost", "aput", "apatch", "adelete", "ahead", "aoptions", "arequest",
    "Session", "AsyncSession",
    "Response", "Request",
    # Auth
    "BasicAuth", "DigestAuth", "BearerAuth", "OAuth2Auth",
    # Cookies
    "CookieJar",
    # Caching
    "MemoryCache", "DiskCache",
    # Middleware
    "Middleware", "LoggingMiddleware", "RetryMiddleware",
    # Streaming
    "SSEEvent", "StreamReader", "iter_sse", "aiter_sse",
    # Exceptions
    "FluxiumError", "ConnectionError", "TimeoutError", "HTTPError",
    "SSLError", "ProxyError", "TooManyRedirects",
    # Version
    "__version__", "__author__",
]
