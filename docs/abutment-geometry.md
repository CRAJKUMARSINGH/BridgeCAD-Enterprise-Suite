# Abutment geometry — the resolved datum stack

How the abutment is dimensioned, where each level comes from, and which sheet
reads which number. The governing rule: **one resolver, every consumer** —
`sheets/2/5/8` never recompute these levels from raw inputs.

## The stack

`bridgecad_core.abutment_stack.resolve_abutment_stack(project)` returns a
frozen `AbutmentStack` with every level the drawings need:

| Level | Source | Notes |
|---|---|---|
| `pile_cut_rl` | `foundation_details` | pile cutoff RL |
| `pile_cap_bot` / `pile_cap_top` | cutoff + `pile_cap_thickness_mm` | cap thickness governs, not a stored RL |
| `cap_bot` | pile cap top | abutment cap bears on the pile cap |
| `cap_top` | cap_bot + `abutment_cap_depth_mm` | default 600 mm (IRC:21 ≥ 450) |
| `bearing_seat` | cap_top + pedestal | bearing shelf |
| `slab_bot` | structural deck soffit | wearing-coat underside = slab top |
| `slab_top` | deck top − wearing coat | coat is a separate band, not merged |
| `dirt_wall_top` | underside of approach slab | = `slab_bot` at the rear |
| `dirt_wall_bot` | dirt wall base on cap rear ledge | on the cap, not the shaft |
| `app_slab_bot` / `app_slab_top` | dirt wall top −/+ `approach_slab_thickness_mm` | ~200–400 mm |

Wearing coat thickness defaults to 65 mm (`superstructure.wearing_coat_thickness_mm`).

## Geometry helpers

- `compute_dirt_wall_geometry(project)` (`geometry_extras.py`) — the single
  source for dirt-wall plan/elevation extents; sheets 2, 4, 5 and 8 all call
  it. The wall sits on the **cap rear ledge**, thickness
  `dirt_wall_thickness_mm` (default 300 mm), height driven by the approach-slab
  underside.
- `skew.support_line(project, chainage)` — rotated support line for skewed
  alignments; `effective_span_m` applies the IRC skew reduction
  (clear span × cos θ). `skew=0` reproduces square geometry exactly.

## Sheets

- **Sheet 2 (long section)** — continuous wearing coat over deck *and*
  approach slab; pile caps drawn under piers; abutment stack levels tagged.
- **Sheet 5 (pier & abutment details)** — cap, dirt wall on the rear ledge,
  approach slab behind the wall, bearing seat, construction joint, PVC water
  bar note, weep holes, and the clause-tagged checks table.
- **Sheet 8 (side elevations)** — abutment end-face with cap/dirt wall/
  approach slab, pier transverse cut sized by `pier_cap_length_m` (not shaft
  length) and `pile_cap_thickness_mm`, plus the checks table.

## QA gates

`validation.py` enforces the same limits the checks table prints:
cap depth ≥ 450 mm, cap projections 150–300 mm, dirt-wall thickness vs
approach-slab + freeboard, weep-hole spacing ≤ 3 m, plus the skew (SKW-001..003)
and bill-provenance (BIL-001/002) rules.

Dead-expression audit: `python scripts/audit_dead_geometry.py` (or
`make audit-draw`) reports pure expressions evaluated and discarded in the
sheet modules — the signature of geometry computed then dropped.
