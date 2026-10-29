# Sheet 2 — LONGITUDINAL SECTION — review checklist

**Sheet key:** `sheet2_long_section` · **Scale:** 1:200 H / declared V · **Module:** `sheet2_long_section.py`
**Required before review:** every `AUTO` and `SCRIPT` row `☑`.

## A. Frame and scale

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| A1 | Geometry inside frame | `inside_frame` | AUTO | ☐ |
| A2 | Scale honest, or NTS with bar | `scale_honest` | AUTO | ☐ |
| A3 | Vertical exaggeration declared in the title block | `MANUAL: V.E. note` | MANUAL | ☐ |
| A4 | Two scale bars where V.E. ≠ 1 | `MANUAL: bar count` | MANUAL | ☐ |
| A5 | No duplicated geometry | `no_duplicate_geometry` | AUTO | ☐ |
| A6 | No zero-length lines | `no_zero_length_lines` | AUTO | ☐ |

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
| C3 | `dimlfac` 1000 on all | `dimension_scale` | AUTO | ☐ |
| C4 | Notes sourced | `notes_sourced` | AUTO | ☐ |
| C5 | Freeboard dimension is a true entity, not text | `MANUAL: freeboard check` | MANUAL | ☐ |

## D. Deck and superstructure

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| D1 | Deck slab at `deck_thickness_mm` | `MANUAL: thickness check` | MANUAL | ☐ |
| D2 | Wearing course at `wearing_coat_thickness_mm` | `MANUAL: WC check` | MANUAL | ☐ |
| D3 | Kerb, footpath, parapet/crash barrier at full heights | `MANUAL: profile check` | MANUAL | ☐ |
| D4 | Deck line follows `gradient_pct` | `gradient_matches` | AUTO | ☐ |
| D5 | Camber profile from `camber_mm` | `MANUAL: camber check` | MANUAL | ☐ |
| D6 | Separate hatches: concrete `ANSI31`, bituminous `AR-SAND`, earth `ANSI37` | `MANUAL: hatch check` | MANUAL | ☐ |

## E. Bearings, joints, substructure

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| E1 | Pedestal drawn at `pier_pedestal_height_m` | `MANUAL: pedestal check` | MANUAL | ☐ |
| E2 | Bearing symbols match the schedule, one per row | `MANUAL: bearing count` | MANUAL | ☐ |
| E3 | Expansion joints at both abutments, `gap_mm` | `MANUAL: joint check` | MANUAL | ☐ |
| E4 | Pier connected to its cap — no floating support | `MANUAL: connectivity` | MANUAL | ☐ |

## F. Foundation ordering

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| F1 | tip < cutoff < cap bottom < cap top | `foundation_ordering` | AUTO | ☐ |
| F2 | Cutoff sits inside the cap | `MANUAL: cutoff position` | MANUAL | ☐ |
| F3 | Cap at `pile_cap_width_m`, not a default | `MANUAL: cap width` | MANUAL | ☐ |
| F4 | Pile group matches `piles_per_pier` at `pile_spacing_m` | `MANUAL: pile group` | MANUAL | ☐ |
| F5 | Foundation branch correct for `fd.type` (PILE / WELL / OPEN) | `MANUAL: branch check` | MANUAL | ☐ |

## G. Ground and water

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| G1 | Strata from borelog, not invented | `layer_used` | AUTO | ☐ |
| G2 | Strata absent where there is no borelog — not faked | `MANUAL: absence check` | MANUAL | ☐ |
| G3 | HFL / LWL / scour at correct RLs | `MANUAL: level check` | MANUAL | ☐ |
| G4 | Water lines on the registered linetypes, not hardcoded | `MANUAL: linetype check` | MANUAL | ☐ |
| G5 | Apron and pitching at `design_scour_depth_m` | `MANUAL: protection check` | MANUAL | ☐ |

## H. Layers

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| L1 | `SUPER-DECK` used | `layer_used` | AUTO | ☐ |
| L2 | `SUPER-WEARING` used | `layer_used` | AUTO | ☐ |
| L3 | `SUB-BEARING` used, ≥ 2 | `layer_used` | AUTO | ☐ |
| L4 | `SUB-EXPJOINT` used | `layer_used` | AUTO | ☐ |
| L5 | `FOUND-CAP` used | `layer_used` | AUTO | ☐ |
| L6 | `FOUND-PILE` used | `layer_used` | AUTO | ☐ |
| L7 | `FOUND-SOIL` used | `layer_used` | AUTO | ☐ |
| L8 | `CIVIL-HFL` and `CIVIL-SCOUR` used | `layer_used` | AUTO | ☐ |

## I. Cross-sheet

| # | Requirement | Assertion | Mode | OK |
|---|---|---|---|---|
| X1 | Pier X matches sheet 1 within 1 mm | `cross_sheet_alignment` | AUTO | ☐ |
| X2 | Origin chainage equals sheet 1's section marker | `cross_sheet_alignment` | AUTO | ☐ |
| X3 | Bearing symbols agree with sheet 6 schedule | `MANUAL: schedule parity` | MANUAL | ☐ |

## Sign-off

| | |
|---|---|
| Reviewer | |
| Date | |
| Blocker marks raised | |
| Residual marks accepted | |
| Signed | ☐ |
