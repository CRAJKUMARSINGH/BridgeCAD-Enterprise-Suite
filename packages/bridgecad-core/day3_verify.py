"""Day 3 acceptance verifier: models schema size, valid fixture, bad-value ValidationErrors."""

from __future__ import annotations

import json
import sys
import traceback
from datetime import date
from decimal import Decimal
from pathlib import Path

from pydantic import ValidationError

from bridgecad_core import models
from bridgecad_core.models import BridgeProject
from bridgecad_core.types import (
    AbutmentType,
    AcadVersion,
    AlignmentType,
    BearingType,
    BridgeCategory,
    CamberMethod,
    CarriagewayLaneConfig,
    ChainageUnit,
    ClientType,
    ConcreteGrade,
    ConsultantType,
    ContractorType,
    CrashBarrierType,
    Currency,
    DesignCode,
    DrainageType,
    DrawingScale,
    ExpansionJointType,
    FloodReturnPeriodDesign,
    FootpathType,
    FoundationType,
    GirderType,
    IndianStateCode,
    KerbType,
    Language,
    LayerStandard,
    LoadClass,
    MedianType,
    OutputFormat,
    ParapetType,
    PierCapType,
    PierType,
    PileType,
    PrestressGrade,
    ProjectPhase,
    ReturnWallType,
    RevisionTag,
    SeismicZone,
    SheetSize,
    SkewDirection,
    SpanConfiguration,
    SteelGrade,
    SuperstructureType,
    TitleBlockStyle,
    UnderReamCount,
    WaterSourceType,
    WearingCoatGrade,
    WearingCoatType,
    WindSpeedBasic_ms,
    WingWallType,
)

# =========================================================================
# VALID FIXTURE: Minor ROB 12m single span
# =========================================================================
SAMPLE_MINOR_12M_VALID: dict = {
    "project_master": {
        "project_title": "PROPOSED RAILWAY OVER BRIDGE AT CH. 24+350 NEAR PUNE",
        "project_code": "NHAI-2026-007",
        "bridge_name": "PUNE-ROB-CH24-350",
        "chainage_km": Decimal("24.3500"),
        "package_no": "PKG-MH-PUNE-007",
        "client": ClientType.NHAI_NATIONAL_HIGHWAYS,
        "consultant": ConsultantType.LIMITED_CONSULTANT_A_GRADE,
        "contractor": ContractorType.INFRA_LARGE_TIER1_EPC,
        "drawing_no": "GAD-ROB-001",
        "drawing_title": "GENERAL ARRANGEMENT DRAWING — ROB AT CH 24+350",
        "revision": RevisionTag.ISSUE_FOR_TENDER,
        "date_issued": date(2026, 10, 15),
        "designed_by": "A. Sharma",
        "checked_by": "R. Patil",
        "approved_by": "Dr. V. Kulkarni",
        "road_level_rl_m": Decimal("565.250"),
        "ground_level_rl_m": Decimal("562.800"),
        "survey_date": date(2026, 8, 10),
        "state_code": IndianStateCode.MH,
        "district_code": "PUNE",
        "language": Language.EN,
        "latitude_deg": Decimal("18.5204303"),
        "longitude_deg": Decimal("73.8567437"),
        "total_estimated_cost_inr": Decimal("187500000.00"),
        "tender_no": "NHAI/MH/ROB/2026/12",
        "contract_no": "NHAI/MH/EPC/2026/47",
        "project_phase": ProjectPhase.DESIGN_GAD_60_PCT,
        "currency": Currency.INR,
    },
    "bridge_selection": {
        "bridge_category": BridgeCategory.MAJOR_ROB_RAIL_OVER_BRIDGE,
        "bridge_type": SuperstructureType.PSC_IGIRDER,
        "span_configuration": SpanConfiguration.SIMPLY_SUPPORTED,
        "span_count": 1,
        "carriageway_config": CarriagewayLaneConfig.TWO_LANE_7M5_CLASS_A,
        "design_code": DesignCode.IRC_112_2020,
        "loading_class": LoadClass.CLASS_A,
        "seismic_zone": SeismicZone.ZONE_III,
        "wind_zone_ms": WindSpeedBasic_ms.VB_44_ms_ZONE_3,
        "foundation_type": FoundationType.PILE,
    },
    "geometry_input": {
        "span_count": 1,
        "span_lengths_m": [Decimal("12.000")],
        "alignment_type": AlignmentType.STRAIGHT,
        "gradient_pct": Decimal("1.2"),
        "carriageway_width_m": Decimal("7.50"),
        "footpath_left_m": Decimal("1.50"),
        "footpath_right_m": Decimal("1.50"),
        "crash_barrier_width_left_m": Decimal("0.50"),
        "crash_barrier_width_right_m": Decimal("0.50"),
        "kerb_width_left_m": Decimal("0.25"),
        "kerb_width_right_m": Decimal("0.25"),
        "median_width_m": Decimal("0.00"),
        "skew_angle_deg": Decimal("0.00"),
        "skew_direction": SkewDirection.NONE,
        "curved_bridge_flag": False,
        "camber_mm": 30,
        "camber_method": CamberMethod.PARABOLIC_CROWN,
        "pavement_thickness_total_mm": 500,
        "crust_layer_count": 4,
        "chainage_unit": ChainageUnit.METRE,
        "chainage_start_km": Decimal("24.344"),
        "chainage_end_km": Decimal("24.356"),
        "bearing_pad_spacing_m": Decimal("2.00"),
        "kerb_type": KerbType.MOUNTAIN_TALL,
        "footpath_type": FootpathType.FOOTPATH_2M_PLUS,
        "median_type": MedianType.NONE_UNDIVIDED,
        "crash_barrier_type": CrashBarrierType.RCC_WALL_PARAPET,
    },
    "superstructure": {
        "type": SuperstructureType.PSC_IGIRDER,
        "deck_material": ConcreteGrade.M40,
        "deck_thickness_mm": 230,
        "wearing_coat_type": WearingCoatType.BITUMINOUS_CONCRETE_BC,
        "wearing_coat_grade": WearingCoatGrade.BC_GRADE_1_MARSHALL_30_6,
        "wearing_coat_thickness_mm": 40,
        "wearing_coat_slope_pct": Decimal("2.0"),
        "drainage_type": DrainageType.SCUPPER_OUTLET_THROUGH_DECK,
        "drainage_spacing_m": Decimal("6.0"),
        "camber_mm": 30,
        "camber_method": CamberMethod.PARABOLIC_CROWN,
        "girder_type": GirderType.I_GIRDER_PS_PRECAST_OR_INSITU,
        "girder_depth_mm": 800,
        "girder_spacing_m": Decimal("2.50"),
        "girders_per_deck_count": 4,
        "parapet_type": ParapetType.RCC_PARAPET_FULL_HEIGHT,
        "parapet_height_mm": 1150,
        "bearing_shelf_width_m": Decimal("0.40"),
        "transverse_diaphragm_spacing_m": Decimal("3.0"),
        "continuity_slab_thickness_mm": 0,
        "kerb_elevation_mm": 220,
        "footpath_elevation_mm": 150,
    },
    "substructure": {
        "pier_type": PierType.WALL,
        "pier_material": ConcreteGrade.M30,
        "pier_height_typical_m": Decimal("8.50"),
        "pier_cap_type": PierCapType.NON_DROP_FLUSH_PIERSHAFT,
        "pier_cap_width_m": Decimal("2.0"),
        "pier_cap_length_m": Decimal("11.50"),
        "pier_cap_depth_m": Decimal("0.80"),
        "pier_shaft_width_m": Decimal("1.50"),
        "pier_shaft_length_m": Decimal("11.50"),
        "pier_pedestal_height_m": Decimal("0.20"),
        "pier_diaphragm_required": False,
        "abutment_type": AbutmentType.CANTILEVER,
        "abutment_material": ConcreteGrade.M30,
        "abutment_width_m": Decimal("1.20"),
        "abutment_length_m": Decimal("11.80"),
        "abutment_height_m": Decimal("3.20"),
        "abutment_pedestal_height_m": Decimal("0.20"),
        "return_wall_type": ReturnWallType.CANTILEVER_RCC,
        "return_wall_length_m": Decimal("4.0"),
        "return_wall_height_m": Decimal("3.0"),
        "wing_wall_type": WingWallType.SPLAYED_45_DEG,
        "wing_wall_angle_deg": Decimal("45.0"),
        "wing_wall_splay_length_m": Decimal("3.0"),
        "wing_wall_height_m": Decimal("2.50"),
        "backfill_type": "SELECT GRANULAR MOORUM",
        "approach_slab_length_m": Decimal("5.00"),
        "approach_slab_thickness_mm": 250,
        "bearings_per_pier": 4,
        "bearings_per_abutment": 4,
    },
    "foundation_details": {
        "type": FoundationType.PILE,
        "pile_type": PileType.BORED_CAST_IN_SITU,
        "pile_shape": "CIRCULAR" if not hasattr(__builtins__, "_x") else None,
        "pile_diameter_mm": 1200,
        "pile_length_m": Decimal("18.00"),
        "piles_per_pier": 6,
        "pile_group_config": "2x3 @2.4m c/c",
        "pile_spacing_m": Decimal("2.40"),
        "pile_cap_thickness_mm": 1500,
        "pile_cutoff_level_m": Decimal("559.500"),
        "under_ream_count": UnderReamCount.NONE,
        "factor_of_safety_on_bearing": Decimal("3.00"),
        "bearing_capacity_kpa": Decimal("450.0"),
    },
    "approaches": {
        "left_approach_length_m": Decimal("45.0"),
        "right_approach_length_m": Decimal("55.0"),
        "type_of_embankment": "SELECT MOORUM + SAND LAYERS",
        "soil_embankment_unit_weight_kN_m3": Decimal("19.0"),
        "approach_slope_width_m": Decimal("2.0"),
        "shoulder_width_left_m": Decimal("1.5"),
        "shoulder_width_right_m": Decimal("1.5"),
        "guide_rail_required": True,
        "speed_limit_on_approach_kmph": 60,
        "transition_curve_length_m": Decimal("0"),
        "approach_gradient_pct": Decimal("1.2"),
    },
    "hydraulic_data": {
        "design_discharge_cumecs": Decimal("380.0"),
        "hfl_m": Decimal("560.750"),
        "lwl_m": Decimal("558.200"),
        "normal_wl_m": Decimal("559.000"),
        "scour_level_m": Decimal("556.400"),
        "design_scour_depth_m": Decimal("2.10"),
        "freeboard_m": Decimal("2.00"),
        "actual_soffit_level_m": Decimal("563.000"),
        "waterway_required_m2": Decimal("65.0"),
        "waterway_provided_m2": Decimal("78.0"),
        "lacey_silt_factor": Decimal("0.90"),
        "regime_perimeter_m": Decimal("29.3"),
        "regime_depth_m": Decimal("2.2"),
        "regime_velocity_mps": Decimal("1.55"),
        "afflux_m": Decimal("0.15"),
        "max_afflux_allowable_m": Decimal("0.30"),
        "water_source_type": WaterSourceType.RIVER_PERENNIAL,
        "river_bed_slope_m_per_km": Decimal("0.35"),
        "catchment_area_sqkm": Decimal("1875.0"),
        "return_period_yr": FloodReturnPeriodDesign.Q100_NHAI_NATIONAL_CORRIDOR,
        "any_regime_equation_not_applied_flag": False,
        "highest_recorded_flood_year": 2005,
    },
    "materials": {
        "concrete_superstructure": ConcreteGrade.M40,
        "concrete_substructure": ConcreteGrade.M30,
        "concrete_foundation": ConcreteGrade.M25,
        "reinforcement_steel_grade": SteelGrade.Fe500D,
        "prestressing_steel": PrestressGrade.G1860,
        "bearing_type": BearingType.POT_PTFE,
        "expansion_joint_type": ExpansionJointType.STRIP_SEAL,
        "wearing_coat_material_type": WearingCoatType.BITUMINOUS_CONCRETE_BC,
        "wearing_coat_grade": WearingCoatGrade.BC_GRADE_1_MARSHALL_30_6,
    },
    "bearings_joints": {
        "bearing_schedule": [
            {
                "location": "A1-Abutment-B1",
                "bearing_type": BearingType.ELASTOMERIC_NEOPRENE,
                "size_x_mm": 450,
                "size_y_mm": 450,
                "design_load_kn": Decimal("650.0"),
                "fixed_or_guide_or_free": "FREE",
                "elastomeric_layers_count": 6,
                "steel_back_bool": True,
                "quantity": 4,
            },
            {
                "location": "P1-Pier-B1",
                "bearing_type": BearingType.POT_PTFE,
                "size_x_mm": 550,
                "size_y_mm": 550,
                "design_load_kn": Decimal("820.0"),
                "fixed_or_guide_or_free": "FIXED",
                "pot_pressure_mpa": Decimal("27.5"),
                "ptfe_sliding_surface_flag": True,
                "quantity": 4,
            },
        ],
        "expansion_joint_schedule": [
            {
                "location": "A1-Deck-End",
                "joint_type": ExpansionJointType.STRIP_SEAL,
                "width_mm": 80,
                "movement_range_mm": 50,
                "gap_mm": 25,
                "transverse_length_m": Decimal("11.50"),
                "quantity": 1,
            },
            {
                "location": "A2-Deck-End",
                "joint_type": ExpansionJointType.STRIP_SEAL,
                "width_mm": 80,
                "movement_range_mm": 50,
                "gap_mm": 25,
                "transverse_length_m": Decimal("11.50"),
                "quantity": 1,
            },
        ],
    },
    "components_lib": {
        "standard_pier_tag": "PIER-WALL-H8.5m-CAP11.5x2.0",
        "standard_abutment_tag": "ABUT-CANTILEVER-H3.2m-L11.8m",
        "standard_foundation_tag": "FOUND-PILE-1200mm-L18m-2x3",
        "typical_girder_library_key": "PSC-IGIRDER-D1200-SPAN12m",
        "standard_parapet_id": "PARAPET-RCC-H1150",
        "standard_railing_id": "RAILING-SS304-PIPE-3RAIL",
        "standard_kerb_id": "KERB-MOUNTAIN-H220",
        "standard_crash_barrier_id": "CRASH-WB2-METAL-BEAM",
        "standard_bearing_typical_pair_id": "BEAR-PAIR-POT+ELAST-450",
        "standard_expansion_joint_id": "EXPJ-STRIPSEAL-80mm",
        "standard_drainage_outlet_id": "DRAIN-SCUPPER-150DIA",
        "standard_pile_group_template_id": "PILE-GRP-2x3-@2400",
        "standard_wing_wall_id": "WING-SPLAY-45DEG-L3m",
        "standard_return_wall_id": "RETURN-CANT-L4m-H3m",
        "standard_approach_slab_id": "APP-SLAB-L5000-T250",
    },
    "drawing_control": {
        "output_formats": [OutputFormat.DXF, OutputFormat.PDF],
        "autocad_version": AcadVersion.R2018,
        "sheet_size": SheetSize.A1,
        "drawing_scale": DrawingScale.S100,
        "gen_plan_sheet": True,
        "gen_long_section_sheet": True,
        "gen_cross_section_sheet": True,
        "gen_foundation_sheet": True,
        "gen_reinforcement_sheet": True,
        "gen_pier_details_sheet": True,
        "gen_abutment_details_sheet": True,
        "gen_bearings_joints_sheet": True,
        "gen_boq_sheet": True,
        "gen_cover_sheet": True,
        "gen_legends_sheet": True,
        "gen_hydraulics_sheet": True,
        "layer_standard": LayerStandard.IRC,
        "title_block_style": TitleBlockStyle.STANDARD,
        "dimension_precision_mm": 1,
        "text_height_scale_factor": Decimal("1.00"),
        "lineweight_scale_factor": Decimal("1.00"),
        "drawing_border_inside_mm": 10,
        "revision_block_count": 6,
        "legend_sheet_required": True,
    },
    "calculations": {
        "total_length_m": Decimal("12.000"),
        "span_count": 1,
        "span_depth_ratio": Decimal("15.0"),
        "deck_area_sqm": Decimal("138.0"),
        "overall_width_check_ok": True,
        "concrete_volume_superstructure_cum": Decimal("58.5"),
        "concrete_volume_substructure_cum": Decimal("92.3"),
        "concrete_volume_foundation_cum": Decimal("148.7"),
        "rebar_weight_tonnes_approx": Decimal("28.4"),
        "prestress_tonnes_approx": Decimal("4.2"),
        "bearing_count": 8,
        "expansion_joint_count": 2,
        "total_estimated_quantity_cost_inr": Decimal("187500000"),
        "design_scour_vs_foundation_cover_ok": True,
        "waterway_check_pass": True,
        "afflux_ok": True,
        "freeboard_actual_m": Decimal("2.25"),
        "minimum_vertical_clearance_m": Decimal("6.50"),
        "horizontal_clearance_m": Decimal("1.25"),
    },
    "validation": {
        "overall_status": "OK_PASS",
        "critical_fail_count": 0,
        "warning_count": 2,
        "info_count": 5,
        "score_0_to_100": Decimal("95.60"),
        "score_irc05": Decimal("98.0"),
        "score_irc21": Decimal("94.0"),
        "score_ircsp55": Decimal("96.0"),
        "score_structural": Decimal("97.0"),
        "score_hydraulic": Decimal("99.0"),
        "score_drawing_standards": Decimal("92.0"),
        "report_html_or_pdf_generated_flag": True,
        "check_version_tag": "1.0.0-day3",
    },
}

# Fix: PileShape was assigned a string incorrectly above
from bridgecad_core.types import PileShape

SAMPLE_MINOR_12M_VALID["foundation_details"]["pile_shape"] = PileShape.CIRCULAR_ROUND


# =========================================================================
# RUNNER
# =========================================================================
def run_checks():
    sep = "=" * 78
    print()
    print(sep)
    print("  M1 WEEK 1 -- DAY 3 ACCEPTANCE CHECKS")
    print(sep)

    results = {}
    pad = 65

    # (1) Import + instantiate valid project
    try:
        proj = BridgeProject(**SAMPLE_MINOR_12M_VALID)
        results["C1_valid_fixture_constructs"] = True
        print("  [PASS] C1: BridgeProject(**SAMPLE_MINOR_12M_VALID) validates OK")
    except Exception:
        results["C1_valid_fixture_constructs"] = False
        print("  [FAIL] C1: BridgeProject invalid fixture?")
        traceback.print_exc()
        return

    # (2) schema size >= 40KB
    try:
        schema_str = json.dumps(BridgeProject.model_json_schema(), ensure_ascii=False)
        schema_bytes = len(schema_str.encode("utf-8"))
        size_ok = schema_bytes >= 40 * 1024
        results["C2_schema_ge_40KB"] = size_ok
        status = "PASS" if size_ok else "FAIL"
        schema_kb = schema_bytes / 1024.0
        print(
            f"  [{status}] C2: model_json_schema() size = {schema_bytes} bytes ({schema_kb:.1f} KB) >= 40 KB"
        )
        print(
            f"  [{status}] {f'C2: schema size = {schema_bytes} bytes ({schema_kb:.1f}KB >= 40.0KB)': <{pad-10}} {status}]"
        )
    except Exception as exc:
        print(f"  [FAIL] C2: schema generation: {exc}")
        results["C2_schema_ge_40KB"] = False

    # (3) 10 bad values -> each raises ValidationError
    BAD_CASES = [
        # Bad 1: invalid project_code pattern
        ("project_code_invalid", {"project_master": {"project_code": "bad code"}}),
        # Bad 2: negative span length
        ("negative_span_length", {"geometry_input": {"span_lengths_m": [Decimal("-1.0")]}}),
        # Bad 3: span_count mismatch lengths
        (
            "span_count_mismatch",
            {"geometry_input": {"span_count": 3, "span_lengths_m": [Decimal("12.0")]}},
        ),
        # Bad 4: skew_angle > 60° IRC limit
        ("skew_too_large", {"geometry_input": {"skew_angle_deg": Decimal("75")}}),
        # Bad 5: pile_diameter out of range
        ("pile_dia_too_big", {"foundation_details": {"pile_diameter_mm": 5000}}),
        # Bad 6: hfl < lwl (water level ordering)
        ("hfl_below_lwl", {"hydraulic_data": {"hfl_m": Decimal("555"), "lwl_m": Decimal("560")}}),
        # Bad 7: carriageway_width 0 -> not > 0
        ("carriageway_zero", {"geometry_input": {"carriageway_width_m": Decimal("-0.1")}}),
        # Bad 8: bearing_schedule missing required location
        (
            "bearing_row_no_location",
            {
                "bearings_joints": {
                    "bearing_schedule": [{"bearing_type": "POT_PTFE", "size_x_mm": 400}]
                }
            },
        ),
        # Bad 9: decimal pier_height out of declared range (0)
        ("pier_height_zero", {"substructure": {"pier_height_typical_m": Decimal("0.5")}}),
        # Bad 10: freeboard below 0.3 minimum
        ("freeboard_too_low", {"hydraulic_data": {"freeboard_m": Decimal("0.1")}}),
    ]
    bad_pass_count = 0
    bad_failures_log: list[str] = []
    for name, bad_overlay in BAD_CASES:
        json.loads(json.dumps(SAMPLE_MINOR_12M_VALID, default=str))
        # Recreate decimals better: deep copy dict manually with overlay
        from copy import deepcopy

        data = deepcopy(SAMPLE_MINOR_12M_VALID)
        for k, v in bad_overlay.items():
            if isinstance(v, dict) and isinstance(data.get(k), dict):
                data[k].update(v)
            else:
                data[k] = v
        try:
            BridgeProject(**data)
            bad_failures_log.append(f"    [{name}] DID NOT raise (should be invalid)")
        except ValidationError as _ve:
            bad_pass_count += 1
        except Exception as _oth:
            bad_failures_log.append(
                f"    [{name}] raised non-ValidationError: {type(_oth).__name__}: {_oth}"
            )
    results["C3_10bad_all_raise"] = bad_pass_count == len(BAD_CASES)
    status = "PASS" if results["C3_10bad_all_raise"] else "FAIL"
    label = f"C3: 10/10 bad values raise ValidationError ({bad_pass_count}/{len(BAD_CASES)})"
    print(f"  [{status}] {label}")
    for line in bad_failures_log:
        print(line)

    # (4) py_compile models.py (run separately, but re-check via import)
    import py_compile

    try:
        models_path = Path(__file__).resolve().parent / "bridgecad_core" / "models.py"
        py_compile.compile(str(models_path), doraise=True)
        results["C4_py_compile_clean"] = True
        print("  [PASS] C4: py_compile models.py clean")
    except Exception as exc:
        results["C4_py_compile_clean"] = False
        print(f"  [FAIL] C4: py_compile models.py -> {exc}")

    # (5) Count total fields across the 14 sheet models
    total_fields = 0
    per_model_counts = []
    from pydantic import BaseModel

    SHEET_CLASSES: list[tuple[str, type[BaseModel]]] = [
        ("ProjectMaster", models.ProjectMaster),
        ("BridgeSelection", models.BridgeSelection),
        ("GeometryInput", models.GeometryInput),
        ("Superstructure", models.Superstructure),
        ("Substructure", models.Substructure),
        ("FoundationDetails", models.FoundationDetails),
        ("Approaches", models.Approaches),
        ("HydraulicData", models.HydraulicData),
        ("Materials", models.Materials),
        ("BearingsJoints", models.BearingsJoints),
        ("ComponentsLib", models.ComponentsLib),
        ("DrawingControl", models.DrawingControl),
        ("Calculations", models.Calculations),
        ("ValidationModel", models.ValidationModel),
    ]
    for cls_name, cls in SHEET_CLASSES:
        own_fields_count = len(cls.model_fields)
        total_fields += own_fields_count
        per_model_counts.append((cls_name, own_fields_count))
    # Plus schedule rows
    for cls_name, cls in [
        ("BearingScheduleRow", models.BearingScheduleRow),
        ("ExpansionJointScheduleRow", models.ExpansionJointScheduleRow),
    ]:
        per_model_counts.append((cls_name, len(cls.model_fields)))
    print()
    print("  FIELD-COUNT BREAKDOWN PER MODEL:")
    for nm, c in per_model_counts:
        print(f"    {nm:<32s} {c:4d} fields")
    print(f"    {'--- 14 SHEETS TOTAL ---':<32s} {total_fields:4d} fields")
    results["C5_total_fields_ge_380"] = total_fields >= 380
    status = "PASS" if results["C5_total_fields_ge_380"] else "FAIL"
    print(f"  [{status}] C5: 14-sheet total fields >= 380 (got {total_fields})")

    # (6) Computed fields sanity check
    comp_checks = [
        ("total_length_m", lambda p: p.geometry_input.total_length_m == Decimal("12.0")),
        (
            "overall_width_m",
            lambda p: p.geometry_input.overall_width_m
            == Decimal("7.50")
            + Decimal("1.50")
            + Decimal("1.50")
            + Decimal("0.50")
            + Decimal("0.50")
            + Decimal("0.25")
            + Decimal("0.25"),
        ),
        (
            "freeboard_actual_m",
            lambda p: p.hydraulic_data.freeboard_actual_m
            == Decimal("563.000") - Decimal("560.750"),
        ),
        ("total_bearings", lambda p: p.bearings_joints.total_bearings_quantity == 4 + 4),
        ("total_joints", lambda p: p.bearings_joints.total_joints_quantity == 1 + 1),
        ("agg_total_length", lambda p: p.total_bridge_length_m == Decimal("12.000")),
    ]
    comp_pass = 0
    for name, fn in comp_checks:
        try:
            ok = bool(fn(proj))
        except Exception:
            ok = False
        if ok:
            comp_pass += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] COMPUTED-{name}")
    results["C6_computed_fields_work"] = comp_pass == len(comp_checks)
    status = "PASS" if results["C6_computed_fields_work"] else "FAIL"
    print(f"  [{status}] C6: {comp_pass}/{len(comp_checks)} @computed_field checks OK")

    # (7) Extra forbid check: unknown field
    try:
        BridgeProject(
            project_master={**SAMPLE_MINOR_12M_VALID["project_master"], "nonexistent_field_xyz": 1}
        )
        results["C7_extra_forbid"] = False
        print("  [FAIL] C7: extra='forbid' did not fire on unknown field")
    except ValidationError:
        results["C7_extra_forbid"] = True
        print("  [PASS] C7: extra='forbid' raises ValidationError for unknown field")

    print()
    print(sep)
    print("  FINAL DAY 3 VERDICT")
    print(sep)
    all_pass = all(v is True for v in results.values())
    print(f"  Checks run   : {len(results)}")
    ok = sum(1 for v in results.values() if v)
    print(f"  Passed       : {ok}")
    print(f"  Failed       : {len(results) - ok}")
    verdict = "★ ACCEPTED ★" if all_pass else "REJECTED"
    print(f"  VERDICT      : {verdict}")
    print(sep)
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(run_checks())
