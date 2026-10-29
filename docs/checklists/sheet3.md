# Sheet 3 — CROSS SECTION — review checklist

**Sheet key:** `sheet3_cross_section` · **Scale:** 1:50 · **Module:** `sheet3_cross_section.py`
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
| B1 | All 12 mandatory fields | `title_block_complete` | AUTO | ☐ |
| B2 | Numbering matches manifest | `sheet_numbering` | AUTO | ☐ |
| B3 | Issue status present | `issue_status_present` | AUTO | ☐ |
| B4 | Revision strip | `MANUAL: no assertion` | MANUAL | ☐ |

## C. Text and dimensions

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| C1 | Legal text heights only | `text_heights` | AUTO | ☐ |
| C2 | ≥ 10 dimensions | `dimension_count` | AUTO | ☐ |
| C3 | `dimlfac` 1000 — carriageway reads 11.500, not 624 | `dimension_scale` | AUTO | ☐ |
| C4 | No duplicate `CW=` text beside the native dimension | `MANUAL: double-dimensioning` | MANUAL | ☐ |
| C5 | Notes sourced | `notes_sourced` | AUTO | ☐ |

## D. Geometry

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| D1 | Section normal to the deck edge on skewed bridges | `support_skewed` | AUTO | ☐ |
| D2 | Deck rotation from `superelevation_pct` / `cross_fall_pct` | `MANUAL: rotation check` | MANUAL | ☐ |
| D3 | Deck top a single continuous profile, camber + SE combined | `MANUAL: profile continuity` | MANUAL | ☐ |
| D4 | Girder/deck depth at model values | `MANUAL: depth check` | MANUAL | ☐ |
| D5 | Kerb, footpath, wearing course, parapet all at full dimension | `MANUAL: element check` | MANUAL | ☐ |
| D6 | Drainage fall arrows point to the low kerb | `MANUAL: arrow direction` | MANUAL | ☐ |

## E. Layers

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| L1 | `SUPER-WEARING` used | `layer_used` | AUTO | ☐ |
| L2 | `SUPER-KERB` used | `layer_used` | AUTO | ☐ |
| L3 | `SUPER-PARAPET` used | `layer_used` | AUTO | ☐ |
| L4 | `SUPER-DECK` used | `layer_used` | AUTO | ☐ |
| L5 | `SUPER-CAMBER` used | `layer_used` | AUTO | ☐ |
| L6 | `SUPER-DRAINAGE` used | `layer_used` | AUTO | ☐ |
| L7 | `SUPER-FOOTPATH` used where footpath > 0 | `layer_used` | AUTO | ☐ |

## F. Cross-sheet

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| X1 | Overall width equals sheet 1 deck width | `cross_sheet_alignment` | AUTO | ☐ |
| X2 | Skew sense agrees with sheet 1 | `support_skewed` | AUTO | ☐ |

## Sign-off

| | |
|---|---|
| Reviewer | |
| Date | |
| Blocker marks raised | |
| Residual marks accepted | |
| Signed | ☐ |
