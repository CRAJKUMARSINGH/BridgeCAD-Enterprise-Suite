# Post-Test Debug Protocol

Deterministic order. Do not skip to patching.

Companion to `scripts/robot/run_robot.py` (the persona walker) and `artifacts/TRIAGE_LOG.md`
(the S1/S2 register). Severity / class vocabulary lives in the triage log header.

## Step 1 — Freeze the repro

The robot writes `{persona}_report.json` containing `seed` + full `trace`.
Replay exactly:

```sh
python scripts/robot/run_robot.py --url http://localhost:8517 --out artifacts/robot
```

Same seed → same path. Never debug from a screenshot alone.

## Step 2 — Minimize (delta debug)

Halve the trace, re-run, keep the half that still fails. Repeat to ≤ 6 steps.
A 400-step failure that reduces to "fill span=0, click Generate" is a one-line fix.

## Step 3 — Bisect

```sh
git bisect start
git bisect bad HEAD
git bisect good <last-known-good>
git bisect run python -m pytest -m "unit or api" -x -q
```

Guilty commit → `git show` it. Fix forward, don't revert blindly.

## Step 4 — Classify

| Sev | Definition | Gate |
|---|---|---|
| S1 | crash, 500, corrupt/empty export, wrong engineering number | blocks merge |
| S2 | silent no-op, missing validation, wrong label, unicode mojibake | blocks merge |
| S3 | layout overflow, a11y warning, slow tab | next sprint |
| S4 | cosmetic | backlog |

## Step 5 — Root cause (not symptom)

Answer all four in the issue body:

1. Where does the bad value first become bad? (trace it, cite file:line)
2. Why wasn't it caught before? (missing test / missing oracle)
3. What is the *class* of bug — validation, state, encoding, concurrency, units?
4. What else shares that class? (grep for siblings — fix all, or file follow-ups)

## Step 6 — Patch

One patch = one class. Follow `PATCH_GUIDE.md`. Never mix a refactor into a fix.

## Step 7 — Regression test first

Write the failing test from the minimized trace, watch it go red, then patch.

## Step 8 — Verify

```sh
python -m pytest tests/ -m "not slow" -q
python scripts/robot/run_robot.py --url http://localhost:8517 --out artifacts/robot
python scripts/robot/triage.py --metrics
```

All green, plus `S1 == S2 == 0`.

## Step 9 — Record

```sh
python scripts/robot/triage.py --ingest artifacts/robot
```

That appends the row to `artifacts/TRIAGE_LOG.md`: symptom, sev, class, patch §.
Then move it to Closed with the patch SHA and the regression-test path.
