"""
M9 E2E fixture verifier.

Loads each fixture JSON → builds BridgeProject → generates 7-sheet DXF + BOQ
+ ZIP bundle → checks against expected values from the fixture.

Run:
    cd "BridgeCAD Enterprise Suite"
    python tests/e2e/run_e2e.py
"""
from __future__ import annotations

import json
import sys
import zipfile
import tempfile
import traceback
from decimal import Decimal
from pathlib import Path

# ── package path bootstrap ─────────────────────────────────────────────────
_SUITE = Path(__file__).parents[2]
for _pkg in ["bridgecad-core", "bridgecad-io", "bridgecad-draw",
             "bridgecad-bill", "bridgecad-qa", "bridgecad-export"]:
    _p = _SUITE / "packages" / _pkg
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

SEP = "=" * 72

#: Every generated sheet must carry real geometry. A sheet that is only a title
#: block — the DEF-3.2 scaffold failure mode — has fewer than this and must not
#: ship silently. Complements the byte-size floor in E5.
MIN_SHEET_ENTITIES = 20


# ---------------------------------------------------------------------------
# Fixture → BridgeProject builder
# ---------------------------------------------------------------------------

def _build_from_fixture(data: dict):
    """Convert a fixture JSON dict into a BridgeProject instance."""
    from bridgecad_core.models import (
        BridgeProject, ProjectMaster, BridgeSelection, GeometryInput,
        Superstructure, Substructure, FoundationDetails, Approaches,
        HydraulicData, Materials, BearingsJoints, BearingScheduleRow,
        ExpansionJointScheduleRow, ComponentsLib, DrawingControl,
        Calculations, ValidationModel,
    )
    from bridgecad_core import types as T

    p = data["project"]

    def _enum(cls_name: str, value):
        if value is None: return None
        cls = getattr(T, cls_name)
        if isinstance(value, str):
            # Try by name first, then value
            for m in cls:
                if m.name == value or m.value == value:
                    return m
        if isinstance(value, (int, float)):
            # IntEnum: match by value
            for m in cls:
                if m.value == int(value):
                    return m
        return None

    def _dec(v): return Decimal(str(v)) if v is not None else None
    def _int(v): return int(v) if v is not None else None

    pm_d  = p["project_master"]
    bs_d  = p["bridge_selection"]
    gi_d  = p["geometry_input"]
    ss_d  = p["superstructure"]
    sub_d = p["substructure"]
    fd_d  = p["foundation_details"]
    ap_d  = p["approaches"]
    hd_d  = p["hydraulic_data"]
    mt_d  = p["materials"]
    bj_d  = p["bearings_joints"]
    cl_d  = p["components_lib"]
    dc_d  = p["drawing_control"]
    ca_d  = p["calculations"]
    vl_d  = p["validation"]

    # Bearing rows
    bear_rows = []
    for r in bj_d.get("bearing_schedule", []):
        bear_rows.append(BearingScheduleRow(
            location              = r["location"],
            bearing_type          = _enum("BearingType", r["bearing_type"]),
            size_x_mm             = _int(r.get("size_x_mm")),
            size_y_mm             = _int(r.get("size_y_mm")),
            design_load_kn        = _dec(r.get("design_load_kn")),
            fixed_or_guide_or_free= r.get("fixed_or_guide_or_free"),
            elastomeric_layers_count= _int(r.get("elastomeric_layers_count")),
            pot_pressure_mpa      = _dec(r.get("pot_pressure_mpa")),
            ptfe_sliding_surface_flag = bool(r.get("ptfe_sliding_surface_flag", False)),
            quantity              = _int(r.get("quantity", 1)) or 1,
        ))

    expj_rows = []
    for r in bj_d.get("expansion_joint_schedule", []):
        expj_rows.append(ExpansionJointScheduleRow(
            location           = r["location"],
            joint_type         = _enum("ExpansionJointType", r["joint_type"]),
            width_mm           = _int(r.get("width_mm")),
            movement_range_mm  = _int(r.get("movement_range_mm")),
            gap_mm             = _int(r.get("gap_mm")),
            transverse_length_m= _dec(r.get("transverse_length_m")),
            quantity           = _int(r.get("quantity", 1)) or 1,
        ))

    output_fmts = [_enum("OutputFormat", f)
                   for f in dc_d.get("output_formats", ["DXF"])]
    output_fmts = [f for f in output_fmts if f is not None]

    return BridgeProject(
        project_master=ProjectMaster(
            project_title  = pm_d["project_title"],
            project_code   = pm_d["project_code"],
            bridge_name    = pm_d["bridge_name"],
            chainage_km    = _dec(pm_d.get("chainage_km")),
            client         = _enum("ClientType", pm_d["client"]),
            revision       = _enum("RevisionTag", pm_d.get("revision","R0")),
            state_code     = _enum("IndianStateCode", pm_d.get("state_code","MH")),
            language       = _enum("Language", pm_d.get("language","EN")),
            road_level_rl_m  = _dec(pm_d.get("road_level_rl_m")),
            ground_level_rl_m= _dec(pm_d.get("ground_level_rl_m")),
            project_phase  = _enum("ProjectPhase", pm_d.get("project_phase")),
            currency       = _enum("Currency", pm_d.get("currency","INR")),
        ),
        bridge_selection=BridgeSelection(
            bridge_category    = _enum("BridgeCategory",    bs_d["bridge_category"]),
            bridge_type        = _enum("SuperstructureType", bs_d["bridge_type"]),
            span_configuration = _enum("SpanConfiguration", bs_d["span_configuration"]),
            span_count         = _int(bs_d["span_count"]),
            carriageway_config = _enum("CarriagewayLaneConfig", bs_d["carriageway_config"]),
            design_code        = _enum("DesignCode",       bs_d["design_code"]),
            loading_class      = _enum("LoadClass",        bs_d["loading_class"]),
            seismic_zone       = _enum("SeismicZone",      bs_d["seismic_zone"]),
            wind_zone_ms       = _enum("WindSpeedBasic_ms",bs_d["wind_zone_ms"]),
            foundation_type    = _enum("FoundationType",   bs_d["foundation_type"]),
        ),
        geometry_input=GeometryInput(
            span_count                 = _int(gi_d["span_count"]),
            span_lengths_m             = [_dec(x) for x in gi_d["span_lengths_m"]],
            alignment_type             = _enum("AlignmentType", gi_d.get("alignment_type","STRAIGHT")),
            gradient_pct               = _dec(gi_d.get("gradient_pct",0)),
            carriageway_width_m        = _dec(gi_d["carriageway_width_m"]),
            footpath_left_m            = _dec(gi_d.get("footpath_left_m",0)),
            footpath_right_m           = _dec(gi_d.get("footpath_right_m",0)),
            crash_barrier_width_left_m = _dec(gi_d.get("crash_barrier_width_left_m",0.45)),
            crash_barrier_width_right_m= _dec(gi_d.get("crash_barrier_width_right_m",0.45)),
            kerb_width_left_m          = _dec(gi_d.get("kerb_width_left_m",0.25)),
            kerb_width_right_m         = _dec(gi_d.get("kerb_width_right_m",0.25)),
            median_width_m             = _dec(gi_d.get("median_width_m",0)),
            skew_angle_deg             = _dec(gi_d.get("skew_angle_deg",0)),
            skew_direction             = _enum("SkewDirection", gi_d.get("skew_direction","NONE")),
            curved_bridge_flag         = bool(gi_d.get("curved_bridge_flag",False)),
            camber_mm                  = _int(gi_d.get("camber_mm",20)),
            camber_method              = _enum("CamberMethod", gi_d.get("camber_method","PARABOLIC_CROWN")),
            chainage_unit              = _enum("ChainageUnit", gi_d.get("chainage_unit","METRE")),
            chainage_start_km          = _dec(gi_d.get("chainage_start_km")),
            chainage_end_km            = _dec(gi_d.get("chainage_end_km")),
        ),
        superstructure=Superstructure(
            type                     = _enum("SuperstructureType", ss_d["type"]),
            deck_material            = _enum("ConcreteGrade",      ss_d["deck_material"]),
            deck_thickness_mm        = _int(ss_d.get("deck_thickness_mm",200)),
            wearing_coat_type        = _enum("WearingCoatType",    ss_d.get("wearing_coat_type")),
            wearing_coat_grade       = _enum("WearingCoatGrade",   ss_d.get("wearing_coat_grade")),
            wearing_coat_thickness_mm= _int(ss_d.get("wearing_coat_thickness_mm")),
            girder_type              = _enum("GirderType",         ss_d.get("girder_type")),
            girder_depth_mm          = _int(ss_d.get("girder_depth_mm")) or None,
            girder_spacing_m         = _dec(ss_d.get("girder_spacing_m")) if ss_d.get("girder_spacing_m") else None,
            girders_per_deck_count   = _int(ss_d.get("girders_per_deck_count")) or None,
            parapet_type             = _enum("ParapetType",        ss_d.get("parapet_type")),
            parapet_height_mm        = _int(ss_d.get("parapet_height_mm")),
            camber_mm                = _int(ss_d.get("camber_mm")),
            camber_method            = _enum("CamberMethod",       ss_d.get("camber_method")),
        ),
        substructure=Substructure(
            pier_type               = _enum("PierType",       sub_d["pier_type"]),
            pier_material           = _enum("ConcreteGrade",  sub_d["pier_material"]),
            pier_height_typical_m   = _dec(sub_d.get("pier_height_typical_m",6)),
            pier_cap_type           = _enum("PierCapType",    sub_d.get("pier_cap_type","NON_DROP_FLAT")),
            pier_cap_width_m        = _dec(sub_d.get("pier_cap_width_m",1.8)),
            pier_cap_length_m       = _dec(sub_d.get("pier_cap_length_m",9.0)),
            pier_cap_depth_m        = _dec(sub_d.get("pier_cap_depth_m",0.65)),
            pier_shaft_width_m      = _dec(sub_d.get("pier_shaft_width_m",1.2)),
            pier_shaft_length_m     = _dec(sub_d.get("pier_shaft_length_m",9.0)),
            pier_pedestal_height_m  = _dec(sub_d.get("pier_pedestal_height_m",0.15)),
            pier_diaphragm_required = bool(sub_d.get("pier_diaphragm_required",False)),
            abutment_type           = _enum("AbutmentType",   sub_d["abutment_type"]),
            abutment_material       = _enum("ConcreteGrade",  sub_d["abutment_material"]),
            abutment_width_m        = _dec(sub_d.get("abutment_width_m",1.0)),
            abutment_length_m       = _dec(sub_d.get("abutment_length_m",9.2)),
            abutment_height_m       = _dec(sub_d.get("abutment_height_m",2.8)),
            abutment_pedestal_height_m= _dec(sub_d.get("abutment_pedestal_height_m",0.15)),
            return_wall_type        = _enum("ReturnWallType", sub_d.get("return_wall_type","CANTILEVER_RCC")),
            return_wall_length_m    = _dec(sub_d.get("return_wall_length_m",3.5)),
            return_wall_height_m    = _dec(sub_d.get("return_wall_height_m",2.5)),
            wing_wall_type          = _enum("WingWallType",   sub_d.get("wing_wall_type","SPLAYED_45_DEG")),
            wing_wall_angle_deg     = _dec(sub_d.get("wing_wall_angle_deg",45.0)),
            wing_wall_splay_length_m= _dec(sub_d.get("wing_wall_splay_length_m",2.5)),
            wing_wall_height_m      = _dec(sub_d.get("wing_wall_height_m",2.0)),
            backfill_type           = sub_d.get("backfill_type","SELECT MOORUM"),
            approach_slab_length_m  = _dec(sub_d.get("approach_slab_length_m",3.5)),
            approach_slab_thickness_mm= _int(sub_d.get("approach_slab_thickness_mm",200)),
            bearings_per_pier       = _int(sub_d.get("bearings_per_pier",4)),
            bearings_per_abutment   = _int(sub_d.get("bearings_per_abutment",4)),
        ),
        foundation_details=FoundationDetails(
            type                       = _enum("FoundationType", fd_d.get("type", fd_d.get("foundation_type"))),
            pile_type                  = _enum("PileType",       fd_d.get("pile_type","BORED_CAST_IN_SITU")),
            pile_shape                 = _enum("PileShape",      fd_d.get("pile_shape","CIRCULAR_ROUND")),
            pile_diameter_mm           = _int(fd_d.get("pile_diameter_mm")) or None,
            pile_length_m              = _dec(fd_d.get("pile_length_m")) if fd_d.get("pile_length_m") else None,
            piles_per_pier             = _int(fd_d.get("piles_per_pier")) or None,
            pile_group_config          = fd_d.get("pile_group_config"),
            pile_spacing_m             = _dec(fd_d.get("pile_spacing_m")) if fd_d.get("pile_spacing_m") else None,
            pile_cap_thickness_mm      = _int(fd_d.get("pile_cap_thickness_mm")) or None,
            pile_cutoff_level_m        = _dec(fd_d.get("pile_cutoff_level_m")),
            under_ream_count           = _enum("UnderReamCount", fd_d.get("under_ream_count",0)),
            factor_of_safety_on_bearing= _dec(fd_d.get("factor_of_safety_on_bearing",3.0)),
            bearing_capacity_kpa       = _dec(fd_d.get("bearing_capacity_kpa",350.0)),
        ),
        approaches=Approaches(
            left_approach_length_m  = _dec(ap_d.get("left_approach_length_m",30)),
            right_approach_length_m = _dec(ap_d.get("right_approach_length_m",30)),
            type_of_embankment      = ap_d.get("type_of_embankment","SELECT MOORUM"),
            soil_embankment_unit_weight_kN_m3 = _dec(ap_d.get("soil_embankment_unit_weight_kN_m3",18.5)),
            approach_slope_width_m  = _dec(ap_d.get("approach_slope_width_m",1.5)),
            shoulder_width_left_m   = _dec(ap_d.get("shoulder_width_left_m",1.0)),
            shoulder_width_right_m  = _dec(ap_d.get("shoulder_width_right_m",1.0)),
            guide_rail_required     = bool(ap_d.get("guide_rail_required",False)),
            speed_limit_on_approach_kmph= _int(ap_d.get("speed_limit_on_approach_kmph",50)),
            transition_curve_length_m= _dec(ap_d.get("transition_curve_length_m",0)),
            approach_gradient_pct   = _dec(ap_d.get("approach_gradient_pct",0.5)),
        ),
        hydraulic_data=HydraulicData(
            design_discharge_cumecs = _dec(hd_d.get("design_discharge_cumecs",85)),
            hfl_m                   = _dec(hd_d.get("hfl_m", 117.5)),
            lwl_m                   = _dec(hd_d.get("lwl_m", 113.2)),
            normal_wl_m             = _dec(hd_d.get("normal_wl_m", 114.5)),
            scour_level_m           = _dec(hd_d.get("scour_level_m", hd_d.get("scour_level_rl_m", 105.5))),
            design_scour_depth_m    = _dec(hd_d.get("design_scour_depth_m", 8.45)),
            freeboard_m             = _dec(hd_d.get("freeboard_m", 1.5)),
            actual_soffit_level_m   = _dec(hd_d.get("actual_soffit_level_m", 118.5)),
            waterway_required_m2    = _dec(hd_d.get("waterway_required_m2",28.5)),
            waterway_provided_m2    = _dec(hd_d.get("waterway_provided_m2",35)),
            lacey_silt_factor       = _dec(hd_d.get("lacey_silt_factor",0.85)),
            regime_perimeter_m      = _dec(hd_d.get("regime_perimeter_m",16.5)),
            regime_depth_m          = _dec(hd_d.get("regime_depth_m",1.5)),
            regime_velocity_mps     = _dec(hd_d.get("regime_velocity_mps",1.2)),
            afflux_m                = _dec(hd_d.get("afflux_m",0.12)),
            max_afflux_allowable_m  = _dec(hd_d.get("max_afflux_allowable_m",0.30)),
            water_source_type       = _enum("WaterSourceType", hd_d.get("water_source_type","RIVER_PERENNIAL")),
            river_bed_slope_m_per_km= _dec(hd_d.get("river_bed_slope_m_per_km",0.5)),
            catchment_area_sqkm     = _dec(hd_d.get("catchment_area_sqkm",580)),
            return_period_yr        = _enum("FloodReturnPeriodDesign", hd_d.get("return_period_yr","Q50_MAJOR_BRIDGE_STANDARD")),
            any_regime_equation_not_applied_flag= bool(hd_d.get("any_regime_equation_not_applied_flag",False)),
            highest_recorded_flood_year= _int(hd_d.get("highest_recorded_flood_year",2000)),
        ),
        materials=Materials(
            concrete_superstructure   = _enum("ConcreteGrade",      mt_d.get("concrete_superstructure", mt_d.get("deck_concrete_grade", "M30"))),
            concrete_substructure     = _enum("ConcreteGrade",      mt_d.get("concrete_substructure", mt_d.get("pier_concrete_grade", "M30"))),
            concrete_foundation       = _enum("ConcreteGrade",      mt_d.get("concrete_foundation", mt_d.get("foundation_concrete_grade", "M30"))),
            reinforcement_steel_grade = _enum("SteelGrade",         mt_d.get("reinforcement_steel_grade", mt_d.get("rebar_grade", "FE500D"))),
            prestressing_steel        = _enum("PrestressGrade",     mt_d.get("prestressing_steel","G1860")),
            bearing_type              = _enum("BearingType",        mt_d.get("bearing_type","ELASTOMERIC_NEOPRENE")),
            expansion_joint_type      = _enum("ExpansionJointType", mt_d.get("expansion_joint_type","COMPRESSION_SEAL")),
            wearing_coat_material_type= _enum("WearingCoatType",    mt_d.get("wearing_coat_material_type")),
            wearing_coat_grade        = _enum("WearingCoatGrade",   mt_d.get("wearing_coat_grade")),
        ),
        bearings_joints=BearingsJoints(
            bearing_schedule=bear_rows,
            expansion_joint_schedule=expj_rows,
        ),
        components_lib=ComponentsLib(**{k: str(v) for k, v in cl_d.items()}),
        drawing_control=DrawingControl(
            output_formats            = output_fmts or [T.OutputFormat.DXF],
            autocad_version           = _enum("AcadVersion",    dc_d.get("autocad_version","R2018")),
            sheet_size                = _enum("SheetSize",       dc_d.get("sheet_size","A1")),
            drawing_scale             = _enum("DrawingScale",    dc_d.get("drawing_scale",100)),
            gen_plan_sheet            = bool(dc_d.get("gen_plan_sheet",True)),
            gen_long_section_sheet    = bool(dc_d.get("gen_long_section_sheet",True)),
            gen_cross_section_sheet   = bool(dc_d.get("gen_cross_section_sheet",True)),
            gen_foundation_sheet      = bool(dc_d.get("gen_foundation_sheet",True)),
            gen_reinforcement_sheet   = bool(dc_d.get("gen_reinforcement_sheet",False)),
            gen_pier_details_sheet    = bool(dc_d.get("gen_pier_details_sheet",True)),
            gen_abutment_details_sheet= bool(dc_d.get("gen_abutment_details_sheet",True)),
            gen_bearings_joints_sheet = bool(dc_d.get("gen_bearings_joints_sheet",True)),
            gen_boq_sheet             = bool(dc_d.get("gen_boq_sheet",True)),
            gen_cover_sheet           = bool(dc_d.get("gen_cover_sheet",True)),
            gen_legends_sheet         = bool(dc_d.get("gen_legends_sheet",True)),
            gen_hydraulics_sheet      = bool(dc_d.get("gen_hydraulics_sheet",True)),
            layer_standard            = _enum("LayerStandard",   dc_d.get("layer_standard","IRC")),
            title_block_style         = _enum("TitleBlockStyle", dc_d.get("title_block_style","STANDARD")),
            dimension_precision_mm    = _int(dc_d.get("dimension_precision_mm",1)),
            text_height_scale_factor  = _dec(dc_d.get("text_height_scale_factor",1.0)),
            lineweight_scale_factor   = _dec(dc_d.get("lineweight_scale_factor",1.0)),
            drawing_border_inside_mm  = _int(dc_d.get("drawing_border_inside_mm",10)),
            revision_block_count      = _int(dc_d.get("revision_block_count",4)),
            legend_sheet_required     = bool(dc_d.get("legend_sheet_required",True)),
        ),
        calculations=Calculations(
            total_length_m = _dec(ca_d.get("total_length_m",12)),
            span_count     = _int(ca_d.get("span_count",1)),
            span_depth_ratio= _dec(ca_d.get("span_depth_ratio",13)),
            deck_area_sqm  = _dec(ca_d.get("deck_area_sqm",100)),
            overall_width_check_ok= bool(ca_d.get("overall_width_check_ok",True)),
            concrete_volume_superstructure_cum= _dec(ca_d.get("concrete_volume_superstructure_cum",32)),
            concrete_volume_substructure_cum  = _dec(ca_d.get("concrete_volume_substructure_cum",58)),
            concrete_volume_foundation_cum    = _dec(ca_d.get("concrete_volume_foundation_cum",78)),
            rebar_weight_tonnes_approx        = _dec(ca_d.get("rebar_weight_tonnes_approx",18)),
            prestress_tonnes_approx           = _dec(ca_d.get("prestress_tonnes_approx",0)),
            bearing_count          = _int(ca_d.get("bearing_count",8)),
            expansion_joint_count  = _int(ca_d.get("expansion_joint_count",2)),
            total_estimated_quantity_cost_inr= _dec(ca_d.get("total_estimated_quantity_cost_inr",9500000)),
            design_scour_vs_foundation_cover_ok= bool(ca_d.get("design_scour_vs_foundation_cover_ok",True)),
            waterway_check_pass    = bool(ca_d.get("waterway_check_pass",True)),
            afflux_ok              = bool(ca_d.get("afflux_ok",True)),
            freeboard_actual_m     = _dec(ca_d.get("freeboard_actual_m",1.8)),
            minimum_vertical_clearance_m= _dec(ca_d.get("minimum_vertical_clearance_m",4.5)),
            horizontal_clearance_m = _dec(ca_d.get("horizontal_clearance_m",1.0)),
        ),
        validation=ValidationModel(
            overall_status       = vl_d.get("overall_status","OK_PASS"),
            critical_fail_count  = _int(vl_d.get("critical_fail_count",0)),
            warning_count        = _int(vl_d.get("warning_count",0)),
            info_count           = _int(vl_d.get("info_count",0)),
            score_0_to_100       = _dec(vl_d.get("score_0_to_100",90)),
            check_version_tag    = vl_d.get("check_version_tag","1.0.0-rc1"),
        ),
    )


# ---------------------------------------------------------------------------
# Single fixture runner
# ---------------------------------------------------------------------------

def _run_fixture(fixture_path: Path) -> tuple[str, bool, list[str]]:
    """Run one fixture. Returns (fixture_id, passed, error_messages)."""
    with fixture_path.open(encoding="utf-8") as f:
        data = json.load(f)

    fid      = data["_meta"]["fixture_id"]
    expected = data["expected"]
    errors: list[str] = []

    try:
        project = _build_from_fixture(data)
    except Exception as exc:
        return fid, False, [f"Build failed: {exc}"]

    # E1 — total length
    tl = float(project.geometry_input.total_length_m)
    if abs(tl - expected["total_length_m"]) > 0.01:
        errors.append(f"total_length={tl} ≠ expected {expected['total_length_m']}")

    # E2 — span count
    sc = project.geometry_input.span_count
    if sc != expected["span_count"]:
        errors.append(f"span_count={sc} ≠ expected {expected['span_count']}")

    # E3 — overall width in range (with 0.5 m tolerance)
    ow = float(project.geometry_input.overall_width_m)
    width_tolerance = 0.5  # metres
    min_allowed = expected["overall_width_m_min"] - width_tolerance
    max_allowed = expected["overall_width_m_max"] + width_tolerance
    if not (min_allowed <= ow <= max_allowed):
        errors.append(f"overall_width={ow:.2f}m outside [{expected['overall_width_m_min']}, {expected['overall_width_m_max']}] (±{width_tolerance} m tolerance)")

    # E4 — QA score
    try:
        from bridgecad_core.validation import run_all
        report = run_all(project)
        if report.score < expected["qa_score_min"]:
            errors.append(f"qa_score={report.score} < min {expected['qa_score_min']}")
    except Exception as exc:
        errors.append(f"QA check failed: {exc}")

    # E5 — DXF sheets + size + entity-count check
    try:
        import ezdxf
        from bridgecad_draw.booklet import generate_package
        with tempfile.TemporaryDirectory() as td:
            sheets = generate_package(project, Path(td), prefix=fid, scale_denom=100)
            total_kb = sum(s.stat().st_size for s in sheets) // 1024
            if len(sheets) < expected["dxf_sheets"]:
                errors.append(f"dxf_sheets={len(sheets)} < {expected['dxf_sheets']}")
            if total_kb < expected["dxf_total_kb_min"]:
                errors.append(f"dxf_total={total_kb}KB < min {expected['dxf_total_kb_min']}KB")
            # A scaffolded sheet (title block only) cannot ship: count real
            # modelspace entities per sheet, not just bytes.
            for s in sheets:
                n = len(list(ezdxf.readfile(str(s)).modelspace()))
                if n < MIN_SHEET_ENTITIES:
                    errors.append(
                        f"{s.name}: only {n} entities (< {MIN_SHEET_ENTITIES}) — scaffold sheet"
                    )
    except Exception as exc:
        errors.append(f"DXF gen failed: {exc}"); traceback.print_exc()

    # E6 — BOQ grand total
    try:
        from bridgecad_bill.processor import extract_and_price
        boq = extract_and_price(project)
        # Apply tolerance factor (99%) to BOQ minimum
        tolerance_factor = 0.99
        min_required = expected["boq_grand_total_inr_min"] * tolerance_factor
        if float(boq.grand_total) < min_required:
            errors.append(f"boq_total=INR {float(boq.grand_total):,.0f} < min {expected['boq_grand_total_inr_min']:,} (tolerance {tolerance_factor*100:.0f}%)")
    except Exception as exc:
        errors.append(f"BOQ failed: {exc}")

    # E7 — ZIP bundle contents
    try:
        from bridgecad_export.orchestrator import export_all
        with tempfile.TemporaryDirectory() as td:
            bundle = export_all(project, Path(td), prefix=fid)
            with zipfile.ZipFile(bundle) as zf:
                entries = zf.namelist()
            if expected["zip_has_manifest"] and not any("manifest.json" in e for e in entries):
                errors.append("ZIP missing manifest.json")
            if expected["zip_has_dxf"] and not any(e.endswith(".dxf") for e in entries):
                errors.append("ZIP missing .dxf files")
            if expected["zip_has_xlsx"] and not any(e.endswith(".xlsx") for e in entries):
                errors.append("ZIP missing .xlsx file")
    except Exception as exc:
        errors.append(f"Export failed: {exc}"); traceback.print_exc()

    passed = len(errors) == 0
    return fid, passed, errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixture_files = sorted(fixtures_dir.glob("*.json"))

    if not fixture_files:
        print("No fixture files found in", fixtures_dir)
        return 1

    print(); print(SEP)
    print("  M9 E2E FIXTURE SUITE")
    print(SEP)
    print(f"  Fixtures found: {len(fixture_files)}")
    print()

    results: list[tuple[str, bool]] = []
    for fp in fixture_files:
        fid, passed, errors = _run_fixture(fp)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {fid}")
        for e in errors:
            print(f"         x {e}")
        results.append((fid, passed))

    passed_n = sum(1 for _, ok in results if ok)
    total    = len(results)
    all_ok   = passed_n == total

    print(); print(SEP)
    print(f"  Fixtures run : {total}")
    print(f"  Passed       : {passed_n}")
    print(f"  Failed       : {total - passed_n}")
    print(f"  VERDICT      : {'*** ACCEPTED ***' if all_ok else 'REJECTED'}")
    print(SEP)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
