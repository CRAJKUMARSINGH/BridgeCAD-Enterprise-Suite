# M1 Week-2 GAD Drawing Refactor — BridgeCAD Enterprise Suite

**Specification date:** 2026-10-07
**Owner:** Bridge GAD Draw Pipeline
**Repository root:** `e:\Rajkumar\Bridge_GAD_Yogendra_Borse\`
**Target packages:** `packages/bridgecad-draw/bridgecad_draw/*` (canonical root sheets), `packages/bridgecad-core/bridgecad_core/geometry/*`

---

## 1. Problem

The current 7-sheet GAD DXF package (bridgecad-draw) has three quality defects
that materially hurt output correctness and page-space elegance:

1. **Plan and Long-Section views use a rigid fixed vertical bottom-margin**
   (hard-coded `_PLAN_Y0 = _MARGIN + _TB_H + 10.0` and
   `draw_y0 = _MARGIN + _TB_H + _CHAINAGE_H + 10.0`). These waste 15–25 mm of
   A1 page height per sheet and prevent drawings from being optimally sized.
2. **Pier level in elevation has no coherent datum relationship with the plan
   view's northern deck edge.** Plan pier labels P1/P2 are placed on the
   southern edge and the pier-cap top RL in elevation is computed to an
   arbitrary formula (`hfl_rl − pier_height_typical`). The relationship
   "pier-cap-top RL ↔ plan's northern deck-edge RL" is therefore *invisible*
   to the reader and visually misaligned across sheets.
3. **There is no side / end-face elevation page** in the booklet. The
   transverse cross-face of piers and abutments (showing parapet, deck
   thickness, bearings, full pile group, wing walls, return walls) is not
   drawn anywhere.

Further, the user's intent "overall updation in tune w/ latest bridge drawing
standards and practice" mandates we audit:

- IRC SP:55-2019 text height, lineweight, and scale tables;
- IRC:21 cross-section / end-view practices;
- Proper end-section cut markers (⌃ section arrows) on Sheet 1 Plan.

## 2. Users & Goals

| User | Goal |
|---|---|
| Bridge Designer (producer) | Generate a visually coherent 8-sheet GAD DXF package whose pier/abutment levels on Sheet 2 line up with the north-edge annotation baseline on Sheet 1, with no wasted space. |
| Site Engineer (consumer) | Read pier levels on Sheet 2, then glance at Sheet 1 and immediately see that pier P1 sits on chainage X *at the north edge* — same baseline. |
| Checking Engineer | Confirm that the new Sheet 8 (Side Elevation) pier-transverse and abutment-end-face views match the 3D dimensions on Sheets 1/2/5, to IRC standards. |
| BridgeCAD QA verifier | Run `smoke_test_m3.py` on simple_12m and get: 8/8 sheets generated, each ≥10 KB; a new verifier that asserts the 3 alignments above visually pass. |

## 3. Non-Goals

Out of scope for this refactor:

- Reinforcement drawings (`gen_reinforcement_sheet` stays False).
- SVG / PDF / PNG engine overrides — we only rework DXF (engines/ unchanged unless primitive-level fixes are needed there).
- BOQ (Sheet 7) or bearings-joints (Sheet 6) content changes — those pages are unrelated.
- Changing the legacy `bridgecad_draw/sheets/*.py` duplicates. They stay untouched; the booklet manifest already points to `bridgecad_draw.sheetX_*` at package root which is the canonical set.

---

## 4. Functional Requirements

### FR-1 Bottom vertical constraint on Sheet 1 Plan is auto-fit, not fixed.

**When** drawing sheet 1 Plan, the engine SHALL decide `_PLAN_Y0` automatically
from the following rules in priority order:

1. Title block stays anchored at sheet bottom, height = 65 mm (IRC SP:55 compliant).
2. 6 mm tidy gutter between bottom of the lowest annotation on plan view (scale bar or chainage tags) and top of title block.
3. The plan view and its annotations (north arrow, chainage tags, span dims, scale bar, width dims) expand *to use the freed vertical space* — scaling denominator is allowed to grow if more room permits (resulting in larger drawing OR more readable annotation room).
4. No hard minimum of 10 mm between title-block and lowest plan element shall remain in the code.

### FR-2 Bottom vertical constraint on Sheet 2 Long-Section is auto-fit.

Analogous to FR-1. The datum RL drawn at the bottom (chainage axis) shall be
placed 6 mm above the title-block top edge. The scale factors `sc_h` and
`sc_v` SHALL be recalculated so the vertical range fits tightly from the
lowest RL line (pile tip) to the highest (top of deck + 2.5 m) with only a
3 mm gutter for labels above. `draw_h` grows by the margin previously
wasted (approximately 15 mm).

### FR-3 Plan pier labels move to the NORTHERN deck edge.

Pier labels `P1, P2, …` on Sheet 1 SHALL be placed at y = northern-deck-edge
+ a tidy offset (2 × text_height spacing) instead of the current southern
edge placement. Chainage tags SHALL remain on the south edge to preserve
visual separation.

### FR-4 Pier top-of-cap RL in elevation ties to plan northern-deck edge datum.

1. Add a computed RL to `LongSectionGeometry`:
   - `pier_top_of_cap_rl_m: list[float]` — top-of-cap RL per pier.
   - `plan_northern_edge_reference_rl: float` — single RL that represents the
     plan-northern deck reference (top-of-deck RL is the answer).
2. On Sheet 2 Long Section, draw a new short horizontal section reference line
   spanning the pier shaft width at `pier_top_of_cap_rl`, labelled `T.O.C.
   P1 (RL xxx.xxx)` with a level tag *and* emit a sheet-coordinate
   annotation comment that asserts this y-coordinate (in mm) equals the
   `plan_northern_edge_reference_rl`'s vy() projection — i.e., if you
   overlay Sheet 1 and Sheet 2 physically, the northern deck edge (top RL)
   lines through to the pier cap top RL.
3. Ensure the pier shaft is drawn with its TOP at `pier_top_of_cap_rl` (real
   value), not the current `soffit − pedestal − cap` approximation.

### FR-5 Section cut indicators on Sheet 1 Plan for Sheet 8 views.

Add section arrows:
- `⌃ A-A` just upstream of A1 abutment → marks the abutment-end-face cut
  (Sheet 8 View 1).
- `⌃ B-B` at pier P1 (single span) or first internal pier → transverse pier
  cut (Sheet 8 View 2).
- Section arrows follow IRC SP:55 Clause 11.4 style: arrowheads, thick
  ends, label on cut plane.

### FR-6 New Sheet 8 — Side Elevations (two views on one A1 page).

Add `bridgecad_draw/sheet8_side_elevations.py` exposing `generate(...)` and
register it as the 8th entry in `booklet._SHEET_MANIFEST`:

```
(8, "sheet8_side_elevations", "Sheet8_SideElevations", 50)
```

Contents of the sheet:

| # | View | Content |
|---|---|---|
| 1 | Abutment End-Face A2 (looking back from A2 towards A1) | Full transverse face: deck, wearing coat, kerbs, parapet, bearings, abutment shaft, return walls (left/right), wing wall splay indicators, approach-slab hatch, foundation/pile group under, all RL tags, dimension strings. |
| 2 | Pier Transverse Face P1 (if ≥1 internal pier, else a notional pier section) | Deck slab, girder soffit, bearings, pier cap, pier shaft, pile cap, full pile-group elevation with column/pile count labels, all RL tags. |

If the project has no internal piers (span_count=1), View 2 SHALL gracefully
fall back to an "Abutment-Typical Transverse Section" to populate the page.

### FR-7 Booklet renumbers sheets to correctly reflect 8 total.

All `total_sheets` arguments to `draw_title_block` across sheets 1 through 7
SHALL be updated from "7" to "8". Sheet 8 total_sheets is also "8".

### FR-8 IRC standards polish pass across Sheet 1/2/8 titles & scales.

Each sheet title block `drawing_title` string SHALL match the naming pattern
from IRC SP:55 Annex D example GAD:

- Sheet 1: `GENERAL ARRANGEMENT — PLAN VIEW`
- Sheet 2: `GENERAL ARRANGEMENT — LONGITUDINAL SECTION`
- Sheet 8: `GENERAL ARRANGEMENT — SIDE & END ELEVATIONS`

Scale strings SHALL use the PREFERRED_SCALE from `irc_sp55.preferred_scale()`
falling back to manual override only if content cannot fit; "Not to Scale"
disclaimers SHALL remain but be demoted to 2 pt smaller, grey colour.

---

## 5. Non-Functional Requirements

### NFR-1 Backwards compatibility

`smoke_test_m3.py` SHALL continue to pass (generating ≥7 sheets) — except now
it generates 8 sheets, all ≥10 KB.

### NFR-2 Repo cleanliness

Only files under these paths are touched:

```
packages/bridgecad-draw/bridgecad_draw/*.py           (root sheets + booklet)
packages/bridgecad-core/bridgecad_core/geometry/long_section.py
```

The `sheets/` duplicate tree, `engines/` directory, `primitives.py`,
`layers.py`, `titleblocks.py` and `dxf_engine.py` are modified only if
necessary to support FR-1..FR-8 with new primitive helpers.

### NFR-3 3rd-party free

No new pip dependencies. Keep using `ezdxf` (already present — confirmed by
working smoke test).

### NFR-4 Performance

Simple-12m 8-sheet run SHALL complete in ≤ 2.5× today's 7-sheet runtime.

---

## 6. Constraints, Assumptions, Open Questions

- **Constraint A:** Title block height of 65 mm is IRC SP:55 minimum and
  MUST NOT be reduced. See user-answer "Maximal shrink" was declined.
- **Constraint B:** Sheet size remains A1 landscape (841 × 594 mm). No A0.
- **Assumption 1:** `soffit_rl` and `top_of_deck_rl` values from geometry
  are the authoritative RL references; we will derive all other RLs from
  them plus known thicknesses (girder depth, deck, wearing coat, pedestal,
  pier_cap_depth) — not from the old `hfl_rl − pier_height_typical`
  approximation.
- **Assumption 2:** For single-span projects without internal piers, View 2
  of Sheet 8 falls back to a "Typical Abutment Transverse Section" (there
  is no pier to cut — we show A1 end-face instead and label it).
- **Open Question 1 (resolvable later, not blocker):** Should we emit a
  `SHEET_ORDER.md` file? User did not ask for docs → non-goal.

---

## 7. Acceptance Criteria

### rule AC-1: Sheet 1 Plan vertical auto-fit

Run `python smoke_test_m3.py`. Open the resulting
`smoke_output_simple_12m/simple_12m_Sheet1_Plan.dxf` in a DXF inspector or
ezdxf load script. The lowest non-title-block, non-border polyline/text Y
coordinate SHALL be ≤ (title-block-top + 12 mm). Equivalently: the
`plan_y0` value in Sheet 1 after refactor SHALL be ≤ (`_MARGIN + _TB_H + 8`)
measured by running a probe script.

### rule AC-2: Sheet 2 Long-Section vertical auto-fit

Likewise on Sheet 2, the chainage-axis baseline Y SHALL be ≤ (title-block
top + 9 mm) — i.e., the old +10 mm hard floor between TB top and chainage
is gone.

### rule AC-3: Pier labels P1/P2 on Sheet 1 sit above NORTHERN deck edge

On Sheet 1 Plan: `y(text_P1) > y(max_transverse_deck_corner)` — i.e., label
is visually *above* (north) of the deck northern corner.

### rule AC-4: Pier top-of-cap RL on Sheet 2 equals plan-reference RL

For the simple_12m project the pier_top_of_cap_rl (if no pier, abutment cap
top RL is used) SHALL equal `ls.top_of_deck_rl − girder_depth − deck_thickness
− wc_thickness − pedestal − cap_depth` as verified by:

```python
assert abs(pier_top_of_cap_rl - calc) < 0.01
```

### rule AC-5: Section-cut markers present on Sheet 1

Sheet 1 DXF SHALL contain text entities with content containing "A-A" and
"B-B" and have section-arrow polylines on layer `STRUC-SECTION` at those
locations.

### rule AC-6: Sheet 8 exists and has ≥20 KB of content

8th entry in booklet manifest present. Generated DXF `Sheet8_SideElevations`
size ≥ 20 KB (two views guarantee this).

### rule AC-7: All 8 sheets generated in smoke_test_m3.py

Smoke test output reports "Generated 8 sheets" and "All sheets > 10KB:
PASS".

### rule AC-8: All sheet title blocks total_sheets = "8"

Assert via regex scan of DXF text entities: every sheet has "Sheet X / 8"
or `total_sheets` rendered string equals "8".

### rubric AC-9: Drawing elegance (page-space economy)

**Scale 0–3.** 3 = ≥8 % of previously-wasted vertical space is now
occupied by actual drawing / readable annotation; 2 = 4–8 %; 1 = marginal
improvement; 0 = no change. Threshold ≥ 2 to pass. Evidence: compare the
drawing extent rectangles before/after via ezdxf bounding-box probe on
smoke_output_simple_12m sheets 1 and 2.

### rubric AC-10: Standards conformance (IRC SP:55 text heights & scales)

**Scale 0–3.** 3 = All sheet titles ≥ 4.0 mm (A1), subtitles 3.0–3.5 mm,
dimension strings 2.5 mm (within ±0.2 mm), correct PREFERRED_SCALE per
view type; 2 = most pass, 1 minor deviation tolerated; 1 = 2+ deviations
< 0.5 mm; 0 = non-compliant labels / wrong scales. Threshold ≥ 2 to pass.

---

## 8. Glossary

| Term | Meaning |
|---|---|
| TB | Title Block — 65 mm band anchored at sheet bottom. |
| GAD | General Arrangement Drawing. |
| T.O.C. | Top Of Concrete — top of the pier cap. |
| T.O.D. | Top Of Deck (wearing coat included) — also called formation. |
| N-edge / Northern edge | Transverse positive-Y side of the deck on plan view. |
| A1, A2 | First and Second Abutments (start / end of bridge chainage). |
| P1, P2… | Internal piers |
| V.E. | Vertical Exaggeration factor applied to long-section vertical scale. |
