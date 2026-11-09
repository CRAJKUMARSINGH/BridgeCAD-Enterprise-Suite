# Robotic Test Guide

**Purpose.** A repeatable, scripted way to "exercise the app like a user" —
no clicking, no manual setup. Every command below is deterministic (seeded),
prints a pass/fail verdict, and exits non-zero on failure, so it can be wired
into CI or run by hand *from time to time* before a push, a merge, or a demo.

**Where to run it.** Always from the **repo root** (there is no nested
sub-project to step into). The repo is zero-install: `python -m bridgecad`
bootstraps the workspace on its own.

---

## 1. The 60-second check — all three personas

The fastest end-to-end confidence check. Runs a novice, an intermediate, and
an expert journey in sequence and prints one verdict per persona.

```powershell
python scripts/robotic_smoke.py --persona all --seed 42
```

Equivalent convenience target (if `make` is on your PATH):

```powershell
make robotic
```

Expected tail:

```text
[BASIC] passed=True  steps=3
[INTERMEDIATE] passed=True  steps=2
[ADVANCED] passed=True  steps=3
Wrote reports\smoke_report_seed42.json
```

Exit code `0` = all personas passed; non-zero = at least one did not.

---

## 2. Run one persona at a time (to isolate a failure)

| Persona | Simulates | What it proves | Flags |
|---|---|---|---|
| Basic | A first-time user | `verify` passes, an 11-span drawing package generates, PDFs are produced | `--seed`, `--iterations` |
| Intermediate | A user tweaking inputs | Generation still succeeds and the QA score stays ≥ 60 | `--seed`, `--mutations` |
| Advanced | A power user / developer | The project schema serialises, and `tests/unit` passes | `--seed`, `--hypothesis`, `--e2e` |

```powershell
python scripts/basic_user_robot.py        --seed 123 --iterations 3
python scripts/intermediate_user_robot.py --seed 456 --mutations 5
python scripts/advanced_user_robot.py     --seed 789
```

Optional heavier variants for the advanced persona:

```powershell
python scripts/advanced_user_robot.py --seed 789 --hypothesis
python scripts/advanced_user_robot.py --seed 789 --e2e
```

Each run writes a JSON evidence file next to the others under `reports/`
(`reports/basic_robot.json`, `reports/intermediate_robot.json`,
`reports/advanced_robot.json`). Those files are scratch output and are **not**
committed.

**Change the seed** to widen coverage without changing the code:

```powershell
python scripts/robotic_smoke.py --persona all --seed 7
python scripts/robotic_smoke.py --persona all --seed 99
```

---

## 3. The full robotic sweep (the "green stack")

Run this before a push or a merge. Each line must be green. The last three
lines are the **draw lanes** — without them "green" would only prove the
frontend contract, never that a drawing package was actually produced.

```powershell
python -m ruff check packages/ apps/ scripts/
python -m ruff format --check packages/ apps/ scripts/
python -m pytest tests/docs -q -m "not slow"
python scripts/verify_docs.py
python scripts/robotic_smoke.py --persona all --seed 42
python -m pytest tests/draw -m draw -q
python -m pytest tests/drawings --regression -q
python tests/e2e/run_e2e.py
```

Expected results:

| Step | Expected |
|---|---|
| `ruff check` | `All checks passed!` |
| `ruff format --check` | `N files already formatted` |
| `pytest tests/docs` | all pass, some deselected (slow lane) |
| `verify_docs.py` | `3 passed, 0 failed, 3 skipped` (lychee/mkdocs/sphinx skipped when absent) |
| `robotic_smoke.py` | every persona `passed=True`, exit `0` |
| `pytest tests/draw -m draw` | promoted sheets pass; pre-RC1 scaffolds xfail or are deselected (see below) |
| `pytest tests/drawings --regression` | `N passed`; layer audit and PDF/A gates green |
| `tests/e2e/run_e2e.py` | `28` fixtures, each `*** ACCEPTED ***`; every sheet ≥ 20 entities |

> **Scaffold baseline (not a regression).** Sheets 2, 3, 4, 6 and 7 are the
> documented pre-RC1 scaffolds and carry no dimensions yet, so
> `test_non_scaffold_sheets_are_dimensioned` is `xfail` and the scaffold lane in
> `.github/workflows/draw.yml` is `continue-on-error`. The three lines above are
> only "green" when the *non-scaffold* sheet contracts and the E2E fixture
> packages pass — the scaffold xfails are expected.

Equivalent convenience target (if `make` is on your PATH):

```powershell
make green-stack
```

---

## 4. The release gate (heavier lane)

When you want the same bar CI and release candidates use:

```powershell
python rc1_smoke.py
python -m bridgecad verify
python -m pytest tests/ --ignore=tests/e2e --ignore=tests/benchmarks --ignore=tests/draw --ignore=tests/drawings --ignore=tests/refs -m "not slow" -q --cov
```

These are the same commands exposed as `make smoke`, `make verify`, and
`make cov`.

---

## 5. Suggested cadence

- **Every code change** → Section 1 (all three personas, seed 42).
- **Before a push / PR** → Section 3 (the full sweep).
- **Before a release or demo** → Section 4 (the release gate).
- **Weekly, or after a dependency bump** → Section 2 with two extra seeds.

---

## 6. Troubleshooting

- **Long lanes look frozen.** Python block-buffers stdout when piped. Prefix
  with `-u` to stream live: `python -u -m pytest tests/docs -q -m "not slow"`.
- **`fatal: Unable to create '.git/index.lock'`.** A stale Windows lock.
  Run `python scripts/clear_stale_locks.py --force`. If the file survives,
  delete `.git/index.lock` from your editor and retry.
- **`reports/` and `outputs/` dirty your tree.** They are generated. Add
  `reports/` to `.gitignore`, or restore `outputs/` before committing.
- **A persona fails but unit tests pass.** Re-run just that persona with a
  fresh seed (Section 2) to see whether it is a real regression or an edge case.

---

## 7. Post-test debug playbook

When a persona fails, work the following order — cheapest check first. This is the
persona-CLI view; the general protocol (classify → minimize → bisect → patch) lives in
[docs/TRIAGE_AND_DEBUG.md](docs/TRIAGE_AND_DEBUG.md) and
[docs/PATCH_GUIDE.md](docs/PATCH_GUIDE.md).

1. **Re-run just that persona, fresh seed, streaming output.**

   ```powershell
   python -u scripts/basic_user_robot.py --seed 7 --iterations 1
   ```

   Then read its evidence file (`reports/basic_robot.json`, `reports/intermediate_robot.json`,
   `reports/advanced_robot.json`, or `reports/smoke_report_seed*.json`).

2. **Core model & acceptance.** `python -m bridgecad verify` must print
   `★ ACCEPTED ★` for both Day 3 (model, 7 checks) and Day 4 (geometry/QA, 8 checks).

3. **Generation forensics.**

   ```powershell
   python -m bridgecad generate 11span
   Get-ChildItem outputs\11span_110m_rcc_slab
   ```

   Confirm `project_*.json`, the eight `*Sheet*.dxf` / `*.pdf` pairs, and the GAD PDF exist.

4. **Drawing contract** (needs `ezdxf`).

   ```powershell
   python -m pytest tests/draw -q --tb=line -k "not visual"
   ```

   Several XFAILs on scaffold sheets are expected (see Section 8).

5. **Collect artefacts for a patch PR:** the failing `reports/*_robot.json`, the relevant
   `outputs/**/project_*.json`, one failing DXF + its PDF, the full `verify` log, and
   `pytest --tb=short` output.

---

## 8. Known residual issues

- **QA score lives behind the CLI, not always in the project JSON.** A generated
  `project_*.json` may omit `qa_score` / `qa.score`, so `robotic_smoke.py`'s intermediate
  persona reports `score: null` (treated leniently). The authoritative score comes from
  `python -m bridgecad qa <project.json>`. `scripts/intermediate_user_robot.py` calls that
  CLI explicitly and, with `--strict-qa`, fails when the score is missing or `< 60`.
- **Missing optional dependencies.** `hypothesis` is only needed for the advanced property
  lane; when absent, `scripts/advanced_user_robot.py --hypothesis` records the step as
  `skipped` instead of failing, so zero-extra-deps environments stay green. `ezdxf` is
  required for the `tests/draw` lane.
- **Legacy geometry bugs are already fixed.** The off-by-one pier/footing loops
  (`range(1, nspan)` → empty for a single-span bridge) and the degenerate `ABTL = 0`
  abutment wall in `src/bridge_gad/` carry the C1.5 fix (an explicit simple-span path plus
  a `FUTL`/`ALCL` fallback ladder). New work should use `packages/bridgecad-draw`, which is
  the primary generation path.
- **Scaffold-sheet XFAILs are intentional.** The under-dimensioned scaffold sheets stay
  XFAIL until the roadmap finishes sheet dimensioning; do not treat them as hard failures.

---

**See also:** [GUIDE.md](GUIDE.md) (the authoritative operating guide),
[CONTRIBUTING.md](CONTRIBUTING.md) (workflow and gates), and
[README.md](README.md) (repo orientation).
