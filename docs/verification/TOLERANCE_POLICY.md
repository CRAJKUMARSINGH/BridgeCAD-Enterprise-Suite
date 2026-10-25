# Verification Tolerance Policy

Tolerances define what "correct" means for automated V&V. Any benchmark
outside its tier fails the build.

| Tier | Method | Tolerance | Rationale |
|------|--------|-----------|-----------|
| A | Closed-form, single formula | exact (0 decimal places) | No numerical method involved |
| B | Series / numerical integration | 0.1% relative | Convergence-limited |
| C | Iterative solver | 0.5% relative | Solver tolerance dominates |
| D | Cross-tool (STAAD/MIDAS/CSI) | 1.0% relative | Different formulations |
| E | Drawing / geometry | 0 mm positional, exact layer set | Deterministic by design |

## Rules
1. Every benchmark declares its tier in the test file.
2. Tier is chosen by method, never by how hard it is to pass.
3. Tightening a tolerance is a feature; loosening one needs a written reason in the PR.
4. Golden files are regenerated only with an explicit justification in the PR body.
5. Tolerance changes are reviewed as engineering decisions, not as test fixes.

## Prohibited
- `pytest.approx` with a default tolerance on a Tier A case.
- Snapshot tests that pass by re-recording output without inspection.
