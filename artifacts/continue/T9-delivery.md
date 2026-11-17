# T9 — Delivery index (NO commit, NO push)

Prepared 2026-11-15. Working tree only. Nothing staged, committed or pushed.

## 0. Tree state

- HEAD: `e969b72979196f78e2d04129c2462268d6caf099` (branch `main`) — unchanged all session.
- `packages/bridgecad-catalogue/bridgecad_catalogue/registry.py` SHA-256
  `ADD973A4D45B6B108A575C090CF9BABAD340495D80AA1C8372570D3855184FA2` — **unchanged** from the
  recorded `T1c` value, so this session was not a second writer of that file.
- Snapshots: `T1d-head.txt` … (earlier capture) and this session's final capture
  `T9-final-head.txt`, `T9-final-status.txt`, `T9-final-diff-stat.txt`, `T9-final-tracked.diff`,
  `T9-final-untracked.txt`.
- Untracked inventory: 150 paths (`T9-final-untracked.txt`), of which 13 are top-level `?? ` entries in
  `T9-final-status.txt` (the rest are files inside `artifacts/**`, `outputs/**`).

## 1. Reviewed tracked diff (18 files, +839 / −341)

| File | Δ | Rationale (reviewed) |
|---|---|---|
| `packages/bridgecad-core/…/geometry/long_section.py` | +53 | Canonical support-level input: passes `shaft_height_m`, leaves `authority` unset (auto HEIGHT_CONTROLLED/LEVEL_CONTROLLED); `cap_thk<=0 ⇒ footing_depth_m=None`; `pile_cutoff_level_m` carried only as `pile_cutoff_rl_m`; raises on CONFLICT (fail-closed drawing guard). |
| `packages/bridgecad-catalogue/…/schema.py` | +45 | **(Blocker 1)** seven `_free` design dials (footing-bottom RL / footing depth / cap depth / bearing depth / pedestal height / wearing depth / pile-cap thickness) so a designed footing is a *declared input*, not a fabricated constant. |
| `packages/bridgecad-core/…/models.py` | +10 | **(Blocker 1)** `FoundationDetails.footing_bottom_rl_m` — the founding RL field the dial writes into. |
| `packages/bridgecad-draw/…/layout_audit.py` | +273 | **(Blocker 3)** measured `Region` rectangles (sheet/frame/title-block/notes), `layout_checks()` gate (clipping/title_block/notes_zone/scales/text_floor), and the `_is_note_line` fix (a decimal is not a note). |
| `packages/bridgecad-qa/…/__init__.py` | +5 | Export `QualityManifest`/`Gate`/`Verdict`. |
| `scripts/generate_all_pwd_gads.py` | +190 | **(Blockers 1, 2, 4 + transactional generation)** consume the dials; write the named RL chain into `params.resolved.json` (`_support_level_chain`); emit a fail-closed `quality.json` beside every production package; stage each package in a temp directory and publish only after the required generation checks pass, else publish a labelled `FAILED-RUN/` + `FAILED-RUN.txt`. |
| `packages/bridgecad-draw/…/sheet2_long_section.py` | +38 | Pier base/soil line drawn from the record `shaft_base_rl_m` (fallback only when the record is absent). |
| `packages/bridgecad-draw/…/sheet4_foundation.py` | +52 | Footing levels from `typical_pier_support_level`; footing block gated when the record is UNRESOLVED (no invented footing). |
| `packages/bridgecad-draw/…/sheet5_pier_abutment_details.py` | +13 | Pier shaft height from the record `shaft_height_m`. |
| `packages/bridgecad-draw/…/sheet8_side_elevations.py` | +43 | Shaft base / cap datums from `ls.support_level_records[0]`. |
| `packages/bridgecad-io/…/excel_reader.py` | +13 | Blank-template girder prefills so the canonical workbook round-trips: when no type is chosen, mirror the legacy prefills (`girder_depth_mm=1200`, spacing 2.5 m, 4/deck); an explicit girder type keeps its own cells and still errors. |
| `packages/bridgecad-catalogue/…/registry.py` | +8 | Two arch cards gain `fidelity_note`; the truthful `approximation: True` flag is **preserved**. |
| `scripts/prove_detection.py` | +47 | Cut per-mutation copy volume (extra ignore dirs + `_IGNORE_EXT` binary list) — the combined-suite stall fix. |
| `tests/draw/test_qa_audit_rows.py` | +27 | **(Blocker 3)** `_is_note_line` rejects decimals / keeps notes; `Region.intersects` semantics. |
| `tests/pwd/booklet_oracle.json`, `tests/pwd/test_booklet_oracle.py`, `tests/unit/test_support_levels.py` | +60 | Oracles/tests brought in line with the newer implementation (never the reverse). |
| `CREAT.md` | −303 | Session log (user work). |

Uncommitted **untracked** inventory (150 paths) is listed verbatim in `T9-final-untracked.txt`; the
load-bearing ones are the evidence dirs `artifacts/**`, the drivers `scripts/gad_reference_overlay.py`
and `artifacts/gad-acceptance/_gen_nine_span.py`, the tests `tests/draw/test_nine_span_cross_view.py`,
`tests/unit/test_quality_manifest.py` and `tests/unit/test_required_content.py`, the QA modules
`packages/bridgecad-qa/bridgecad_qa/quality_manifest.py`, `required_content.py` + `required_content.json`,
and `outputs/11span_110m_rcc_slab/`.

## 2. Test reports

| Run | Result | Where |
|---|---|---|
| Cross-view / nine-span draw tests | **12 passed** | `tests/draw/test_nine_span_cross_view.py` |
| io + api + integration | **13 passed** (no regressions after the reader fix) | this session |
| Re-verified after the approval-wording sweep: `unit` + `draw` + `pwd` | **626 passed / 2 skipped / 5 xfailed** in 112 s | this session |
| Re-verified after the approval-wording sweep: `integration` + `api` + `io/tests` | **13 passed** in 57 s | this session |
| Production browser/API journey | **16 / 16 pass** (exit 0) | `artifacts/browser-results/report.txt`, `T8-journey-report.md` |
| Combined pytest suite | **1461 passed / 9 skipped / 5 xfailed** in 962 s | `artifacts/continue/T8-full-suite.txt`, `full-after.xml` |
| Quality manifest + draw suites (blockers 2/3) | **371 passed / 2 skipped / 5 xfailed** in 87 s | this session |
| Catalogue + support-levels + quality-manifest | **118 passed** | this session |
| Required-content + quality-manifest units | **27 passed** in 4 s | `tests/unit/test_required_content.py` (18) + `tests/unit/test_quality_manifest.py` (9) |
| Full `tests/unit` lane | **183 passed / 2 warnings** | this session |
| Drawing-audit rows incl. new `_is_note_line`/`Region` tests | **40 passed** in 10 s | `tests/draw/test_qa_audit_rows.py` |

Skips/xfails are reported separately from passes; nothing was xfail-silenced.

## 3. Resolved inputs

Nine-span slab fixture `BR-I-2022-002`, 9 × 10 m = 90 m, 8 piers, OPEN foundation, pier height 6.0 m,
HFL 100.0, road 102.5. Two records are produced, and both are evidence:

**(a) Honest default — no founding RL supplied.** Record in
`artifacts/gad-acceptance/nine_span_slab/summary.json`:

- `support_level_record.status = UNRESOLVED`, `authority = HEIGHT_CONTROLLED`
- `shaft_base_rl_m = 94.975`, `cap_top_rl_m = 101.775`, `cap_bottom_rl_m = 100.975`
- `footing_bottom_rl_m = null`, issue `E-MISSING-FOOTING-DEPTH` (never guessed)
- `params.resolved.json` + `render-status.json` alongside.

**(b) Deliverable — explicitly supplied, geometrically consistent founding RL.** A declared input whose
arithmetic is consistent; it is **not** an engineering approval (structural adequacy is a separate human
verdict). `artifacts/gad-acceptance/nine_span_slab_resolved/` with the explicitly supplied stack
(`wearing 75 mm`, `bearing depth 50 mm`, `pedestal 0.15 m`, `cap depth 0.8 m`,
`footing thickness 1500 mm`, `footing bottom RL 93.425`):

- all **8** piers `status = RESOLVED`, `authority = LEVEL_CONTROLLED`, no issue codes
- `shaft_base_rl_m = 94.925`, `cap_top_rl_m = 101.725`, `cap_bottom_rl_m = 100.925`, `shaft_height_m = 6.000`
- 9 sheets, `layout_checks.passed = true`; `quality: generation_gates_passed = true,
  quality_and_layout_passed = false, accepted = false` (the `required_content` gate FAILS on five
  declared gaps; reference fidelity BLOCKED; review PENDING) — acceptance is correctly withheld.

Variant-validation evidence (`artifacts/gad-acceptance/variant-validation.json`, `all_checks_passed: true`,
**12/12 invariant checks**): the honest default stays `UNRESOLVED`; the conflicting control
(`pier_height_m = 8.0` over the same stack) is **rejected** with `E-CONFLICT-SHAFT-HEIGHT` **before any
DXF is written** (`sheets: []`, published only under a labelled `FAILED-RUN/`); the 7-span and skew-15°
resolved variants both pass; `cap_bottom RL is span-invariant` (9-span `{100.925}` == 7-span `{100.925}`);
and three required-content checks hold — manifest measured (`applicable=66 of 75`), no `IMPLEMENTED`
requirement unmet, and the `required_content` gate **honestly FAILS** on the five declared PARTIAL/MISSING
gaps rather than falsely passing.

The spec-fixture conflict guard is proven separately: adding `shaft_height_m=6.0` to a RESOLVED
fixture yields `E-CONFLICT-SHAFT-HEIGHT`.

## 4. Drawings

- Nine-span 9-sheet DXF package (honest default): `artifacts/gad-acceptance/nine_span_slab/e969b729…/*.dxf`
  (Sheet1 247 · Sheet2 314 · Sheet3 73 · Sheet4 139 · Sheet5 194 · Sheet6 87 · Sheet7 276 ·
  Sheet8 263 · Sheet9 192 entities).
- Nine-span 9-sheet DXF package (resolved deliverable): `artifacts/gad-acceptance/nine_span_slab_resolved/e969b729…/*.dxf`,
  plus 7-span and skew-15° resolved packages beside it. Each carries a fail-closed `quality.json`
  (closed-verdict enums, fail-closed defaults) and a `layout-audit.json` with the measured region
  rectangles.
- API-produced package: `artifacts/browser-results/gad-draw.zip` (9 DXF);
  full bundle `artifacts/browser-results/export-bundle.zip` (16 files: 9 DXF + BOQ xlsx/csv/pdf +
  QA html + BBS csv/xlsx + `manifest.json`).
- Long-bridge variant: `outputs/11span_110m_rcc_slab/` (DXF + PDF).

## 5. Comparison evidence (Item 7)

- Baseline: `CODE-JUNCTION/GENERAL ARRANGEMENT DRAWINGS.pdf` — SHA-256
  `38C224549A50CC72A20AAA01E07B33618789DC4D3881844363BDA199DD44A23D`, 11 284 253 bytes,
  **27 pages** A2 landscape, drawing numbers `BR- I / 2022 - 001`…`015`, no revision printed
  (first issue) ⇒ `artifacts/reference-overlay/reference-manifest.json`.
- `artifacts/reference-overlay/comparison.json` — `status: PARTIAL`; `VAR-PIER-BASE-DISCREPANCY`
  **AGREE** (was DISAGREE 5.0 m); `VAR-SUPPORT-LEVELS` **AGREE** (the named RL chain is exposed in
  `params.resolved.json` under `support_levels.typical`/`.supports` and compared level-for-level with
  the canonical record); other invariant conventions AGREE.
- Calibrated overlays + side-by-side PNGs: `artifacts/reference-overlay/overlays/*.png`.

## 6. Blockers (honest, not silently worked around)

**Four implementation blockers addressed this session; maintenance and reference limitations remain;
GAD acceptance pending.** (Evidence for each is named below.)

1. ~~**Catalogue design dials MISSING**~~ → **IMPLEMENTED.** `schema.py` now carries the seven `_free`
   dials (footing-bottom RL, footing depth, cap depth, bearing depth, pedestal height, wearing depth,
   pile-cap thickness) and `models.FoundationDetails.footing_bottom_rl_m` backs the founding RL. They
   are consumed by `resolve` / `_build_project` / `_pier_support_level_input`, so the explicitly supplied
   stack resolves all 8 piers — proven by the RESOLVED variant (§3b). The honest default is unchanged
   (UNRESOLVED with `E-MISSING-FOOTING-DEPTH`). The dial's own `note` describes it as an explicitly
   supplied founding RL, not an approval.
2. ~~**Fail-closed quality manifest MISSING**~~ → **IMPLEMENTED.** `bridgecad_qa/quality_manifest.py`
   (closed-verdict enums, `__post_init__` fail-closed defaults, `set()` rejecting invalid gate+verdict)
   with unit tests in `tests/unit/test_quality_manifest.py`; `quality.json` is emitted by both
   `generate_all_pwd_gads.generate_one` for every production package **and** the acceptance driver. The
   gates are split so a green generation run is never mistaken for acceptance: `generation_gates_passed`
   covers `generation` / `model_validation` / `geometry_contract`; `quality_and_layout_passed` adds
   `required_content` / `layout`; `accepted` additionally requires `reference_fidelity = PASSED` and
   `engineering_review = APPROVED`. The resolved deliverable therefore reads
   `generation_gates_passed: true, quality_and_layout_passed: false, accepted: false`.
   **Required-content manifest (delivered with this blocker):** the §4 manifest now exists twice —
   human-reviewed `artifacts/gad-acceptance/reference_requirements.json` and machine-checked
   `packages/bridgecad-qa/bridgecad_qa/required_content.json` (75 requirements, emitted per package as
   `required-content.json`). A requirement is credited only when declared `IMPLEMENTED` **and** measured
   present in the DXF; drawing text and title-block text are kept in separate scopes so title-block
   boilerplate cannot satisfy a drawing-content requirement. The gate **honestly FAILS** on five declared
   gaps (`RC-PLAN-11`, `RC-FDN-05`, `RC-RFT-05`, `RC-TTL-06` PARTIAL; `RC-BABT-02` MISSING).
3. ~~**Layout region-rectangle gating PARTIAL**~~ → **IMPLEMENTED for the reserved zones.**
   `layout_audit` now exposes `Region` rectangles for sheet / frame / title-block / notes and
   `layout_checks` reports clipping / title_block / notes_zone / scales / text_floor measured from the
   rendered DXFs (`passed: true`; 0 outside frame, 0 intrusions, min text 1.8 mm). The `_is_note_line`
   classifier was tightened to reject decimals (`"10.0 m (eff 9.7)"`), which had manufactured a phantom
   notes zone on the skew sheet. **Limitation (not closed):** the reserved-zone checks prove only that
   nothing intrudes into the title-block / notes / frame rectangles. They do **not** prove the absence of
   label–label, dimension–geometry or schedule overlaps. No per-view rectangles are declared, so those
   remain a measured text-pair count (`annotation_overlap_count = 17` on the nine-span, reported in
   `quality.json` and `layout-audit.json`) rather than a pass/fail region check.
4. ~~**`VAR-SUPPORT-LEVELS` BLOCKED**~~ → **AGREE.** `generate_all_pwd_gads._support_level_chain` writes
   the full named RL chain into `params.resolved.json` (`support_levels.typical` / `.supports`, with
   `status`/`authority`/`levels_m`/`provenance`/`issues`), and `gad_reference_overlay.py` compares it
   level-for-level with the canonical record in `summary.json` — `cap_bottom`, `shaft_base` and
   `footing_bottom` all agree.

**Transactionality (the conflicting case).** A CONFLICT is detected **before generation**: the run
returns `sheets: []` and no DXF is written. Drafting is staged in a temporary directory and published
only after the required generation checks pass; a rejected run publishes nothing but a clearly labelled
`FAILED-RUN/` directory, which cannot be mistaken for a deliverable and never merges with a previous run.
Verified: the conflict fixture `artifacts/gad-acceptance/nine_span_slab_conflict/` now contains **only**
`FAILED-RUN/` (`failure-report.json` + `quality.json`). The production driver additionally drops a
`FAILED-RUN.txt` marker beside the rejected label (proven separately against
`generate_all_pwd_gads.generate_one`).

**Still open — maintenance and reference limitations (recorded honestly, not worked around):**

5. **Duplicate tree (maintenance task retained)** — `bridgecad_draw/sheets/*` duplicates the root sheet
   modules (contract/plugin base); only the root modules are production. A maintenance hazard, not a
   defect; retained as an open task in
   `reference_requirements.json.duplicate_renderer_maintenance_task`.
6. **Reference limitation** — the booklet contains no nine-span sheet, so an *exact nine-span
   reproduction* is **not** claimed. This does **not** prevent checking applicable booklet conventions
   and details alongside independently verified nine-span geometry, which is what §5/§6 report
   (`comparison.json` status `PARTIAL`; the §6 calibrated per-reference-page comparison awaits the
   approved reference PDF).
7. **Five declared required-content gaps** — `RC-PLAN-11`, `RC-FDN-05`, `RC-RFT-05`, `RC-TTL-06`
   (PARTIAL) and `RC-BABT-02` (MISSING) are declared unmet, so the `required_content` gate FAILS. They
   are declared gaps, not silent passes.

## 7. Confirmation

No `git add`, `git commit`, `git push` was performed. The tree is preserved exactly as delivered.

**Wording check.** A case-insensitive search for the literal claim `"GAD complete"` (and `"GAD accepted"`,
`"GAD is complete"`) across the tree returns **no matches**. The standing, correct phrase is in place
where the status is asserted: `artifacts/test-results/00-tree-freeze.md` ("**Generated draft — GAD
acceptance pending**", spec §10), the T2 closure statement ("**Four implementation blockers addressed;
maintenance and reference limitations remain; GAD acceptance pending.**") and the governing spec
`CODE-JUNCTION/BRIDGECAD_GAD_ACCEPTANCE_RESOLUTION.md`. The only `GAD Complete` strings are the preserved
attachment's filename `ATTACHED ASSETS/LISP_Solid_Slab_GAD_Complete_Archive.md` (a source archive title,
not a status claim).

**Approval-wording correction.** "approved foundation stack" → "**explicitly supplied, geometrically
consistent foundation stack**", and the synonymous "approved founding RL" → "**explicitly supplied
founding RL**" in the catalogue dial note (`schema.py`), the canonical contract comments
(`long_section.py`, `models.py`), the sheet-4 comment, the overlay driver prose and the matching
`comparison.json` reason. No engineering approval for the stack exists, so no artifact calls it
approved. `gates_passed` → `generation_gates_passed` / `quality_and_layout_passed` (with
`accepted` kept separate) throughout the manifest, driver and tests.
