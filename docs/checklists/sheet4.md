# Sheet 4 — FOUNDATION — review checklist

**Sheet key:** `sheet4_foundation` · **Scale:** 1:50 · **Module:** `sheet4_foundation.py`
**Required before review:** every `AUTO` and `SCRIPT` row `☑`.

## A. Frame and scale

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| A1 | Geometry inside frame | `inside_frame` | AUTO | ☐ |
| A2 | Scale honest | `scale_honest` | AUTO | ☐ |
| A3 | No duplicated geometry | `no_duplicate_geometry` | AUTO | ☐ |
| A4 | No zero-length lines | `no_zero_length_lines` | AUTO | ☐ |

## B. Title block and issue

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| B1 | All 12 mandatory fields — including the ones currently blank | `title_block_complete` | AUTO | ☐ |
| B2 | Numbering matches manifest | `sheet_numbering` | AUTO | ☐ |
| B3 | Issue status present | `issue_status_present` | AUTO | ☐ |
| B4 | Revision strip | `MANUAL: no assertion` | MANUAL | ☐ |

## C. Text and dimensions

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| C1 | Legal text heights only | `text_heights` | AUTO | ☐ |
| C2 | ≥ 10 dimensions | `dimension_count` | AUTO | ☐ |
| C3 | `dimlfac` 1000 | `dimension_scale` | AUTO | ☐ |
| C4 | Notes sourced | `notes_sourced` | AUTO | ☐ |

## D. Plan geometry

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| D1 | Cap at `pile_cap_width_m` × `pile_cap_length_m` | `MANUAL: cap size` | MANUAL | ☐ |
| D2 | Cap and pile grid rotated by `skew_angle_deg` | `support_skewed` | AUTO | ☐ |
| D3 | Pile positions from `compute_pile_group_layout` | `MANUAL: layout check` | MANUAL | ☐ |
| D4 | No decorative circle that is not a real feature | `MANUAL: geometry audit` | MANUAL | ☐ |
| D5 | Well branch: outer/inner steining, dredge hole, curb | `MANUAL: well branch` | MANUAL | ☐ |
| D6 | Open branch: stepped footing with offsets | `MANUAL: open branch` | MANUAL | ☐ |

## E. Section and schedule

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| E1 | tip < cutoff < cap bottom < cap top | `foundation_ordering` | AUTO | ☐ |
| E2 | Vertical exaggeration declared | `MANUAL: V.E. note` | MANUAL | ☐ |
| E3 | Main bar dia/spacing per face on `STRUC-DETAIL` | `MANUAL: rebar callout` | MANUAL | ☐ |
| E4 | No `or 1500` fallbacks — missing input shows `—` | `table_cells_sourced` | AUTO | ☐ |
| E5 | Every schedule cell sourced from `fd` or `hd` | `MANUAL: source audit` | MANUAL | ☐ |

## F. Layers

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| L1 | `FOUND-CAP` used | `layer_used` | AUTO | ☐ |
| L2 | `FOUND-PILE` used | `layer_used` | AUTO | ☐ |
| L3 | `FOUND-WELL` used on well fixtures | `layer_used` | AUTO | ☐ |
| L4 | `FOUND-OPEN` used on open fixtures | `layer_used` | AUTO | ☐ |
| L5 | `STRUC-DETAIL` used | `layer_used` | AUTO | ☐ |

## G. Cross-sheet

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| X1 | Cap centre X matches sheet 2 pier X | `cross_sheet_alignment` | AUTO | ☐ |
| X2 | Cap skew agrees with sheet 1 deck shear | `support_skewed` | AUTO | ☐ |

## Sign-off

| | |
|---|---|
| Reviewer | |
| Date | |
| Blocker marks raised | |
| Residual marks accepted | |
| Signed | ☐ |
