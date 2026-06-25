"""
Fluxium — A fast, versatile HTTP library.
Author: Siddhant Bayas
"""

from .__version__ import __author__, __version__
from .api import (
    adelete,
    aget,
    ahead,
    aoptions,
    apatch,
    apost,
    aput,
    arequest,
    delete,
    get,
    head,
    options,
    patch,
    post,
    put,
    request,
)
from .auth import BasicAuth, DigestAuth  # noqa: F401
from .cache import DiskCache, HishelCache, MemoryCache
from .cookies import CookieJar
from .exceptions import (
    ConnectionError,
    FluxiumError,
    FluxiumWarning,
    HTTPError,
    InsecureSSLWarning,
    ProxyError,
    RetryWarning,
    SSLError,
    TimeoutError,
    TooManyRedirects,
)
from .middleware import (
    LoggingMiddleware,
    Middleware,
    RateLimitMiddleware,
    RetryMiddleware,
)
from .models import Request, Response  # noqa: F401
from .oauth2 import BearerAuth, OAuth2Auth  # noqa: F401
from .session import AsyncSession, Session
from .streaming import SSEEvent, StreamReader, aiter_sse, iter_sse
from .timeout import Timeout

__all__ = [
    "AsyncSession",
    "ConnectionError",
    # Cookies
    "CookieJar",
    "DiskCache",
    "FluxiumError",
    # Exceptions
    "FluxiumWarning",
    "HTTPError",
    "HishelCache",
    "InsecureSSLWarning",
    "LoggingMiddleware",
    # Caching
    "MemoryCache",
    # Middleware
    "Middleware",
    "ProxyError",
    "RateLimitMiddleware",
    "RetryMiddleware",
    "RetryWarning",
    # Streaming
    "SSEEvent",
    "SSLError",
    "Session",
    "StreamReader",
    # Timeout
    "Timeout",
    "TimeoutError",
    "TooManyRedirects",
    "__author__",
    # Version
    "__version__",
    "adelete",
    "aget",
    "ahead",
    "aiter_sse",
    "aoptions",
    "apatch",
    "apost",
    "aput",
    "arequest",
    "delete",
    # Core
    "get",
    "head",
    "iter_sse",
    "options",
    "patch",
    "post",
    "put",
    "request",
]
