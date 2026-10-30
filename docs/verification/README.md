# Verification & Validation (V&V)

This directory holds the benchmark lane for the calculation engine in
`packages/bridgecad-core`. Its job is narrow: prove that every deterministic
function still returns the value it is *defined* to return, and let one command
fail the build when it does not.

## The tier model

`TOLERANCE_POLICY.md` defines five tiers by the *method* a function uses, not by
how easy it is to pass:

| Tier | Method | Tolerance |
|------|--------|-----------|
| A | Closed-form, single formula | exact |
| B | Series / numerical integration | 0.1% relative |
| C | Iterative solver | 0.5% relative |
| D | Cross-tool reference | 1.0% relative |
| E | Drawing / geometry | 0 mm positional, exact layer set |

Each benchmark declares its tier in `tests/verification/cases.py`. The tier
selects the tolerance applied by `assert_within_tier` — a Tier A case compares
exactly, a Tier E case uses the thread-thin geometric tolerance. See
[TOLERANCE_POLICY.md](TOLERANCE_POLICY.md) for the full rationale and rules.

## What a benchmark actually checks

No expected value is copied from an external standard. Every case is one of:

- **A closed-form identity** justified from first principles — `to_dxf_mm` is
  metres times 1000, deck volume is `length x width x thickness`, a priced line
  is `rate x quantity`, `sum(span_lengths) == total_length`.
- **A structural invariant** — a pile group's centroid sits at the group origin,
  a compliance score stays inside `[0, 100]`, a span boundary list starts at 0
  and increases monotonically, a rule registry has no duplicate ids.

If a value cannot be derived this way, it is not asserted — a different
invariant is chosen instead.

## How a benchmark maps to a module

Each `Case` in `cases.py` names the engine module it exercises
(`module`, e.g. `bridgecad_core.geometry.foundation`) and a `check` callable.
`tests/verification/test_benchmarks.py` parametrises one pytest item per case
over `REGISTRY`, reusing the existing `tests/unit/conftest.py` fixtures
(`project`, `blank_project`, `span_variant`) so no fixture logic is duplicated.

`BENCHMARKS.md` is the human-readable index: one row per case with its id,
module, tier and the property it verifies.

## How drift fails the build

Any change that moves a case outside its tier tolerance raises an
`AssertionError` and fails `python -m pytest tests/verification`. Because the
assertions are identities rather than snapshots, a failure means behaviour
changed — it is never silenced by re-recording output (see rule 4 in
`TOLERANCE_POLICY.md`).

## Adding a new case

1. Write a `_check_*` function taking a `BenchContext` and asserting either a
   closed-form identity or a structural invariant with `assert_within_tier`.
2. Append a `Case(id, module, tier, description, assertion, check)` to
   `REGISTRY` in `tests/verification/cases.py`.
3. Add a matching row to `BENCHMARKS.md`.
4. Run `python -m pytest tests/verification -q` and
   `python -m ruff check tests/verification`.
