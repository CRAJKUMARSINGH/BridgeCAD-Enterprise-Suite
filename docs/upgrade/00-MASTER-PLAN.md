# BridgeCAD Enterprise Suite — 52-Week Upgrade to Industry-Standard Drawing Output

**Status:** governing document. Supersedes `MASTER_ROADMAP.md` §12 for all
drawing-engine work.
**Version:** 1.0 · **Baseline commit:** `2acef08`
**Owner:** repository maintainer
**Throughput assumption:** one maintainer, ~10 focused hours per week.
Team of 3 compresses Q1 weeks 5–13 into 3 calendar weeks; Q2 onward compresses
roughly 2:1. Do not compress Q1 weeks 1–4 — they are the measurement baseline.

---

## 1. Why this plan exists

The Suite generates plausible-looking sheets that an engineer cannot issue. The
gap is not aesthetic. It is that **the drawing engine operates in paper
millimetres while the repository's own coordinate contract declares model space
to be 1:1 millimetre**, and no sheet honours the contract.

Concretely, at baseline:

| # | Defect | Evidence |
|---|---|---|
| 1 | Scale is fit-to-paper, then labelled as a declared ratio | `sheet1_plan.py` `scale = min(scale_h, scale_v) * 0.93`; title block stamps `1:{scale_denom}` from the argument |
| 2 | Both primary sheets self-declare "Not to Scale" | `sheet1_plan.py`, `sheet2_long_section.py` view labels |
| 3 | The coordinate contract is never called | `coordinates.py` + `titleblocks.draw_sheet_frame()` exist; sheets 1–5 call `draw_border`/`draw_title_block` instead |
| 4 | `CoordMapper` is constructed then discarded | `sheet2_long_section.py`, replaced by local `hx()`/`vy()` closures |
| 5 | Dimensions are exploded lines + text, no DIMENSION entity | `primitives.dim_linear_h/v` |
| 6 | The one native dimension sets no `dimlfac`, so it reads paper mm | `sheet3_cross_section.py` `add_linear_dim` |
| 7 | Vertical exaggeration hardcoded (`v_exag=2.0`, `sc*1.5`) and undeclared | `sheet2`, `sheet4` |
| 8 | Text height derived from fit scale, so it varies per project | `th = max(2.5, sc_h * 0.4)` |
| 9 | 33 of 53 registered layers unused; sections omit bearings, pedestals, pile caps, wearing course, kerb, parapet, drainage, strata | `layers.py` vs sheet modules |
| 10 | Title block fields blank on sheets 3 and 4 | no `scale_str`, no date, no check/approve |
| 11 | Skew shears the deck but not the supports | `sheet1_plan.py` deck parallelogram vs axis-aligned pier rectangles |
| 12 | Dead statements discard computed values | `sheet2` pile-cap thickness, pile spacing; `sheet4`; `bill/processor.py` |
| 13 | E2E checks file count and total kilobytes only | `tests/e2e/run_e2e.py` E5 |
| 14 | Pile cap drawn above the cutoff level (inverted) | `sheet4_foundation.py` `cap_top = pile_cut + cap_thickness` |

**Root cause:** the geometry layer was built to put *something* on the page; the
paperwork layer (contract, coordinates, frame, layer registry) was written
afterwards to describe the intent. The two were never joined. Any fix that
touches only the sheets will be re-broken by the next feature.

---

## 2. Principles

1. **Measure before you fix.** Weeks 1–4 exist so that every later week can
   prove it did not regress. No refactor before the assertion harness is green
   against baseline-known-bad output.
2. **One coordinate system.** Model space is millimetres, 1:1, Y up, datum
   declared. Paper scale is applied at plot time only. `coordinates.py` clause
   set is law.
3. **Dimensions are entities.** A dimension the reader can measure, with
   `dimlfac` set so the text reads real metres, on a named DIMSTYLE.
4. **Text heights come from paper.** 2.5 / 3.5 / 5.0 / 7.0 mm at plot scale,
   nothing else. No adaptive heights.
5. **A sheet is either to scale or it says so in the title block.** Auto-fit is
   permitted only with an explicit `SCALE: NTS` and a graphic scale bar.
6. **Every drawn element traces to a model field or a standard clause.** No
   geometry invented inside a sheet module.
7. **Deleted code beats new code.** Removing `draw_border` from sheets is worth
   more than any new drawing feature.

---

## 3. Phase structure

| Phase | Weeks | Theme | Exit gate |
|---|---|---|---|
| **Q1-A** | 1–4 | Freeze, golden cases, assertion harness | Harness green on 5 golden cases; baseline defect ledger committed |
| **Q1-B** | 5–10 | Coordinate contract enforcement | No sheet calls `draw_border`; every sheet passes origin/frame/scale assertions |
| **Q1-C** | 11–13 | Native dimensions | Every dimension is a DIMENSION entity with correct `dimlfac` |
| **Q2-A** | 14–18 | Text hierarchy + title block completion | Fixed paper heights; no blank mandatory title fields |
| **Q2-B** | 19–23 | Sheet 2 reconstruction (long section) | Bearings, pedestals, caps, strata present and asserted |
| **Q2-C** | 24–26 | Sheet 4 reconstruction (foundation) | Cutoff/cap/tip ordering asserted; well + open foundation branches |
| **Q3-A** | 27–30 | Sheet 5/6 reconstruction | Pier/abutment/bearing/joint detail asserted |
| **Q3-B** | 31–34 | Skew, superelevation, camber correctness | Skewed supports match skewed deck |
| **Q3-C** | 35–38 | BOQ derivation | Multiplier table retired for formwork + rebar |
| **Q4-A** | 39–43 | Visual regression + engineer review | 5 golden cases signed off per bridge family |
| **Q4-B** | 44–47 | Standards traceability matrix | Every drawn element mapped to an IRC clause |
| **Q4-C** | 48–52 | Release gate | `construction-ready` claim unlocked |

Dependencies: Q1-A gates everything. Q2-B and Q2-C may run in parallel once
Q1-C is green. Q3-C depends on Q2-C (quantities need correct geometry).

---

## 4. Definition of done (per week)

A week is done only when all six hold:

1. Code merged to `main`.
2. New assertions added to `tests/draw/` and failing before the fix.
3. Full harness green: `python tests/draw/run_dxf_assertions.py`.
4. `make lint && make test` green.
5. All 28 E2E fixtures still emit 8 sheets.
6. Week entry in `docs/upgrade/PROGRESS.md` with before/after entity counts.

---

## 5. Global acceptance metrics

Tracked weekly in `docs/upgrade/METRICS.md`. Baseline captured in week 1.

| Metric | Baseline | Target |
|---|---|---|
| Sheets declaring a true scale | 0 / 8 | 8 / 8 |
| Sheets with `NTS` correctly declared | 2 / 8 (unlabelled in TB) | 8 / 8 |
| Native DIMENSION entities per package | ~1 | ≥ 120 |
| Dimensions with `dimlfac` = 1000 | 0 | all |
| Distinct text heights in a package | 14–22 | 6 |
| Registered layers used | 20 / 53 | 53 / 53 |
| Blank mandatory title-block fields | 6 per sheet | 0 |
| Assertions in harness | 0 | ≥ 90 |
| Golden cases with engineer sign-off | 0 / 5 | 5 / 5 |

---

## 6. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Contract migration breaks all 28 fixtures | High | High | Fixtures assert geometry not pixels; migrate one sheet per week, keep both frame functions behind a flag until week 10 |
| Solo maintainer burnout in Q2 | Medium | High | Q2 weeks are capped at one sheet each; no week touches two sheets |
| Engineer reviewer unavailable | Medium | High | Recruit by week 30; Q4-A is worthless without it |
| Scope creep into 3D/SVG engines | High | Medium | 3D frozen until week 52 |
| Standards mis-citation | Medium | High | Every clause in the traceability matrix cited by number and year, checked in review |
| Golden cases too few to catch regressions | Medium | Medium | 5 cases span slab, T-beam, PSC girder, box culvert, skew |

---

## 7. File map

| File | Contents |
|---|---|
| `00-MASTER-PLAN.md` | this document |
| `Q1-W01-W13-FOUNDATION.md` | weeks 1–13 |
| `Q2-W14-W26-SECTIONS.md` | weeks 14–26 |
| `Q3-W27-W38-DETAILS.md` | weeks 27–38 |
| `Q4-W39-W52-RELEASE.md` | weeks 39–52 |
| `PROGRESS.md` | weekly log |
| `METRICS.md` | metric table, updated weekly |
| `DEFECT-LEDGER.md` | every baseline defect, with the week that closes it |
| `TRACEABILITY.md` | drawn element → IRC clause (from week 44) |

---

## 8. What is frozen until week 52

- 3D, SVG and PNG engines (`engines/`)
- `bridgecad-ai` optimiser
- React console and Streamlit tabs
- Plugin count (stays at 3)
- New bridge types
- Mobile
