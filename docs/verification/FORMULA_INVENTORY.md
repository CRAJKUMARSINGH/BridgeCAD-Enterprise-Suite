# Formula Inventory — module → test → benchmark

W05 deliverable. One row per formula module: the module under test, the
hypothesis property lane that pins its behaviour over a domain
(`tests/properties/`), and the V&V benchmark ids that pin a closed-form
identity or structural invariant (`tests/verification/cases.py`).

A module with a property test but no benchmark is a *coverage* signal, not a
defect: it means the contract is asserted over a domain rather than at an exact
value. A module with neither is a gap and must not ship.

| Formula module | Property lane (`tests/properties/`) | V&V benchmark ids (`tests/verification/`) |
|---|---|---|
| `bridgecad_core.geometry.coordinates` | `test_properties.py::test_to_dxf_mm_is_linear_in_metres`, `::test_to_world_coords_inverts_to_sheet_coords` | VV-COORD-001…006 |
| `bridgecad_core.geometry.long_section` | `test_properties.py::test_span_and_pier_contract` | VV-LSEC-001…007 |
| `bridgecad_core.geometry.foundation` | `test_properties.py::test_pile_group_is_centred_and_symmetric`, `::test_zero_piles_is_domain_not_applicable`, `::test_well_foundation_yields_no_pile_positions` | VV-FND-001…006 |
| `bridgecad_core.geometry.plan` | (benchmark-only) | VV-PLAN-001…004 |
| `bridgecad_core.geometry.cross_section` | (benchmark-only) | VV-XSEC-001…005 |
| `bridgecad_core.quantities` | `test_properties.py::test_boq_add_accumulates_items_in_order`, `::test_boq_rebar_control_total_equals_sum_of_kg_items` | VV-QTY-001…006 |
| `bridgecad_core.costs` | `test_properties.py::test_cost_is_rate_times_quantity`, `::test_cost_total_is_sum_of_item_amounts` | VV-COST-001…002 |
| `bridgecad_core.validation` | `test_properties.py::test_validation_score_is_bounded`, `::test_validation_score_is_monotonic_in_failures` | VV-VAL-001…003 |
| `bridgecad_core.validation_registry` | (benchmark-only) | VV-REG-001…003 |
| `bridgecad_core.models` | `test_properties.py::test_geometry_input_rejects_span_below_one_metre`, `::test_geometry_input_rejects_non_positive_carriageway_width` | VV-MOD-001…003 |
| `bridgecad_core.types` | (benchmark-only) | VV-TYP-001…002 |
| `bridgecad_core.units` | `test_units.py` (round-trips, linearity, rounding invariants, domain guards) | (unit lane only) |
| `bridgecad_core.standards.irc_05` | (unit lane: `tests/unit/`) | — |
| `bridgecad_core.standards.irc_21` | (unit lane: `tests/unit/`) | — |
| `bridgecad_core.standards.irc_sp55` | (unit lane: `tests/unit/`) | — |
| `bridgecad_core.standards.morth_specs` | (unit lane: `tests/unit/`) | — |

## The three guards a formula must carry

1. **Unit guard** — a value cannot cross SI↔FPS without an explicit,
   direction-named conversion (`bridgecad_core.units`). A wrong-unit read is a
   `UnitError`, never a silent number.
2. **Rounding policy** — printed quantities use `round_sig` / `round_engineering`
   (Decimal + `ROUND_HALF_UP`), never the bare `round()` — so output is
   deterministic across interpreters.
3. **Domain guard** — inputs are validated at the Pydantic boundary
   (`GeometryInput` span ≥ 1 m, carriageway ≥ 3.5 m, …). See
   `tests/properties/test_properties.py` "Input-domain validation".

## How to keep this current

Adding a formula module means adding a row here, a property test in
`tests/properties/`, and — where a closed-form identity exists — a `Case` in
`tests/verification/cases.py`. `tests/docs/…` does not gate this file; review
does.
