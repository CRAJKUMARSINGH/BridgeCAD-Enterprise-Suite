# PWD GAD Enrichment Guide

**Executed baseline (2026-11-13, commit `5d5f99e`):** 15/15 types generated nine-sheet DXF packages; all 135 DXFs passed structural audit. The full default run nevertheless produced **24 entirely white PNGs**. Generation is not a reference-match or construction-approval result.

**Historical claims below:** earlier resolver/entity counts and PDF-match labels were not established by this audit. See [the executed verification supplement](BRIDGECAD_SUPPLEMENTARY_PATCH.md) and [the v.md application ledger](V_INSTRUCTIONS_APPLIED.md). Current changes add choice sweeps, strict identity mapping, deterministic output and nonblank-render failure reporting.

---

## Historical capability claims requiring reference verification

| Capability | Historical claim | Current reference verdict |
|---|---|---|
| `total_length` tracks span overrides | ✅ | Not independently verified |
| `soffit_level` moves when `deck_thickness` changes | ✅ | Not independently verified |
| `pier_count = span_count − 1` (or 0 for box-cell/arch) | ✅ | Not independently verified |
| `bearing_type` auto-derives (PSC→POT, Arch→NONE) | ✅ | Not independently verified |
| Skew angle stored and passed through (`skew_deg`) | ✅ | Not independently verified |
| Freeboard constraint (soffit < HFL + freeboard) rejected | ✅ | Not independently verified |
| Weak SBC for open foundation rejected | ✅ | Not independently verified |
| Sweep matrix (`pier_height_m=6:12:3`) produces 3 valid variants | ✅ | Not independently verified |
| Abutment battered profile (LISP `abt1()`, 14 vertices) | ✅ | Not independently verified |
| Dirt wall + construction joint + water-bar note | ✅ | Not independently verified |
| Continuous wearing coat over approach slabs | ✅ | Not independently verified |
| Abutment cap projections (front/rear) | ✅ | Not independently verified |
| Level tags (BEARING SEAT, TOP OF CAP, BASE OF SHAFT) | ✅ | Not independently verified |
| Scale caption matches geometry (`fit.py` ladder) | ✅ | Not independently verified |
| 270 m type 010 uses correct 1:500 scale (not 1:100) | ✅ | Not independently verified |
| T-beam girder cross-section (3 or 4 girders) | ✅ | Not independently verified |
| PSC I-girder cross-section | ✅ | Not independently verified |
| PSC Box girder cross-section | ✅ | Not independently verified |
| Pile foundation plan + elevation | ✅ | Not independently verified |
| Well foundation plan | ✅ | Not independently verified |

---

## 🔧 10 Enrichment gaps (ranked by priority)

### GAP 01 — Box-cell multi-unit primitive (Priority: CRITICAL)

**What the PDF shows (type 004):** 3 separate units, 61.25 m total, clear cell 5000×5000,
500 mm walls, 500×500 haunches at every corner, 100 mm CJ between units, 1100 mm raft,
900 mm rubble apron, cut-off wall at scour+0.3 m depth, PCC toe wall.

**Earlier engine description (recheck current code):** Plain slab proxy (single rectangle per span). Cell geometry,
haunches, CJs, apron and cut-off wall are all absent.

**Fix:** Implement `bridgecad_draw/geometry/box_cell.py` as specified in SS3.txt Primitive 1.
Full spec is in `CODE-JUNCTION/BridgeCAD_Plan_Patch/SS3.txt` — the `CellGrid` dataclass,
6-edges-per-cell audit, cut-off wall derivation, and layer set
(`SUB-BOX-CELL`, `SUB-BOX-HAUNCH`, `SUB-RAFT`, `SUB-CUTOFF`, `SUB-APRON`).

```python
# packages/bridgecad-draw/bridgecad_draw/geometry/box_cell.py
@dataclass(frozen=True)
class CellGrid:
    unit_cell_counts: tuple[int, ...]   # e.g. (4, 3, 4) for type 004
    clear_m: Decimal                     # 5.0 m
    wall_m: Decimal                      # 0.5 m
    haunch_m: Decimal                    # 0.5 m
    # ... see SS3.txt for full implementation
```

---

### GAP 02 — Arch ring / coordinate schedule (Priority: HIGH)

**What the PDF shows (type 014):** 31-point soffit coordinate table, parabola
`Y = 0.04955X²`, 350 mm ring, 200×200 haunches at 900 c/c, spandrel columns.

**Earlier engine description (recheck current code):** Rectangular deck approximation. Arch ring, columns,
haunches and the schedule table are absent.

**Fix:** Implement `arch_schedule.py` from SS3.txt Primitive 2:
- `arch_soffit_polyline(schedule_mm, origin)` — place the PDF table verbatim
- `arch_ring_outline(soffit, ring_mm)` — offset extrados along station normals
- `spandrel_columns(soffit, spacing_m, deck_soffit)` — vertical columns on 4183 grid
- `parabola_check(schedule_mm, a=0.04955)` — report deviation on the sheet

---

### GAP 03 — Precast block arch with sockets (Priority: HIGH)

**What the PDF shows (type 015):** 61.94 m span, 3 strips, 27 blocks @ 400 thick,
sockets 800×620×200, 100 mm strip gaps, spandrel openings, 10.0 m carriageway.

**Earlier engine description (recheck current code):** Rectangular deck approximation.

**Fix:** Implement `precast_arch.py` from SS3.txt Primitive 3:
- `block_chain(span_m, rise_m, n_blocks)` — 27 blocks on the arch curve
- `strip_offsets(strip_count, strip_mm, gap_mm)` — 3 strips centred
- `socket_pocket(block, width_mm=620, depth_mm=200)` — pocket in each block

---

### GAP 04 — Pier batter default (Priority: MEDIUM)

**What the PDF shows:** Pier shafts in types 006/007/008 are visibly tapered
(wider at base, narrower at cap) with a 1:10 batter.

**Earlier engine description (recheck current code):** Rectangular pier on Sheet 5 — `pier_batter_1n` field
exists but fixtures leave it `None`, so the batter-trapezoid branch never fires.

**Fix:** Set a default in the resolver:

```python
# packages/bridgecad-catalogue/bridgecad_catalogue/resolve.py
# in _derive(), after pier_count:
if p.get("pier_batter_1n") is None:
    if p["foundation_type"] in ("OPEN", "PILE"):
        p["pier_batter_1n"] = Decimal("10")   # 1:10, typical IRC practice
```

Then the Sheet 5 pier elevation already uses `pier_batter_1n` (implemented in
the Venice-patch) and will draw the tapered shape automatically.

---

### GAP 05 — Footing section detail (Priority: MEDIUM)

**What the PDF shows:** Stepped footing with PCC levelling course (100 mm M-15),
soil strata hatch, and scour line annotation with arrow.

**Earlier engine description (recheck current code):** Plain rectangle footing without steps or soil profile.

**Fix:** Extend `sheet4_foundation.py` with:
1. PCC toe course: `rectangle(msp, x, y_base-0.1, w, 0.1, layer="FOUND-OPEN")`
2. Soil strata hatch below scour: `hatch_rect(..., layer="FOUND-SOIL")`
3. Scour arrow + "DESIGN SCOUR RL {r:.3f}" text (already in sheet2, copy pattern)

---

### GAP 06 — Skew propagation to Sheet 2 piers (Priority: MEDIUM)

**What the PDF shows (type 006, skew 20°):** Pier and abutment lines on the
longitudinal section are drawn at the skew angle, not perpendicular.

**Earlier engine description (recheck current code):** Perpendicular pier rectangles regardless of skew.

**Fix:** In `sheet2_long_section.py` pier loop, replace the rectangle with the
rotated outline from `bridgecad_core.skew.support_line()` (already wired in
`sheet1_plan.py` — the same call pattern applies):

```python
from bridgecad_core.skew import support_line
sl = support_line(project, chainage_m=cumul)
# use sl.p_left, sl.p_right for the near and far face of the pier
```

---

### GAP 07 — Wing wall as solid profile (Priority: LOW)

**What the PDF shows:** Wing wall drawn as a filled trapezoid with the top face
falling at 1:10 from the full cap top.

**Earlier engine description (recheck current code):** Dashed indicator line only (correct slope, wrong layer/style).

**Fix:** In `sheet8_side_elevations.py` `_draw_abutment_endface()`:
```python
# Change this:
line(msp, start, end, layer="SUB-ABUT", color=3, linetype="DASHED")
# To: draw a filled trapezoid polyline on SUB-ABUT lw=35
```

---

### GAP 08 — Pier cap inline dimensions on Sheet 2 (Priority: LOW)

**What the PDF shows:** Each pier on the longitudinal section has inline cap
width, cap depth, and shaft width dimensions.

**Earlier engine description (recheck current code):** T.O.C. level tags only; no cap dimensional strings.

**Fix:** In the pier cap loop in `sheet2_long_section.py`, add:
```python
dim_linear_h(msp, cap_x0, cap_top_y - th*4, cap_x1, cap_top_y - th*4,
             dim_y=cap_top_y - th*4, label=f"Cap={cap_w:.2f}m", text_height=th*0.8)
```

---

### GAP 09 — Camber default for new fixtures (Priority: LOW)

**What the PDF shows:** Dashed camber parabola on the cross-section.

**Earlier engine description (recheck current code):** Camber is omitted when `camber_mm = 0` (the default
for all PWD fixtures).

**Fix:** In `resolve.py`, derive a minimum camber from span:
```python
if p.get("camber_mm") is None:
    span = max(p["span_lengths"])
    p["camber_mm"] = max(10, int(float(span) * 1000 / 1000))  # L/1000, min 10 mm
```

---

### GAP 10 — Variant note in title block (Priority: LOW)

**What the PDF shows:** Title block fields PROJECT / BRIDGE / DRAWING NO / SCALE / DATE.
Scale now updates correctly with `fit.py`.

**What is missing:** When non-empty overrides are applied (e.g. `--set pier_height_m=9`),
there is no indication in the title block that this is a variant.

**Fix:** Add a `VARIANT` field to `draw_title_block()` that appends a note like
`"Variant: pier_height_m=9"` in small text below the scale line.

---

## Implementation order

```
1. GAP 04  pier_batter default     → 3 lines in resolve.py
2. GAP 09  camber default          → 2 lines in resolve.py  
3. GAP 06  skew propagation Sheet 2 → ~15 lines in sheet2_long_section.py
5. GAP 05  footing section detail  → ~20 lines in sheet4_foundation.py
4. GAP 07  wing wall solid profile → 5 lines in sheet8_side_elevations.py
6. GAP 08  pier cap dims Sheet 2   → 5 lines in sheet2_long_section.py
7. GAP 10  variant title note      → 10 lines in titleblocks.py
8. GAP 01  box-cell primitive      → ~200 lines new file (CellGrid)
9. GAP 02  arch schedule           → ~150 lines new file (arch_schedule.py)
10. GAP 09  precast arch            → ~100 lines new file (precast_arch.py)
```

These are historical proposals, not approved patches. Line count does not establish risk. Reconcile the current model, reference dimensions and regression evidence before changing geometry.

---

## Historical proposals (validate engineering assumptions before applying)

```bash
# GAP 04: pier batter default
# Add to resolve.py _derive(), after pier_count line:
#   if p.get("pier_batter_1n") is None and p["foundation_type"] in ("OPEN","PILE"):
#       p["pier_batter_1n"] = Decimal("10")

# GAP 09: camber default
# Add to resolve.py _derive():
#   if not p.get("camber_mm"):
#       p["camber_mm"] = max(10, int(float(max(p["span_lengths"])) * 1000 / 1000))

# Resolve only; dry-run does not generate or certify drawings:
python scripts/generate_all_pwd_gads.py --dry-run
```
