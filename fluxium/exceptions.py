"""Fluxium exception hierarchy and warnings."""


class FluxiumWarning(UserWarning):
    """Base warning for fluxium deprecations and non-fatal issues."""


class InsecureSSLWarning(FluxiumWarning):
    """Warning when TLS verification is disabled."""


class RetryWarning(FluxiumWarning):
    """Warning emitted before a retry attempt."""

    def __init__(self, attempt: int, max_retries: int, url: str, reason: str):
        self.attempt = attempt
        self.max_retries = max_retries
        self.url = url
        self.reason = reason
        super().__init__(f"Retry {attempt}/{max_retries} for {url}: {reason}")


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
