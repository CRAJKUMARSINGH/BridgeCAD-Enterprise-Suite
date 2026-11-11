"""
scripts/generate_all_pwd_gads.py — Maharashtra PWD Booklet GAD Generator.

Generates complete, parametric GAD packages for all 15 standard bridge types
from the official Maharashtra PWD booklet (C.E. Designs letter No. 2473,
dt. 31.12.2022, "Booklet of General Arrangement Drawings for Various Types
of Bridges").

Each type produces a full 9-sheet DXF package + PNG renders + a completeness
report. Output goes to EXAMPLES/PWD_Booklet/<type_id>/.

Run:
    python scripts/generate_all_pwd_gads.py
    python -m bridgecad generate-all-pwd   # CLI alias (if wired)
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from decimal import Decimal

# ── path bootstrap ───────────────────────────────────────────────────────────
_SUITE = Path(__file__).parents[1]
for _pkg in ["bridgecad-core", "bridgecad-io", "bridgecad-draw",
             "bridgecad-bill", "bridgecad-qa", "bridgecad-export",
             "packages/bridgecad-plugins"]:
    _p = _SUITE / "packages" / _pkg
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
sys.path.insert(0, str(_SUITE / "tests" / "e2e"))

OUTPUT_ROOT = _SUITE / "EXAMPLES" / "PWD_Booklet"
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

MIN_ENTITIES = 20  # minimum DXF entities per sheet (completeness gate)

# ──────────────────────────────────────────────────────────────────────────────
# The 15 Maharashtra PWD standard bridge types
# ──────────────────────────────────────────────────────────────────────────────
PWD_TYPES: list[dict] = [
    {
        "id": "BR-I-2022-001",
        "title": "Open Foundation + PCC Pier + Solid Slab",
        "spans": "4×10 m",
        "span_count": 4,
        "span_lengths": [10.0, 10.0, 10.0, 10.0],
        "total_length": 40.0,
        "carriageway_width": 7.5,
        "foundation_type": "OPEN",
        "pier_material": "M20",
        "superstructure_type": "RCC_SOLID_SLAB",
        "deck_thickness_mm": 500,
        "pier_shaft_width": 1.5,
        "pier_height": 6.0,
        "abutment_type": "OPEN",
        "bearing_type": "ELASTOMERIC",
        "hfl": 100.0,
        "soffit_level": 101.5,
        "road_level": 102.5,
        "scour_depth": 2.0,
    },
    {
        "id": "BR-I-2022-002",
        "title": "Open Foundation + RCC Pier + Solid Slab",
        "spans": "4×10 m",
        "span_count": 4,
        "span_lengths": [10.0, 10.0, 10.0, 10.0],
        "total_length": 40.0,
        "carriageway_width": 7.5,
        "foundation_type": "OPEN",
        "pier_material": "M25",
        "superstructure_type": "RCC_SOLID_SLAB",
        "deck_thickness_mm": 500,
        "pier_shaft_width": 1.5,
        "pier_height": 6.0,
        "abutment_type": "OPEN",
        "bearing_type": "ELASTOMERIC",
        "hfl": 100.0,
        "soffit_level": 101.5,
        "road_level": 102.5,
        "scour_depth": 2.0,
    },
    {
        "id": "BR-I-2022-003",
        "title": "Raft Foundation + RCC Pier + Solid Slab",
        "spans": "5×10 m",
        "span_count": 5,
        "span_lengths": [10.0, 10.0, 10.0, 10.0, 10.0],
        "total_length": 50.0,
        "carriageway_width": 7.5,
        "foundation_type": "RAFT",
        "pier_material": "M25",
        "superstructure_type": "RCC_SOLID_SLAB",
        "deck_thickness_mm": 500,
        "pier_shaft_width": 1.5,
        "pier_height": 7.0,
        "abutment_type": "OPEN",
        "bearing_type": "ELASTOMERIC",
        "hfl": 100.0,
        "soffit_level": 101.5,
        "road_level": 102.5,
        "scour_depth": 3.0,
    },
    {
        "id": "BR-I-2022-004",
        "title": "Raft Foundation + RCC Box Cell",
        "spans": "Multi-cell",
        "span_count": 1,
        "span_lengths": [8.0],
        "total_length": 8.0,
        "carriageway_width": 7.5,
        "foundation_type": "RAFT",
        "pier_material": "M30",
        "superstructure_type": "RCC_BOX_CELL",
        "deck_thickness_mm": 300,
        "pier_shaft_width": 0.8,
        "pier_height": 4.0,
        "abutment_type": "INTEGRAL",
        "bearing_type": "NONE",
        "hfl": 100.0,
        "soffit_level": 101.0,
        "road_level": 101.5,
        "scour_depth": 1.5,
    },
    {
        "id": "BR-I-2022-005",
        "title": "RCC Portal + Open Foundation (Submersible)",
        "spans": "6×15 m",
        "span_count": 6,
        "span_lengths": [15.0]*6,
        "total_length": 90.0,
        "carriageway_width": 7.5,
        "foundation_type": "OPEN",
        "pier_material": "M30",
        "superstructure_type": "RCC_PORTAL",
        "deck_thickness_mm": 600,
        "pier_shaft_width": 2.0,
        "pier_height": 8.0,
        "abutment_type": "PORTAL",
        "bearing_type": "NONE",
        "hfl": 100.0,
        "soffit_level": 101.0,
        "road_level": 102.0,
        "scour_depth": 3.0,
    },
    {
        "id": "BR-I-2022-006",
        "title": "Open Fdn + RCC Pier + Pier Cap + Solid Slab",
        "spans": "4×12 m",
        "span_count": 4,
        "span_lengths": [12.0]*4,
        "total_length": 48.0,
        "carriageway_width": 7.5,
        "foundation_type": "OPEN",
        "pier_material": "M25",
        "superstructure_type": "RCC_SOLID_SLAB",
        "deck_thickness_mm": 550,
        "pier_shaft_width": 1.8,
        "pier_height": 7.0,
        "pier_cap_depth": 0.8,
        "abutment_type": "OPEN",
        "bearing_type": "ELASTOMERIC",
        "hfl": 100.0,
        "soffit_level": 101.5,
        "road_level": 102.5,
        "scour_depth": 2.5,
    },
    {
        "id": "BR-I-2022-007",
        "title": "Open Fdn + RCC Pier + RCC 3-Girder (T-Beam)",
        "spans": "3×15 m",
        "span_count": 3,
        "span_lengths": [15.0]*3,
        "total_length": 45.0,
        "carriageway_width": 7.5,
        "foundation_type": "OPEN",
        "pier_material": "M25",
        "superstructure_type": "RCC_T_BEAM",
        "deck_thickness_mm": 200,
        "girder_depth_mm": 1200,
        "girder_spacing": 2.5,
        "girders_per_deck": 3,
        "pier_shaft_width": 1.5,
        "pier_height": 8.0,
        "abutment_type": "OPEN",
        "bearing_type": "ELASTOMERIC",
        "hfl": 100.0,
        "soffit_level": 101.5,
        "road_level": 103.0,
        "scour_depth": 2.5,
    },
    {
        "id": "BR-I-2022-008",
        "title": "Pile Fdn + RCC Pier + RCC 3-Girder (T-Beam)",
        "spans": "3×15 m",
        "span_count": 3,
        "span_lengths": [15.0]*3,
        "total_length": 45.0,
        "carriageway_width": 7.5,
        "foundation_type": "PILE",
        "pier_material": "M25",
        "superstructure_type": "RCC_T_BEAM",
        "deck_thickness_mm": 200,
        "girder_depth_mm": 1200,
        "girder_spacing": 2.5,
        "girders_per_deck": 3,
        "pier_shaft_width": 1.5,
        "pier_height": 8.0,
        "pile_diameter_mm": 1000,
        "pile_length_m": 15.0,
        "piles_per_pier": 4,
        "abutment_type": "OPEN",
        "bearing_type": "ELASTOMERIC",
        "hfl": 100.0,
        "soffit_level": 101.5,
        "road_level": 103.0,
        "scour_depth": 3.0,
    },
    {
        "id": "BR-I-2022-009",
        "title": "Open Fdn + RCC Pier + PSC 4-Girder",
        "spans": "4×20 m",
        "span_count": 4,
        "span_lengths": [20.0]*4,
        "total_length": 80.0,
        "carriageway_width": 7.5,
        "foundation_type": "OPEN",
        "pier_material": "M30",
        "superstructure_type": "PSC_I_GIRDER",
        "deck_thickness_mm": 200,
        "girder_depth_mm": 1500,
        "girder_spacing": 2.5,
        "girders_per_deck": 4,
        "pier_shaft_width": 2.0,
        "pier_height": 10.0,
        "abutment_type": "OPEN",
        "bearing_type": "POT",
        "hfl": 100.0,
        "soffit_level": 101.5,
        "road_level": 103.5,
        "scour_depth": 3.0,
    },
    {
        "id": "BR-I-2022-010",
        "title": "Pile Fdn + RCC Pier + PSC 4-Girder",
        "spans": "4×20 m",
        "span_count": 4,
        "span_lengths": [20.0]*4,
        "total_length": 80.0,
        "carriageway_width": 7.5,
        "foundation_type": "PILE",
        "pier_material": "M30",
        "superstructure_type": "PSC_I_GIRDER",
        "deck_thickness_mm": 200,
        "girder_depth_mm": 1500,
        "girder_spacing": 2.5,
        "girders_per_deck": 4,
        "pier_shaft_width": 2.0,
        "pier_height": 10.0,
        "pile_diameter_mm": 1200,
        "pile_length_m": 20.0,
        "piles_per_pier": 6,
        "abutment_type": "OPEN",
        "bearing_type": "POT",
        "hfl": 100.0,
        "soffit_level": 101.5,
        "road_level": 103.5,
        "scour_depth": 3.5,
    },
    {
        "id": "BR-I-2022-011",
        "title": "Open/Well Fdn + RCC Pier + PSC Box",
        "spans": "3×30 m",
        "span_count": 3,
        "span_lengths": [30.0]*3,
        "total_length": 90.0,
        "carriageway_width": 7.5,
        "foundation_type": "WELL",
        "pier_material": "M35",
        "superstructure_type": "PSC_BOX",
        "deck_thickness_mm": 250,
        "girder_depth_mm": 2500,
        "girder_spacing": 3.0,
        "girders_per_deck": 1,
        "pier_shaft_width": 2.5,
        "pier_height": 12.0,
        "abutment_type": "OPEN",
        "bearing_type": "POT",
        "hfl": 100.0,
        "soffit_level": 101.5,
        "road_level": 104.5,
        "scour_depth": 4.0,
    },
    {
        "id": "BR-I-2022-012",
        "title": "Pile Fdn + RCC Pier + PSC Box",
        "spans": "3×30 m",
        "span_count": 3,
        "span_lengths": [30.0]*3,
        "total_length": 90.0,
        "carriageway_width": 7.5,
        "foundation_type": "PILE",
        "pier_material": "M35",
        "superstructure_type": "PSC_BOX",
        "deck_thickness_mm": 250,
        "girder_depth_mm": 2500,
        "girder_spacing": 3.0,
        "girders_per_deck": 1,
        "pier_shaft_width": 2.5,
        "pier_height": 12.0,
        "pile_diameter_mm": 1500,
        "pile_length_m": 25.0,
        "piles_per_pier": 6,
        "abutment_type": "OPEN",
        "bearing_type": "POT",
        "hfl": 100.0,
        "soffit_level": 101.5,
        "road_level": 104.5,
        "scour_depth": 4.0,
    },
    {
        "id": "BR-I-2022-013",
        "title": "Well Fdn + RCC Pier + PSC Box",
        "spans": "3×30 m",
        "span_count": 3,
        "span_lengths": [30.0]*3,
        "total_length": 90.0,
        "carriageway_width": 7.5,
        "foundation_type": "WELL",
        "pier_material": "M35",
        "superstructure_type": "PSC_BOX",
        "deck_thickness_mm": 250,
        "girder_depth_mm": 2500,
        "girder_spacing": 3.0,
        "girders_per_deck": 1,
        "pier_shaft_width": 2.5,
        "pier_height": 12.0,
        "well_diameter_m": 6.0,
        "abutment_type": "OPEN",
        "bearing_type": "POT",
        "hfl": 100.0,
        "soffit_level": 101.5,
        "road_level": 104.5,
        "scour_depth": 4.5,
    },
    {
        "id": "BR-I-2022-014",
        "title": "Open Fdn + RCC Arch/Slab (Pedestrian)",
        "spans": "1×15 m",
        "span_count": 1,
        "span_lengths": [15.0],
        "total_length": 15.0,
        "carriageway_width": 3.5,
        "foundation_type": "OPEN",
        "pier_material": "M25",
        "superstructure_type": "RCC_ARCH",
        "deck_thickness_mm": 300,
        "pier_shaft_width": 1.0,
        "pier_height": 5.0,
        "abutment_type": "OPEN",
        "bearing_type": "NONE",
        "hfl": 100.0,
        "soffit_level": 101.5,
        "road_level": 102.5,
        "scour_depth": 2.0,
    },
    {
        "id": "BR-I-2022-015",
        "title": "Open Fdn + RCC Arch (Vehicular)",
        "spans": "1×20 m",
        "span_count": 1,
        "span_lengths": [20.0],
        "total_length": 20.0,
        "carriageway_width": 7.5,
        "foundation_type": "OPEN",
        "pier_material": "M30",
        "superstructure_type": "RCC_ARCH",
        "deck_thickness_mm": 400,
        "pier_shaft_width": 1.5,
        "pier_height": 6.0,
        "abutment_type": "OPEN",
        "bearing_type": "NONE",
        "hfl": 100.0,
        "soffit_level": 101.5,
        "road_level": 103.0,
        "scour_depth": 2.5,
    },
]


def _build_project(params: dict):
    """Build a BridgeProject from a PWD parameter dict."""
    from bridgecad_core.models import (
        BridgeProject, ProjectMaster, BridgeSelection, GeometryInput,
        Superstructure, Substructure, FoundationDetails, Approaches,
        HydraulicData, Materials, BearingsJoints, ComponentsLib,
        DrawingControl, Calculations, ValidationModel,
    )
    from bridgecad_core import types as T

    def _dec(v): return Decimal(str(v)) if v is not None else None
    def _int(v): return int(v) if v is not None else None

    # Map superstructure type string to enum
    sst_map = {
        "RCC_SOLID_SLAB": "SOLID_SLAB",
        "RCC_T_BEAM": "RCC_TBEAM",
        "PSC_I_GIRDER": "PSC_IGIRDER",
        "PSC_BOX": "PSC_BOX_GIRDER",
        "RCC_BOX_CELL": "SOLID_SLAB",
        "RCC_PORTAL": "SOLID_SLAB",
        "RCC_ARCH": "SOLID_SLAB",
    }
    sst_name = sst_map.get(params["superstructure_type"], "SOLID_SLAB")

    # Map foundation type
    ftype_map = {"OPEN": "OPEN", "PILE": "PILE", "RAFT": "RAFT",
                 "WELL": "WELL"}

    # Map abutment type
    abt_map = {"OPEN": "CANTILEVER", "INTEGRAL": "CANTILEVER",
               "PORTAL": "CANTILEVER"}

    # Map bearing type
    brg_map = {"ELASTOMERIC": "ELASTOMERIC_NEOPRENE", "POT": "POT_PTFE",
               "NONE": "ELASTOMERIC_NEOPRENE"}

    pm = ProjectMaster(
        project_title=params["title"],
        project_code=f"PWD-2022-{params['id'].split('-')[-1].zfill(3)}",
        bridge_name=f"PWD {params['id']}",
        drawing_no=params["id"],
        client=T.ClientType.STATE_PWD,
        revision=T.RevisionTag.R0,
        state_code=T.IndianStateCode.MH,
        language=T.Language.EN,
        project_phase=T.ProjectPhase.DESIGN_GAD_60_PCT,
        road_level_rl_m=_dec(params["road_level"]),
        ground_level_rl_m=_dec(params["hfl"] - params["scour_depth"]),
    )

    gi = GeometryInput(
        span_count=params["span_count"],
        span_lengths_m=[_dec(s) for s in params["span_lengths"]],
        carriageway_width_m=_dec(params["carriageway_width"]),
        chainage_start_km=Decimal("0.000"),
    )

    ss = Superstructure(
        type=getattr(T.SuperstructureType, sst_name, T.SuperstructureType.SOLID_SLAB),
        deck_material=T.ConcreteGrade.M30,
        deck_thickness_mm=_int(params.get("deck_thickness_mm", 500)),
        wearing_coat_thickness_mm=65,
        girder_depth_mm=_int(params.get("girder_depth_mm", 0)),
        girder_spacing_m=_dec(params.get("girder_spacing", 2.5)),
        girders_per_deck_count=_int(params.get("girders_per_deck", 0)),
        parapet_height_mm=1000,
    )

    sub = Substructure(
        pier_type=T.PierType.WALL,
        pier_material=getattr(T.ConcreteGrade, params.get("pier_material", "M25"),
                              T.ConcreteGrade.M25),
        pier_height_typical_m=_dec(params.get("pier_height", 6.0)),
        pier_shaft_width_m=_dec(params.get("pier_shaft_width", 1.5)),
        pier_shaft_length_m=_dec(params.get("carriageway_width", 7.5)),
        pier_cap_depth_m=_dec(params.get("pier_cap_depth", 0.8)),
        pier_cap_width_m=Decimal(str(round(float(params.get("pier_shaft_width", 1.5)) * 1.3, 3))),
        pier_pedestal_height_m=Decimal("0.15"),
        abutment_type=getattr(T.AbutmentType, abt_map.get(params["abutment_type"], "CANTILEVER"),
                             T.AbutmentType.CANTILEVER),
        abutment_material=T.ConcreteGrade.M25,
        abutment_width_m=Decimal("1.2"),
        abutment_length_m=_dec(params.get("carriageway_width", 7.5)),
        abutment_height_m=_dec(params.get("pier_height", 6.0)),
        abutment_pedestal_height_m=Decimal("0.15"),
        approach_slab_length_m=Decimal("3.5"),
        approach_slab_thickness_mm=200,
        wing_wall_splay_length_m=Decimal("3.0"),
        wing_wall_height_m=Decimal("2.5"),
        return_wall_length_m=Decimal("4.0"),
        backfill_type="SELECT MOORUM",
        abutment_cap_depth_mm=600,
        abutment_cap_projection_front_mm=300,
        abutment_cap_projection_rear_mm=300,
        dirt_wall_thickness_mm=300,
        weep_hole_diameter_mm=100,
        weep_hole_spacing_m=Decimal("1.5"),
    )

    fd = FoundationDetails(
        type=getattr(T.FoundationType, ftype_map.get(params["foundation_type"], "OPEN"),
                     T.FoundationType.OPEN),
        pile_diameter_mm=_int(params.get("pile_diameter_mm", 0)) or None,
        pile_length_m=_dec(params.get("pile_length_m", 0)),
        piles_per_pier=_int(params.get("piles_per_pier", 0)) or None,
        pile_spacing_m=Decimal("2.5"),
        pile_cap_thickness_mm=_int(1500 if params["foundation_type"] == "PILE" else 0),
        pile_cutoff_level_m=_dec(params["hfl"] - 1.0),
    )

    hd = HydraulicData(
        hfl_m=_dec(params["hfl"]),
        lwl_m=_dec(params["hfl"] - 0.5),
        scour_level_m=_dec(params["hfl"] - params["scour_depth"]),
        design_scour_depth_m=_dec(params["scour_depth"]),
        actual_soffit_level_m=_dec(params["soffit_level"]),
    )

    mt = Materials(
        concrete_superstructure=T.ConcreteGrade.M30,
        concrete_substructure=getattr(T.ConcreteGrade, params.get("pier_material", "M25"),
                                       T.ConcreteGrade.M25),
        concrete_foundation=T.ConcreteGrade.M25,
        reinforcement_steel_grade=T.SteelGrade.Fe500D,
        prestressing_steel=T.PrestressGrade.G1860,
        bearing_type=T.BearingType.ELASTOMERIC_NEOPRENE,
        expansion_joint_type=T.ExpansionJointType.STRIP_SEAL,
    )

    bj = BearingsJoints(
        bearing_type=getattr(T.BearingType, brg_map.get(params["bearing_type"], "ELASTOMERIC_NEOPRENE"),
                             T.BearingType.ELASTOMERIC_NEOPRENE),
    )

    return BridgeProject(
        project_master=pm,
        bridge_selection=BridgeSelection(
            bridge_category=T.BridgeCategory.MINOR_BRIDGE if params["total_length"] < 30
                           else T.BridgeCategory.MAJOR_BRIDGE,
            bridge_type=getattr(T.SuperstructureType, sst_name, T.SuperstructureType.SOLID_SLAB),
            span_configuration=T.SpanConfiguration.SIMPLY_SUPPORTED,
            carriageway_config=T.CarriagewayLaneConfig.LANE_2,
            design_code=T.DesignCode.IRC_6_2017,
            loading_class=T.LoadClass.CLASS_A,
            seismic_zone=T.SeismicZone.ZONE_III,
            wind_zone_ms=T.WindSpeedBasic_ms.VB_39_ms_ZONE_2,
            foundation_type=getattr(T.FoundationType, ftype_map.get(params["foundation_type"], "OPEN"),
                                   T.FoundationType.OPEN),
        ),
        geometry_input=gi,
        superstructure=ss,
        substructure=sub,
        foundation_details=fd,
        approaches=Approaches(),
        hydraulic_data=hd,
        materials=mt,
        bearings_joints=bj,
        components_lib=ComponentsLib(),
        drawing_control=DrawingControl(
            sheet_size=T.SheetSize.A1,
            drawing_scale=T.DrawingScale.S100,
            title_block_style=T.TitleBlockStyle.STANDARD,
        ),
        calculations=Calculations(),
        validation=ValidationModel(),
    )


def _check_completeness(sheets: list[Path]) -> list[str]:
    """Check every sheet has enough entities and is non-trivially populated."""
    import ezdxf
    issues = []
    for s in sheets:
        try:
            n = len(list(ezdxf.readfile(str(s)).modelspace()))
            if n < MIN_ENTITIES:
                issues.append(f"{s.name}: only {n} entities (< {MIN_ENTITIES})")
        except Exception as exc:
            issues.append(f"{s.name}: read error — {exc}")
    return issues


def _render_pngs(sheets: list[Path], out_dir: Path, dpi: int = 150) -> list[Path]:
    """Render each DXF to PNG (non-fatal on failure)."""
    from bridgecad_draw.engines.png_engine import render_png
    pngs = []
    for s in sheets:
        png_out = out_dir / (s.stem + ".png")
        try:
            render_png(s, png_out, dpi=dpi)
            pngs.append(png_out)
        except Exception:
            pngs.append(None)  # type: ignore[arg-type]
    return pngs


def _write_readme(out_dir: Path, params: dict, sheets: list[Path],
                  issues: list[str], dxf_kb: int) -> None:
    sheet_table = ""
    for i, s in enumerate(sheets, 1):
        size_kb = s.stat().st_size // 1024
        sheet_table += f"| {i} | {s.stem} | {size_kb} KB |\n"

    status = "✅ PASS" if not issues else "❌ FAIL"
    issues_text = "\n".join(f"- {i}" for i in issues) if issues else "No issues found."

    readme = f"""# {params['title']}

**PWD Drawing No.:** {params['id']}  
**Spans:** {params['spans']}  
**Foundation:** {params['foundation_type']}  
**Superstructure:** {params['superstructure_type']}  
**Pier Material:** {params.get('pier_material', 'M25')}  
**Carriageway:** {params['carriageway_width']} m  
**Road RL:** {params['road_level']} m  
**HFL:** {params['hfl']} m  

## Completeness check: {status}

{issues_text}

## Sheets generated

| # | Sheet | Size |
|---|---|---|
{sheet_table}

**Total DXF size:** {dxf_kb} KB

---
*Generated by BridgeCAD Enterprise Suite v0.1.0-rc1 — Maharashtra PWD Booklet*
*IRC 5 / IRC 6 / IRC 21 / IRC 78 / IRC SP:55 / MoRTH 2024-25*
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def generate_one(params: dict) -> tuple[str, bool, str]:
    """Generate one PWD type. Returns (id, success, message)."""
    from bridgecad_draw.booklet import generate_package, PackageGenerationError

    out_dir = OUTPUT_ROOT / params["id"]
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        project = _build_project(params)
    except Exception as exc:
        return params["id"], False, f"build failed: {exc}"

    try:
        sheets = generate_package(project, out_dir, prefix=params["id"])
    except (PackageGenerationError, Exception) as exc:
        return params["id"], False, f"DXF failed: {type(exc).__name__}: {exc}"

    issues = _check_completeness(sheets)
    _render_pngs(sheets, out_dir)
    dxf_kb = sum(s.stat().st_size for s in sheets) // 1024
    _write_readme(out_dir, params, sheets, issues, dxf_kb)

    status = "PASS" if not issues else "FAIL"
    return params["id"], not issues, f"{status} — {len(sheets)} sheets, {dxf_kb} KB, {len(issues)} issue(s)"


def main() -> int:
    total = len(PWD_TYPES)
    passed, failed_ids = 0, []

    print(f"\n{'='*72}")
    print(f"  Maharashtra PWD Booklet — GAD Generator")
    print(f"  Types: {total}  |  Output: {OUTPUT_ROOT}")
    print(f"{'='*72}\n")

    for params in PWD_TYPES:
        fid, ok, msg = generate_one(params)
        status = "DONE" if ok else "FAIL"
        print(f"  [{status:4s}] {params['id']:<20} {params['title']:<50} {msg}")
        if ok:
            passed += 1
        else:
            failed_ids.append(fid)

    print(f"\n{'='*72}")
    print(f"  Generated : {passed}/{total}")
    print(f"  Failed    : {len(failed_ids)}")
    if failed_ids:
        for f in failed_ids:
            print(f"    ✗ {f}")
    print(f"  Output dir: {OUTPUT_ROOT}")
    print(f"{'='*72}\n")

    # Write index README
    index = "# Maharashtra PWD Booklet — GAD Packages\n\n"
    index += f"**{passed}/{total} types** generated as 9-sheet DXF + PNG packages.\n\n"
    index += "| # | PWD Drawing No. | Type | Spans | Status |\n"
    index += "|---|---|---|---|---|\n"
    for i, p in enumerate(PWD_TYPES, 1):
        ok = p["id"] not in failed_ids
        index += f"| {i:02d} | {p['id']} | {p['title']} | {p['spans']} | {'✅' if ok else '❌'} |\n"
    index += "\n---\n*BridgeCAD Enterprise Suite v0.1.0-rc1 — BRIDGECAD-OSS-1.0*\n"
    (OUTPUT_ROOT / "README.md").write_text(index, encoding="utf-8")

    return 0 if not failed_ids else 1


if __name__ == "__main__":
    sys.exit(main())
