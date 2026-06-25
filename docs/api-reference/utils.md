# Utils

`fluxium/utils.py`

## Functions

| Function | Returns | Description |
|---|---|---|
| `encode_url(url, params=None)` | `str` | IDNA-encode hostname + append query params |
| `netrc_credentials(host)` | `tuple[str, str] \| None` | Read credentials from `~/.netrc` |
| `merge_headers(*dicts)` | `dict` | Merge header dicts, lowercase keys |

## encode_url

```python
encode_url("https://example.com/path", {"q": "hello world", "page": 1})
# "https://example.com/path?q=hello+world&page=1"

encode_url("https://münchen.de/path")
# "https://xn--mnchen-3ya.de/path"
```

## netrc_credentials

```python
netrc_credentials("api.example.com")
# ("username", "password") or None
```

Results are cached per host — netrc file is read at most once.

## merge_headers

```python
merge_headers(
    {"Accept": "application/json"},
    {"Authorization": "Bearer xxx"}
)
# {"accept": "application/json", "authorization": "Bearer xxx"}
```

Later dicts override earlier ones. All keys are lowercased.
