# CREAT.md — rolling 24-hour continuity log

**Standing rule** (also recorded in [README.md](README.md)): this file keeps only
the **last 24 hours** of work. Appending a new entry deletes anything older, so
the log stays a continuity hand-off between agents and engineers rather than a
second changelog. Durable history lives in [CHANGELOG.md](CHANGELOG.md).

Introduced by the `CODE-JUNCTION/00 FOR ALL APPS` brief (Phase 2).

---

## Standing rules

- **Rolling window.** Keep the last 24 hours only; delete the stale portion on
  every append.
- **Exempt from duplicate-file removal.** `Attached_Folder/`, `Test_Files/`, and
  any "how to use" guide are never deleted as redundant.
- **Commit identity.** Set it locally before committing:

  ```bash
  git config user.name  "RAJKUMAR SINGH CHAUHAN"
  git config user.email "<maintainer address — see the team password manager>"
  ```

  The address is deliberately **not** written here or in any root doc:
  `tests/docs/test_doc_integrity.py::test_no_pii_in_tracked_docs` rejects a
  personal email in `README.md`, `GUIDE.md`, `CONTRIBUTING.md`, `SECURITY.md`,
  `CODE_OF_CONDUCT.md`, `DOCS_INDEX.md`, and `CHANGELOG.md`.
- **Build stays green.** Every step must leave `make lint`, `make test`, and the
  React console's `typecheck` / `test` / `build` passing.

---

## 2026-10-30

### Workspace

- **Git write deadlock cleared.** `git add`/`commit`/`mv` were failing with
  `Unable to create '.git/index.lock': File exists`. Diagnosis: no live `git`
  process — the `.git/*.lock` files were leftovers from an interrupted
  merge/checkout, and stale duplicate background `pytest -m slow` jobs were
  competing for the same artifacts. Fix: stop the duplicates, then
  `python scripts/clear_stale_locks.py --force` immediately before each write.
- **CODE-JUNCTION retired.** The 52-week corpus plus the 10-day brief were read
  and applied (wave 1) and the staged folder removed; the content now lives in
  `docs/upgrade/` (`00-MASTER-PLAN.md`, `Q1..Q4`, `DEFECT-LEDGER.md`, …).
- **Redundant trees deleted** (all regenerable): `TEST-28102026/`,
  `tests/e2e/random_drawings/`, `.verify/`, `.bridge_repo_pdf_work/`,
  `.vercel/`, `apps/web-console/audit_wc.json`, `_probe_*.py`. `.gitignore`
  extended so `TEST-*/`, `.verify/`, `.bridge_repo_pdf_work/`, `.vercel/` and
  `tests/e2e/random_drawings/` stay out of `git status`.

### Roadmap

- **W01 — repo truth-up.** `ARCHITECTURE.md`, ADR-0001 flipped to Accepted,
  `docs/how-to-use-video.md` (video-form guide, wired into `mkdocs.yml` nav and
  `DOCS_INDEX.md`), `README.md` link fixes, `TEST_DEPLOYMENT_SUMMARY.md` moved
  under `archive/`. (The destructive "rename folder to bridgecad-suite" item was
  deliberately skipped.)
- **W02 — dependency discipline.** `suite-ci.yml` unit job now runs a
  **Python 3.11 + 3.12 matrix**. The root `Dockerfile` builds from
  `requirements.lock` (pinned) instead of the legacy loose `requirements.txt`,
  and both the image `CMD` and the `ci.yml` container smoke now exercise the
  Suite facade `bridgecad` — the legacy `src/bridge_gad` surface is fenced
  (ADR-0001).
- **W03 (partial) — test harness + CI baseline.** Seeded `tests/unit/` with
  **109 pure-function tests** over `bridgecad_core` (coordinate transforms,
  pile-group layouts, span/pier contract, quantities, validation scoring,
  clause registry, costs, enums) plus **6 CORS tests** pinning the gateway's
  KERO-001 hardening (115 in `tests/unit`). This also repairs `make test`,
  whose target (`pytest packages tests/unit -q`) pointed at a directory that
  did not exist. Coverage ratchet set: `[tool.coverage.report] fail_under = 75`
  in `pyproject.toml`, and `[tool.coverage.run] source = ["packages"]` so a
  bare `--cov` measures exactly what the CI job's `--cov=packages` does; the
  CI unit selection measures **75.80%**. `ruff format --check` was failing on
  18 files — a red `lint` job that gates the whole suite chain — and is now
  clean. `make lint` / `make format` now use the CI scope (`packages apps
  scripts`) instead of `ruff check .` (2387 phantom errors from fenced legacy
  trees); new `make cov` target runs the CI unit selection with the ratchet.
- **KERO-001 ported to the active gateway.** `apps/api-gateway/bridgecad_api/
  main.py` shipped `allow_origins=["*"]` with `allow_credentials=True` —
  insecure, browser-rejected, and contradicting `README_RAJKUMAR.md` §2
  ("enforced in code"). The legacy `src/bridge_gad/api.py` hardening is now in
  the Suite: origins come from `API_CORS_ORIGINS`, a wildcard is refused when
  `ENV=production`, and `allow_credentials` is `False`.
- **Reviewer briefs verified closed.** The `sample-gad-drawings/` patches'
  concrete gaps are closed: PII scan uses `git grep` over tracked files (1),
  `suite-ci.yml` is at repo root, not nested (2), `readme = "README.md"`
  resolves (3), the README orientation table fences the legacy generation (6),
  and the gateway ZIP path uses `NamedTemporaryFile` via `_staged_zip_response`
  instead of `mktemp()` (7). Gaps 4–5 (sheet completeness, BOQ traceability) are
  the roadmap weeks, tracked in `docs/upgrade/`.

### Verification

- `ruff check packages apps scripts` clean · `ruff format --check packages apps
  scripts` clean (was 18 files red) · `scripts/verify_docs.py --json`
  pass 3 / fail 0 · fast suite `734 passed` (test_visual deselected) ·
  slow mutation gate `16 passed` in 32:19 · Q1-W1 exit gate
  `dump_dxf_facts.py --selftest` green.
- W03 evidence: `tests/unit` 115 passed · CI unit selection `156 passed`,
  coverage **75.80% ≥ 75** ("Required test coverage of 75.0% reached") ·
  `make test` 534 passed.
- GitHub repo page given a description + 14 topics; Streamlit console boots
  (`/_stcore/health` → 200 `ok`).

### Not taken (explicitly out of scope this pass)

- Roadmap W03 remainder (mypy/ruff as *required* PR checks, one green `main`
  run), V&V framework (W04+), sheet coordinate contract migration weeks 5–13.
- Independent-engineer sign-off; Netlify link (needs `NETLIFY_AUTH_TOKEN`).
- Rendering the actual `docs/assets/how-to-use.mp4` (storyboard + player only).

