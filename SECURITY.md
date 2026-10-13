# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.0-rc1 | ✅ Yes (current) |
| < 0.1.0 | ❌ No |

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Report security issues by emailing **security@bridgecad.io** with:

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact assessment
4. Suggested fix (if known)

You will receive an acknowledgement within **48 hours** and a full response within **7 business days**.

## Scope

In scope:
- Remote code execution via malicious Excel upload
- Path traversal in file output paths
- API key / authentication bypass
- SQL injection in database queries
- SSRF in export endpoints

Out of scope:
- Theoretical / unproven attack vectors
- Issues requiring physical access
- Social engineering attacks
- Issues in dependencies (report upstream)

## Security Architecture

- **File uploads** are written to a temporary directory and deleted after processing. Maximum size: 50 MB.
- **API keys** are stored only in environment variables, never in code or database.
- **Docker containers** run as non-root users.
- **SQL queries** use SQLAlchemy ORM with parameterised queries — no raw SQL interpolation.
- **Output paths** are validated against a configured `OUTPUT_DIR` before writing.

## Disclosure Policy

We follow [Responsible Disclosure](https://en.wikipedia.org/wiki/Responsible_disclosure). We will:
- Acknowledge your report promptly
- Work with you to understand and reproduce the issue
- Credit you in the release notes (unless you prefer anonymity)
- Not pursue legal action for good-faith security research
