"""
Generate 25 BridgeCAD Excel templates across 5 bridge categories × 5 variants each.

Categories:
  minor_bridges/    — RCC T-Beam, 1–3 spans, Class A, PMGSY / state road
  major_bridges/    — PSC I-Girder / Box Girder, 3–6 spans, NHAI / state highway
  viaducts/         — PSC I-Girder / Box, 6–12 spans, urban flyover / ROB+viaduct
  culverts/         — RCC Box Culvert 1–3 cell, PMGSY / drainage
  robs_rubs_fobs/   — ROB / RUB / FOB over railway / road crossings

Run:  cd "BridgeCAD Enterprise Suite"
      python scripts/generate_templates.py
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

# ── path bootstrap ────────────────────────────────────────────────────────────
SUITE = Path(__file__).parent.parent
for pkg in ["bridgecad-core", "bridgecad-io"]:
    p = SUITE / "packages" / pkg
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from bridgecad_io.excel_template import generate_template

# ── Template definitions ──────────────────────────────────────────────────────
# Each entry: (category_dir, filename_stem, title, project_overrides)

TEMPLATES = [
    # ── MINOR BRIDGES (5 variants) ────────────────────────────────────────────
    (
        "minor_bridges",
        "minor_1x12m_class_a",
        "Minor Bridge 1×12m Simply Supported RCC T-Beam Class A",
        {
            "span_count": 1,
            "span_lengths_m": [Decimal("12.0")],
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "RCC_TBEAM",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_A",
            "foundation_type": "PILE",
        },
    ),
    (
        "minor_bridges",
        "minor_2x12m_class_a",
        "Minor Bridge 2×12m Simply Supported RCC T-Beam Class A",
        {
            "span_count": 2,
            "span_lengths_m": [Decimal("12.0"), Decimal("12.0")],
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "RCC_TBEAM",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_A",
            "foundation_type": "PILE",
        },
    ),
    (
        "minor_bridges",
        "minor_1x18m_class_a",
        "Minor Bridge 1×18m Simply Supported RCC T-Beam Class A",
        {
            "span_count": 1,
            "span_lengths_m": [Decimal("18.0")],
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "RCC_TBEAM",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_A",
            "foundation_type": "PILE",
        },
    ),
    (
        "minor_bridges",
        "minor_3x12m_class_a_well",
        "Minor Bridge 3×12m RCC T-Beam Well Foundation",
        {
            "span_count": 3,
            "span_lengths_m": [Decimal("12.0")] * 3,
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "RCC_TBEAM",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_A",
            "foundation_type": "WELL",
        },
    ),
    (
        "minor_bridges",
        "minor_1x24m_class_a_footpath",
        "Minor Bridge 1×24m RCC T-Beam with Footpath",
        {
            "span_count": 1,
            "span_lengths_m": [Decimal("24.0")],
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "RCC_TBEAM",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_A",
            "foundation_type": "PILE",
        },
    ),
    # ── MAJOR BRIDGES (5 variants) ────────────────────────────────────────────
    (
        "major_bridges",
        "major_3x30m_psc_igirder",
        "Major Bridge 3×30m PSC I-Girder Simply Supported Class A+70R",
        {
            "span_count": 3,
            "span_lengths_m": [Decimal("30.0")] * 3,
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "PSC_IGIRDER",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_A",
            "foundation_type": "PILE",
        },
    ),
    (
        "major_bridges",
        "major_4x25m_psc_igirder_70r",
        "Major Bridge 4×25m PSC I-Girder Class 70R NHAI 2-lane",
        {
            "span_count": 4,
            "span_lengths_m": [Decimal("25.0")] * 4,
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "PSC_IGIRDER",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_70R",
            "foundation_type": "PILE",
        },
    ),
    (
        "major_bridges",
        "major_5x30m_psc_box_continuous",
        "Major Bridge 5×30m PSC Box Girder Continuous Class 70R",
        {
            "span_count": 5,
            "span_lengths_m": [Decimal("30.0")] * 5,
            "carriageway_width_m": Decimal("10.50"),
            "bridge_type": "PSC_BOX_GIRDER",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_70R",
            "foundation_type": "PILE",
        },
    ),
    (
        "major_bridges",
        "major_3x45m_psc_igirder_nhai",
        "Major Bridge 3×45m PSC I-Girder NHAI National Corridor",
        {
            "span_count": 3,
            "span_lengths_m": [Decimal("45.0")] * 3,
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "PSC_IGIRDER",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_70R",
            "foundation_type": "PILE",
        },
    ),
    (
        "major_bridges",
        "major_4x30m_rcc_tbeam_skew15",
        "Major Bridge 4×30m RCC T-Beam Skew 15°",
        {
            "span_count": 4,
            "span_lengths_m": [Decimal("30.0")] * 4,
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "RCC_TBEAM",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_A",
            "foundation_type": "PILE",
        },
    ),
    # ── VIADUCTS (5 variants) ──────────────────────────────────────────────────
    (
        "viaducts",
        "viaduct_6x25m_psc_igirder_urban",
        "Urban Viaduct 6×25m PSC I-Girder Class 70R",
        {
            "span_count": 6,
            "span_lengths_m": [Decimal("25.0")] * 6,
            "carriageway_width_m": Decimal("10.50"),
            "bridge_type": "PSC_IGIRDER",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_70R",
            "foundation_type": "PILE",
        },
    ),
    (
        "viaducts",
        "viaduct_8x30m_psc_box_expressway",
        "Expressway Viaduct 8×30m PSC Box Girder",
        {
            "span_count": 8,
            "span_lengths_m": [Decimal("30.0")] * 8,
            "carriageway_width_m": Decimal("14.0"),
            "bridge_type": "PSC_BOX_GIRDER",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_70R",
            "foundation_type": "PILE",
        },
    ),
    (
        "viaducts",
        "viaduct_10x25m_psc_igirder_nh_corridor",
        "NH Corridor Viaduct 10×25m PSC I-Girder",
        {
            "span_count": 10,
            "span_lengths_m": [Decimal("25.0")] * 10,
            "carriageway_width_m": Decimal("10.50"),
            "bridge_type": "PSC_IGIRDER",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_70R",
            "foundation_type": "PILE",
        },
    ),
    (
        "viaducts",
        "viaduct_6x30m_psc_box_balanced_cantilever",
        "Balanced Cantilever Viaduct 6×30m PSC Box",
        {
            "span_count": 6,
            "span_lengths_m": [Decimal("30.0")] * 6,
            "carriageway_width_m": Decimal("10.50"),
            "bridge_type": "PSC_BOX_GIRDER",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_70R",
            "foundation_type": "PILE",
        },
    ),
    (
        "viaducts",
        "viaduct_4x35m_steel_composite",
        "Steel Composite Viaduct 4×35m Class 70R",
        {
            "span_count": 4,
            "span_lengths_m": [Decimal("35.0")] * 4,
            "carriageway_width_m": Decimal("10.50"),
            "bridge_type": "STEEL_COMPOSITE",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_70R",
            "foundation_type": "PILE",
        },
    ),
    # ── CULVERTS (5 variants) ──────────────────────────────────────────────────
    (
        "culverts",
        "culvert_1cell_3x2_5m",
        "Single Cell RCC Box Culvert 3.0×2.5m IRC SP:13",
        {
            "span_count": 1,
            "span_lengths_m": [Decimal("3.0")],
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "BOX_CULVERT",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_A",
            "foundation_type": "OPEN",
        },
    ),
    (
        "culverts",
        "culvert_1cell_6x3m",
        "Single Cell RCC Box Culvert 6.0×3.0m",
        {
            "span_count": 1,
            "span_lengths_m": [Decimal("6.0")],
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "BOX_CULVERT",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_A",
            "foundation_type": "OPEN",
        },
    ),
    (
        "culverts",
        "culvert_2cell_3x2_5m",
        "2-Cell RCC Box Culvert 2×3.0×2.5m PMGSY",
        {
            "span_count": 1,
            "span_lengths_m": [Decimal("6.0")],
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "BOX_CULVERT",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_A",
            "foundation_type": "OPEN",
        },
    ),
    (
        "culverts",
        "culvert_pipe_1200mm_double",
        "Double Pipe Culvert 1200mm dia RCC NP3",
        {
            "span_count": 1,
            "span_lengths_m": [Decimal("1.2")],
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "PIPE_CULVERT_MULTI",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_A",
            "foundation_type": "OPEN",
        },
    ),
    (
        "culverts",
        "culvert_arch_8m_span",
        "RCC Arch Culvert 8.0m Span Open Spandrel",
        {
            "span_count": 1,
            "span_lengths_m": [Decimal("8.0")],
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "ARCH_CULVERT",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_A",
            "foundation_type": "OPEN",
        },
    ),
    # ── ROBs / RUBs / FOBs (5 variants) ───────────────────────────────────────
    (
        "robs_rubs_fobs",
        "rob_1x12m_single_track",
        "Railway Over Bridge (ROB) 1×12m PSC Single Track",
        {
            "span_count": 1,
            "span_lengths_m": [Decimal("12.0")],
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "PSC_IGIRDER",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_A",
            "foundation_type": "PILE",
            "bridge_category": "ROB",
        },
    ),
    (
        "robs_rubs_fobs",
        "rob_3x18m_double_track",
        "ROB 3×18m PSC I-Girder Double Track Railway",
        {
            "span_count": 3,
            "span_lengths_m": [Decimal("18.0")] * 3,
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "PSC_IGIRDER",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_A",
            "foundation_type": "PILE",
            "bridge_category": "ROB",
        },
    ),
    (
        "robs_rubs_fobs",
        "rub_box_single_lane",
        "Railway Under Bridge (RUB) Box Culvert Single Lane",
        {
            "span_count": 1,
            "span_lengths_m": [Decimal("5.0")],
            "carriageway_width_m": Decimal("4.50"),
            "bridge_type": "BOX_CULVERT",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_A",
            "foundation_type": "OPEN",
            "bridge_category": "RUB",
        },
    ),
    (
        "robs_rubs_fobs",
        "fob_pedestrian_3x18m",
        "Foot Over Bridge (FOB) 3×18m PSC I-Girder",
        {
            "span_count": 3,
            "span_lengths_m": [Decimal("18.0")] * 3,
            "carriageway_width_m": Decimal("3.00"),
            "bridge_type": "PSC_IGIRDER",
            "design_code": "IRC_112_2020",
            "loading_class": "PEDESTRIAN_ONLY",
            "foundation_type": "PILE",
            "bridge_category": "FOB",
        },
    ),
    (
        "robs_rubs_fobs",
        "rob_viaduct_4x25m_urban",
        "Urban ROB Viaduct 4×25m PSC I-Girder NHAI",
        {
            "span_count": 4,
            "span_lengths_m": [Decimal("25.0")] * 4,
            "carriageway_width_m": Decimal("7.50"),
            "bridge_type": "PSC_IGIRDER",
            "design_code": "IRC_112_2020",
            "loading_class": "CLASS_70R",
            "foundation_type": "PILE",
            "bridge_category": "ROB",
        },
    ),
]


def main() -> None:
    generated = 0
    failed = 0

    print()
    print("=" * 64)
    print("  BridgeCAD — Generating 25 Excel Templates")
    print("=" * 64)

    for cat_dir, stem, title, _overrides in TEMPLATES:
        out_dir = SUITE / "templates" / cat_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{stem}.xlsx"

        if out_path.exists():
            print(f"  [skip] {cat_dir}/{stem}.xlsx  (already exists)")
            continue

        try:
            p = generate_template(out_path, title=title)
            sz_kb = p.stat().st_size // 1024
            print(f"  [OK]   {cat_dir}/{stem}.xlsx  ({sz_kb} KB)")
            generated += 1
        except Exception as exc:
            print(f"  [FAIL] {cat_dir}/{stem}.xlsx  — {exc}")
            failed += 1

    total = len(list((SUITE / "templates").rglob("*.xlsx")))
    print()
    print(f"  Generated : {generated}")
    print(f"  Failed    : {failed}")
    print(f"  Total xlsx: {total}/25")
    print("=" * 64)


if __name__ == "__main__":
    main()
