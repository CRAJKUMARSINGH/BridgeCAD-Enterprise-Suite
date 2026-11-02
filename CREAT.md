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

## 2026-11-01

### Workspace

- **`CODE-JUNCTION/1.TXT` applied selectively** — honouring the "IF SUITABLY
  NEEDED" rule, every claim was checked against the working tree before acting.
  - *Applied:* bare `tuple` annotations in `morth_specs.py` → `tuple[int, int]`
    (mypy `--strict`); trailing `import math` hoisted out of the end of
    `irc_21.py` (ruff E402); complete public re-exports added to
    `bridgecad_core/standards/__init__.py` and `bridgecad_core/__init__.py`.
  - *Rejected:* the brief's rewritten `load_combinations.py` — the module
    already exists with a live, tested API and the rewrite would break
    `tests/compliance/test_load_combinations.py`; likewise its `pyproject.toml`
    mypy `files` key (cosmetic only). The brief's invalid enum literals
    (`POT_BEARING`, `MODULAR`, `ARCH_BRIDGE`) were replaced with real
    `bridgecad_core.types` members.
- **7 orphaned plugins restored** — `arch_bridge`, `cable_stayed`,
  `pipe_culvert`, `psc_boxgirder`, `solid_slab`, `steel_composite`, and
  `voided_slab` now each ship a manifest, defaults, and draw-overrides. **10
  stray marker files deleted** — files literally named
  `['manifest.json', 'draw_overrides.py', 'defaults.yaml']`. The registry now
  discovers **10/10** plugins.
- **New wiring guard** — `scripts/verify_wiring.py` plus
  `tests/plugins/test_plugin_wiring.py`, so the "defined-but-unreachable" class
  of defect cannot recur silently.

### Roadmap

- No new roadmap week opened. This pass cleared wiring and re-export debt
  carried from the `CODE-JUNCTION` intake; the 52-week plan in `docs/upgrade/`
  is unchanged.

### Verification

- `python scripts/verify_wiring.py` → WIRING OK (10 plugins wired, standards
  fully exported, no bare generics).
- `pytest tests/compliance tests/verification -q` → **92 passed**.
- `pytest tests/docs -q -m "not slow"` → **41 passed**, 16 deselected.
- `pytest tests/docs -q -m "slow"` → **16 passed** in 37:45.
- `mypy .../standards --strict` clean · `ruff check` and `ruff format --check`
  clean.
- **False "hang" resolved.** A `tests/docs` lane that showed no output for
  ~38 minutes was **not** hung — it completed (row above). The blank screen was
  output withholding: `Select-Object -Last N` cannot stream, and a piped
  `python` block-buffers stdout (proven — a `Tee-Object` log file did not
  appear until the process exited). The single genuinely unbounded wait, the
  `check_doc_paths.py` subprocess in `tests/docs/test_gates_selfcheck.py`, now
  carries `timeout=300`.

### Not taken (explicitly out of scope this pass)

- `pytest-timeout` dev dependency plus a global `timeout` ini key. Deferred
  deliberately: the ini key breaks every `pytest` run when the plugin is not
  installed, and local runs do not install the dev extras. Awaiting the
  maintainer's go-ahead.
- Committing any of the above (standing rule: commit only on explicit
  instruction).
