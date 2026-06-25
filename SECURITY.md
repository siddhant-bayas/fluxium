# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 2.0.0 | Yes |
| 1.0.0 | No (critical retry bug, upgrade recommended) |

## Reporting a Vulnerability

To report a security vulnerability, please open a GitHub issue with the `security` label or contact the maintainer directly at the email listed on the GitHub profile.

Do not disclose security issues publicly until a fix is released.

## Known Issues

- **v1.0.0 retry bug**: The retry mechanism in v1 does not trigger due to a boolean evaluation bug. Fixed in v2.0.0. Users on v1 should upgrade immediately.
