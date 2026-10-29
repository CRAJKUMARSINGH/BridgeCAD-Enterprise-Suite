# Sheet 8 — SIDE ELEVATIONS — review checklist

**Sheet key:** `sheet8_side_elevations` · **Scale:** 1:200 · **Module:** `sheet8_side_elevations.py`
**Required before review:** every `AUTO` and `SCRIPT` row `☑`.

Note: `sheet8_side_elevations` has no `FRAMES` entry at baseline — add one in
week 5 or the frame rows stay red.

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
| B1 | All 12 mandatory fields | `title_block_complete` | AUTO | ☐ |
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

## D. Content

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| D1 | Elevation silhouette agrees with sheet 2 longitudinal section | `cross_sheet_alignment` | AUTO | ☐ |
| D2 | Soffit and deck levels at model RLs | `MANUAL: level check` | MANUAL | ☐ |
| D3 | Pier heights consistent with sheet 5 | `MANUAL: height parity` | MANUAL | ☐ |
| D4 | Skew visible in elevation where skew ≠ 0 | `support_skewed` | AUTO | ☐ |
| D5 | No element present that is absent from sheets 1–5 | `MANUAL: consistency audit` | MANUAL | ☐ |

## E. Layers

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| L1 | `STRUC-OUTLINE` used | `layer_used` | AUTO | ☐ |
| L2 | `SUB-PIER` used | `layer_used` | AUTO | ☐ |
| L3 | `TEXT-LEVEL` used | `layer_used` | AUTO | ☐ |

## Sign-off

| | |
|---|---|
| Reviewer | |
| Date | |
| Blocker marks raised | |
| Residual marks accepted | |
| Signed | ☐ |
