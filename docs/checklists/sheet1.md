# Sheet 1 — PLAN — review checklist

**Sheet key:** `sheet1_plan` · **Scale:** 1:200 (or NTS) · **Module:** `sheet1_plan.py`
**Required before review:** every `AUTO` and `SCRIPT` row `☑`.

## A. Frame and scale

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| A1 | Geometry inside the declared frame | `inside_frame` | AUTO | ☐ |
| A2 | Declared scale matches drawn extent, or NTS with scale bar | `scale_honest` | AUTO | ☐ |
| A3 | Layout exists, viewport at declared scale | `viewport_scale` | AUTO | ☐ |
| A4 | No duplicated geometry — deck drawn once | `no_duplicate_geometry` | AUTO | ☐ |
| A5 | No zero-length lines | `no_zero_length_lines` | AUTO | ☐ |

## B. Title block and issue

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| B1 | All 12 mandatory fields populated | `title_block_complete` | AUTO | ☐ |
| B2 | Sheet number and total match the manifest | `sheet_numbering` | AUTO | ☐ |
| B3 | Issue status block present | `issue_status_present` | AUTO | ☐ |
| B4 | Revision strip from revision history | `MANUAL: no assertion` | MANUAL | ☐ |
| B5 | Scale cell reads the true ratio or `NTS` | `MANUAL: TB text content` | MANUAL | ☐ |

## C. Text and dimensions

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| C1 | Text heights from the six legal paper values | `text_heights` | AUTO | ☐ |
| C2 | ≥ 10 native DIMENSION entities | `dimension_count` | AUTO | ☐ |
| C3 | Every dimension `dimlfac` 1000 | `dimension_scale` | AUTO | ☐ |
| C4 | Every note sourced | `notes_sourced` | AUTO | ☐ |
| C5 | Chainage labels legible, correct km format | `MANUAL: format check` | MANUAL | ☐ |

## D. Content

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| D1 | Deck outline drawn once, at `overall_width_m` | `drawn_extent` | AUTO | ☐ |
| D2 | Piers at true chainages from `span_lengths_m` | `cross_sheet_alignment` | AUTO | ☐ |
| D3 | Supports rotated by `skew_angle_deg`, same sense as the deck | `support_skewed` | AUTO | ☐ |
| D4 | Abutment footprints at both ends, correct type | `MANUAL: footprint check` | MANUAL | ☐ |
| D5 | Section markers A-A / B-B at the right chainages, arrows the right way | `MANUAL: marker direction` | MANUAL | ☐ |
| D6 | Superelevation run-off extent shown where `superelevation_pct` ≠ 0 | `MANUAL: run-off check` | MANUAL | ☐ |
| D7 | Curved bridges: true arc, supports radial | `MANUAL: curvature check` | MANUAL | ☐ |
| D8 | No dimension string duplicated as free text | `MANUAL: double-dimensioning` | MANUAL | ☐ |

## E. Layers

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| L1 | `SUPER-DECK` used | `layer_used` | AUTO | ☐ |
| L2 | `SUB-PIER` used | `layer_used` | AUTO | ☐ |
| L3 | `SUB-ABUT` used | `layer_used` | AUTO | ☐ |
| L4 | `CIVIL-CHAINAGE` used | `layer_used` | AUTO | ☐ |
| L5 | `SYM-SECTIONMARK` used | `layer_used` | AUTO | ☐ |
| L6 | `STRUC-CENTRELINE` used | `layer_used` | AUTO | ☐ |

## F. Cross-sheet

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| X1 | Pier X matches sheet 2 within 1 mm | `cross_sheet_alignment` | AUTO | ☐ |
| X2 | Section marker chainage equals sheet 2 origin chainage | `cross_sheet_alignment` | AUTO | ☐ |

## Sign-off

| | |
|---|---|
| Reviewer | |
| Date | |
| Blocker marks raised | |
| Residual marks accepted | |
| Signed | ☐ |
