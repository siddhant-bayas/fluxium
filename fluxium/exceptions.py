"""Fluxium exception hierarchy."""


class FluxiumError(Exception):
    """Base exception for all fluxium errors."""


class ConnectionError(FluxiumError):
    """Failed to establish a connection."""


class TimeoutError(FluxiumError):
    """Request timed out."""


class HTTPError(FluxiumError):
    """HTTP response with 4xx or 5xx status code."""

    def __init__(self, msg: str = "", response=None):
        super().__init__(msg)
        self.response = response


class SSLError(ConnectionError):
    """SSL/TLS handshake or certificate verification failed."""


class ProxyError(ConnectionError):
    """Proxy connection failed."""


class TooManyRedirects(FluxiumError):
    """Exceeded the maximum number of redirects."""
