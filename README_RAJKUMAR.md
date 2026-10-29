# README_RAJKUMAR.md — operator handbook

Day-to-day setup, run, test and deploy notes for the maintainer. The project's
public front door is [README.md](README.md); the authoritative technical
document is [GUIDE.md](GUIDE.md). This file is the operator's companion —
shortcuts, the exact commands that gate a release, and the repo settings that
live outside git.

---

## 1. What this repository is

One parametric Excel workbook in. A seven-sheet standards-compliant bridge GAD
package, a priced Bill of Quantities and a QA compliance report out. Nine Python
packages (`core`, `io`, `draw`, `bill`, `qa`, `export`, `plugins`, `ai`, `infra`)
behind four interfaces: a Typer CLI, a FastAPI gateway, a Streamlit console and a
React web console.

Authoritative detail: [GUIDE.md](GUIDE.md). Documentation map:
[DOCS_INDEX.md](DOCS_INDEX.md).

---

## 2. Setup

### Python

```bash
git clone https://github.com/CRAJKUMARSINGH/BridgeCAD-Enterprise-Suite.git
cd BridgeCAD-Enterprise-Suite

python -m bridgecad info        # interpreter, repo root, resolved paths
python -m bridgecad verify      # acceptance verifiers
```

`sitecustomize.py` bootstraps the workspace, so the checks above run with no
install. For development, install editable with dev extras:

```bash
pip install -e ".[dev]"
```

Runtime pins live in [requirements.txt](requirements.txt); documentation-only
pins live in [docs/requirements-docs.txt](docs/requirements-docs.txt).

### React console

```bash
cd apps/web-console
npm ci
npm run dev        # http://localhost:5173
```

The console expects the API on `http://localhost:8000`. Point it elsewhere with
`VITE_API_BASE_URL` in `apps/web-console/.env.local`.

### Environment

```bash
cp .env.example .env
```

Two variables matter operationally and are enforced in code:

| Variable | Effect |
|---|---|
| `ENV` | Set to `production` to require an explicit CORS allowlist |
| `API_CORS_ORIGINS` | Comma-separated origins; a wildcard is refused in production |

---

## 3. One-click run

```bash
make api     # FastAPI on :8000, health at /health
make web     # React console on :5173
make ui      # Streamlit console
```

Both the API and the console can be started from Docker instead:

```bash
docker compose up api
```

---

## 4. Deploy

```bash
cp .env.example .env
docker compose -f docker-compose.prod.yml up -d     # full production stack
```

The React console is deployed to Netlify using [netlify.toml](netlify.toml)
(SPA redirects, cache and security headers, pinned runtime). Full walkthrough:
[docs/deployment.md](docs/deployment.md). If a deploy misbehaves, start with
[docs/troubleshooting.md](docs/troubleshooting.md).

---

## 5. Test and gate commands

Everything a release must pass, in the order it usually fails:

```bash
make lint                 # ruff check
make typecheck            # mypy packages apps
make test                 # unit tests
make wing                 # Wing geometry + drawing suite
make test-integration     # full pipeline
make test-e2e             # 28 fixtures x 7 checks
make smoke                # rc1_smoke.py release gate
make verify-docs          # documentation integrity + path gates
make docs-check           # external and internal links, doc paths
```

Two gates worth knowing about because they are easy to trip:

- `python scripts/pin_golden.py` — rebuilds the canonical model for every golden
  case and diffs it against `tests/draw/golden/pins/`. A change that legitimately
  moves the model needs `--regenerate` and the reason in the pull request.
- `lint-imports --config import_linter_contract.ini` — enforces the GUIDE.md §3
  architecture invariants. It analyses the real import graph, so the workspace
  must be installed first.

React console gates:

```bash
cd apps/web-console
npm run typecheck && npm test && npm run build
```

---

## 6. Repository settings not stored in git

### Git identity (local only)

```bash
git config user.name  "RAJKUMAR SINGH CHAUHAN"
git config user.email "<maintainer address — team password manager>"
```

The address is deliberately not committed anywhere. Root docs are scanned for
personal email and phone numbers, and that check is intentional.

### GitHub Topics

Topics are a repository setting, not a file — set them once in
**Settings → General → Topics**:

```text
bridge-engineering   bridge-design-automation   irc-standards
morth                morth-schedule-of-rates
parametric-design    dxf-generation             engineering-cad
python               fastapi                    react-vite
```

### Repository description

```text
One parametric Excel workbook in — seven-sheet IRC/MORTH bridge GAD drawings,
a priced Bill of Quantities and a QA compliance report out.
```

### Pull-request title for the reach pass

```text
🚀 Max-Reach Polish: Beautiful README + Professional Repo Enhancement
```

---

## 7. Where to look when something is off

| Symptom | Start here |
|---|---|
| A doc gate fails | `python scripts/verify_docs.py --json` |
| The Wing suite fails | `make wing-report` — per-sheet structural report |
| A golden pin drifted | `python scripts/pin_golden.py <slug>` — prints the field diff |
| An import contract broke | `lint-imports --config import_linter_contract.ini -v` |
| The release gate fails | `python rc1_smoke.py` — names the failing check |
| Stale git locks block a commit | `python scripts/clear_stale_locks.py` |

---

## 8. Continuity

Working-session hand-off lives in [CREAT.md](CREAT.md) and keeps only the last
24 hours. Durable history lives in [CHANGELOG.md](CHANGELOG.md); plan-level
status lives in [MASTER_ROADMAP.md](MASTER_ROADMAP.md).
