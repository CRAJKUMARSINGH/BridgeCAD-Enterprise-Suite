# M1 Week-2 GAD Drawing Refactor — Implementation Tasks

**Spec:** `.trae/specs/m1_week2_draw_refactor_2026-10-07/spec.md`
**Repository root:** `e:\Rajkumar\Bridge_GAD_Yogendra_Borse\`
**Last update:** 2026-10-07

Implementation order respects the dependency graph:
geometry (core) → drawing constants/sheets (1/2/8) → booklet manifest → smoke + verifier.

---

## Task 1: LongSectionGeometry — add pier T.O.C. RLs & plan-northern-edge reference

**Files to modify:**
- `packages/bridgecad-core/bridgecad_core/geometry/long_section.py`

**What to do:**
1. Add two fields to `LongSectionGeometry`:
   - `pier_top_of_cap_rl_m: list[float]` — index aligned to `pier_chainage_m`
   - `plan_northern_edge_reference_rl: float` = `top_of_deck_rl`
   - (for single-span with 0 piers) still provide
     `pier_top_of_cap_rl_m: list[float]` empty and also provide
     `abutment_top_of_rail_rl_m: float` = `top_of_deck_rl` as the fallback
     reference
2. Inside `compute_long_section_geometry()`, for each pier chainage:
   `pier_top_of_cap_rl = soffit_rl - pedestal_h - pier_cap_depth` where
   pedestal_h = sub.pier_pedestal_height_m or 0.2 m, pier_cap_depth =
   sub.pier_cap_depth_m or 0.8 m (both from project.substructure).

**Depends on:** Nothing. (geometry is read-only consumed by sheets; safe first)

### Task-local Test Requirements (TRs)

- **rule TR-T1a:** For a 3×12m continuous project, `pier_chainage_m` has 2
  entries and `pier_top_of_cap_rl_m` has 2 matching entries, each =
  `soffit_rl - 0.2 - 0.8` (default values) to within 1e-6 m.
- **rule TR-T1b:** For simple_12m, `pier_top_of_cap_rl_m == []` (empty list,
  no piers) and `plan_northern_edge_reference_rl == top_of_deck_rl`.
- **rule TR-T1c:** Module still exports `__all__` correctly — `compute_*`
  callable and the new fields are documented via type hints.

**Status:** pending

---

## Task 2: Sheet 1 Plan — loosen vertical auto-fit, move pier labels north, add A-A / B-B section markers

**Files to modify:**
- `packages/bridgecad-draw/bridgecad_draw/sheet1_plan.py`

**What to do:**
1. **Auto-fit Y0:** Replace `_PLAN_Y0 = _MARGIN + _TB_H + 10.0` with a
   runtime calculation. Before drawing plan content, compute the "lowest
   annotation Y" (plan south + scale-bar + chainage-tag + span dims all
   leave space). Then place the plan such that the lowest visible element
   sits exactly at `_MARGIN + _TB_H + 6 mm` gutter. Equivalently:
   - Start with a trial scale & positioning.
   - After computing annotation positions (span dim below deck, chainage
     tags, scale bar), measure their minimum Y.
   - If `min_y > target_lowest_y` (= TB top + 6 mm), translate *the whole
     plan + all annotations down* by `(min_y - target_lowest_y)` to occupy
     the freed vertical space (increasing drawing scale where possible).
   - Simplified implementation acceptable: just set initial `_PLAN_Y0` to
     `_MARGIN + _TB_H + 3 mm` (removing the 10 mm hard floor) *and* reduce
     the `*0.85` fit-shrink from 0.85 → 0.93; this alone yields the
     required behaviour without full two-pass layout.
2. **Move pier labels north:** In the "Piers" drawing loop, label Y becomes
   `vpos(half_w) + text_h*2` (north side) instead of `vpos(-half_w) -
   text_h*2` (south side). Dimension lines stay south; labels migrate.
3. **Section arrows A-A and B-B:** Add a helper primitive `section_arrow()`
   to primitives.py if missing (use polyline + text on STRUC-SECTION). Draw
   `A-A` at 10% of total_len before A1 and `B-B` at first pier chainage
   (or 1 m after A1 if no pier). Mark with `⌃` visual arrows on both
   sides.

### Task-local Test Requirements

- **rule TR-T2a:** `plan_y0` effective bottom (min of all drawn Y) ≤
  `_MARGIN + _TB_H + 12 mm` — verified by ezdxf bounding-box scan of
  Sheet 1 after generation.
- **rule TR-T2b:** For a 3-span project, text entity "P1" Y-centroid >
  deck northern corner Y (pier label sits visually north).
- **rule TR-T2c:** Sheet 1 has text entities with substring "A-A" and
  "B-B", each having an associated polyline on layer `STRUC-SECTION`.

**Status:** pending

---

## Task 3: Sheet 2 Long-Section — loosen vertical auto-fit, tie pier T.O.C. to plan-northern RL reference

**Files to modify:**
- `packages/bridgecad-draw/bridgecad_draw/sheet2_long_section.py`

**What to do:**
1. **Auto-fit draw_y0:** Remove the hard 10 mm term in
   `draw_y0 = _MARGIN + _TB_H + _CHAINAGE_H + 10.0`. Replace with
   `draw_y0 = _MARGIN + _TB_H + _CHAINAGE_H + 3 mm` (minimal gutter).
   Further: grow `draw_h` by the recovered 7 mm, recalc scales.
2. **Use new LS geometry fields:**
   - Pull `ls.plan_northern_edge_reference_rl` (top of deck RL).
   - Pull `ls.pier_top_of_cap_rl_m[i]` for pier i.
   - Draw pier shafts with top at `vy(pier_top_of_cap_rl_m[i])` instead of
     the old `soffit − pedestal − cap` manual calc.
   - Draw a T.O.C. P{idx} level tag immediately right of pier cap top,
     level-tagged to the RL.
3. Add a fine dashed guide-line (layer `STRUC-SECTION`) horizontally from
   the pier T.O.C. rightwards to the level axis, terminating at a
   mini-level-tag to confirm alignment to `plan_northern_edge_reference`
   — i.e., the reader can visually trace the same RL across the sheet.

### Task-local Test Requirements

- **rule TR-T3a:** chainage_axis_baseline_Y ≤ `_MARGIN + _TB_H +
  _CHAINAGE_H + 9 mm` on the generated Sheet 2 DXF.
- **rule TR-T3b:** Pier rectangle top Y-coordinate equals
  `vy(pier_top_of_cap_rl_m[i])` to within 0.05 mm on the DXF.
- **rubric TR-T3c:** T.O.C. label legibility. Score 0–2. 2 = label sits
  clear of other entities; 1 = some crowding; 0 = overlap. Threshold ≥ 1.

**Status:** pending

---

## Task 4: New Sheet 8 Side & End Elevations (two views, separate page)

**Files to create/modify:**
- Create: `packages/bridgecad-draw/bridgecad_draw/sheet8_side_elevations.py`
- Modify: `packages/bridgecad-draw/bridgecad_draw/booklet.py`
- Modify: every sheet `*_plan.py`, `*_long_section.py`, `*_cross_section.py`,
  `*_foundation.py`, `*_pier_abutment_details.py`, `*_bearings_joints.py`,
  `*_bill_of_quantities.py` — change the single `total_sheets="7"` → `"8"`
  literal passed to `draw_title_block(...)`.

**What to do (Sheet 8):**
1. Expose `generate(project, output_path, scale_denom=50) -> Path` matching
   the standard booklet signature.
2. A1 landscape, border + title block `"GENERAL ARRANGEMENT — SIDE & END
   ELEVATIONS"`, `sheet_no="8"`, `total_sheets="8"`.
3. Split page horizontally 50/50: left half = View 1 (Abutment A2
   End-Face looking back); right half = View 2 (Pier Transverse Cut B-B or
   fallback Abutment Typical Section if span_count==1).
4. **View 1 (Abutment A2 End-Face):** Deck top, wearing coat, kerbs,
   parapet/railing, footpaths, bearings, abutment shaft (rect with
   hatch), return walls L/R, wing wall splay dashed lines, approach slab
   (partial hatch), piles (if applicable) or open footing steps, RL tags
   at: approach-road-formation, top-of-deck, soffit, bearing seat, top
   of abutment, base of abutment, pile tip / foundation bottom. Width
   dims: parapet-to-parapet, carriageway, bearing centres.
5. **View 2 (Pier P1 Transverse):** Deck top, girder webs & flanges (I or
   box outline as appropriate), bearings, pier cap rectangle (hatch),
   pier shaft (hatch), pile cap rectangle (hatch), piles in column/pile
   count (draw first and last explicitly + dashed for the rest), all RL
   tags. Label each pile "1200 Ø BORED PILE / 2 nos c/c 2.4 m" as
   applicable. If span_count == 1 → fall back to a "Typical Abutment
   Transverse Section" instead (copy View 1 but labelled as "TYPICAL
   ABUTMENT TRANSVERSE SECTION").
6. Use layers per layers.py registry (SUB-ABUT, SUB-PIER, FOUND-PILE etc.)
   and dimensions via `dim_linear_v`/`h`.

**Booklet update:**
- Prepend `(8, "sheet8_side_elevations", "Sheet8_SideElevations", 50)` as
  the 8th entry in `_SHEET_MANIFEST`. Update any "7/7" progress log
  string inside `generate_package` to 8.

### Task-local Test Requirements

- **rule TR-T4a:** 8th entry in booklet manifest points to
  `sheet8_side_elevations`.
- **rule TR-T4b:** `simple_12m_Sheet8_SideElevations.dxf` is generated by
  smoke run and is ≥ 20 KB.
- **rule TR-T4c:** Sheet 8 DXF contains two distinct "VIEW LABEL" header
  text entities: one for abutment end-face, one for pier/fallback.
- **rule TR-T4d:** Regex/ezdxf scan of all 8 generated sheet DXFs shows
  that every sheet title-block reports `"/ 8"` (total_sheets = 8).

**Status:** pending

---

## Task 5: Standards polish + smoke verifier update + acceptance verifier

**Files to modify:**
- Create: `packages/bridgecad-draw/m1w2_verify.py` (new acceptance suite)
- Optionally tweak sheet title fonts + scale string patterns in sheet 1,
  2, 8: `drawing_title` strings already match Annex D patterns, demote
  "Not to Scale" disclaimer 10% smaller + colour 8 gray as per FR-8.

**What to do:**
1. Build `m1w2_verify.py` that:
   - Runs booklet generate on simple_12m (reuse the fixture from the
     existing smoke_test_m3 without the file-writing assertions).
   - Runs probe checks AC-1 … AC-8 inclusive (all rule ACs).
   - Reports pass/fail per AC + a final verdict.
2. Demote the "Not to Scale" disclaimer font size to 90% of current and
   colour=8 (grey) on sheets 1, 2, 8.

### Task-local Test Requirements

- **rule TR-T5a:** `m1w2_verify.py` runs cleanly EXIT 0 (all 8 rule ACs
  pass).
- **rubric TR-T5b:** AC-9 elegance metric. Compare smoke outputs: find
  bounding-box height ratio of drawing-area / usable-page (usable = sheet
  height minus margin minus TB) for sheets 1 and 2 before vs after. Must
  gain ≥ 4% (i.e., was using 64%, now ≥ 68%). Threshold ≥ 2 score.
- **rubric TR-T5c:** AC-10 IRC conformance. Probe 10+ text entities on
  Sheet 8: titles 4–5 mm, dimensions 2.5±0.3 mm, all labels ≥ 1.8 mm.
  Threshold ≥ 2 score.

**Status:** pending

---

## Task 6: Clean up shadow sheets directory (optional safety audit)

**Files to modify:** None directly. If we find that
`bridgecad_draw/sheets/sheet1_plan.py` is still imported anywhere via a
path we didn't notice → fix it. Otherwise just audit once.

**What to do:** Grep import lines for `from .sheets.`. Confirm booklet.py
import path is `f".{mod_attr}"` with package=`bridgecad_draw` — this
resolves to `bridgecad_draw.sheetX_*` (root files canonical). If shadow
dir has an `__init__.py` that re-exports, nothing to do; otherwise leave
shadow copies untouched by design.

### Task-local Test Requirements

- **rule TR-T6a:** No module in the draw package imports the
  `bridgecad_draw.sheets.*` duplicates; only root `.sheetX_*` active.

**Status:** pending

---

## AC → Task coverage matrix

All rule/rubric acceptance criteria from spec covered:

| AC | Task(s) |
|---|---|
| AC-1 Plan vertical auto-fit | Task 2 |
| AC-2 LongSection vertical auto-fit | Task 3 |
| AC-3 Pier labels NORTH on Sheet 1 | Task 2 |
| AC-4 Pier T.O.C. RL = plan-reference | Task 1 + Task 3 |
| AC-5 A-A / B-B section markers | Task 2 |
| AC-6 Sheet 8 exists ≥20KB | Task 4 |
| AC-7 8 sheets in smoke | Task 4 + Task 5 |
| AC-8 total_sheets = "8" everywhere | Task 4 |
| AC-9 (rubric) page-space economy | Tasks 2,3 — measured in Task 5 |
| AC-10 (rubric) IRC standards conformance | Tasks 4,5 — verified by Task 5 |
