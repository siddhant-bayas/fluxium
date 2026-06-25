# Contributing to Fluxium

## Setup

```bash
git clone https://github.com/siddhant-bayas/fluxium.git
cd fluxium
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Development

### Linting

```bash
ruff check fluxium/
ruff format --check fluxium/
```

### Type checking

```bash
mypy fluxium/
```

### Testing

```bash
# Unit tests only (no network)
pytest tests/ -k "not network"

# All tests (requires network for httpbin.org)
pytest tests/
```

### Pre-commit hooks

```bash
pre-commit install
pre-commit run --all-files
```

## Code Style

- Python 3.9+ compatible
- Type hints on all public APIs
- `__all__` in `__init__.py` for public surface control
- `from __future__ import annotations` in all modules
- 100 char line length (ruff)

## Pull Request Checklist

1. Code passes `ruff check` and `ruff format --check`
2. `mypy fluxium/` passes with no errors
3. All unit tests pass (`pytest tests/ -k "not network"`)
4. New features include tests
5. Public API changes are documented in `docs/api.md`
6. Breaking changes documented in `docs/changelog.md`

## Release

1. Update version in `fluxium/__version__.py` and `pyproject.toml`
2. Update `docs/changelog.md`
3. Push a GitHub release (tag `v2.x.x`)
4. CI automatically publishes to PyPI via trusted publishing
