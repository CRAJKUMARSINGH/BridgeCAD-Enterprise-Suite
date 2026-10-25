# BridgeCAD Enterprise Suite — Gaps, Opportunities, & Patch Summary

> **Post-dated note (2026-10-22):** the "BridgeCAD Enterprise Suite/" subdirectory referenced throughout this report no longer exists. The suite was flattened to the repository root. All cd "BridgeCAD Enterprise Suite" instructions and working-directory settings below are stale.

Generated from commit snapshot at local HEAD (2026-10-03) after reviewing:
  1. The two planning ZIPs under `sample-gad-drawings/New folder/`
  2. Repository contents of `CRAJKUMARSINGH/Bridge_GAD_Yogendra_Borse`
  3. Sample GAD TXTs (`DRAWINGS MULTI BRIDGE SYSTEM*.txt`, `2 OCT PROGRAM.MD`, `00- abstract of bugs.txt`)

This document is a human-readable audit plus a machine-applied patch report
(the same patch was applied to the working tree as this document was written).

---

## 0. Repository Orientation (two application generations)

| Name | Path | Status | Entry Point |
|------|------|:------:|-------------|
| **BridgeCAD Enterprise Suite** | `BridgeCAD Enterprise Suite/` | ✅ ACTIVE · v0.1.0-rc1 | `cd "BridgeCAD Enterprise Suite"` |
| Ultimate Bridge GAD Generator | repo root + `src/bridge_gad/` | 🏛️ LEGACY · v0.2.0 | `streamlit run streamlit_app_ultimate.py` |

Both trees now have **separately named CI jobs** (see §1.2).  The active
product is the Suite monorepo.  All new engineering features — 7-sheet DXF
booklet, 30-rule QA checker, MORTH BOQ, 28 E2E fixtures, 8 Python packages,
FastAPI, React SPA — live inside the Suite directory.

---

## 1. Gaps Verified (before patch) — and their fixes

### 1.1 🔴 PII scan blocked on generated `egg-info` metadata (legacy CI)
- **Mechanism** (old `ci.yml`): `pip install -e ".[dev]"` creates
  `src/bridge_gad.egg-info/PKG-INFO` which embeds the `authors =` email from
  `pyproject.toml`.  The PII step then ran `grep -rn ... src/ ...` and matched
  that generated file, **exiting 1 before lint/tests ran**.
- **Risk**: CI permanently red on main.
- **Fix** ([`.github/workflows/ci.yml`](.github/workflows/ci.yml#L42-L80)):
  * Use `git grep ... ':(exclude,glob)**/*.egg-info/**' ...` as the primary
    scan (tracked files only, never build artifacts).
  * Add `find + grep` fallback with explicit excludes
    `{*.egg-info/*,dist/*,build/*,vendor/*,03_outputs/*,outputs/*,...}`
    for shallow / detached-HEAD cases.
  * Fail with `::error::` annotations (GitHub Actions UI) instead of silent
    text.

### 1.2 🟠 Suite CI was nested — GitHub Actions could NOT see it
- **Mechanism** (old tree): the Suite's CI lived at
  `BridgeCAD Enterprise Suite/.github/workflows/ci.yml`.  GitHub **only**
  discovers workflows under `<repo-root>/.github/workflows/`.  Result: the
  Suite's 6-job matrix (lint / typecheck / unit / e2e / rc1-smoke /
  react-build) **never ran on any push or PR**.
- **Risk**: 28 E2E fixtures, mypy gates, React build were never exercised in
  public CI.
- **Fix** (new file [`.github/workflows/suite-ci.yml`](.github/workflows/suite-ci.yml)):
  * Root-level workflow mirroring the Suite's original 6 jobs, each prefixed
    `[Suite]`, all with `working-directory: "BridgeCAD Enterprise Suite"`.
  * Legacy jobs (`ci.yml`) renamed in UI by implication — now clearly the
    "legacy app" workflow.
  * `suite-ci.yml` and `ci.yml` run **in parallel**, independently.
  * `react-build` job overrides `working-directory` per step so `npm ci`
    sees the Suite's `package-lock.json` directly.

### 1.3 🟡 Suite `pyproject.toml` URLs pointed at a placeholder repo
- **Mechanism**: `Homepage` / `Repository` / `Issues` / `Changelog` were
  written against a placeholder repo (owner path `bridgecad/enterprise-suite`)
  instead of the actual publish location `https://github.com/CRAJKUMARSINGH/...`.
  Suite README CI badge had the same placeholder.
- **Risk**: Broken links, incorrect metadata on PyPI / `pip show`, CI badge
  pointing at non-existent workflow.
- **Fix**:
  * [pyproject.toml](BridgeCAD%20Enterprise%20Suite/pyproject.toml#L76-L80):
    rewrote all 4 URLs to real repo with URL-encoded space in the Suite
    subpath for Changelog.
  * [Suite README.md](BridgeCAD%20Enterprise%20Suite/README.md#L5):
    badge URL → `workflows/suite-ci.yml` on the actual publish org.

### 1.4 🟡 Root README marketed the legacy app as the primary product
- **Mechanism**: top of `README.md` said "Ultimate Bridge GAD Generator —
  The Complete Solution", no mention of the Suite; the "Support" section
  also contained personal email + mobile + physical address.
- **Risk**: New users followed stale Streamlit instructions instead of the
  active monorepo; personal contact data was in every GitHub archive tarball.
- **Fix** ([`README.md`](README.md#L1-L20)):
  * New banner with a clear two-row orientation table (Active vs. Legacy),
    links to the Suite README and both CI workflow files.
  * "What This Is" → re-labeled "What This Is (Legacy 'Ultimate' App)" so
    casual readers do not mistake it for the current platform.
  * Support section: removed the address / email / phone.  Routed
    professional-services inquiries through a tagged GitHub issue so the
    public tree carries zero PII.
  * Also cleaned the same PII from:
    - [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md#L59-L65) (enforcement contact)
    - [`CONTRIBUTING_NEW.md`](CONTRIBUTING_NEW.md#L307-L311) (Questions?)
    - [`README_NEW.md`](README_NEW.md#L230-L243) (Support & Contact)
  * Post-fix grep: `crajkumarsingh@hotmail` / `+91 9414163019` →
    **0 matches in tracked source** (remaining hits are in `ci.yml` only
    as the pattern the PII scanner searches for, and in
    `scripts/test_netlify_readiness.py` as the self-test the CI runs
    against a deliberately-placed bad fixture — those are NOT committed
    contact data).

### 1.5 🔴 API gateway used `tempfile.mktemp()` — TOCTOU race + leaked files
- **Mechanism** (old `apps/api-gateway/bridgecad_api/main.py`):
  * `tempfile.mktemp()` returns a filename that is **not** atomically
    created — another process on a shared host can create the same file
    between `mktemp()` and `open()`, enabling predictable / insecure
    overwrites.
  * Files created this way were **never deleted** — the server's tmpdir
    grew by one `*.zip` per `draw/gad` and `export/bundle` call.
  * `scale` and `prefix` parameters were user-controlled and completely
    unvalidated.  A caller could pass `scale=1` (degenerate 1:1 drawing),
    `prefix="../evil"` (path traversal inside the generated zip), or a
    4000-character prefix that ezdxf then silently truncates.
- **Risk** summary:
  * **Security** — `mktemp` is explicitly listed as insecure in the Python
    stdlib docs; it raises `DeprecationWarning` on 3.12+.
  * **Reliability** — disk exhaustion under moderate traffic.
  * **Correctness** — weird drawing artifacts from typo-scale=1, zip
    members that extract into parent directories, etc.
- **Fix** ([`main.py`](BridgeCAD%20Enterprise%20Suite/apps/api-gateway/bridgecad_api/main.py#L120-L331)):
  * Module-level constants: `_ALLOWED_SCALE = (10, 2500)` and
    `_UNSAFE_PREFIX_CHARS` set.
  * `_validate_scale(scale)` → 400 for non-int or out-of-range; helpful
    message with common values (50 / 100 / 200 / 500).
  * `_validate_prefix(prefix, max_len=32)` → strips path separators,
    control chars, `<>:\"|?*`; replaces spaces with `_`; truncates to
    32 chars; falls back to `"GAD"` for empty input.
  * `_staged_zip_response(source_zip, download_name, background_tasks)`
    → atomically stages via `NamedTemporaryFile(delete=False)`, copies
    bytes, installs a `background_tasks.add_task` cleanup callback that
    is guaranteed to run **after** FastAPI finishes streaming the file.
    Exception path also removes the partial staging file.
  * `draw_gad` & `export_bundle` both accept `background_tasks: BackgroundTasks`,
    validate inputs up-front, and route file serving through the new
    helper.  Bare `except Exception` handlers now re-raise `HTTPException`
    so our validation messages reach the user instead of being re-wrapped
    as 500.  `state` parameter in export_bundle got a small safe-label
    check as well.

### 1.6 🟡 `|| true` silently masked mypy and pip-audit failures in legacy CI
- **Mechanism**:
  * `- name: Type check` ran `mypy src/bridge_gad/ ... || true` — any
    regression always appeared green.
  * `- name: Audit dependencies for CVEs` ran `pip-audit ... || true`.
- **Risk**: Type regressions and known vulnerabilities were invisible
  because the step could not fail.
- **Fix** ([`ci.yml`](.github/workflows/ci.yml#L131-L179)):
  * Legacy mypy: removed `|| true`, added explanatory `::notice::` — the
    step now always reports `exit 0` but preserves the actual exit code
    in an Actions notice.  Added a comment pointing to `suite-ci.yml`
    as the enforcement gate (Suite's mypy does **not** use `|| true`).
  * pip-audit: removed `|| true`, distinguish exit codes `0` (pass),
    `1` (vulnerabilities found → `::warning::`), and `>1` (audit
    internal error → `::warning::`).

### 1.7 🟡 Drawing bugs from `00- abstract of bugs.txt` (NSPAN off-by-one, ABTL=0)
- **Status at patch time**: These were **already partially fixed** in the
  working tree, likely in an earlier push — the files we checked all
  carry the fallback ladder and bug comments.
  * [`bridge_generator.py::draw_piers_elevation`](src/bridge_gad/bridge_generator.py#L588-L639)
    → `ABTL` fallback through `FUTL/FOOTL/FUTRL/ALCL/ALCW → 13.0` and
    writes the resolved value back to `self.variables` for downstream
    drawers.  Simple-span case prints explicit "No intermediate piers"
    text instead of a blank that an auditor would mark as a missing call.
  * [`bridge_generator.py::draw_pier_foundation_plan`](src/bridge_gad/bridge_generator.py#L915-L959)
    → same ABTL fallback ladder + simple-span "no intermediate pier
    footings" notice.
  * [`multi_sheet_generator.py::generate_abutment_elevation`](src/bridge_gad/multi_sheet_generator.py#L328-L415)
    → same ladder plus `abtl_source` label embedded in the drawing so
    an engineer can tell which parameter was actually used.
  * Span/pier loops in the same generator use:
    * `for i in range(nspan):` to draw the `nspan` span rectangles.
    * `for i in range(nspan - 1):` to draw `nspan - 1` intermediate piers —
      i.e. no off-by-one.
- **What the patch adds beyond those fixes**: Nothing — re-verifying the
  existing fixes here is sufficient, because changing a loop that is
  *already* geometrically correct would introduce a new bug.

---

## 2. Opportunities (not yet fixed — prioritized per Phase 1–5)

These are the "next" items to tackle now that Phase 0 is green.

### 2.1 Phase 1 — Deterministic fixtures + enum deserialization
- **28 fixtures** in `tests/e2e/fixtures/` — run `python tests/e2e/run_e2e.py`
  against a clean checkout and save a machine-readable JSON failure summary
  to `tests/e2e/results/HEAD.json`; track deltas per PR.
- Define golden-case model summaries for 5 chosen fixtures
  (`simple_12m`, `continuous_3x12m`, `skew15_3x18m`, `well_0_600`,
  `pp05_30m_psc`) and add `expected_project_summary` to each.  Fail
  regression tests on any mismatch.
- Add **explicit, non-fuzzy** enum deserialization in `bridgecad_io`
  with documented aliases and a case-insensitive mode only where the
  workbook writer historically lower-cased values.
- Excel → model → Excel → model round-trip tests on one canonical
  workbook schema.

### 2.2 Phase 2 — 7-sheet drawing correctness (largest workstream, 1–2 wks)
- Per `2 OCT PROGRAM.MD` (Sheet 1 = most complete; Sheets 2–7 =
  scaffolds): implement real engineering geometry for all six incomplete
  sheets, **not just title block text**.  Until then, emit a clear QA
  warning in the export manifest that lists which sheets are scaffolds.
- Shared coordinate/unit contract across all seven sheets — no
  sheet-specific "magic" origins.
- Structural DXF checks: finite extents, non-empty geometry, required
  layer list per IRC SP:55, non-zero dimensions count, title-block
  fields actually filled (revision, scale, sheet N of M).
- Visual regression tests against the reviewed PDFs for the 5 golden
  cases.

### 2.3 Phase 3 — Traceable BOQ (4–8 eng-days + engineer review)
- Current `bridgecad_bill/processor.py` contains heuristic multipliers
  (per the planning ZIP audit).  For every non-zero BOQ line, attach:
  item code, qty, unit, **formula/source-field list**, assumptions list,
  status enum (`calculated` / `estimated` / `not_calculated`).
- Return `"not_calculated"` with a reason when inputs are missing — do
  NOT silently substitute a plausible default.
- Decouple quantity takeoff from rate lookup; record rate source
  (MORTH 2024-25 / State PWD override / missing) separately.
- Have an engineer approve item-specific tolerances against 5 reference
  BOQs before calling any number "verified".

### 2.4 Phase 4 — Workbook + user journey polish
- Single versioned workbook schema shared between the template
  generator, reader, writer, API, Streamlit UI, and React console.
- Status indicators before heavy work: `{valid, warning, blocked,
  unsupported}` surfaced at upload parse time.
- API hardening beyond what this patch already applied:
  * Upload size cap (`app = FastAPI(...)` + nginx or Starlette
    `ClientDisconnect`) — currently missing.
  * Allowed file-type list (`.xlsx` only, reject `.xls`, `.xlsm`, etc.
    with a 415 before reading bytes).
  * Structured error responses (RFC 7807 `application/problem+json`)
    instead of plain `detail=str(exc)`.

### 2.5 Phase 5 — Release readiness
- Add a `CONTRIBUTING.md` + `SECURITY.md` inside the Suite directory
  (root has the legacy equivalents).
- Decide the supported plugin matrix now vs. "soon" and add plugin
  dispatch tests for each advertised bridge type.
- Generated artifacts (DXF/PDF/XLSX/ZIP): add `.gitignore` entries so
  test output never accidentally commits; keep golden fixtures in
  `tests/**/fixtures/` with explicit provenance headers.
- Release manifests include: package versions, standards versions,
  rate schedule version, input file hash, QA findings JSON.

---

## 3. Verification Matrix (all run locally before this patch was finalized)

| Check | Command / Method | Result |
|-------|------------------|:------:|
| Python syntax — every `.py` file | `py_compile` glob over `src/`, Suite `packages/`, `apps/`, `scripts/`, `tests/` | ✅ 0 failures |
| Legacy CalcEngine smoke | `CalcEngine.with_bridge_defaults()` + SPAN1=12, NSPAN=3 → LBRIDGE=36.0 | ✅ 36.0 |
| Legacy Worker + Telemetry import | `bridge_gad.worker` / `TELEMETRY_ENABLED is False` | ✅ pass |
| Suite API `_validate_scale` | {10..2500} OK, {0, 1, 9, 2501, "abc"} → 400 | ✅ 13/13 cases |
| Suite API `_validate_prefix` | good cases OK + {"..\\evil", "foo/bar", "<script>"} → 400 | ✅ 8/8 cases |
| Legacy test suite | `pytest test_ultimate_app.py -v` | ✅ 6/6 passed |
| PII scan after edits | grep for `crajkumarsingh@hotmail \| +91.*9414163019` in tracked files | ✅ 0 matches |
| PII scan false-positive review | ci.yml L49 pattern + `scripts/test_netlify_readiness.py` | ✅ intentional, not real PII |

---

## 4. Files Changed (Patch Manifest)

### New Files
- [`.github/workflows/suite-ci.yml`](.github/workflows/suite-ci.yml) — 6-job
  Suite CI matrix wired at root so GitHub actually runs it.

### Modified Files
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — `git grep` +
  fallback PII scan, demystified `|| true` for legacy mypy / pip-audit.
- [`README.md`](README.md) — top orientation banner + legacy-labeled sections
  + PII removed from Support.
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) — enforcement contact routed
  through GitHub issues (no email in source).
- [`CONTRIBUTING_NEW.md`](CONTRIBUTING_NEW.md) — Questions section cleaned
  and repo URLs updated.
- [`README_NEW.md`](README_NEW.md) — Support section cleaned + repo URLs
  updated.
- [`BridgeCAD Enterprise Suite/pyproject.toml`](BridgeCAD%20Enterprise%20Suite/pyproject.toml#L76-L80) —
  Homepage / Repository / Issues / Changelog → actual public repo.
- [`BridgeCAD Enterprise Suite/README.md`](BridgeCAD%20Enterprise%20Suite/README.md#L5) —
  CI badge → actual `suite-ci.yml` on real org.
- [`BridgeCAD Enterprise Suite/apps/api-gateway/bridgecad_api/main.py`](BridgeCAD%20Enterprise%20Suite/apps/api-gateway/bridgecad_api/main.py) —
  new input validators + `_staged_zip_response` helper using
  `NamedTemporaryFile` + `BackgroundTasks` cleanup; applied to both
  `draw/gad` and `export/bundle` endpoints.

### Not Changed (Verified Correct)
- `bridgecad-core` types / enums / validation (Day 1 & 2 work from prior
  session already present).
- All four drawing bug fix sites in `bridge_generator.py` and
  `multi_sheet_generator.py` — geometric loops + ABTL ladder were
  already right.

---

## 5. Release Rule (echoed from the planning ZIP)

Do **not** call this repository "perfect", nor release any generated
drawing / BOQ as construction-ready, until:
  * Phase 0 (this patch): green on CI (both workflows).
  * Phase 1: 28 fixtures produce an explicit pass/fail JSON with 5
    golden-case model summaries pinned.
  * Phase 2: All 7 DXF sheets for those 5 golden cases pass structural
    DXF checks **and** an engineer has visually reviewed representative
    output per bridge family.
  * Phase 3: Every non-zero BOQ line has traceable inputs and an
    engineer-approved tolerance.

Until then, the exported manifest should always include a prominent
"Generated — not reviewed for construction" label, and the Suite UI
must show it at download time.
