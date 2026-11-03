# Post-test debug protocol

Deterministic order. Do not skip to patching.

Ported from the Venice-patch robotic test kit and adapted to this repo: the
walker lives in `scripts/robot/`, the register in `artifacts/TRIAGE_LOG.md`.

**See also:** [ROBOTIC-TEST-GUIDE.MD](../ROBOTIC-TEST-GUIDE.MD) (how to run the
robots) · [PATCH_GUIDE.md](PATCH_GUIDE.md) (fix patterns by class) ·
[TRIAGE_LOG.md](../artifacts/TRIAGE_LOG.md) (the S1/S2 register).

---

## Step 1 — Freeze the repro

The walker writes `artifacts/robot/{persona}_report.json` containing the `seed`
and the full `trace`. Replay it exactly:

```sh
python scripts/robot/run_robot.py --url http://localhost:8517 --out artifacts/robot
```

Same seed → same path. Never debug from a screenshot alone.

## Step 2 — Minimize (delta debug)

Halve the trace, re-run, keep the half that still fails. Repeat down to ≤ 6
steps. A 400-step failure that reduces to "fill span = 0, click Generate" is a
one-line fix.

## Step 3 — Bisect

```sh
git bisect start <bad> <last-known-good>
git bisect run python -m pytest tests/unit -x
```

Guilty commit → `git show` it. Fix forward; do not revert blindly.

## Step 4 — Classify

| Sev | Definition | Gate |
|---|---|---|
| S1 | crash, 5xx, corrupt/empty export, wrong engineering number | blocks merge |
| S2 | silent no-op, missing validation, wrong label, mojibake | blocks merge |
| S3 | layout overflow, a11y warning, slow tab | next sprint |
| S4 | cosmetic | backlog |

## Step 5 — Root cause (not symptom)

Answer all four in the issue body:

1. Where does the bad value first become bad? Trace it, cite `<file>:<line>`.
2. Why wasn't it caught before? (missing test / missing oracle)
3. What is the *class* of bug — validation, state, encoding, concurrency, units?
4. What else shares that class? Grep for siblings — fix all, or file follow-ups.

## Step 6 — Patch

One patch = one class. Follow [PATCH_GUIDE.md](PATCH_GUIDE.md). Never mix a
refactor into a fix.

## Step 7 — Regression test first

Write the failing test from the minimized trace, watch it go red, then patch.

## Step 8 — Verify

```sh
python -m pytest tests/unit tests/integration -q
python tests/e2e/run_e2e.py
python scripts/robot/run_robot.py --out artifacts/robot
python scripts/robot/gate.py
```

All green, plus `open S1=0` from `python scripts/robot/triage.py --metrics`.

## Step 9 — Record

Append to [TRIAGE_LOG.md](../artifacts/TRIAGE_LOG.md): symptom, sev, root cause,
patch SHA, test path — then flip the row from `UNCONFIRMED` to `OPEN`, or move it
to `Closed` with the SHA.
