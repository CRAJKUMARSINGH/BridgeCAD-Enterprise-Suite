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
