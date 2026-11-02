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

Run this before a push or a merge. Each line must be green.

```powershell
python -m ruff check packages/ apps/ scripts/
python -m ruff format --check packages/ apps/ scripts/
python -m pytest tests/docs -q -m "not slow"
python scripts/verify_docs.py
python scripts/robotic_smoke.py --persona all --seed 42
```

Expected results:

| Step | Expected |
|---|---|
| `ruff check` | `All checks passed!` |
| `ruff format --check` | `N files already formatted` |
| `pytest tests/docs` | all pass, some deselected (slow lane) |
| `verify_docs.py` | `3 passed, 0 failed, 3 skipped` (lychee/mkdocs/sphinx skipped when absent) |
| `robotic_smoke.py` | every persona `passed=True`, exit `0` |

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

**See also:** [GUIDE.md](GUIDE.md) (the authoritative operating guide),
[CONTRIBUTING.md](CONTRIBUTING.md) (workflow and gates), and
[README.md](README.md) (repo orientation).
