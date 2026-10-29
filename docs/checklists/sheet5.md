# Sheet 5 — PIER AND ABUTMENT DETAILS — review checklist

**Sheet key:** `sheet5_pier_abutment_details` · **Scale:** 1:25 / 1:20 details · **Module:** `sheet5_pier_abutment_details.py`
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
| C3 | `dimlfac` 1000 | `dimension_scale` | AUTO | ☐ |
| C4 | Notes sourced — sheet 5's hardcoded list now comes from `notes.yaml` | `notes_sourced` | AUTO | ☐ |

## D. Pier

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| D1 | Elevation matches `pier_type` (single / multi-column / hammerhead / wall) | `MANUAL: type check` | MANUAL | ☐ |
| D2 | Shaft taper per type | `MANUAL: taper check` | MANUAL | ☐ |
| D3 | Plan cut with shaft dimensions, chamfers, cover | `MANUAL: section check` | MANUAL | ☐ |
| D4 | Cap stub drawn — pier does not float | `MANUAL: connectivity` | MANUAL | ☐ |
| D5 | Bearing shelf, pedestal, drip groove | `MANUAL: shelf check` | MANUAL | ☐ |

## E. Reinforcement

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| E1 | Vertical bars, links, cover, laps on `STRUC-DETAIL` | `MANUAL: callout check` | MANUAL | ☐ |
| E2 | Every callout mark exists in the BBS | `MANUAL: BBS parity` | MANUAL | ☐ |
| E3 | BBS columns complete: mark, dia, shape, length, number, total | `MANUAL: BBS columns` | MANUAL | ☐ |

## F. Abutment and wing walls

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| F1 | Abutment per `abutment_type` | `MANUAL: type check` | MANUAL | ☐ |
| F2 | Ballast wall, dirt wall, return wall, approach slab with dowels | `MANUAL: component check` | MANUAL | ☐ |
| F3 | Wing wall at `wing_wall_angle_deg` within 0.5° | `support_skewed` | AUTO | ☐ |
| F4 | Wing splay at `wing_wall_splay_length_m` | `MANUAL: splay check` | MANUAL | ☐ |
| F5 | Backfill hatch on `SUB-BACKFILL` | `layer_used` | AUTO | ☐ |

## G. Layers

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| L1 | `SUB-PIER` used | `layer_used` | AUTO | ☐ |
| L2 | `SUB-ABUT` used | `layer_used` | AUTO | ☐ |
| L3 | `STRUC-DETAIL` used | `layer_used` | AUTO | ☐ |
| L4 | `SUB-BACKFILL` used | `layer_used` | AUTO | ☐ |
| L5 | `SUB-BEARING` used | `layer_used` | AUTO | ☐ |

## H. Cross-sheet

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| X1 | Pier X matches sheet 1 and 2 | `cross_sheet_alignment` | AUTO | ☐ |
| X2 | Bearing shelf agrees with sheet 6 bearing type | `MANUAL: type parity` | MANUAL | ☐ |

## Sign-off

| | |
|---|---|
| Reviewer | |
| Date | |
| Blocker marks raised | |
| Residual marks accepted | |
| Signed | ☐ |
