# BridgeCAD release verification

25 November 2026 IST

## Phase 0 baseline

| Check | Command or evidence | Result |
|---|---|---|
| Audit baseline | Tag `rc1-audit-baseline` at `a488ea8` | 1,976 tracked files and 103,332 Python lines |
| Tagged test inventory | `python -m pytest -p no:hypothesispytest --collect-only -q` in the tagged archive | 1,587 tests collected |
| Clean base collection | `python -m pytest --collect-only -q` in a clean Python 3.11 environment with no dev extras | Pass. 1,532 tests collected, seven optional modules skipped |
| Unit baseline | `coverage run --branch -m pytest -p no:hypothesispytest -q tests/unit` in the tagged archive | 190 tests passed. Combined line and branch coverage from this lane was 72.67%, below the 75% floor |
| CLI after the file moves | `python -m bridgecad verify` | Pass. All 15 checks passed |
| Documentation | `python -m mkdocs build --strict` | Pass locally |
| Reference drawings | `python scripts/capture_release_baseline.py` with the tagged archive and `--repeat-drawings` | Three fixtures generated 11 DXFs each. The two runs differed in each fixture's hash manifest |
| Remote phase gate | CI run and merged Phase 0 pull request | Pending |

The source revision, timings, and SHA-256 values are in `audit/baseline.json`.

## Acceptance status

| Criterion | Status |
|---|---|
| AC-1 Cross-platform install and test | Pending. Python 3.11 on Windows was verified for the checks above |
| AC-2 Base collection | Passed locally on Python 3.11 |
| AC-3 QA registry coverage and advertised count | Pending |
| AC-4 Drawing exception handling | Pending |
| AC-5 Public entry points across types and formats | Pending |
| AC-6 Issued BOQ integrity | Pending |
| AC-7 Byte-identical DXF | Failed at the baseline. All three fixture manifests differed on repeat generation |
| AC-8 Clause traceability and provisional markers | Pending |
| AC-9 Strict typing and lint | Pending |
| AC-10 Coverage | Pending. The measured unit lane was below the repository floor |
| AC-11 Security scanning and SBOM | Pending |
| AC-12 Container service and image checks | Pending |
| AC-13 Accessibility and keyboard walkthrough | Pending |
| AC-14 Bundle and runtime budgets | Pending |
| AC-15 Governance, documentation and ADRs | Partial. Local docs build passed. Publication and the remaining ADRs are pending |
| AC-16 Generated artifact and LFS policy | Pending |
| AC-17 Independent engineering sign-off | Pending. No reviewer or date has been recorded |

Agent-generated engineering values are not a substitute for engineer review.
