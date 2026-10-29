# Sheet 6 — BEARINGS AND EXPANSION JOINTS — review checklist

**Sheet key:** `sheet6_bearings_joints` · **Scale:** 1:10 details · **Module:** `sheet6_bearings_joints.py`
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
| C4 | Notes sourced | `notes_sourced` | AUTO | ☐ |

## D. Bearings

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| D1 | One detail per bearing type in the schedule | `MANUAL: coverage check` | MANUAL | ☐ |
| D2 | Elastomeric: layers, dimensions, total height | `MANUAL: detail check` | MANUAL | ☐ |
| D3 | Pot-PTFE: pot, piston, PTFE, restraint | `MANUAL: detail check` | MANUAL | ☐ |
| D4 | Spherical: mating surfaces, rotation capacity | `MANUAL: detail check` | MANUAL | ☐ |
| D5 | Fixed / guided / free symbols per `fixed_or_guide_or_free` | `MANUAL: symbol check` | MANUAL | ☐ |
| D6 | Dimensions match `size_x_mm` × `size_y_mm` from the schedule | `MANUAL: size parity` | MANUAL | ☐ |

## E. Joints

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| E1 | Detail per `joint_type` | `MANUAL: coverage check` | MANUAL | ☐ |
| E2 | `gap_mm` and `movement_range_mm` shown | `MANUAL: gap check` | MANUAL | ☐ |
| E3 | Seal, nosing, anchorage drawn | `MANUAL: component check` | MANUAL | ☐ |

## F. Schedule parity

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| F1 | One symbol per schedule row — count equal | `MANUAL: count parity` | MANUAL | ☐ |
| F2 | Schedule totals equal the sum of sheet 2 symbols | `MANUAL: sheet 2 parity` | MANUAL | ☐ |

## G. Layers

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| L1 | `SUB-BEARING` used | `layer_used` | AUTO | ☐ |
| L2 | `SUB-EXPJOINT` used | `layer_used` | AUTO | ☐ |
| L3 | `STRUC-DETAIL` used | `layer_used` | AUTO | ☐ |

## Sign-off

| | |
|---|---|
| Reviewer | |
| Date | |
| Blocker marks raised | |
| Residual marks accepted | |
| Signed | ☐ |
