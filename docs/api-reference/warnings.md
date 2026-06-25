# Warnings

`fluxium/exceptions.py`

## FluxiumWarning

```python
class FluxiumWarning(UserWarning):
    """Base warning for fluxium deprecations and non-fatal issues."""
```

Base class for all fluxium warnings.

## InsecureSSLWarning

```python
class InsecureSSLWarning(FluxiumWarning):
    """Warning when TLS verification is disabled."""
```

Emitted automatically when `verify=False`:

```python
import warnings

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    s = fluxium.Session(verify=False)
    # w[0].category == InsecureSSLWarning
```

## RetryWarning

```python
class RetryWarning(FluxiumWarning):
    def __init__(self, attempt: int, max_retries: int, url: str, reason: str)
```

Emitted before retry attempts (when configured).

## Usage

```python
import warnings

# Show all fluxium warnings
warnings.simplefilter("always", fluxium.FluxiumWarning)

# Ignore insecure SSL warnings
warnings.filterwarnings("ignore", category=fluxium.InsecureSSLWarning)
```
