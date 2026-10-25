# Security policy

BridgeCAD Enterprise Suite ingests untrusted spreadsheets and emits files that
get opened in CAD software and shared with clients. Both ends are attack surface.

---

## Supported versions

| Version | Supported | Notes |
|---|---|---|
| `main` | ✅ | All fixes land here first |
| `0.1.0-rc1` | ✅ | Current release candidate |
| `0.0.1` | ⚠️ | Critical fixes only |
| Legacy `src/bridge_gad/` | ⚠️ | Best effort — no new features |

This is pre-1.0 software. Expect the API and the workbook schema to move.

---

## Reporting a vulnerability

**Preferred: GitHub private advisory.**
→ https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite/security/advisories/new

It gives you a private fork, threaded discussion and CVE issuance without
needing an email address in the source tree.

**Do not open a public issue for a vulnerability** unless you are confident it
is informational only.

### What to include

- Affected version or commit
- The entry point — CLI, API, Streamlit, React, or library import
- A minimal reproduction: input file, exact command or HTTP request
- Impact, and who is affected (single user, self-hosted, multi-tenant)
- Your assessment of severity, and your reasoning
- Whether you intend to submit a fix

Attach the input file if you can. Most of our surface is file-driven, so the
file usually *is* the reproduction.

### Timelines

| Stage | Target |
|---|---|
| Acknowledgement | 3 business days |
| Triage and severity assessment | 7 business days |
| Fix for critical / high | 30 days |
| Fix for medium / low | next release |
| Public disclosure | after fix ships, or 90 days, whichever is first |

If we go quiet past a deadline, chase us on the advisory thread. Pre-1.0
maintenance is not full-time and we would rather be nudged than drift.

### Disclosure

Coordinated. We publish a GitHub Security Advisory with a CVE where warranted,
and credit you by name or handle unless you prefer otherwise. If you want to
publish first, tell us and we will work to your date.

### Safe harbour

Good-faith research is not treated as infringement. In particular: do not
worry about the exact scope of a test file you uploaded, and do not worry about
hammering a self-hosted instance while testing.

---

## Scope

### In scope

| Surface | Why |
|---|---|
| `bridgecad_io` — Excel parsing | Untrusted input. zip + XML + openpyxl. |
| Upload endpoints (`/bridges`, `/draw`, `/bills`, `/qa`, `/exports`) | Untrusted input over HTTP |
| `bridgecad_export` — ZIP generation | Member names, path traversal, collisions |
| Temp-file handling in the API | Staging, cleanup, TOCTOU |
| `bridgecad_infra.auth` | API keys, role ladder |
| Input validators (`scale`, `prefix`, `state`) | Unvalidated values reaching the drawing and filesystem layers |
| Dependency supply chain | Pinned lockfile, `pip-audit` in CI |
| Streamlit and React front ends | XSS, CSRF, session handling |
| `nginx/prod.conf` | TLS, headers, upload limits |

### Out of scope

- A self-hosted instance with default credentials left unchanged
- Denial of service from a genuinely enormous but valid workbook (report it, but it may be "expected")
- Anything requiring a compromised dependency to already be installed
- The legacy app's quirks unless they have a security impact
- Findings from an unpatched OS or Python runtime

---

## Known posture — what is already hardened

Documented so you do not re-report these as new:

- **Temp files.** Replaced `tempfile.mktemp()` with `NamedTemporaryFile(delete=False)`
  plus a `BackgroundTasks` cleanup callback. Fixes both the TOCTOU race and the
  unbounded `/tmp` growth.
- **Input validation.** `scale` is range-checked to 10–2500; `prefix` is
  sanitised against path separators, control characters and `<>:"|?*`, then
  truncated to 32 chars.
- **Error leakage.** Validation `HTTPException`s are re-raised rather than
  re-wrapped as generic 500s, so messages are intentional.
- **API key comparison.** Constant-time verification, with a strict
  `admin > engineer > viewer` role ladder.
- **CI.** `pip-audit` runs and distinguishes "vulnerabilities found" from "audit
  itself failed", so neither is silently green.
- **Secrets.** `.env` never committed; `.env.example` documents every variable.
- **PII.** Tracked source carries no contact details, scanned in CI.

---

## Known gaps — open, and fair game

Beating us to these is a valid report:

| Gap | Impact |
|---|---|
| **No upload size cap in the app** | A large workbook is buffered fully. nginx caps at 50 MB but direct-to-uvicorn bypasses it. |
| **No file-type allowlist** | `.xls`, `.xlsm` and arbitrary bytes reach the parser. Should 415 before reading. |
| **ZIP member names not validated on read** | An `.xlsx` is a ZIP. Member paths are not checked for `../` traversal or absurd expansion ratios (zip bomb). |
| **No rate limiting** | API and Streamlit are unthrottled. |
| **No per-resource authorisation** | The role ladder is global. No project-level ACLs. |
| **Error responses are not RFC 7807** | Plain `detail=str(exc)`. Inconsistent and harder to parse. |
| **No request-size or timeout limits on generation** | A pathological workbook can hold a worker. |
| **Artifacts stored on local disk by default** | Multi-instance deploys need the S3 adapter configured, or state diverges. |

---

## Severity

We use CVSS v3.1 base score as a guide, adjusted for this domain:

| Severity | CVSS | Example |
|---|---|---|
| Critical | 9.0–10.0 | RCE from a crafted workbook; auth bypass |
| High | 7.0–8.9 | Arbitrary file write via ZIP member; key leakage |
| Medium | 4.0–6.9 | DoS from a valid workbook; traversal limited to a temp dir |
| Low | 0.1–3.9 | Info disclosure with no privilege change |

Engineering output is also a correctness surface: a value that is unsafe rather
than merely wrong can be rated higher than its CVSS suggests. Say so in your
report and we will weigh it.

---

## What is *not* a vulnerability

- Text-rendering warnings in generated PDFs.
- Sheets 2–7 being scaffolds — documented limitation, not a defect.
- BOQ figures being `estimated` rather than `verified` — see GUIDE.md §11.
- A QA score below 100 on a stock template. Templates are typical, not optimal.
- `DeprecationWarning` noise from third-party libraries.

---

## Credits

Reporters are credited in the advisory and in `CHANGELOG.md` under `Security`.
Thank you — pre-1.0 projects live on this.
