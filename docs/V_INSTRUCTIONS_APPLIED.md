# Uploaded v.md: applicability and implementation ledger

Date: 2026-11-13. Baseline: `5d5f99e68b3efcc36fdfaf295d2e76d986d1fa69`.
The upload traces older commit `cbea900`; its predictions are not current test results.
This patch is applied in the available checkout. It does not write the Windows E: drive or push GitHub changes.

## Decisions

| Instruction | Decision and current evidence |
|---|---|
| B01: scale None crashes sheets 1/2 | Already addressed in current code; sheets import fit helpers, derive captions and generated successfully in the baseline run. Do not reapply the old diff. |
| B02: replace PWD_TYPES | Current source already uses a separate catalogue registry. Do not restore a duplicate table or script-importing registry. Catalogue defaults are frozen by existing tests. Exact correspondence to all PDF dimensions remains unverified. |
| B03: silently default wrong superstructure | Applied fail-closed dictionary/enum lookups, including foundation, abutment, material and bearing identities. Unknown values now fail rather than silently produce a plausible default. All 15 existing catalogue cards still build. |
| B04: add portal/integral/box abutment semantics | Deferred: current adapter deliberately maps to the supported cantilever path. Adding enum names alone would not implement the dependent geometry. Keep the limitation visible until validated sections and downstream consumers exist. |
| B05: NONE bearing creates elastomeric pad | Already corrected: catalogue NONE maps to an unset bearing, not an elastomeric default. Do not add a duplicate NONE enum or substitute the upload's obsolete member names. Bearingless detail completeness still needs reference review. |
| B06: auto-scale sections 3/5 using max span | Do not apply mechanically: a cross section's transverse extent is not its longitudinal span. Actual per-view clipping audits and layout recipes remain needed. |
| B07: entity floor not a reference oracle | Applied truthful structural-only success labels and blank-render failure gates. A complete calibrated semantic/reference oracle remains open; no 15/15 PDF-match claim is made. |
| B08: output root | Already EXAMPLES_PWD. Overrides already use out/pwd_sweep. |
| B09/B10: hardcoded kerbs / pier width | Deferred engineering choice: inspect reference-specific deck, kerb, skew and pier dimensions first. Automatically equating pier length to deck width plus 0.5 m is not independently justified. |
| B11: deterministic output | Applied existing write_deterministic helper to the booklet script outputs; no nonexistent scrub function introduced. Regression check compares every DXF in repeated nine-sheet runs. |
| B12: derive total length | Already performed in catalogue resolver; do not restore hand-maintained duplicate totals. |
| Catalogue scaffold | Already exists, with registry/schema/resolve/sweep and tests. Do not replace it with a dependency on the generator script. |
| Choice sweeps | Applied numeric comma-list support, retaining allowed-choice validation. Reject nonfinite values, malformed lists/ranges, reversed ranges and locked/derived sweep fields. |
| Sweep CI | Added workflow for existing supported 010 span, 006 skew and 009 carriageway dials. Omits undefined cell_clear_m/arch_rise_m dials and nonexistent tests/pwd --sweep option. Structural DXF generation explicitly skips PNG and does not claim visual acceptance. |
| Partial variant rejection | Applied nonzero exit for a batch containing rejected variants, including dry-run. |
| Render success reporting | Added nonblank pixel checks and exception reporting; errors affect package/batch verdict and render-status.json. This detects the observed defect; it does not repair its rendering root cause. |
| New box-cell/arch/precast primitives, BOQ, reinforcement and W76-W85 | Not copied as production implementations: upload has incomplete helpers, ellipses, conflicting data and unsupported type names. See concrete blockers below. |
| .md updates | Corrected enrichment claims and added current CLI, variable/layout, rendering and deployment guidance with master/index links. |
| .txt updates | Inspected docs/requirements-docs.txt and docs/api/requirements.txt; both are dependency lists, so no documentation edits were due. |

## Why the supplied geometry cannot be applied verbatim

- The supplied None-scale guard contains an always-true assertion (`... or True`); this is not a regression test.
- The box-cell formula with counts (4,3,4), clear width 5.0 and wall 0.55 gives `11*5.55 + 3*0.55 = 62.70 m`, while its test expects 61.05 m. The reference span sum quoted elsewhere is 61.25 m. Reconcile end walls, joints and unit lengths before implementation.
- The proposed `gap_pairs(3, ...)` simplifies to 2; multiplying by 2 gives 4, while the proposed test expects 52. The contract mixes strip interfaces with block joints.
- The schedule changes from 31 to 25 points in the upload and explicitly says its Y column was not reverified. It points to PDF page 27 for type 014, whereas the supplied index maps 014 to PDF page 26. Do not treat the pasted schedule as authoritative until checked against that page.
- The precast prototype promises equal arc-length blocks but uses equal horizontal station spacing; socket and block-orientation acceptance is not established.
- BOQ and drawing snippets call undefined helpers and fields (`_cell_areas`, `_block_len`, `raft_width_m`, panel functions, and ellipsis branches). Nominal rebar sizes and rates are proposals, not independently checked design inputs.
- A rule is not implemented merely because a W-number or layer name is present. Each semantic check needs a fixture proving it can fail on a wrong drawing.

Keep approximation flags for 004/014/015. Do not claim six matches, nine mismatches or complete reference parity solely from the older static trace.

## Validation

Executed results: **67 tests passed** in `tests/catalogue` (one external pytest-plugin deprecation warning). The patched DXF-only batch generated **15/15 packages**, and the new actual carriageway choice sweep generated **3/3 nine-sheet packages**. An actual rerender of type 002 Sheet 9 reproduced the blank image and was reported as an error by the new gate. Compilation and `git diff --check` passed. See accompanying logs for evidence. Added tests exercise permitted/rejected choice sweeps, all baseline model identities, misspelled identities, render errors/blank images, partial rejection, repeated-generation determinism and requested-render failure propagation. Existing catalogue tests remain part of the run. The new CI workflow is provided but has not run on GitHub.

The earlier full default run exited zero yet produced 24 blank PNGs. With this patch, reproducing a blank requested output is expected to fail; that is the corrected acceptance behavior, not proof that drawing fidelity has been repaired.
