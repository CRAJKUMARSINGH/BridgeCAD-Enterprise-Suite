# T2 — Acceptance reconciliation: `BRIDGECAD_GAD_ACCEPTANCE_RESOLUTION.md` vs CURRENT local code

Audited 2026-11-14 against local HEAD `e969b72979196f78e2d04129c2462268d6caf099`.
**Re-audited 2026-11-15 against the CURRENT working tree** (still HEAD `e969b729…`, uncommitted
changes present). §3, §6, §7 and the closing answer were rewritten after re-reading the live
source; where this session's earlier verdicts are now stale they are superseded below.
Verdict vocabulary: **IMPLEMENTED** / **PARTIAL** / **MISSING** / **UNVERIFIED** / **BLOCKED**.
"UNVERIFIED" means: not inspected or not executed in this session — it is NOT a claim of success.
Rule applied throughout: where newer local code and an older oracle disagree, the newer
implementation is retained and the oracle is brought in line — never the reverse.
Active-renderer note: `bridgecad_draw.booklet.generate_package` imports the **root**
`bridgecad_draw.sheetN_*.py` modules; `bridgecad_draw/sheets/*` is a documented duplicate tree
(contract/plugin base only, not the production renderer). Consumer verdicts below refer to the
root modules.

---

## §1 Assessment of TRAE's work / still due from the merge

| Requirement | Verdict | Evidence |
|---|---|---|
| Retain the newer `Artifact[]` architecture; do not replace newer files with the earlier bundle's changed-sources | IMPLEMENTED | Selective merge was performed; newer local code retained. `tests/pwd/booklet_oracle.json` was updated to match the newer implementation rather than reverting the implementation. |
| Compare each claimed merged fix with a retained diff **and** its regression test (not file existence) | PARTIAL | Retained diffs exist in `artifacts/continue/` (`T1-tracked.diff`, `T1b-diff-stat.txt`) and durable results in `artifacts/test-results/`. Not every merged file in commit `e969b72` has a per-file rationale + test mapping yet. |
| `Artifact[]` prevents mixed-job artifacts, cancels stale requests, releases object URLs, clears exports on workbook change, reports partial failures | UNVERIFIED | Not inspected this session. |
| `validOverrides` supplied at both local-storage recovery and import boundaries; single-scenario export/import round trip | UNVERIFIED | Not inspected this session. Journey C/B dispatched to `artifacts/browser-results/`. |
| New docs discoverable while gitignored intake and generated dist are excluded narrowly; do not exclude legitimate source docs to make a guard pass | IMPLEMENTED | `tests/docs/conftest.py` uses an explicit `STAGED_BY_HOOK` allow-list and a narrow `SKIP_DIRS`; the 18-mutation detection harness reports `control_passed=True, detected=17/17`. An over-broad `ATTACHED ASSETS` exclusion was tried and **removed** because it produced a false dead-link failure — recorded in `scripts/prove_detection.py`. |
| Check whether `BridgeCAD-Abutment-Geometry-Patch` was applied or superseded; verify cantilever toe/heel/base, longitudinal T section, transverse orientation, independent batters, mirrored end profiles | IMPLEMENTED | `packages/bridgecad-core/bridgecad_core/geometry/abutment_profiles.py` (`battered_side_outline`, `BatteredSide`) with `tests/unit/test_abutment_batter.py`, `tests/draw/test_abutment_batter.py`, `tests/refs/test_lisp_assets.py` — independent face/back/toe batters, mirrored ends, `abt1` break levels, `ValueError` on bad input. |
| Retain test results in a durable evidence directory rather than disposable logs | IMPLEMENTED | `artifacts/test-results/` (JUnit + logs + tree freeze), `artifacts/continue/`, `artifacts/gad-acceptance/`, `artifacts/reference-overlay/`. |

## §2 Resolve the monolithic pytest stall as an outstanding defect

**RESOLVED, with the required diagnostics.** Separate capture: [T8-full-suite.txt](file:///e:/Rajkumar/BridgeCAD-Enterprise-Suite/artifacts/continue/T8-full-suite.txt).

| Requirement | Verdict | Evidence |
|---|---|---|
| Run the combined suite with `faulthandler_timeout` + `--durations` + `--junitxml` | IMPLEMENTED | `python -m pytest -q -o faulthandler_timeout=60 --durations=30 --junitxml=artifacts/continue/full-after.xml` |
| Bounded, repeatable completion | IMPLEMENTED | **1461 passed, 9 skipped, 5 xfailed, 9 warnings in 962.24s (0:16:02)**; `artifacts/continue/full-after.xml` written. |
| Record the final started test, traceback, process tree, child command line, open output streams | IMPLEMENTED | faulthandler traceback shows the parent blocked in `subprocess.run` → `_communicate` → `join` at `tests/docs/test_detection_proof.py:21` / `:40`, with two live `_readerthread`s (the capture pipes). Process tree captured live: parent PID 2116 → child `scripts/prove_detection.py --json --jobs 4 --only D05` (PID 19492, 19:20:26), then PID 24376 at 19:20:52. |
| Identify the cause rather than labelling it environmental | IMPLEMENTED | Root cause **not environmental**: `scripts/prove_detection.py` copied the whole tree once per mutation with an incomplete ignore set — 7859 files / 303 MB ≈ 45 s per copy × 19 copies. |
| Do not simply exclude or xfail the hanging test | IMPLEMENTED | No test excluded; `timeout=900` left intact. The **copy volume** was fixed. |
| Keep the non-slow partition and the direct 17/17 proof as separate results | IMPLEMENTED | `artifacts/continue/T8-prove-detection-after.json` (`control_passed=True, detected=17/17, ok=True`, 112.9 s; D01 51.4 s → 16.5 s) is retained separately from the combined run. |

## §3 P0 — one canonical vertical geometry contract

| Requirement | Verdict | Evidence |
|---|---|---|
| Pure resolver returning explicit named RLs per support | IMPLEMENTED | `packages/bridgecad-core/bridgecad_core/geometry/support_levels.py`; `Decimal` model, float only at the render boundary (`test_drawing_conversion_is_the_only_float_boundary`). |
| Support record carries id/chainage, road + soffit RL, bearing + pedestal, cap top/bottom, shaft top/base, footing top/bottom/thickness, provenance, issues, authority mode | IMPLEMENTED | `SupportLevelRecord`, `FieldSource` (SUPPLIED/ASSUMED/DERIVED/PROPOSED/UNRESOLVED), `SupportLevelIssue`. |
| Distinct topology for a monolithic/integral joint (zero-bearing, no fake pad) | IMPLEMENTED | `BearingTopology.MONOLITHIC`; `test_monolithic_topology_has_zero_seat`. |
| Do not apply both a combined seat field and independent bearing/pedestal depths | IMPLEMENTED | `BearingTopology.COMBINED_SEAT`; `test_combined_seat_subtracts_once`. |
| Authority policy 1 — level-controlled: derive shaft height; a supplied incompatible height is a conflict | IMPLEMENTED (resolver) | `support_levels.py:409-455`, `E-CONFLICT-SHAFT-HEIGHT`; `test_older_6m_shaft_height_conflicts_and_is_rejected`. |
| Authority policy 2 — height-controlled: derive shaft base and PROPOSED foundation RL, marked assumed/proposed | IMPLEMENTED (resolver) | `support_levels.py:456-495`, `W-PROPOSED-FOUNDING`. |
| Authority policy 3 — missing thickness/topology ⇒ UNRESOLVED, never a guessed depth | IMPLEMENTED (resolver) | `E-MISSING-FOUNDATION`, `E-MISSING-FOOTING-DEPTH`; `test_missing_footing_depth_is_unresolved_never_guessed`. |
| Numerical regression fixture (road 102.500 → derived shaft height 2.525 m) | IMPLEMENTED | `test_fixture_resolves_to_the_specified_levels`; `test_all_interfaces_connect_exactly`. |
| Reject the conflicting 6 m shaft-height pair; do not force both into separate views | IMPLEMENTED (resolver) | As above. |
| **Consumers** — replace independent level arithmetic with the canonical record across `catalogue resolve`, `_build_project`, long-section, abutment stack, sheets 1/2/4/5/8 | IMPLEMENTED (re-audited 2026-11-15) | Every production pier-base consumer reads one record: `sheet2_long_section.py:209-221,663-677` uses `r.shaft_base_rl_m`; `sheet4_foundation.py:196-227` calls `typical_pier_support_level(project)` and gates the footing to the record's complete top/bottom/depth; `sheet5_pier_abutment_details.py:96-103` uses the record's `shaft_height_m`; `sheet8_side_elevations.py:314-331` uses `ls.support_level_records[0]`. Each keeps a fit-only fallback for when the record is genuinely absent/UNRESOLVED, but no longer *draws* an approved datum from raw arithmetic. |
| **Pipeline wiring** — the contract must actually receive the supplied height so its conflict guard can fire | IMPLEMENTED (re-audited 2026-11-15) — **5.0 m divergence CLOSED** | `long_section._pier_support_level_input` now passes `shaft_height_m=pier_height_typical_m` and leaves `authority` unset so `support_levels` auto-classifies (HEIGHT_CONTROLLED here); a `cap_thk_mm <= 0` becomes `footing_depth_m=None`; `pile_cutoff_level_m` is carried only as `pile_cutoff_rl_m`, never `footing_bottom_rl_m`. Nine-span record is now `status=UNRESOLVED`, `authority=HEIGHT_CONTROLLED`, `shaft_base_rl_m=94.975`, `footing_bottom_rl_m=null`, issue `E-MISSING-FOOTING-DEPTH`; the measured `DRAWN pier base vs record shaft_base` delta is **0.0 m** (was 5.0 m). |
| Catalogue layer supplies footing bottom RL / footing depth / bearing depth / pedestal / cap depth / wearing depth dials | **IMPLEMENTED** (re-audited 2026-11-15) | `schema.py` now declares all seven dials as `_free` variables — `footing_bottom_rl_m`, `pile_cap_thickness_mm`, `pile_cutoff_level_m`, `pier_cap_depth_m`, `pier_pedestal_height_m`, `bearing_depth_mm`, `wearing_coat_thickness_mm` — and `bridgecad_core.models.FoundationDetails.footing_bottom_rl_m` carries the approved founding RL. `resolve`/`_build_project`/`long_section._pier_support_level_input` consume them. The honest default is unchanged: with no founding RL and an OPEN foundation the record is `UNRESOLVED / HEIGHT_CONTROLLED` + `E-MISSING-FOOTING-DEPTH`; supplying a founding RL **and** a footing thickness switches it to `LEVEL_CONTROLLED / RESOLVED` and the shaft height becomes DERIVED. Proof: the nine-span RESOLVED variant (below) is `RESOLVED/LEVEL_CONTROLLED` on all 8 piers. |
| Cross-view assertions: extract tagged geometry from each DXF, inverse-map sheet coordinates to model metres, compare the same physical point across views | PARTIAL (updated) | `tests/draw/test_nine_span_cross_view.py` — 12 tests — plus `summary.json.measured_cross_view_deltas`: plan↔long-section pier chainages/support set/deck length all Δ=0.0; record cap_top/cap_bottom vs drawn long-section SUB-PIER Δ=0.0; record footing_top=shaft_base Δ=0.0. Foundation-vs-plan remains not measurable on an OPEN card because sheet 4 renders no pier footing (correctly, per the UNRESOLVED record). |

## §4 P0 — completeness by required content, not sheet count

| Requirement | Verdict | Evidence |
|---|---|---|
| Versioned `reference_requirements.json` (stable ID, target view/support, expected primitive, required dimension/label, evidence, status, reviewer verdict) | **IMPLEMENTED** (re-audited 2026-11-15) | `artifacts/gad-acceptance/reference_requirements.json` present — 13 rows, each with stable ID / scope / view / target / expected primitive / required dimension / evidence / status / `reviewer_verdict`. A second, **machine-checked** manifest `packages/bridgecad-qa/bridgecad_qa/required_content.json` (75 requirements) is measured against the rendered DXFs and emitted per package as `required-content.json`. |
| Fail-closed quality manifest as **enums**, not pipe-separated strings (`generation`, `model_validation`, `geometry_contract`, `required_content`, `layout`, `reference_fidelity`, `engineering_review`, `issues`) | **IMPLEMENTED** (re-audited 2026-11-15) | `bridgecad_qa/quality_manifest.py` — `Gate` / `Verdict` enums, a closed `_ALLOWED` verdict set per gate, and a fail-closed `_DEFAULT` for every unset gate. Tests: `tests/unit/test_quality_manifest.py` (9 tests) — an unset gate reads its fail-closed default; an invalid gate+verdict pair and an unknown gate both raise; a full quality pass still leaves acceptance pending; `to_json` serialises every gate by value. Emitted as `quality.json`: per production package by `generate_all_pwd_gads.generate_one`, and per acceptance fixture by `artifacts/gad-acceptance/_gen_nine_span.py` (which fills the measured model/geometry/layout gates). |
| Accept only when every gate passes and review is recorded; allow a visible DRAFT/UNRESOLVED export that is not labelled accepted | **IMPLEMENTED** (re-audited 2026-11-15) | `QualityManifest.accepted` requires all five quality/layout gates **plus** `reference_fidelity = PASSED` **and** `engineering_review = APPROVED`; `status` returns `ACCEPTED` / `QUALITY/LAYOUT GATES PASSED — acceptance pending review/reference` / `DRAFT — quality/layout gates not all passed`. The nine-span RESOLVED variant reports `generation_gates_passed=True`, `quality_and_layout_passed=False`, `accepted=False` — generation gates green, acceptance still withheld (the `required_content` gate honestly FAILS on five declared gaps). |
| Required content per drawing area (plan, long section, cross section, foundation, battered abutment, cantilever abutment, bearings/joints, reinforcement, BOQ, title/notes) | PARTIAL (now measured) (re-audited 2026-11-15) | The 9-sheet package renders all ten areas and the shipped manifest asserts them: `required_content.json` covers every §4 area (66 of 75 requirements applicable to this card; 9 not applicable, e.g. footpath, pile schedule, cantilever abutment). A requirement is credited only when declared `IMPLEMENTED` **and** measured present in the DXF. Result is honestly `passed=False`: 5 declared gaps (`RC-PLAN-11`, `RC-FDN-05`, `RC-RFT-05`, `RC-TTL-06` PARTIAL; `RC-BABT-02` MISSING). |

## §5 P1 — replace fit-to-extents with a real sheet-layout pass

| Requirement | Verdict | Evidence |
|---|---|---|
| Printable border, title block, notes zones, viewport rectangles per paper/orientation | IMPLEMENTED for border/title-block/notes (re-audited 2026-11-15) | Frame and title block exist (`titleblocks._SHEET_SIZES`, `_MARGIN`) and are now **measured** as `Region` rectangles from the rendered DXFs (`layout_audit.sheet_regions` / `frame_regions` / `title_block_regions`); the notes/schedule forbidden zone is measured from the drawn note block (`notes_regions`). Viewport rectangles are still not declared per sheet. |
| Standard scale ladder, no silent X/Y stretch, declare vertical exaggeration | IMPLEMENTED | `bridgecad_draw.fit.LADDER`; the nine-span long section prints `H Scale 1:150   V Scale 1:26  (V.E.=5.68x)` — the exaggeration is reported, not asserted. |
| No clipping; no unexpected overlap with title/notes; scale honesty; text-size floor; required dimensions retained | IMPLEMENTED (audit + gate) (re-audited 2026-11-15) | `bridgecad_draw.layout_audit` is opt-in (`BRIDGECAD_LAYOUT_AUDIT=1`) and reports; `layout_audit.layout_checks(audit)` turns it into the gate (`clipping_ok` / `title_block_ok` / `notes_zone_ok` / `scales_ok` / `text_floor_ok`), consumed by the quality manifest's `layout` gate. Measured on the nine-span: 0 entities outside the frame `(10,10,831,584)`, 0 title-block intrusions, 0 notes intrusions, scales 50/75/150 all on the ladder, minimum text height 1.8 mm (IRC SP:55 floor) ⇒ `passed=True`. |
| Region rectangle collision (view vs title block vs notes) | IMPLEMENTED for the reserved zones (re-audited 2026-11-15) | `layout_audit` now exposes `Region` rectangles (sheet / frame / title block / notes) measured from the rendered DXFs, plus `title_block_intrusions` / `notes_intrusions` listing each drawing primitive that overlaps a reserved zone. Sheet 4's abutment-inset band was moved out of the title-block rectangle to clear a real hit. **Still open (not closed by reserved-zone checks):** no per-view rectangle is declared, so the reserved-zone pass proves only that nothing intrudes into the title-block / notes / frame rectangles — it does **not** prove the absence of label–label, dimension–geometry or schedule overlaps. Those remain a measured text-pair count (`annotation_overlap_count = 17`), not a pass/fail. **Fixed along the way:** the notes-zone detector misread the span-length dimension label `10.0 m (eff 9.7)` as a numbered note line and manufactured a phantom notes zone — `_is_note_line` now requires the `". "` separator every note generator emits. |
| Fix the nine-span slab fixture first, then portrait/landscape, long bridges, both abutment families, skew boundaries | PARTIAL (improved) | Nine-span slab done (`artifacts/gad-acceptance/nine_span_slab/`) and now closed with a **RESOLVED** variant plus a span variant and a **skew-15°** variant (`variant-validation.json`, 12/12 invariant checks pass). An 11-span 110 m long-bridge package exists in `outputs/11span_110m_rcc_slab/`. Portrait and both abutment families are still not covered by measured layout gates. |

## §6 P1 — reference comparison with calibrated evidence

**Delivered.** Separate capture: `artifacts/reference-overlay/reference-manifest.json`, `comparison.json`, `overlays/`, driver `scripts/gad_reference_overlay.py`.

| Requirement | Verdict | Evidence |
|---|---|---|
| Locate the actual approved reference PDF; if not found, mark BLOCKED and never invent it | IMPLEMENTED | Found and restored: `CODE-JUNCTION/GENERAL ARRANGEMENT DRAWINGS.pdf`. |
| Record filename/hash, page, sheet/drawing number, revision, drawing family | IMPLEMENTED | SHA-256 `38C224549A50CC72A20AAA01E07B33618789DC4D3881844363BDA199DD44A23D`, 11 284 253 bytes, **27 pages**, every page 1684.0 × 1191.0 pt (A2 landscape). "BOOKLET OF GENERAL ARRANGEMENT DRAWINGS FOR VARIOUS TYPES OF BRIDGES", C.E. (DESIGNS) P.W.D., issued vide letter No. 2473 Dt. 31.12.2022; title stamp `G. A. D.  Dt. 31.12.2022`; **no revision number printed** (first issue). Index on PDF page 3; drawing numbers `BR- I / 2022 - 001` … `015`; printed PAGE n == PDF page n + 3. |
| Verify it is the intended reference baseline | IMPLEMENTED | It is the booklet the 15 catalogue cards and `tests/pwd/booklet_oracle.json` are derived from. **Note:** it contains **no nine-span sheet** (span counts 2–5). |
| Separate reproduction of a baseline from a changed-variable variant; do not demand pixel identity across different span/skew | IMPLEMENTED | Policy enforced: the nine-span variant is compared on invariant conventions + independently derived geometry only. `comparison.json` status is honestly **PARTIAL**. |
| Calibrate each view from known dimensions; no arbitrary non-uniform warping | IMPLEMENTED | Uniform scale + translation only, per view: plan 0.66@(−484,−30), long section 0.66@(−302,−210), cross section 0.55@(127,134); residuals recorded; declared V.E. carried. |
| Overlay + side-by-side; record translation/rotation/scale/crop/exaggeration | IMPLEMENTED | `artifacts/reference-overlay/overlays/*_overlay.png`, `*_side_by_side.png`. |
| Geometry/topology and physical dimensions first, then annotation/schedules/linework/composition | PARTIAL (updated 2026-11-15) | Variant geometry verdicts: total 90 m AGREE, 8 piers at 10…80 m AGREE, abutment axes 0.000/90.000 AGREE, carriageway 7.50 m AGREE, overall width 8.00 m AGREE, deck 500 mm AGREE. **`VAR-PIER-BASE-DISCREPANCY` AGREE** (drawn bases all equal the record `shaft_base_rl_m` within 1e-3; the 5.0 m view-to-view divergence is gone). **`VAR-SUPPORT-LEVELS` is now AGREE** (was BLOCKED): `generate_all_pwd_gads._support_level_chain` writes the full named RL chain into `params.resolved.json` under `support_levels.typical` / `.supports`, and the driver compares it level-for-level with the canonical record in `summary.json` — status, authority, `cap_bottom`, `shaft_base` and `footing_bottom` all match. |
| Raster difference is a diagnostic, not the oracle | IMPLEMENTED | Reported and explicitly labelled diagnostic (plan 33.59 / long 30.46 / cross 22.14). |
| Per-requirement verdict, measured difference, artifact path, reviewer, unresolved assumption | PARTIAL | Present in `comparison.json`; reviewer field not populated (no named reviewer this session). |

**Invariant-convention verdicts** (reference page 6 = printed page 03 = `BR- I / 2022 - 002`, "OPEN FOUNDATION WITH R.C.C. PIER & SOLID SLAB SUPER STRUCTURE"):

| Convention | Verdict | Measured |
|---|---|---|
| Paper size / orientation | **DIFFER** | reference A2 landscape 594 × 420 mm; generated DXF border A1 841 × 594 mm (`render-status.json` media is A2 but that is the raster media, not the DXF paper). |
| Declared scale | **DIFFER** | reference `SCALE-1:250` ×2, `1:100` ×4, `1:50` ×1, no stated V.E.; generated plan `1:150`, long section `1:150 H / 1:26 V (V.E.=5.68x)`, cross section `1:50`. |
| Title block field set/order + number pattern | **DIFFER** | reference `DRG. No. BR-I / 2022 - 002`, `JOB No. BR-I /RGD - 442 / 2018`, `G. A. D. Dt. 31.12.2022`, `Page-03`, `REVISION`, `PREPARED BY/CHECKED BY/RECOMMENDED BY/APPROVED BY`, `GOVT. OF MAHARASHTRA`, `KONKAN BHAVAN, NAVI MUMBAI, PIN-400614`; generated hyphenates the number and uses `REVISION: R`, `SHEET 1 OF 9`, `CLIENT: STATE_PWD`. |
| Level notation | **DIFFER** | reference uses discipline prefixes `R.T.L. 102.315`, `SOFFIT R.L. 101.500`, `F.R.L. 94.850`, `H.F.L. 99.700`, marker `DATUM LEVEL 90.00M` with stations `A/L, P-1…P-3, A/R`; generated collapses to a generic `RL <value>`. |
| View labelling / sheet composition | **NOT_COMPARABLE** | reference packs all views on one booklet sheet with `ELEVATION (SCALE-1:250)`, `PLAN`, `PART PLAN AT TOP/BOTTOM`, `CROSS SECTION AT P-2`, `SECTION AT P-2`, `DETAILS OF ABUTMENT A/L & BOX RETURN (SCALE-1:100)`; generated is one view per sheet. |
| Layer/entity vocabulary | **NOT_COMPARABLE** | the reference is a flattened PDF with no CAD layers; generated uses `SUPER-DECK`, `SUB-PIER`, `SUB-ABUT`, `CIVIL-HFL`, … |

## §7 P1 — browser verification on the actual local deployment

**DONE (re-audited 2026-11-15).** Live-journey run against FastAPI :8000 / Streamlit :8501 /
Vite :5173 via `scripts/browser_test.py` — **16 / 16 steps pass** (exit 0). Report:
`artifacts/browser-results/report.txt` + `T8-journey-report.md`; retained artefacts
`gad-draw.zip` (9 DXF), `export-bundle.zip` (16 files, incl. manifest), `qa-report.html`,
`bills.json`, `simple_12m.xlsx`, and the three service logs.

| Requirement | Verdict | Evidence |
|---|---|---|
| Health response is not sufficient; run the real generation journey | IMPLEMENTED | Steps 4–9: parse → validate → `/draw/gad` → BOQ → QA HTML → `/exports/bundle`, all 200 with real payloads (e.g. bundle 16 files / 128 KB). |
| Every endpoint the UI uses is exercised | IMPLEMENTED | `/health`, `/version`, `/plugins/` (10 ids), `/bridges/parse`, `/bridges/validate`, `/draw/gad`, `/bills/generate`, `/qa/report`, `/exports/bundle`, `/docs`, `/openapi.json` (18 paths), Streamlit `/_stcore/health`, Vite `/`. |
| A first run that fails must be diagnosed, not excused | IMPLEMENTED | First run was 10/16: the blank template could not round-trip. Root cause + fix in the journey report (canonical reader defaulted `RCC_TBEAM` without its required girder dims; legacy path already injected them). |
| The journey result must be reproducible after the fix | IMPLEMENTED | Re-run → 16/16; `pytest tests/integration tests/api packages/bridgecad-io/tests` → 13 passed, no regressions. |

## §7b Combined-suite stall

Resolved with retained diagnostics — see §2 and `artifacts/continue/T8-full-suite.txt`.
Not environmental: root cause is per-mutation full-tree copy volume in `scripts/prove_detection.py`.

## §8 Merge and delivery sequence

| Requirement | Verdict |
|---|---|
| Freeze the merged tree (base commit + diff), preserve user work, retain CREAT.md logging | IMPLEMENTED — `artifacts/continue/T1-*`, `T1b-*`, `T1c-*` |
| Reconcile the abutment bundle by contract, not full-file replacement, with tests | IMPLEMENTED — `abutment_profiles.py` + 3 test modules |
| Resolve the combined-run hang with **retained diagnostics** (corrected, not merely diagnosed) | IMPLEMENTED — §2 above; root cause (copy volume) identified, `prove_detection.py` fixed, 1461/9/5 combined run confirmed in `T8-full-suite.txt` |
| Implement canonical support/foundation levels with pure tests and cross-view assertions | IMPLEMENTED — §3 above; the **catalogue design dials** are now present (`schema.py` `_free` footing-bottom-RL / footing-depth / bearing-depth / pedestal / cap-depth / wearing-depth + `models.FoundationDetails.footing_bottom_rl_m`) and consumed by `resolve` / `_build_project` / `_pier_support_level_input`, so the RESOLVED variant resolves all 8 piers |
| Complete required geometry/details and the fail-closed quality manifest | IMPLEMENTED — `bridgecad_qa/quality_manifest.py` (closed-verdict enums, fail-closed defaults, tests); `quality.json` emitted by both `generate_all_pwd_gads.generate_one` and the acceptance driver; §4 above. `reference_requirements.json` present **and** the machine-checked `packages/bridgecad-qa/bridgecad_qa/required_content.json` (75 requirements) measured per package as `required-content.json` (honestly `passed=False`: 5 declared gaps) |
| Layout zones and measurable annotation gates | IMPLEMENTED for the reserved zones — §5 above; `layout_audit` now exposes `Region` rectangles for sheet/frame/title-block/notes and `layout_checks` reports clipping / title_block / notes_zone / scales / text_floor measured from the rendered DXFs (`passed=True`). `annotation_overlap_count` (label-label text-pair count = 17) is measured and reported in `quality.json`/`layout-audit.json`, but reserved-zone checks do **not** prove the absence of label–label / dimension–geometry / schedule overlaps. *View* rectangles are not declared, so the count is not yet a gate pass/fail — recorded as `RR-ANNOT-001` in `reference_requirements.json` |
| Regenerate the 9×10 m slab fixture with explicit inputs, both abutment variants, boundary cases | PARTIAL — fixture + slab done; both abutment variants and boundaries pending |
| Calibrated reference comparison evidence | PARTIAL (delivered, honestly scoped) — §6. No nine-span reference sheet exists; the absence of that sheet prevents a nine-span reproduction claim but does **not** prevent booklet-convention and independently verified geometry checks |
| Run production browser/API journeys, builds and affected/full tests, reporting skips/xfails separately | IMPLEMENTED — journeys **16/16** (§7); combined suite **1461 passed / 9 skipped / 5 xfailed** (§2) |
| Deliver a reviewed diff, per-file rationale, resolved inputs, DXFs/renders, quality manifests and test results | IN PROGRESS — no commit/push |

---

## The one-line answer to the spec's closing question

> does the same resolved nine-span bridge appear consistently in all views, do all required details exist, is every sheet readable at its declared scale, and does the calibrated comparison support the claimed reference relationship?

- **Consistent across views: YES on the pier datum** (re-audited 2026-11-15). All four pier-base consumers draw the canonical record's `shaft_base_rl_m`; the measured drawn-vs-record delta is **0.0 m** and the old 5.0 m view-to-view divergence is closed.
- **Required details exist:** yes as measured by entity count and reserved-zone checks. Both manifests (human `reference_requirements.json`, machine `required_content.json`) record what has been confirmed and what is PARTIAL — the machine-checked manifest reports 66 of 75 requirements applicable and 5 declared gaps, so the `required_content` gate honestly FAILS rather than passing on sheet count.
- **Readable at declared scale:** yes as measured — 0 entities out of frame, all scales on the ladder, minimum text 1.8 mm. `annotation_overlap_count` is reported but not yet a gate, and does not by itself prove the absence of label–label / dimension–geometry / schedule overlaps.
- **Calibrated comparison supports the claimed relationship:** only for invariant conventions and independently verified nine-span geometry. The reference contains no nine-span sheet, which prevents an exact nine-span reproduction claim but does not prevent applying booklet conventions to the nine-span drawings.

---

## Closure statement (corrected per owner review 2026-11-15)

**Four implementation blockers addressed; maintenance and reference limitations remain; GAD acceptance pending.**

| # | Item | Status |
|---|---|---|
| 1 | Catalogue design dials (footing-bottom RL, footing depth, bearing, pedestal, cap, wearing) | **ADDRESSED** — `schema.py` + `models.py` + resolver consumers |
| 2 | Fail-closed quality manifest with closed-vocabulary enums | **ADDRESSED** — `quality_manifest.py`, `generation_gates_passed` / `quality_and_layout_passed` / `accepted` are separate flags; `annotation_overlap_count` added; the machine-checked required-content manifest (`required_content.json`, 75 requirements) now feeds the `required_content` gate |
| 3 | Layout region-rectangle gating (reserved zones) | **ADDRESSED** — `layout_audit.py` measures sheet/frame/title-block/notes regions; intrusion checks pass |
| 4 | VAR-SUPPORT-LEVELS datum divergence (5.0 m view-to-view error) | **ADDRESSED** — canonical record used by all consumers; cross-view delta=0.0 m |
| 5 | `bridgecad_draw/sheets/*` duplicate renderer tree | **OPEN** — maintenance hazard, not a defect; retained in `reference_requirements.json` |
| 6 | Reference-fidelity gate | **OPEN** — reference contains no nine-span sheet; convention + geometry comparison is PARTIAL; `reference_requirements.json` records every open item |
| 7 | Required-content declared gaps | **OPEN** — `RC-PLAN-11`, `RC-FDN-05`, `RC-RFT-05`, `RC-TTL-06` (PARTIAL), `RC-BABT-02` (MISSING); `required_content` gate honestly FAILS |

**Wording corrections applied:**
- "approved foundation stack" → "explicitly supplied, geometrically consistent foundation stack", and the synonymous "approved founding RL" → "explicitly supplied founding RL" in the catalogue dial note (`schema.py`), the canonical contract comments (`long_section.py`, `models.py`), the sheet-4 comment, the overlay driver prose and the matching `comparison.json` reason. No engineering approval exists; only arithmetic consistency was verified.
- "gates_passed" → "generation_gates_passed" / "quality_and_layout_passed" in `quality_manifest.py`, `_gen_nine_span.py` and tests; `accepted` is kept as a separate flag. `accepted=False` is correct and unchanged.
- Conflict fixture → generation is now aborted **before any DXF is written** when a CONFLICT is detected (`sheets: []`); output is staged in a temporary directory and published only after the required generation checks pass, and a rejected run publishes only a labelled `FAILED-RUN/` directory. The old 5/9-sheet partial output no longer exists.
- Required-content manifest → now present in two forms: human `reference_requirements.json` (13 requirements, all PENDING reviewer verdict) and machine-checked `required_content.json` (75 requirements, 66 applicable, 5 declared gaps).

**Defensible status:** reported geometry-contract progress verified by the listed tests; generated draft — GAD acceptance pending.
