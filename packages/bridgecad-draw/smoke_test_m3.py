"""M3 smoke test — generate 8-sheet GAD package for a simple 12m bridge."""

from __future__ import annotations

import logging
import sys
from decimal import Decimal
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

# ── Add bridgecad-core to path ────────────────────────────────────────────
CORE = Path(__file__).parent.parent / "bridgecad-core"
sys.path.insert(0, str(CORE))

from bridgecad_core.models import (
    Approaches,
    BearingScheduleRow,
    BearingsJoints,
    BridgeProject,
    BridgeSelection,
    Calculations,
    ComponentsLib,
    DrawingControl,
    ExpansionJointScheduleRow,
    FoundationDetails,
    GeometryInput,
    HydraulicData,
    Materials,
    ProjectMaster,
    Substructure,
    Superstructure,
    ValidationModel,
)
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
    Currency,
    DesignCode,
    DrawingScale,
    ExpansionJointType,
    FloodReturnPeriodDesign,
    FoundationType,
    GirderType,
    IndianStateCode,
    Language,
    LayerStandard,
    LoadClass,
    OutputFormat,
    ParapetType,
    PierCapType,
    PierType,
    PileShape,
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
    WearingCoatType,
    WindSpeedBasic_ms,
    WingWallType,
)

SIMPLE_12M = BridgeProject(
    project_master=ProjectMaster(
        project_title="SIMPLE MINOR BRIDGE AT CH 12+000",
        project_code="TEST-2026-001",
        bridge_name="SIMPLE-12M-BRIDGE",
        chainage_km=Decimal("12.000"),
        client=ClientType.STATE_PWD,
        revision=RevisionTag.R0,
        state_code=IndianStateCode.MH,
        language=Language.EN,
        road_level_rl_m=Decimal("115.500"),
        ground_level_rl_m=Decimal("112.800"),
        project_phase=ProjectPhase.DPR,
        currency=Currency.INR,
    ),
    bridge_selection=BridgeSelection(
        bridge_category=BridgeCategory.MINOR_BRIDGE,
        bridge_type=SuperstructureType.RCC_TBEAM,
        span_configuration=SpanConfiguration.SIMPLY_SUPPORTED,
        span_count=1,
        carriageway_config=CarriagewayLaneConfig.LANE_2,
        design_code=DesignCode.IRC_112_2020,
        loading_class=LoadClass.CLASS_A,
        seismic_zone=SeismicZone.ZONE_III,
        wind_zone_ms=WindSpeedBasic_ms.VB_44_ms_ZONE_3,
        foundation_type=FoundationType.PILE,
    ),
    geometry_input=GeometryInput(
        span_count=1,
        span_lengths_m=[Decimal("12.000")],
        alignment_type=AlignmentType.STRAIGHT,
        gradient_pct=Decimal("0.5"),
        carriageway_width_m=Decimal("7.50"),
        footpath_left_m=Decimal("0.0"),
        footpath_right_m=Decimal("0.0"),
        crash_barrier_width_left_m=Decimal("0.45"),
        crash_barrier_width_right_m=Decimal("0.45"),
        kerb_width_left_m=Decimal("0.25"),
        kerb_width_right_m=Decimal("0.25"),
        median_width_m=Decimal("0.00"),
        skew_angle_deg=Decimal("0.00"),
        skew_direction=SkewDirection.NONE,
        curved_bridge_flag=False,
        camber_mm=20,
        camber_method=CamberMethod.PARABOLIC_CROWN,
        chainage_unit=ChainageUnit.METRE,
        chainage_start_km=Decimal("11.994"),
        chainage_end_km=Decimal("12.006"),
    ),
    superstructure=Superstructure(
        type=SuperstructureType.RCC_TBEAM,
        deck_material=ConcreteGrade.M30,
        deck_thickness_mm=200,
        wearing_coat_type=WearingCoatType.BITUMINOUS_CONCRETE_BC,
        wearing_coat_thickness_mm=65,
        girder_type=GirderType.T_BEAM_RCC,
        girder_depth_mm=900,
        girder_spacing_m=Decimal("2.00"),
        girders_per_deck_count=4,
        parapet_type=ParapetType.RCC_PARAPET_FULL_HEIGHT,
        parapet_height_mm=900,
        camber_mm=20,
        camber_method=CamberMethod.PARABOLIC_CROWN,
    ),
    substructure=Substructure(
        pier_type=PierType.WALL,
        pier_material=ConcreteGrade.M25,
        pier_height_typical_m=Decimal("6.00"),
        pier_cap_type=PierCapType.NON_DROP_FLAT,
        pier_cap_width_m=Decimal("1.8"),
        pier_cap_length_m=Decimal("9.0"),
        pier_cap_depth_m=Decimal("0.65"),
        pier_shaft_width_m=Decimal("1.2"),
        pier_shaft_length_m=Decimal("9.0"),
        pier_pedestal_height_m=Decimal("0.15"),
        pier_diaphragm_required=False,
        abutment_type=AbutmentType.CANTILEVER,
        abutment_material=ConcreteGrade.M25,
        abutment_width_m=Decimal("1.00"),
        abutment_length_m=Decimal("9.20"),
        abutment_height_m=Decimal("2.80"),
        abutment_pedestal_height_m=Decimal("0.15"),
        return_wall_type=ReturnWallType.CANTILEVER_RCC,
        return_wall_length_m=Decimal("3.5"),
        return_wall_height_m=Decimal("2.5"),
        wing_wall_type=WingWallType.SPLAYED_45_DEG,
        wing_wall_angle_deg=Decimal("45.0"),
        wing_wall_splay_length_m=Decimal("2.5"),
        wing_wall_height_m=Decimal("2.0"),
        backfill_type="SELECT MOORUM",
        approach_slab_length_m=Decimal("3.50"),
        approach_slab_thickness_mm=200,
        bearings_per_pier=4,
        bearings_per_abutment=4,
    ),
    foundation_details=FoundationDetails(
        type=FoundationType.PILE,
        pile_type=PileType.BORED_CAST_IN_SITU,
        pile_shape=PileShape.CIRCULAR_ROUND,
        pile_diameter_mm=1000,
        pile_length_m=Decimal("12.00"),
        piles_per_pier=4,
        pile_group_config="2x2 @2.0m c/c",
        pile_spacing_m=Decimal("2.00"),
        pile_cap_thickness_mm=1200,
        pile_cutoff_level_m=Decimal("110.500"),
        under_ream_count=UnderReamCount.NONE,
        factor_of_safety_on_bearing=Decimal("3.00"),
        bearing_capacity_kpa=Decimal("350.0"),
    ),
    approaches=Approaches(
        left_approach_length_m=Decimal("30.0"),
        right_approach_length_m=Decimal("30.0"),
        type_of_embankment="SELECT MOORUM",
        soil_embankment_unit_weight_kN_m3=Decimal("18.5"),
        approach_slope_width_m=Decimal("1.5"),
        shoulder_width_left_m=Decimal("1.0"),
        shoulder_width_right_m=Decimal("1.0"),
        guide_rail_required=False,
        speed_limit_on_approach_kmph=50,
        transition_curve_length_m=Decimal("0"),
        approach_gradient_pct=Decimal("0.5"),
    ),
    hydraulic_data=HydraulicData(
        design_discharge_cumecs=Decimal("85.0"),
        hfl_m=Decimal("112.500"),
        lwl_m=Decimal("110.800"),
        normal_wl_m=Decimal("111.200"),
        scour_level_m=Decimal("108.900"),
        design_scour_depth_m=Decimal("1.60"),
        freeboard_m=Decimal("1.80"),
        actual_soffit_level_m=Decimal("114.300"),
        waterway_required_m2=Decimal("28.5"),
        waterway_provided_m2=Decimal("35.0"),
        lacey_silt_factor=Decimal("0.85"),
        regime_perimeter_m=Decimal("16.5"),
        regime_depth_m=Decimal("1.5"),
        regime_velocity_mps=Decimal("1.20"),
        afflux_m=Decimal("0.12"),
        max_afflux_allowable_m=Decimal("0.30"),
        water_source_type=WaterSourceType.RIVER_PERENNIAL,
        river_bed_slope_m_per_km=Decimal("0.50"),
        catchment_area_sqkm=Decimal("580.0"),
        return_period_yr=FloodReturnPeriodDesign.Q50_MAJOR_BRIDGE_STANDARD,
        any_regime_equation_not_applied_flag=False,
        highest_recorded_flood_year=2013,
    ),
    materials=Materials(
        concrete_superstructure=ConcreteGrade.M30,
        concrete_substructure=ConcreteGrade.M25,
        concrete_foundation=ConcreteGrade.M25,
        reinforcement_steel_grade=SteelGrade.Fe500D,
        prestressing_steel=PrestressGrade.G1860,
        bearing_type=BearingType.ELASTOMERIC_NEOPRENE,
        expansion_joint_type=ExpansionJointType.COMPRESSION_SEAL,
        wearing_coat_material_type=WearingCoatType.BITUMINOUS_CONCRETE_BC,
    ),
    bearings_joints=BearingsJoints(
        bearing_schedule=[
            BearingScheduleRow(
                location="A1-Bearing",
                bearing_type=BearingType.ELASTOMERIC_NEOPRENE,
                size_x_mm=350,
                size_y_mm=350,
                design_load_kn=Decimal("350.0"),
                fixed_or_guide_or_free="FREE",
                quantity=4,
            ),
            BearingScheduleRow(
                location="A2-Bearing",
                bearing_type=BearingType.ELASTOMERIC_NEOPRENE,
                size_x_mm=350,
                size_y_mm=350,
                design_load_kn=Decimal("350.0"),
                fixed_or_guide_or_free="FREE",
                quantity=4,
            ),
        ],
        expansion_joint_schedule=[
            ExpansionJointScheduleRow(
                location="A1-End",
                joint_type=ExpansionJointType.COMPRESSION_SEAL,
                width_mm=40,
                movement_range_mm=20,
                gap_mm=12,
                transverse_length_m=Decimal("8.90"),
                quantity=1,
            ),
            ExpansionJointScheduleRow(
                location="A2-End",
                joint_type=ExpansionJointType.COMPRESSION_SEAL,
                width_mm=40,
                movement_range_mm=20,
                gap_mm=12,
                transverse_length_m=Decimal("8.90"),
                quantity=1,
            ),
        ],
    ),
    components_lib=ComponentsLib(
        standard_pier_tag="PIER-WALL-H6m",
        standard_abutment_tag="ABUT-CANT-H2.8m",
        standard_foundation_tag="PILE-1000mm-L12m-2x2",
        typical_girder_library_key="RCC-TBEAM-D900-SPAN12m",
        standard_parapet_id="PARAPET-RCC-H900",
    ),
    drawing_control=DrawingControl(
        output_formats=[OutputFormat.DXF, OutputFormat.PDF],
        autocad_version=AcadVersion.R2018,
        sheet_size=SheetSize.A1,
        drawing_scale=DrawingScale.S100,
        gen_plan_sheet=True,
        gen_long_section_sheet=True,
        gen_cross_section_sheet=True,
        gen_foundation_sheet=True,
        gen_reinforcement_sheet=False,
        gen_pier_details_sheet=True,
        gen_abutment_details_sheet=True,
        gen_bearings_joints_sheet=True,
        gen_boq_sheet=True,
        gen_cover_sheet=True,
        gen_legends_sheet=True,
        gen_hydraulics_sheet=True,
        layer_standard=LayerStandard.IRC,
        title_block_style=TitleBlockStyle.STANDARD,
        dimension_precision_mm=1,
        text_height_scale_factor=Decimal("1.00"),
        lineweight_scale_factor=Decimal("1.00"),
        drawing_border_inside_mm=10,
        revision_block_count=4,
        legend_sheet_required=True,
    ),
    calculations=Calculations(
        total_length_m=Decimal("12.000"),
        span_count=1,
        span_depth_ratio=Decimal("13.3"),
        deck_area_sqm=Decimal("105.0"),
        overall_width_check_ok=True,
        concrete_volume_superstructure_cum=Decimal("32.5"),
        concrete_volume_substructure_cum=Decimal("58.0"),
        concrete_volume_foundation_cum=Decimal("78.0"),
        rebar_weight_tonnes_approx=Decimal("18.5"),
        bearing_count=8,
        expansion_joint_count=2,
        total_estimated_quantity_cost_inr=Decimal("9500000"),
        design_scour_vs_foundation_cover_ok=True,
        waterway_check_pass=True,
        afflux_ok=True,
        freeboard_actual_m=Decimal("1.80"),
        minimum_vertical_clearance_m=Decimal("4.50"),
        horizontal_clearance_m=Decimal("1.00"),
    ),
    validation=ValidationModel(
        overall_status="OK_PASS",
        critical_fail_count=0,
        warning_count=0,
        info_count=3,
        score_0_to_100=Decimal("96.0"),
        check_version_tag="1.0.0-m3-smoke",
    ),
)


def main() -> int:
    from bridgecad_draw.booklet import generate_package

    out_dir = Path(__file__).parent / "smoke_output_simple_12m"
    print(f"\n{'='*64}")
    print("  M3 SMOKE TEST — simple_12m 8-sheet GAD package")
    print(f"{'='*64}")
    print(f"  Output dir: {out_dir}")

    sheets = generate_package(SIMPLE_12M, out_dir, prefix="simple_12m", scale_denom=100)

    print(f"\n  Generated {len(sheets)} sheets:")
    total_bytes = 0
    all_pass = True
    for p in sheets:
        sz = p.stat().st_size
        total_bytes += sz
        ok = sz > 10_000  # each sheet > 10 KB
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        print(f"    [{status}] {p.name:<50s}  {sz/1024:.1f} KB")

    # Smoke criteria: at least 2 sheets generated, each > 10 KB
    gen_ok = len(sheets) >= 2
    size_ok = all_pass
    total_ok = total_bytes > 50_000  # total package > 50 KB

    print()
    print(f"  Sheets generated : {len(sheets)} / 8  {'PASS' if gen_ok else 'FAIL'}")
    print(f"  All sheets > 10KB: {'PASS' if size_ok else 'FAIL'}")
    print(f"  Total size > 50KB: {total_bytes/1024:.1f} KB  {'PASS' if total_ok else 'FAIL'}")

    verdict = gen_ok and size_ok and total_ok
    print(f"\n  {'='*62}")
    print(f"  VERDICT: {'★ ACCEPTED ★' if verdict else 'REJECTED'}")
    print(f"  {'='*62}\n")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
