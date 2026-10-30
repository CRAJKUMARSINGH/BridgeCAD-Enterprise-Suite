# V&V Benchmark Index

One row per case in `tests/verification/cases.py`. The `Module` column is the
engine module under test; the `Tier` column is the tolerance tier from
[TOLERANCE_POLICY.md](TOLERANCE_POLICY.md). Run the lane with
`python -m pytest tests/verification -q`.

| ID | Module | Tier | What it verifies |
|----|--------|------|------------------|
| VV-COORD-001 | `geometry.coordinates` | A | `to_dxf_mm` is metres x 1000; `MM_PER_M == 1000` |
| VV-COORD-002 | `geometry.coordinates` | E | `sheet_origins` returns one origin for every `SheetId` |
| VV-COORD-003 | `geometry.coordinates` | E | world <-> sheet transform round-trips within tolerance |
| VV-COORD-004 | `geometry.coordinates` | A | chainage-zero sheets (PLAN, LONG_SECTION, BOQ, BEARINGS) anchor at the origin |
| VV-COORD-005 | `geometry.coordinates` | A | cross-section origin sits at the mid of the longest span; rotation == skew |
| VV-COORD-006 | `geometry.coordinates` | A | FOUNDATION anchors at the first span; PIER_ABUTMENT at y = -5 m |
| VV-LSEC-001 | `geometry.long_section` | A | `sum(span_lengths_m) == total_length_m` |
| VV-LSEC-002 | `geometry.long_section` | A | span boundaries: `nspan + 1` values, start 0, strictly increasing, end at total |
| VV-LSEC-003 | `geometry.long_section` | A | interior pier count == `max(nspan - 1, 0)`; piers are interior boundaries |
| VV-LSEC-004 | `geometry.long_section` | A | `freeboard_m == soffit_rl - hfl_rl` |
| VV-LSEC-005 | `geometry.long_section` | A | `pile_tip_rl == pile_cutoff_level - pile_length` |
| VV-LSEC-006 | `geometry.long_section` | A | ground profile has 21 points, chainage monotonic from 0 to total length |
| VV-LSEC-007 | `geometry.long_section` | A | pier top-of-cap list length matches chainages; each == soffit - pedestal - cap depth |
| VV-FND-001 | `geometry.foundation` | E | pile-group centroid is at the group origin |
| VV-FND-002 | `geometry.foundation` | E | pile count matches `piles_per_pier` |
| VV-FND-003 | `geometry.foundation` | E | pile-cap corners form a rectangle centred on the origin |
| VV-FND-004 | `geometry.foundation` | A | cap size == pile spread + pile diameter + 2 x 100 mm |
| VV-FND-005 | `geometry.foundation` | E | standard 3/5/7-pile layouts are centred; min spacing == pile spacing |
| VV-FND-006 | `geometry.foundation` | E | well branch: no piles; inner radius == 0.55 x outer; outer >= 1.5 m |
| VV-PLAN-001 | `geometry.plan` | E | deck corners are a rotated rectangle of `total_length` x `overall_width` |
| VV-PLAN-002 | `geometry.plan` | E | pier centrelines match `pier_positions` on the chainage axis (skew 0) |
| VV-PLAN-003 | `geometry.plan` | A | abutment face separation == `total_length_m` |
| VV-PLAN-004 | `geometry.plan` | A | bearing count == `(nspan + 1) * girders_per_deck_count` |
| VV-XSEC-001 | `geometry.cross_section` | A | crown height `top_of_wearing_coat_y == camber_mm / 1000` |
| VV-XSEC-002 | `geometry.cross_section` | A | slab soffit `bottom_of_slab_y == -deck_thickness_mm / 1000` |
| VV-XSEC-003 | `geometry.cross_section` | A | parabolic camber: centre == camber, both carriageway edges == 0 |
| VV-XSEC-004 | `geometry.cross_section` | A | half-width offsets strictly increase; last == `overall_width / 2` |
| VV-XSEC-005 | `geometry.cross_section` | A | girder soffit == slab soffit - girder depth |
| VV-QTY-001 | `quantities` | A | deck concrete == `length x width x deck_thickness` |
| VV-QTY-002 | `quantities` | A | wearing coat == `length x carriageway_width x coat_thickness` |
| VV-QTY-003 | `quantities` | A | rebar mass linear in volume: `rebar_kg(0) == 0`, `rebar_kg(2V) == 2 x rebar_kg(V)` |
| VV-QTY-004 | `quantities` | A | `_pier_count == max(nspan - 1, 0)` |
| VV-QTY-005 | `quantities` | A | BOQ well-formed: unique codes, non-empty code/description/unit, qty >= 0 |
| VV-QTY-006 | `quantities` | A | steel control total `SUM-200` == sum of the other kg items |
| VV-COST-001 | `costs` | A | line amount == `rate x qty`; total == sum of amounts |
| VV-COST-002 | `costs` | A | unknown codes stay unpriced and contribute 0 to the total |
| VV-VAL-001 | `validation` | A | score == `max(0, 100 - 15 x critical_fails - 3 x warning_fails)` |
| VV-VAL-002 | `validation` | A | score stays in `[0, 100]`: empty report 100, critical-flooded report 0 |
| VV-VAL-003 | `validation` | A | overall status precedence FAIL > WARN > PASS by worst failed severity |
| VV-REG-001 | `validation_registry` | A | 150 rules; ids unique and match `V\d{3}` |
| VV-REG-002 | `validation_registry` | A | `RULE_ID_BY_CHECK` maps each source id to a unique stable id |
| VV-REG-003 | `validation_registry` | A | exactly 30 rules flagged implemented; the first is critical |
| VV-TYP-001 | `types` | A | `ENUM_REGISTRY` resolves each stable enum class name |
| VV-TYP-002 | `types` | A | stable enums are non-empty with unique member values |
| VV-MOD-001 | `models` | A | `geometry_input.total_length_m == sum(span_lengths_m)` |
| VV-MOD-002 | `models` | A | `overall_width_m == carriageway + footpaths + barriers + kerbs (+ others)` |
| VV-MOD-003 | `models` | A | project length/width aliases mirror the geometry-input values |
