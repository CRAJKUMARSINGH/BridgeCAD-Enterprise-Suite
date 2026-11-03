# Chat Log — append-only project journey

**Cadence.** During augmented sessions this log is appended roughly **every 15
minutes** with a timestamped entry, so the journey keeps a durable audit trail
alongside the code. Entries are **append-only**: never edited, never deleted.
Newest entries go at the bottom.

**Companion logs.**
`CREAT.md` — rolling 24-hour continuity hand-off.
`CHANGELOG.md` — durable release history.
`docs/upgrade/PROGRESS.md` — one entry per roadmap week.

---

## 2026-11-01 09:41 IST — bootstrap

- Session opened against the monorepo at `e:\Rajkumar\BridgeCAD-Enterprise-Suite`.
- `CODE-JUNCTION/1.TXT` read and applied **selectively** (the "if suitably
  needed" rule). Verified each claim against the working tree first.
  - Applied: bare `tuple` → `tuple[int, int]` in `morth_specs.py`; hoisted the
    trailing `import math` out of `irc_21.py`; completed public re-exports in
    `bridgecad_core/standards/__init__.py` and `bridgecad_core/__init__.py`.
  - Rejected: the brief's rewritten `load_combinations.py` (module already
    exists with a live, tested API) and its cosmetic `pyproject.toml` mypy
    `files` key. Its invalid enum literals were replaced with real
    `bridgecad_core.types` members.
- Restored 7 orphaned bridge plugins (manifest + defaults + draw-overrides) and
  removed 10 stray marker files named `['manifest.json', 'draw_overrides.py',
  'defaults.yaml']`. Registry discovers **10/10** plugins.
- Added the wiring guard `scripts/verify_wiring.py` and the test
  `tests/plugins/test_plugin_wiring.py`.

## 2026-11-01 09:41 IST — verification gate green

- `tests/compliance` + `tests/verification` → **92 passed**.
- `tests/docs` fast lane → **41 passed**, 16 deselected.
- `tests/docs` slow mutation lane → **16 passed** in 37:45.
- `scripts/verify_wiring.py` → WIRING OK.
- `mypy --strict` on `standards` and `ruff check` / `ruff format --check` clean.

## 2026-11-01 09:41 IST — "hanging lane" diagnosed and bounded

- A `tests/docs` run that showed **no output for ~38 minutes** was investigated.
  Verdict: **not a hang** — it completed (`16 passed`). The blank screen was
  output withholding:
  - `Select-Object -Last N` cannot stream — it must consume the whole upstream
    before it can emit the last N lines.
  - A piped `python` block-buffers stdout; a `Tee-Object` log file did not even
    exist until the process exited (direct proof).
- Ruled out, by inspection: interactive prompt (no `input()`), network and
  `time.sleep` (none), `--strict-config` (errors, cannot hang), and
  `pytest-timeout` (not installed — a real gap, but not the cause).
- The only genuinely **unbounded** wait was the `check_doc_paths.py` subprocess
  in `tests/docs/test_gates_selfcheck.py`; it now carries `timeout=300`.
- Correct invocation recorded: run long lanes with `python -u -m pytest ... -v`
  (or `make test-docs`). Never pipe them through `Select-Object -Last N`.

## 2026-11-01 09:41 IST — documentation hand-off refreshed

- `CREAT.md` rolled to the `2026-11-01` entry; the `2026-10-30` entry was
  removed per the file's own 24-hour rolling-window rule (it remains in git
  history).
- This append-only chat log created as the durable journey trail.

## 2026-11-01 10:35 IST — launch guide authored (attachment never arrived)

- The requested launch-guide file was **empty on two consecutive messages** (the
  `**File:**` field carried no body). Rather than block, the guide was authored
  from **verified repo sources only** — `README.md`, `docs/getting-started.md`,
  `mkdocs.yml`, `Makefile`, `.github/workflows/suite-ci.yml`,
  `scripts/check_doc_paths.py` — so no content is fabricated.
- New page: `docs/launch.md` — prerequisites, Path A zero-install, Path B dev
  install, first end-to-end run, all four interfaces, Docker local + prod,
  verification gates, RC reality check, pre-flight checklist, pitfalls, cheat
  sheet.
- Registered in both gate-critical indexes:
  `DOCS_INDEX.md` (new Guides row) and `mkdocs.yml` (`Launch guide: launch.md`).
- Gates green: `check_doc_paths.py --verbose` → OK; `scripts/verify_docs.py
  --json` → `ok: true`, 3 pass / 0 fail / 3 skip (lychee, mkdocs, sphinx not
  installed locally). Slow mutation lane re-running in the background.

## 2026-11-01 10:35 IST — Green-close W01→W08 HOWTO reviewed (awaiting GO/NO-GO)

- The inline `## HOWTO: Green-close W01 → W08` guide was audited against the
  repo. "green-close" / "close ritual" → **zero** matches repo-wide, so the
  8-step ritual and 6-condition contract are **not yet written**.
- One conflict found: the guide cites W03 coverage `~30%`, but the repo enforces
  `[tool.coverage.report] fail_under = 75`. The repo floor wins.
- Proposed (not applied): a single "Green-close contract" subsection under
  `MASTER_ROADMAP.md` §Operating rules. **No edit made — awaiting GO / NO-GO.**

## 2026-11-01 10:50 IST — Option B: launch content folded into getting-started

- Per the governance rules **"One fact, one place"** and **"Retire, don't fork"**,
  the separate `docs/launch.md` was **retired**. Its still-useful sections were
  **merged into the existing `docs/getting-started.md`**:
  - new **Prerequisites** table,
  - Docker production one-liner + `FASTAPI_URL` cloud note in Path C,
  - **Before you call it launched** (the 8 verification gates),
  - **Release-candidate reality check**,
  - **Pre-flight checklist** (Local / API / Production),
  - **Common pitfalls**, **Cheat sheet**.
- Reverted both registration points: `DOCS_INDEX.md` (launch row removed;
  getting-started description broadened to "Start here: …") and `mkdocs.yml`
  ("Launch guide" nav entry removed). No new file → no registration cost.
- `GUIDE.md` stays the deep reference; `docs/deployment.md` stays the production
  doc; getting-started is now the single "start here / launch" surface.
- Gates re-run green: `check_doc_paths.py --verbose` → OK; `scripts/verify_docs.py
  --json` → `ok: true` (3 pass / 0 fail / 3 skip).

## 2026-11-01 11:05 IST — getting-started.md replaced with the author's merged revision

- Rajkumar supplied the final merged `docs/getting-started.md` (option B) and it
  was dropped in, replacing the first draft of the merge.
- One artifact corrected on entry: stray backticks wrapped around the clone URL
  **inside** the `bash` fence (`git clone \`https://…\``) — inside a fence those
  are literal and would trigger command substitution. Removed in both places
  (Path A and One-line recipes).
- `DOCS_INDEX.md` getting-started description re-aligned ("common pitfalls"
  replaces "pre-flight checklist").
- Verified claims: extras `dev` / `draw` / `api` / `ui` all exist in
  `pyproject.toml`; `ezdxf is required` is a real runtime message.
- **Flagged (not changed):** the console script is named `bridgecad`, not
  `bridgecad-cli` — root `pyproject.toml` and `apps/cli-console/pyproject.toml`
  both define `bridgecad = …`. Docs repo-wide (getting-started, README,
  `.github/ISSUE_TEMPLATE/bug_report.yml`) say `bridgecad-cli`. Pre-existing
  mismatch; awaiting a decision on whether to fix repo-wide.
- Gates green: `check_doc_paths.py --verbose` → OK; `scripts/verify_docs.py
  --json` → `ok: true` (3 pass / 0 fail / 3 skip).

## 2026-11-01 11:15 IST — decisions taken: LEAVE / GO / COMMIT

- **CLI naming → LEAVE.** The `bridgecad` (script) vs `bridgecad-cli` (docs)
  mismatch is recorded as known debt; no sweep performed.
- **Green-close → GO.** Added the *Green-close contract* under
  `MASTER_ROADMAP.md` §Operating rules: the six-condition contract, the
  eight-step close ritual, and the coverage floor pinned at the repo's real
  **75 %** ratchet (`fail_under`), not the 30 % figure from the external note.
  The trim rule is back-referenced, not duplicated.
- **Commit → yes.** Doc changes committed by pathspec; unrelated working-tree
  changes deliberately left untouched.
- Gates green after the roadmap edit: `check_doc_paths.py` → OK;
  `verify_docs.py --json` → `ok: true` (3 pass / 0 fail / 3 skip).

## 2026-11-01 11:40 IST — committed (two focused commits)

- `1dcebf5` — `docs: fold launch guide into getting-started, retire launch.md`
  (docs/getting-started.md, DOCS_INDEX.md, mkdocs.yml, CHATLOG.md).
- `a0104a2` — `docs(roadmap): add green-close contract to Operating rules`
  (MASTER_ROADMAP.md).
- Unrelated working-tree changes were left untouched; both commits are by
  pathspec.

### Environment note — recurring git lock litter

- Committing was blocked by stale `.git/*.lock` files (index, HEAD, AUTO_MERGE,
  packed-refs) dated from a previous session. No git process was running.
- `scripts/clear_stale_locks.py` and PowerShell `Remove-Item` both reported
  failure or silently did nothing — a Windows handle (consistent with Defender's
  `MpCopyAccelerator`) blocks deletion, so git leaves fresh locks behind after
  each write.
- Working remedy: delete the lock with the editor-level delete tool (which
  succeeds) **immediately** before the git write. Residue was cleared afterwards;
  `.git` now reports 0 lock files.
- Follow-up worth a script fix: `clear_stale_locks.py` should fall back to a
  rename-with-unique-suffix when `unlink()` does not actually remove the file.

<!-- Append new ~15-minute entries below this line, newest last. -->

## 2026-11-01 12:05 IST — new guide folded by ownership (no new file)

- A further guide arrived with an empty `**File:**` body again, outlining four
  areas: (1) design tiers Basic/Intermediate/Advanced, (2) a ~1000-user
  test-run, (3) the bug-report mechanism, (4) the patch workflow.
- Grounded each area against the repo before writing; decided **fold, split by
  ownership, no new page** (the option that honours *One fact, one place* and
  *Retire, don't fork*).
- **Areas 3 & 4 were already owned** — `.github/ISSUE_TEMPLATE/bug_report.yml`
  is the bug-report source of truth; `CONTRIBUTING.md` §3/§5/§11/§12 owns the
  patch workflow. Added pointers, not copies:
  - `CONTRIBUTING.md` §13 renamed *Questions and bugs*; added the issue-form
    link and the `python -m bridgecad info` + `troubleshooting.md` first steps.
  - `CONTRIBUTING.md` §11: one post-merge line to re-run the tier suite on a
    clean clone of `main`.
- **Areas 1 & 2 were genuinely new:**
  - `docs/getting-started.md` — new *What the Suite handles* section: a tier
    table mapping Basic/Intermediate/Advanced to the built-in templates and
    their scope. Labelled a planning figure, not a measured mix.
  - `docs/deployment.md` — new *Capacity / volume smoke test (proxy)* section
    beside *Scaling*/*Pre-flight checklist*: per-tier pipeline smoke, a
    tier-weighted batch loop (600 + 300 + 100), interface checklist link, and
    pass criteria. Called a **proxy for volume, not a measured capacity** —
    there is no load harness in the repo. Added one Pre-flight checklist item.
- Claims verified: 28 fixtures really exist in `tests/e2e/fixtures/`; hydraulics
  is real (`HydraulicData`, `gen_hydraulics_sheet`, `score_hydraulic`).
- No `DOCS_INDEX.md` / `mkdocs.yml` change needed.
- Gates green: `check_doc_paths.py --verbose` → OK; `scripts/verify_docs.py
  --json` → `ok: true` (3 pass / 0 fail / 3 skip).

## 2026-11-01 12:20 IST — committed and pushed

- Committed the four-file doc set: `5dfe1e4` — `docs: fold tier guide into
  getting-started, deployment, and CONTRIBUTING` (docs/getting-started.md,
  docs/deployment.md, CONTRIBUTING.md, CHATLOG.md; +98 / −1). Diff reviewed
  before staging — only the intended hunks; unrelated working-tree changes left
  untouched. No lock friction (`.git` had 0 lock files).
- Pushed to origin (`c446a12..5dfe1e4  main -> main`), publishing all **9**
  local commits ahead of the remote. `main` now tracks `origin/main` in sync.
  Direct push to `main`, per the user's explicit confirmation.

## 2026-11-02 08:55 IST — CODE-JUNCTION/BridgeCAD_unwired_fixes applied

- Applied the 10-fix patch from `CODE-JUNCTION/BridgeCAD_unwired_fixes`. The
  patch is a snapshot from base `c446a12`, so the live tree had diverged in
  **both** directions; each file was classified with
  `git diff --no-index` before touching it — apply / splice / skip, never a
  blind overwrite.
- **Applied as-is:** `engines/_render.py` (new shared DXF→matplotlib renderer);
  `engines/dxf_engine.py`, `png_engine.py`, `svg_engine.py` (M3 stubs → real
  implementations); `bridgecad_export/booklet.py` (M6 stub → re-export of
  `generate_package` + `generate_pdf_booklet`); `apps/cli-console/bridgecad_cli/__main__.py`
  (new, `python -m bridgecad_cli`); `tests/integration/test_io_wiring.py` (new).
- **Spliced (live was newer — adapted, not overwritten):**
  `engines/pdf_engine.py` kept the W07 PDF/A-1b engine and **added**
  `generate_pdf_booklet`; `bridgecad_io/excel_template.py` gained the
  `_fast_mode: bool = False` param (fix #4); `bridgecad/__main__.py` took the
  patch's correct `run_all(project)` → `score(report)` QA path and dropped the
  duplicate function-level `import subprocess`, while **keeping** the live
  calc-sheet block and banner line the patch lacked.
- **Skipped (live newer):** `Makefile` (already CI-scoped, has `cov` /
  `drawing-standards`), `bridgecad_io/json_adapter.py` (keep W08
  `project_schema()`); `csv_adapter.py` / `excel_writer.py` already identical.
- **Fix #8 applied — flagged:** `apps/cli-console/pyproject.toml` script renamed
  `bridgecad` → `bridgecad-cli`, resolving the long-standing naming mismatch and
  reversing the earlier `LEAVE` decision; the banner and docs already say
  `bridgecad-cli`, and root `pyproject.toml` keeps the `bridgecad` shim, so no
  collision.
- **Verified:** `tests/integration/test_io_wiring.py` → **7 passed**;
  `tests/integration` → 7 passed; `tests/drawings` → **14 passed** (W07 PDF/A
  engine intact after the splice); import smoke of all new/changed modules OK.
  `scripts/verify_docs.py --json` reports one **pre-existing** failure
  (`test_defect_13_referenced_scripts_exist`) caused entirely by untracked
  `CODE-JUNCTION/Venice-patch/` scratch docs referencing absent `scripts/*_robot.py`
  — unrelated to this patch and absent from the committed tree.

## 2026-11-02 08:57 IST — CODE-JUNCTION/1.TXT audited: nothing due

- Audited `CODE-JUNCTION/1.TXT` (the wiring + strict-typing repair, base
  `c446a12`) against the live tree before applying anything — the "if due"
  rule. **Every substantive defect is already fixed**; the file is stale.
  - #1 bare `tuple` in `morth_specs.py` → already `tuple[int, int]` (3 sites).
  - #2 missing `standards/load_combinations.py` → **exists** (IRC:6-2017 table).
  - #3 `standards/__init__.py` partial exports → complete; `verify_wiring.py`
    reports *"standards fully exported"*.
  - #4 `irc_05` / `irc_21` unreachable from the root → `compute_hydraulics`,
    `check_structural_adequacy` and the combination API are exported.
  - #5 seven orphaned plugins → all **10** plugin dirs carry
    `manifest.json` + `defaults.yaml` + `draw_overrides.py`; no bracket marker.
  - #6 `irc_21.py` trailing `import math` → hoisted to line 16.
  - Guard `scripts/verify_wiring.py` and `tests/plugins/test_plugin_wiring.py`
    already present; the patch's `tests/standards/test_load_combinations.py`
    would **fork** the live `tests/compliance/test_load_combinations.py`
    (governance: "Retire, don't fork"), so it was not added.
- **Verified:** `python scripts/verify_wiring.py` → *WIRING OK — 10 plugins
  wired, standards fully exported, no bare generics*; `pytest tests/compliance
  tests/plugins -q` → **45 passed**.
- Only unapplied delta is #7, the `[tool.mypy] files = [...]` key. Deliberately
  left out again: `suite-ci.yml` invokes mypy with **explicit per-package
  paths**, which override the config `files` key, so it is inert for CI and was
  previously rejected as cosmetic. No files changed this turn.

## 2026-11-02 09:01 IST — CODE-JUNCTION/Genspark-Patch applied (`bridgecad-fixes.patch`)

- Applied `CODE-JUNCTION/Genspark-Patch/BridgeCAD-QA-Package/BridgeCAD-QA-Package/bridgecad-fixes.patch`
  (9 files, +137/−8) file-by-file against the live tree. The patch is a snapshot,
  so each hunk was checked for staleness first. (`00- abstract of bugs.txt` was
  read and set aside: it diagnoses the separate `Bridge_GAD_Yogendra_Borse`
  legacy repo and ends "awaiting authorization".)
- **Applied — bill package:**
  - `models.py`: `BillItem.status` / `BillItem.basis`, and the
    `BillOfQuantities.items` flat-view property (`boq.items` used to raise
    `AttributeError`).
  - `provenance.py`: `__str__` on `LineStatus` and `RateSource`, so `f"{status}"`
    stops leaking `LineStatus.CALCULATED` into reports.
  - `processor.py`: new `attach_provenance: bool = True`; `extract_and_price`
    now stamps each priced line's status/basis; `build_boq` calls with
    `attach_provenance=False` so it stays the single provenance path.
  - `formatters/csv_formatter.py`: `Status` + `Basis` columns added; subtotal /
    contingency / grand-total rows widened to 10 columns.
- **Applied — core:** `BridgeProject.with_updates(**sections)` — a *validated*
  alternative to `model_copy(update=…)`, closing the span-count bypass.
- **Applied — export:** `create_bundle()` gains `project` / `failures`; it now
  calls `build_manifest()` (review label + scaffold list) and stamps
  `boq_provenance`; `orchestrator.export_all()` records per-stage `failures` and
  forwards them. The new params are optional, so the other caller
  (`scripts/robotic_test_viaduct.py`) is unaffected.
- **Applied — cli-console:** `draw gad` title now derived from
  `_SHEET_MANIFEST` (was hard-coded `/7`); new `draw booklet` alias command
  (the documented form); `template new` accepts `--type simple_12m` as well as
  the positional form.
- **Skipped:** the `DOCS_INDEX.md` hunk deletes the `docs/interop.md` row — but
  `docs/interop.md` **now exists** and is registered, so the deletion would
  break doc-integrity. Stale; left alone.
- **Lint fix during apply:** ruff `UP037` on the patch's quoted
  `-> "BridgeProject"` (file has `from __future__ import annotations`) →
  unquoted.
- **Verified:** `pytest tests/draw/test_boq_provenance.py tests/unit
  tests/integration tests/verification` → **186 passed**; ruff clean on all
  eight changed files; functional smoke — `boq.items` 26 lines with
  calculated/estimated/not_calculated statuses + formulas, `with_updates()`
  revalidates and raises `KeyError` on an unknown section, bundle manifest
  carries `review_label` + `scaffold_sheets` + `boq_provenance`, CLI
  `template new` works via `--type` **and** positional, `draw booklet`
  registers.
- Pre-existing, not from this patch: ruff `UP035` in
  `packages/bridgecad-io/bridgecad_io/excel_reader.py` (a locally modified,
  uncommitted file). Nothing committed this turn.

## 2026-11-02 09:20 IST — Venice-patch (robotic testing kit)

- `CODE-JUNCTION/v*-Patch` glob resolves to **`CODE-JUNCTION/Venice-patch`**
  (the only match). Read `instructions.txt`, `SUGGESTED_PATCHES.md`, the
  `ROBOTIC_TESTING_GUIDE.md`, and all four persona scripts. It is a **testing
  kit, not a unified diff** — payload is 4 persona scripts + 5 prose fixes
  (P1–P5). Classified each suggestion against the live tree (apply / skip).
- **Installed (new, ruff-clean):** `scripts/robotic_smoke.py`,
  `scripts/basic_user_robot.py`, `scripts/intermediate_user_robot.py`,
  `scripts/advanced_user_robot.py`. This also **closes the prior
  `test_defect_13_referenced_scripts_exist` failure** (the kit's docs named
  these scripts; they now exist on disk).
- **P4 — applied:** `Makefile` gains a `robotic` target (all four personas,
  seeded) + PHONY entry.
- **P1 — applied:** `bridgecad_draw/booklet.py` de-duplicates only the
  "ezdxf is required" `ImportError` via a module-level warn-once flag; a genuine
  sheet-import error still warns per-sheet.
- **P2 — applied:** `bridgecad/__init__.py` gains `ensure_workspace()` (called
  on import) so `python -c "import bridgecad"` and IDE runners get the same
  `packages/*` + `apps/*` path mapping `sitecustomize.py` provides.
- **P5 — applied:** `fastapi>=0.115` added to `[project.optional-dependencies].dev`
  so the one `importorskip("fastapi")` API test (`tests/unit/test_api_cors.py`)
  stops being silent-skipped.
- **P3 — NOT applied:** standardise a QA score block in the generated project
  JSON. The 11-span generator dumps the project via `dump_project` with no QA
  block; doing this right needs a generator change, so it is deliberately left
  out of this pass.
- **Lint drift caught during verification:** the in-scope `ruff format --check`
  reported drift in 7 pre-existing/untracked files carried over from the earlier
  patches (`excel_formatter.py`, `processor.py`, `models.py`, `ifc_engine.py`,
  `orchestrator.py`, `_fields.py`, `compliance_engine.py`) + `UP035` in
  `excel_reader.py`. Normalised them so the CI lint gate stays green.
- **Verified:** `ruff check` + `ruff format --check` → clean on
  `packages/ apps/ scripts/` (211 files formatted); `pytest tests/docs -q -m
  "not slow"` → **41 passed, 16 deselected**; `python scripts/verify_docs.py`
  → **3 passed, 0 failed, 3 skipped**; `python scripts/robotic_smoke.py
  --persona all --seed 42` → **BASIC/INTERMEDIATE/ADVANCED all `passed=True`**,
  exit 0, `reports/smoke_report_seed42.json` written. Nothing committed this
  turn.

## 2026-11-02 09:27 IST — commit + push, and a robotic test guide

- **Committed and pushed** `39f05eb` (see prior entry) → `origin/main`
  (`5dfe1e4..39f05eb`). Scope was source/docs/tests only, per instruction:
  `CODE-JUNCTION/`, `reports/`, and regenerated `outputs/` binaries excluded.
  Windows stale `.git/index.lock` blocked staging twice; resolved via
  `scripts/clear_stale_locks.py` then an editor-level unlink of the surviving
  lock.
- **Added `ROBOTIC-TEST-GUIDE.MD`** at the repo root (user request): a
  copy-paste PowerShell playbook for exercising the app on demand — the
  all-persona smoke, each persona individually, the full "green stack" sweep,
  the release gate, a suggested cadence, and troubleshooting.
- Written to respect the doc gates: only existing `scripts/*.py` appear in
  fenced blocks; generated artefacts (`reports/*.json`, `outputs/*`) are named
  inline (fences are what the path audit scans); no phantom-suite string; all
  relative `.md` links resolve.
- **Verified:** `python scripts/check_doc_paths.py` → OK; `pytest tests/docs -q
  -m "not slow"` → **41 passed, 16 deselected**; `python scripts/verify_docs.py`
  → **3 passed, 0 failed, 3 skipped**. New file is uncommitted.

## 2026-11-02 09:48 IST — Venice-patch, applied as an adapted safe subset

- **Read `CODE-JUNCTION/Venice-patch/instructions.txt`** (1,713 lines). It is a
  *persona test-plan + triage apparatus*, not a unified diff — so it was audited
  claim-by-claim against the live tree. Applied the **adapted safe subset** the
  user selected, not the verbatim drop.
- **New harness (`tools/`):** `personas.py` (fixed the upstream `__WIDTHS`
  NameError → `_WIDTHS`), `run_robot.py` (persona-weighted Playwright walker),
  `triage.py` (failure → triage row), `gate.py` (merge gate reading the log).
  Hardcoded `BridgeCAD Enterprise Suite/` paths removed; the flat repo root is
  used instead.
- **New register + playbooks:** `artifacts/TRIAGE_LOG.md`, root
  `TRIAGE_AND_DEBUG.md`, root `PATCH_GUIDE.md` — all rewritten so no fenced
  block names a nonexistent path, and the phantom-suite string is gone.
- **Two upstream gate bugs fixed** so `make gates` is not red on day one: both
  `gate.py` and `triage.py --metrics` now honour the Status column, so the
  seeded `UNCONFIRMED` predictions do **not** count as open S1/S2. Verified: a
  row flipped to `OPEN` is detected (12/12), baseline is 0.
- **Makefile:** spliced (not replaced) `robot`, `robot-full`, `gates` targets +
  `URL ?=`, leaving the existing `robotic` target intact.
- **Deliberately NOT applied** (would overwrite live, tested files or break
  gates): `tests/conftest.py`, `.github/ISSUE_TEMPLATE/config.yml`,
  `.github/PULL_REQUEST_TEMPLATE.md`, the `.githooks/pre-push` hook, and a new
  `docs/TEST_PLAN.md`. `artifacts/robot/` added to `.gitignore`; the log stays
  tracked.
- **Verified:** `python scripts/check_doc_paths.py` → OK; `python -m ruff check
  tools/` + `format --check` → clean; `pytest tests/docs -q -m "not slow"` →
  **41 passed, 16 deselected**; `python scripts/verify_docs.py` → **3 passed, 0
  failed, 3 skipped**; `python tools/gate.py` → exit 0; `python tools/triage.py
  --metrics` → `open S1=0 S2=0`. Nothing committed this turn.

## 2026-11-02 09:51 IST — CODE-JUNCTION/1.TXT audited → NOT DUE (no change)

- **Action:** audited the wiring-fix kit `CODE-JUNCTION/1.TXT` against the live
  tree before applying. It is pinned to an old base commit (`c446a12`) and ships
  an `apply_patch.py` that overwrites four core/package files, rewrites 7 plugin
  dirs, and deletes marker files.
- **Verdict:** every one of its six defects is already fixed in the live tree,
  and the live fix is more thorough. The kit as a whole is **superseded**, and
  applying it verbatim would be **destructive**.
- **Per-defect audit (all already resolved):** 1) `standards/load_combinations.py`
  exists and carries a *newer* IRC:6 + EN 1990 API (`LoadCase`, `IRC6_LOAD_CASES`,
  `irc6_combinations`, `combinations_for`) — the kit would replace it with an
  older, incompatible `Action`/`ALL_COMBINATIONS` table and break imports; 2) all
  10 plugin dirs already ship real `manifest.json` + `defaults.yaml` +
  `draw_overrides.py`, no bracket-named marker file; 3) `morth_specs.py` already
  annotates `tuple[int, int]` at all three sites; 4) `standards/__init__.py`
  already exports the full surface including `irc_sp55` constants and the
  combination API; 5) `bridgecad_core/__init__.py` already exports IRC:5, IRC:21
  and the combination API; 6) the mypy `files` key is absent but **moot** — every
  invocation (`make typecheck` → `mypy packages apps`; CI → explicit per-package
  paths) passes explicit paths, so `files` never takes effect and the
  `warn_unused_configs` note never fires.
- **Additionally stale:** `scripts/verify_wiring.py` already exists and is
  *superior* (8 checks vs the kit's 7, plus a `bridge_types ∈ SuperstructureType`
  check); `tests/plugins/` already exists with 6 passing tests. The kit's proposed
  `tests/standards/test_load_combinations.py` imports symbols that no longer exist
  → it would fail on arrival. Its root `PATCH_NOTES.md` would also be an
  unregistered root markdown file (doc-gate risk).
- **Evidence:** `python scripts/verify_wiring.py` → `WIRING OK — 10 plugins wired,
  standards fully exported, no bare generics.` (exit 0); `pytest tests/plugins -q`
  → **6 passed**.
- **Decision:** apply nothing. No files written. Awaiting a genuine patch.
```

## 2026-11-02 10:44 IST — Venice-patch I2 applied as an adapted core (tools/ → scripts/robot/)

Applied the follow-up Venice message (`CODE-JUNCTION/Venice-patch/I2.txt`) as the
**adapted core** the user selected. I2 was written against a tree whose premises
partly do not hold here, so two of its items were dropped with reason.

**Two questions I2 asked, answered against this repo:**
1. `scripts/mkdocs_hooks.py` stages root docs via an **explicit `STAGE`
   allowlist** (GUIDE / README / CONTRIBUTING / CHANGELOG / SECURITY /
   CODE_OF_CONDUCT / DOCS_INDEX) — no `rglob("*.md")`. A new root `.md` is never
   auto-staged, so a new doc must live in `docs/` *and* be registered.
2. `tests/docs/conftest.py` `SKIP_DIRS` has no `artifacts` member, and
   `git check-ignore artifacts/TRIAGE_LOG.md` → **not ignored** (only
   `artifacts/robot/` is). So I2's stated reason for moving the log to `docs/` —
   "`artifacts/` is very likely gitignored, which would leave `gate.py` reading an
   untracked file and passing vacuously in CI" — is **false here**. The log is
   tracked and already scanned by the doc suite.

**Applied (genuinely due):**
- Relocated the persona harness `tools/` → **`scripts/robot/`**. `tools/` sat
  *outside* the CI lint scope (`ruff check packages apps scripts`), so those four
  files were never linted; `scripts/**` is in scope. `tools/` deleted.
- `personas.py`: added the `_WIDTHS` drift guard
  `assert set(_WIDTHS) == set(Tier)`.
- `gate.py`: widened the blast-radius `PATH` regex for flat paths — it now
  matches any repo-relative file (not just `packages|apps|tests`), so
  `scripts/robot/*.py`, `pyproject.toml` and `docs/*.md` are recorded:
  `(?:^|[\s`(])((?:[\w.\-]+/)*[\w.\-]+\.(?:py|js|ts|tsx|yml|yaml|toml|json|md))`.
  `parse()` now uses `PATH.finditer`.
- `pyproject.toml`: dropped `"tools/**" = ["T20"]`; added
  `"scripts/robot/run_robot.py" = ["T20", "E402"]` — its `sys.path.insert` +
  sibling-`personas` import is deliberate, the same precedent as the other
  scripts listed there.
- `Makefile`: `robot` / `robot-full` / `gates` now call `scripts/robot/*`.
- Rebased live refs `tools/` → `scripts/robot/` in `TRIAGE_AND_DEBUG.md` (5) and
  `artifacts/TRIAGE_LOG.md` (2). Earlier CHATLOG entries left as written
  (append-only).

**Deliberately NOT applied (cut list):**
- The log **stays** at `artifacts/TRIAGE_LOG.md`. It is tracked, gate-clean and
  already scanned; moving it into `docs/` would publish the live S1/S2 register in
  the public site nav and impose a DOCS_INDEX + mkdocs-nav registration tax on a
  file that churns on every ingest — for zero correctness gain.
- `.githooks/pre-push`, `.github/workflows/robot.yml`,
  `.github/ISSUE_TEMPLATE/defect.yml` — new CI / hook / governance surface. I2's
  rationale (untracked log) does not apply, and a POSIX `sh` pre-push hook does
  not run on this Windows box.

**Verification (all green):**
- `ruff check packages apps scripts` → *All checks passed*;
  `ruff format --check scripts/robot` → 4 files formatted.
- `python scripts/robot/personas.py` → exit 0 (guard holds).
- `python scripts/robot/gate.py` → exit 0; `--metrics` → `open S1=0 S2=0`.
- `python scripts/check_doc_paths.py` → *OK — every path referenced in a code
  block exists*.
- `pytest tests/docs -q -m "not slow"` → **41 passed, 16 deselected**.
- `python scripts/verify_docs.py --json` → **3 pass / 0 fail / 3 skip**.
- Regex spot-check: extracts `['docs/PATCH_GUIDE.md', 'pyproject.toml',
  'scripts/robot/gate.py']`; seed log parses to 0 blocking entries.

## 2026-11-02 11:20 IST — Verified "do tests generate drawings?" claim set

Audited the pasted claim set against the live tree. Six of seven hold; one is
false.

**Confirmed:**
- `suite-ci.yml` L138-144 runs `pytest tests/ --ignore=tests/e2e
  --ignore=tests/benchmarks --ignore=tests/draw --ignore=tests/drawings
  --ignore=tests/refs --ignore=tests/interop` — the default lane paints nothing
  (the claim's list omitted `tests/benchmarks`; otherwise exact).
- `--regression` is defined in `tests/conftest.py` L28-33 (not the subdir
  conftest) and `draw.yml` L75 runs `pytest -q tests/drawings --regression`.
- Scaffold sheets: `draw.yml` L31-35 — "sheets 2-4, 6, 7 are documented
  scaffolds (tests/draw/sheets.spec.json)" under `continue-on-error: true`.
- `MIN_SHEET_ENTITIES = 20` (`tests/e2e/run_e2e.py` L34, enforced L401-403).
- `run_e2e.py` does not match `python_files = ["test_*.py"]`
  (`pyproject.toml` L282); CI runs it as `python tests/e2e/run_e2e.py`
  (`suite-ci.yml` L169).

**Refuted — claim #2:** "`tests/drawings` collects zero tests unless you pass
`--regression`; run it plain and you get a green tick over an empty lane."
Empirically false: plain `pytest tests/drawings -q` → **14 passed in 73.72s**
(real DXF + PDF/A-1b written). `--regression` only *adds* a `regression`
markexpr filter; with it unset the markexpr is empty so every test runs. The
"collects ZERO / exit 5" hazard is real but lives in **`tests/draw`**
(`pytest tests/draw -m draw`), where a never-registered `scaffold_only` marker
collected zero under `continue-on-error` — documented in `draw.yml` L25-27 and
already fixed by switching to name-based `-k` selection.

**Operational note nuance:** the churn is real but `tests/e2e/output/**` and
`outputs/**` binaries are **tracked** (`git ls-files` shows them; `.gitignore`
`outputs/*.dxf|pdf|xlsx` cannot untrack already-committed files), so dirty-tree
symptoms show as `M`, not `??`. Generation working, not corruption — agreed.

## 2026-11-03 10:04 IST — Venice-kit docs fork retired; persona suite parked

Applied the remaining due deltas of `CODE-JUNCTION/Venice-patch/I2.txt` and
cleaned up the one artifact the earlier passes left inconsistent.

- **Doc fork retired.** The 2026-11-02 09:48 pass placed `TRIAGE_AND_DEBUG.md` and
  `PATCH_GUIDE.md` at the repo **root**, while the later pass registered **`docs/`**
  copies in `DOCS_INDEX.md` + the `mkdocs.yml` nav. That is a fork, which "one
  fact, one place" forbids. The `docs/` copies win — registered, gate-passing,
  with resolved cross-links. Deleted the root duplicates and rebased the two bare
  refs in `artifacts/TRIAGE_LOG.md` (`TRIAGE_AND_DEBUG.md` →
  `docs/TRIAGE_AND_DEBUG.md`; `PATCH_GUIDE.md` → `docs/PATCH_GUIDE.md`).
- **Enforcement layer confirmed present** (changed this session, still
  uncommitted): `scripts/sync_labels.py` (`defect`, `needs-triage`),
  `.github/ISSUE_TEMPLATE/defect.yml`, `config.yml` contact links, the Triage
  block in `.github/PULL_REQUEST_TEMPLATE.md`, `.githooks/pre-push`, `Makefile`
  `hooks` / `hooks-check`, `.github/workflows/robot.yml`.
- **Parked — persona test suite.** The kit's oracles assert
  `design_girder(span_m, carriageway_m, grade)` → `.depth_m` / `.concrete_m3` and
  the routes `/api/v1/design`, `/api/v1/export/{dxf,pdf,zip,…}`. A repo-wide grep
  shows those symbols exist **only inside the patch docs** — the live engine and
  API do not expose them. A verbatim port of `tests/robot/{conftest,test_*.py}`
  would collect green-by-skip at best and red at worst (`test_ui_playwright.py`
  imports `playwright` at module scope → collection error where it is absent), and
  `docs/TEST_PLAN.md` describes those same non-existent suites. Deferred pending a
  retarget to the real contract rather than shipping oracles for a contract the
  tree does not have.

**Verified (all green):** `python scripts/check_doc_paths.py` → OK;
`python scripts/verify_docs.py --json` → 3 pass / 0 fail / 3 skip;
`python -m pytest tests/docs -q -m "not slow"` → **41 passed, 16 deselected**;
`python scripts/robot/gate.py` → exit 0; `--metrics` → `open S1=0 S2=0`;
`python -m ruff check packages apps scripts` → *All checks passed*; YAML parse of
`defect.yml` / `config.yml` / `robot.yml` / `mkdocs.yml` → ok. Nothing committed
(standing rule: commit only on explicit instruction).

## 2026-11-03 10:29 IST — persona suite retargeted to the real contract

Decision taken: **retarget to the real contract** rather than port the kit
verbatim or drop it. The Venice kit's oracles named `design_girder`,
`/api/v1/design` and `/api/v1/export/*` — symbols that exist only inside the
patch docs. Each oracle was mapped onto the live engine/API/export symbol, and
only the tests the real contract supports were written.

- **New lane — `tests/robot/`** (marker `robot`): `conftest.py` (real
  `BridgeProject` via the e2e fixture, the real gateway `app` + `TestClient`, a
  real `.xlsx` upload payload); `test_engine_oracles.py` (7 engineering oracles);
  `test_api_contract.py` (`/health`, `/version`, `/bridges/{parse,validate}`,
  `/draw/gad`, `/bills/generate`, `/qa/report`, `/exports/bundle`, `/plugins`,
  RFC 7807 `415`/`422`, 50 MiB cap); `test_exports.py` (8-sheet draw, DXF audit,
  byte determinism, workbook round-trip); `test_ui_streamlit.py` (`AppTest` page
  sweep + unicode input).
- **Contract facts pinned:** the draw package emits **8 sheets, not 7**; the ASGI
  object is `app`; uploads are `.xlsx` only; a bad `scale` returns a plain
  FastAPI `HTTPException(400)` (not problem+json) — the test asserts the actual
  shape, not the aspirational one.
- **Wiring:** `robot` marker registered in `pyproject.toml`; the `suite-ci.yml`
  unit job now runs `--ignore=tests/robot`; a new `oracles` job in `robot.yml`
  installs `dev,api,ui,draw` plus `httpx openpyxl`.
- **`docs/TEST_PLAN.md`** written against the retargeted lane and registered in
  `DOCS_INDEX.md`, the `mkdocs.yml` nav, and
  `.github/ISSUE_TEMPLATE/config.yml`.

**Verified (all green):** `python -m pytest tests/robot` → **31 passed,
5 warnings**; `python -m pytest tests/docs -q -m "not slow"` → **41 passed,
16 deselected**; `python scripts/check_doc_paths.py` → OK;
`python -m ruff check packages apps scripts` → *All checks passed*;
`python scripts/robot/gate.py` → exit 0; `--metrics` → `open S1=0 S2=0`.
Nothing committed (standing rule: commit only on explicit instruction).

