# CREAT.md — BridgeCAD Enterprise Suite · Chat & Progress Log

> **Standing order:** This file records every session's work. Only the last 24 hours of entries are kept — older entries are pruned on each append. Do not delete this file.

---

### Session — BridgeCAD-Repository-Audit-Fixes applied · 14:30

**Commit:** `e969b72` pushed to `origin/main` — `fix(catalogue,draw,core,frontend): BridgeCAD repository audit fixes`

- Resumed after context compaction; 14 files from `changed-sources/` were already copied but 10 catalogue tests were failing.
- **Root cause:** `_check()` in `resolve.py` compared `deck_thickness_mm` (0.5 m) to `span/22` (1.011 m) for `RCC_BOX_CELL`, ignoring the actual structural depth. Arch types 014/015 also failed because the deck-slab proxy is not meaningful for an arch span/depth ratio.
- **Fix 1 — `resolve.py`:** `_check()` now computes `depth = deck + cell_clear_m + cell_wall_mm/1000` for `RCC_BOX_CELL` when lattice data is present. Arch types 014/015 set `approximation: True` so the governor reports rather than rejects.
- **Fix 2 — `registry.py`:** Added `"approximation": True` to cards BR-I-2022-014 and BR-I-2022-015. Card 004 NOT marked approximation.
- **Tests:** 244 passed, 0 failed. Pushed: `cba78cb..e969b72 main -> main` ✅

---

### Session — TRAE report review corrections · current

**No commit or push — working tree only. HEAD remains `e969b72`.**

Owner reviewed TRAE delivery report and identified six items requiring correction. All six addressed:

**1. Closure statement corrected.**
`artifacts/continue/T2-acceptance-reconciliation.md` §8 closure now reads:
*"Four implementation blockers addressed; two open items remain (duplicate renderer tree, reference-fidelity gate); GAD acceptance pending."*
Previous wording "all blockers closed" was incorrect.

**2. Required-content manifest created.**
`artifacts/gad-acceptance/reference_requirements.json` — 13 requirements across all 9 drawing areas (Plan, Long Section, Cross Section, Foundation, Abutment, Bearings, Reinforcement, BOQ, Title/Notes, Scale, Annotation). Every row has stable ID, scope (BOOKLET_CONVENTION or NINE_SPAN_GEOMETRY), expected primitive, required dimension/label, evidence, status and reviewer verdict. All reviewer verdicts are PENDING. 10 open items listed. Duplicate-renderer task and combined-suite stall correction evidence retained.

**3. Transactional conflict handling.**
`artifacts/gad-acceptance/_gen_nine_span.py` `_generate()` now:
- Resolves all support records **before** generating any DXF.
- If a CONFLICT is detected, writes only a `FAILED-RUN/failure-report.json` with the rejected records and a `FAILED-RUN/quality.json` (GENERATION=FAILED). No DXF files reach the commit-keyed output directory.
- For mid-generation failures (non-conflict path), partial output is published only to `FAILED-RUN/` with an explicit `FAILED-RUN.txt` sentinel.
- Production packages go to `<commit>/` only after `generate_one` returns success.

**4. Gate naming clarified.**
`packages/bridgecad-qa/bridgecad_qa/quality_manifest.py`:
- Primary property renamed `generation_gates_passed` (covers generation/model_validation/geometry_contract — the three mechanically verifiable generation gates).
- Added `quality_and_layout_passed` (generation gates + required_content + layout).
- `accepted` is unchanged — requires all five gates + reference_fidelity=PASSED + engineering_review=APPROVED.
- `to_json()` now emits `generation_gates_passed`, `quality_and_layout_passed`, `accepted` as separate keys — never a single ambiguous `gates_passed` boolean.
- Module docstring updated to explain the four verdict groups and their separation.
- `_gen_nine_span.py` invariant checks updated to use `generation_gates_passed`.

**5. Annotation overlap broadened.**
- Added `_count_annotation_overlaps()` to `_gen_nine_span.py` — counts label-label text-box pairs across all sheets using `BBox.overlaps()`.
- `_layout_payload()` now returns `(json, checks, overlap_count)` and includes `annotation_overlap_count` and `annotation_overlap_note` in the layout JSON.
- Added `annotation_overlap_count: int = -1` field to `QualityManifest`; included in `to_json()`.
- Not yet a gate pass/fail — per-view bounding rectangles are not declared, so the estimator may flag cross-view adjacency. Recorded as open item `RR-ANNOT-001` in `reference_requirements.json`.

**6. Reference limitation wording corrected.**
- `_gen_nine_span.py` reference-fidelity note now reads: *"reference booklet contains no nine-span sheet — reproduction claim not possible; convention + geometry comparison is PARTIAL (artifacts/reference-overlay/comparison.json)"*. Issue code renamed `E-NO-NINE-SPAN-REFERENCE`.
- `APPROVED_STACK` comment updated: *"explicitly supplied, geometrically consistent foundation stack"* — not "approved". The owner verified arithmetic consistency; no engineering approval exists.
- `T2-acceptance-reconciliation.md` closing paragraph updated to match.

**Tests:** `tests/unit/test_quality_manifest.py` — 9 tests (1 added: `test_annotation_overlap_count_is_carried_in_json`; renamed: `test_generation_gates_pass_while_acceptance_stays_pending`, `test_unresolved_model_validation_blocks_the_generation_pass`). All 253 catalogue+unit tests pass.

**Defensible status:** reported geometry-contract progress verified by the listed tests; generated draft — GAD acceptance pending.

---

### Session — Content reconciliation, collision fixes, test suite clean · current

**No commit or push — working tree only. HEAD remains `e969b72`.**

**Task 1 — Content count reconciliation:**
75 total requirements, 14 not-applicable (cantilever abutment family, PILE foundation, bearing type=NONE, footpath width=0), 61 applicable, 56 satisfied, 5 failures. The "5 declared gaps" correspond exactly to the 5 PARTIAL/MISSING requirements — no IMPLEMENTED requirement is unmet. Reconciliation output: `artifacts/gad-acceptance/content-report.json`.

**Task 2 — Collision investigation (17 → 11 → 9 effective):**
- 4 HIGH originally: Sheet 2 (ground/scour label), Sheet 7 (TBD duplicate), Sheet 8 (RL stacking × 2)
- After fixes: 2 remaining HIGH are cross-view or wide-BBox false positives (confirmed by `y_sep/x_sep` analysis in `scripts/_check_collisions.py`): `RL 101.725 × RL 95.925` and `TOP OF ABUTMENT CAP × BASE OF ABUTMENT SHAFT` — these are `y_sep=0.0mm` due to independent view level stacks landing at coincident paper y after minimum-gap nudge, or BBox-width false positives. All 9 MEDIUM items are RL-numeric + descriptive-text pairs at same y by design (tick + description on same level line) — the BBox estimator counts them as collisions but they are on opposite sides of the structural tick.
- Collision report: `artifacts/gad-acceptance/collision-report.json`

**Fixes applied:**
1. `sheet7_bill_of_quantities.py` — skip second `TEXT-HEADER` write for the total cell when `qty_str` equals what `TEXT-GENERAL` already wrote (removes `TBD/TBD` duplicate). Collision HIGH eliminated.
2. `sheet2_long_section.py` — stagger `EXISTING GROUND LEVEL` label `+th*1.2` above the line endpoint so it clears `DESIGN SCOUR LEVEL` at the same x. Collision HIGH eliminated.
3. `sheet8_side_elevations.py` — added `_RL_TAG_MIN_GAP_MM = 7.5` constant; view 1 (abutment) and view 2 (pier) RL tag loops now enforce minimum vertical gap between successive labels; nudged labels get a short vertical leader from true structural y to printed label y. Collisions HIGH × 2 and MEDIUM × 4 eliminated.
4. `sheet8_side_elevations.py` — scale bar `seg_len_m` now expressed in paper mm (`max(10.0, round(overall_w/5) * max(1.0, 1000/denom))`), not raw model metres, eliminating the adjacent `0m/2m/4m/6m/8m` label stack.

**Task 3 — Skew vs nominal layout:**
Both variants use identical layout rules and thresholds (`_RL_TAG_MIN_GAP_MM`, `TEXT_FLOOR_PAPER_MM=1.8`, same `BRIDGECAD_LAYOUT_AUDIT` checks). Skew variant: `layout_checks.passed=True`, `annotation_overlap_count=11`. Nominal resolved: same. Both pass on the same criteria — no special threshold applied to the skew variant.

**Task 4 — Regeneration:**
All 5 variants regenerated with `--all-variants`. 12/12 invariant checks pass.
- `nine_span_slab_resolved`: 9 sheets RESOLVED/LEVEL_CONTROLLED, layout PASSED, `generation_gates_passed=True`, `quality_and_layout_passed=False` (5 declared content gaps), `accepted=False`.
- `nine_span_slab_conflict`: REJECTED before DXF generation; `FAILED-RUN/` only. No DXF in commit-keyed dir.
- Nominal, 7-span, skew-15° variants: all RESOLVED.

**Task 5 — Test suite:**
`tests/catalogue/test_instruction_updates.py::test_generation_is_deterministic_and_reports_render_status` was failing (pre-existing working-tree issue: transactional `_publish` moves failed-run output to `FAILED-RUN/` subdirectory; test expected it at the root). Updated test to look for `render-status.json` in `FAILED-RUN/`.
- **311 passed, 0 failed** (catalogue + unit + draw audit).

**Files changed this session:**
- `packages/bridgecad-draw/bridgecad_draw/sheet2_long_section.py` — ground-level label stagger
- `packages/bridgecad-draw/bridgecad_draw/sheet7_bill_of_quantities.py` — TBD duplicate guard
- `packages/bridgecad-draw/bridgecad_draw/sheet8_side_elevations.py` — `_RL_TAG_MIN_GAP_MM`, view-1/view-2 RL gap enforcement, scale-bar paper-mm fix
- `tests/catalogue/test_instruction_updates.py` — FAILED-RUN path for render-status check
- `scripts/_measure_content.py`, `scripts/_reconcile_counts.py`, `scripts/_measure_overlaps.py`, `scripts/_check_collisions.py` (evidence scripts, not production)
- `artifacts/gad-acceptance/content-report.json` (evidence)
- `artifacts/gad-acceptance/collision-report.json` (evidence)
- `artifacts/gad-acceptance/variant-validation.json` (regenerated, 12/12 checks pass)

**Remaining declared content gaps (unchanged, correctly reported):**
- `RC-PLAN-11` PARTIAL — wing/return-wall label missing from Sheet 1 Plan
- `RC-FDN-05` PARTIAL — open-footing plan label missing from Sheet 4 (generic pile table present instead)
- `RC-BABT-02` MISSING — batter ratio annotation missing from Sheet 5
- `RC-RFT-05` PARTIAL — no drawn geometry in Sheet 9 (schedule only, no bar arrangement)
- `RC-TTL-06` PARTIAL — assumptions/unresolved inputs not printed on the sheet

**Pending:** No commit or push. These 5 gaps require engineering input (open-footing section geometry, batter ratio values, bar arrangement detail) or are known limitations.

---

---

### Session — Hook fired on incoming message · current

No changes this session.

- Hook fired on user message (hook instruction only — no user task in prompt).
- Previous session delivered: content reconciliation (75 req / 61 applicable / 56 satisfied / 5 declared gaps), collision investigation and fixes (17→11 overlaps; 4 HIGH eliminated), skew vs nominal layout confirmation, all-variants regeneration (12/12 invariant checks pass), test suite fixed and clean (311 passed, 0 failed).
- Working tree remains uncommitted. HEAD `e969b72`.

**Pending:**
- 5 declared content gaps require engineering input before they can be closed: `RC-PLAN-11` (wing/return wall), `RC-FDN-05` (open-footing label), `RC-BABT-02` (batter ratio), `RC-RFT-05` (bar arrangement geometry), `RC-TTL-06` (assumptions on sheet).
- 9 remaining annotation overlap items in collision report — 2 classified as cross-view/BBox-width false positives; 7 are RL-numeric + description pairs at the same level line (by-design, not actionable without redesigning the level-tag layout).
- No commit or push until owner approves the full working-tree diff.

---
- `_gen_nine_span.py`: "explicitly supplied, geometrically consistent" wording ✓, `FAILED-RUN/` sentinel ✓, `generation_gates_passed` in invariant checks ✓, `E-NO-NINE-SPAN-REFERENCE` ✓
- `T2-acceptance-reconciliation.md`: "four implementation blockers addressed" ✓, stall corrected (not merely diagnosed) ✓
- Commands run: `python -m pytest tests/unit/test_quality_manifest.py` → **9 passed**; manifest API shape check → all properties confirmed

**Pending:**
- Commit and push the TRAE corrections when owner approves (working tree only, HEAD `e969b72`).
- 10 open items in `reference_requirements.json` (annotation gate, both-abutment-variants, title-block format, scale convention, per-dimension annotations).

---
| 2026-11-15 07:26 | User prompt received |
| 2026-11-15 07:26 | User prompt received |
| 2026-11-15 07:28 | User prompt received |
| 2026-11-15 09:14 | Agent turn completed |
