# Defect Ledger

**Rule:** every defect gets a row before it gets a fix. A row closes only when
its assertion is un-xfailed and green. `blocker` rows block the week.

**Severity:** `blocker` (wrong or unissuable output) · `major` (non-compliant) ·
`minor` (cosmetic) · `accepted` (deliberate, with rationale).

Baseline captured week 1 against commit `2acef08`.

| ID | Sev | Symptom | File | Line / symbol | Closes | Status |
|---|---|---|---|---|---|---|
| D-01 | blocker | Scale is fit-to-paper but labelled as a declared ratio | `sheet1_plan.py` | `scale = min(scale_h, scale_v) * 0.93` | W6 | open |
| D-02 | blocker | Sheets self-declare "Not to Scale" while stamping a ratio | `sheet1_plan.py`, `sheet2_long_section.py` | view labels | W6 | open |
| D-03 | blocker | Coordinate contract never called; sheets use `draw_border` | `sheet1..5_*.py` | `draw_border(...)` | W9 | open |
| D-04 | blocker | `CoordMapper` constructed then discarded | `sheet2_long_section.py` | `CoordMapper(...)` | W7 | open |
| D-05 | blocker | Dimensions are exploded lines + text, no entity | `primitives.py` | `dim_linear_h`, `dim_linear_v` | W12 | open |
| D-06 | blocker | Native dimension has no `dimlfac`, reads paper mm | `sheet3_cross_section.py` | `add_linear_dim` | W11 | open |
| D-07 | major | Vertical exaggeration hardcoded and undeclared | `sheet2` (`v_exag=2.0`), `sheet4` (`sc*1.5`) | | W8 | open |
| D-08 | major | Text height derived from fit scale, varies per project | sheets 1–5 | `th = max(2.5, sc_h*0.4)` | W14 | open |
| D-09 | blocker | 33 of 53 layers unused; sections omit bearings, pedestals, caps, WC, kerb, parapet, drainage, strata | `layers.py` vs sheets | | W19–W22 | open |
| D-10 | major | Title-block mandatory fields blank on sheets 3, 4 | `sheet3`, `sheet4` | `draw_title_block` args | W15 | open |
| D-11 | major | Skew shears deck but not supports | `sheet1_plan.py` | deck `deck_pts` vs pier rects | W31 | open |
| D-12 | minor | Dead statements discard computed values | `sheet2`, `sheet4`, `bill/processor.py` | see week 7 | W7 | open |
| D-13 | blocker | E2E checks file count and KB only | `tests/e2e/run_e2e.py` | E5 | W4 | open |
| D-14 | blocker | Pile cap drawn above pile cutoff (inverted) | `sheet4_foundation.py` | `cap_top = pile_cut + cap_thickness` | W21 | open |
| D-15 | major | `total_sheets="8"` literal vs docs claiming 7 | all sheets, `GUIDE.md` §5.2 | | W16 | open |
| D-16 | major | `booklet` scale override forces BOQ sheet to 1:N | `booklet.py` | `sc = sheet_scale if scale_denom == 100 else scale_denom` | W16 | open |
| D-17 | major | Deck is two lines + hatch; no build-up | `sheet2_long_section.py` | deck block | W19 | open |
| D-18 | major | Pier floats; no foundation connection | `sheet5_pier_abutment_details.py` | `pier_by` base | W27 | open |
| D-19 | major | Wing wall ignores `wing_wall_angle_deg` and splay length | `sheet5_pier_abutment_details.py` | `ww_pts` | W29 | open |
| D-20 | minor | Table cells fall back to constants via `or 1500` | `sheet4_foundation.py` | schedule rows | W25 | open |
| D-21 | major | No page setup, layout or plot style | whole engine | — | W39 | open |
| D-22 | major | No PDF measurement proof | — | — | W40 | open |

Append rows as they are found. Never delete a row.
