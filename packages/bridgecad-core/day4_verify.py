"""Day 4 acceptance verifier — geometry modules + validation engine (8 checks)."""
from __future__ import annotations

import sys
import traceback
from datetime import date
from decimal import Decimal

from bridgecad_core.geometry.cross_section import compute_cross_section_geometry
from bridgecad_core.geometry.foundation import compute_pile_group_layout
from bridgecad_core.geometry.long_section import compute_long_section_geometry
from bridgecad_core.geometry.plan import compute_plan_geometry
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
    ValidationSeverity,
    WaterSourceType,
    WearingCoatGrade,
    WearingCoatType,
    WindSpeedBasic_ms,
    WingWallType,
)
from bridgecad_core.validation import run_all

# ── Day-3 SAMPLE fixture reconstructed ──────────────────────────────────────
SAMPLE = BridgeProject(
    project_master=ProjectMaster(
        project_title="PROPOSED RAILWAY OVER BRIDGE AT CH. 24+350 NEAR PUNE",
        project_code="NHAI-2026-007", bridge_name="PUNE-ROB-CH24-350",
        chainage_km=Decimal("24.3500"), package_no="PKG-MH-PUNE-007",
        client=ClientType.NHAI_NATIONAL_HIGHWAYS,
        consultant=ConsultantType.LIMITED_CONSULTANT_A_GRADE,
        contractor=ContractorType.INFRA_LARGE_TIER1_EPC,
        drawing_no="GAD-ROB-001",
        drawing_title="GENERAL ARRANGEMENT DRAWING — ROB AT CH 24+350",
        revision=RevisionTag.ISSUE_FOR_TENDER,
        date_issued=date(2026,10,15), designed_by="A. Sharma",
        checked_by="R. Patil", approved_by="Dr. V. Kulkarni",
        road_level_rl_m=Decimal("565.250"), ground_level_rl_m=Decimal("562.800"),
        survey_date=date(2026,8,10), state_code=IndianStateCode.MH,
        district_code="PUNE", language=Language.EN,
        latitude_deg=Decimal("18.5204303"), longitude_deg=Decimal("73.8567437"),
        total_estimated_cost_inr=Decimal("187500000.00"),
        tender_no="NHAI/MH/ROB/2026/12", contract_no="NHAI/MH/EPC/2026/47",
        project_phase=ProjectPhase.DESIGN_GAD_60_PCT, currency=Currency.INR,
    ),
    bridge_selection=BridgeSelection(
        bridge_category=BridgeCategory.MAJOR_ROB_RAIL_OVER_BRIDGE,
        bridge_type=SuperstructureType.PSC_IGIRDER,
        span_configuration=SpanConfiguration.SIMPLY_SUPPORTED,
        span_count=1,
        carriageway_config=CarriagewayLaneConfig.TWO_LANE_7M5_CLASS_A,
        design_code=DesignCode.IRC_112_2020, loading_class=LoadClass.CLASS_A,
        seismic_zone=SeismicZone.ZONE_III,
        wind_zone_ms=WindSpeedBasic_ms.VB_44_ms_ZONE_3,
        foundation_type=FoundationType.PILE,
    ),
    geometry_input=GeometryInput(
        span_count=1, span_lengths_m=[Decimal("12.000")],
        alignment_type=AlignmentType.STRAIGHT, gradient_pct=Decimal("1.2"),
        carriageway_width_m=Decimal("7.50"),
        footpath_left_m=Decimal("1.50"), footpath_right_m=Decimal("1.50"),
        crash_barrier_width_left_m=Decimal("0.50"),
        crash_barrier_width_right_m=Decimal("0.50"),
        kerb_width_left_m=Decimal("0.25"), kerb_width_right_m=Decimal("0.25"),
        median_width_m=Decimal("0.00"), skew_angle_deg=Decimal("0.00"),
        skew_direction=SkewDirection.NONE, curved_bridge_flag=False,
        camber_mm=30, camber_method=CamberMethod.PARABOLIC_CROWN,
        pavement_thickness_total_mm=500, crust_layer_count=4,
        chainage_unit=ChainageUnit.METRE,
        chainage_start_km=Decimal("24.344"), chainage_end_km=Decimal("24.356"),
        bearing_pad_spacing_m=Decimal("2.00"),
        kerb_type=KerbType.MOUNTAIN_TALL, footpath_type=FootpathType.FOOTPATH_2M_PLUS,
        median_type=MedianType.NONE_UNDIVIDED,
        crash_barrier_type=CrashBarrierType.RCC_WALL_PARAPET,
    ),
    superstructure=Superstructure(
        type=SuperstructureType.PSC_IGIRDER, deck_material=ConcreteGrade.M40,
        deck_thickness_mm=230,
        wearing_coat_type=WearingCoatType.BITUMINOUS_CONCRETE_BC,
        wearing_coat_grade=WearingCoatGrade.BC_GRADE_1_MARSHALL_30_6,
        wearing_coat_thickness_mm=40, wearing_coat_slope_pct=Decimal("2.0"),
        drainage_type=DrainageType.SCUPPER_OUTLET_THROUGH_DECK,
        drainage_spacing_m=Decimal("6.0"), camber_mm=30,
        camber_method=CamberMethod.PARABOLIC_CROWN,
        girder_type=GirderType.I_GIRDER_PS_PRECAST_OR_INSITU,
        girder_depth_mm=800, girder_spacing_m=Decimal("2.50"),
        girders_per_deck_count=4,
        parapet_type=ParapetType.RCC_PARAPET_FULL_HEIGHT,
        parapet_height_mm=1150, bearing_shelf_width_m=Decimal("0.40"),
        transverse_diaphragm_spacing_m=Decimal("3.0"),
        continuity_slab_thickness_mm=0, kerb_elevation_mm=220,
        footpath_elevation_mm=150,
    ),
    substructure=Substructure(
        pier_type=PierType.WALL, pier_material=ConcreteGrade.M30,
        pier_height_typical_m=Decimal("8.50"),
        pier_cap_type=PierCapType.NON_DROP_FLUSH_PIERSHAFT,
        pier_cap_width_m=Decimal("2.0"), pier_cap_length_m=Decimal("11.50"),
        pier_cap_depth_m=Decimal("0.80"), pier_shaft_width_m=Decimal("1.50"),
        pier_shaft_length_m=Decimal("11.50"), pier_pedestal_height_m=Decimal("0.20"),
        pier_diaphragm_required=False,
        abutment_type=AbutmentType.CANTILEVER, abutment_material=ConcreteGrade.M30,
        abutment_width_m=Decimal("1.20"), abutment_length_m=Decimal("11.80"),
        abutment_height_m=Decimal("3.20"), abutment_pedestal_height_m=Decimal("0.20"),
        return_wall_type=ReturnWallType.CANTILEVER_RCC,
        return_wall_length_m=Decimal("4.0"), return_wall_height_m=Decimal("3.0"),
        wing_wall_type=WingWallType.SPLAYED_45_DEG,
        wing_wall_angle_deg=Decimal("45.0"), wing_wall_splay_length_m=Decimal("3.0"),
        wing_wall_height_m=Decimal("2.50"),
        backfill_type="SELECT GRANULAR MOORUM",
        approach_slab_length_m=Decimal("5.00"), approach_slab_thickness_mm=250,
        bearings_per_pier=4, bearings_per_abutment=4,
    ),
    foundation_details=FoundationDetails(
        type=FoundationType.PILE, pile_type=PileType.BORED_CAST_IN_SITU,
        pile_shape=PileShape.CIRCULAR_ROUND, pile_diameter_mm=1200,
        pile_length_m=Decimal("18.00"), piles_per_pier=6,
        pile_group_config="2x3 @2.4m c/c", pile_spacing_m=Decimal("2.40"),
        pile_cap_thickness_mm=1500, pile_cutoff_level_m=Decimal("559.500"),
        under_ream_count=UnderReamCount.NONE,
        factor_of_safety_on_bearing=Decimal("3.00"),
        bearing_capacity_kpa=Decimal("450.0"),
    ),
    approaches=Approaches(
        left_approach_length_m=Decimal("45.0"),
        right_approach_length_m=Decimal("55.0"),
        type_of_embankment="SELECT MOORUM + SAND LAYERS",
        soil_embankment_unit_weight_kN_m3=Decimal("19.0"),
        approach_slope_width_m=Decimal("2.0"),
        shoulder_width_left_m=Decimal("1.5"), shoulder_width_right_m=Decimal("1.5"),
        guide_rail_required=True, speed_limit_on_approach_kmph=60,
        transition_curve_length_m=Decimal("0"),
        approach_gradient_pct=Decimal("1.2"),
    ),
    hydraulic_data=HydraulicData(
        design_discharge_cumecs=Decimal("380.0"), hfl_m=Decimal("560.750"),
        lwl_m=Decimal("558.200"), normal_wl_m=Decimal("559.000"),
        scour_level_m=Decimal("556.400"), design_scour_depth_m=Decimal("2.10"),
        freeboard_m=Decimal("2.00"), actual_soffit_level_m=Decimal("563.000"),
        waterway_required_m2=Decimal("65.0"), waterway_provided_m2=Decimal("78.0"),
        lacey_silt_factor=Decimal("0.90"), regime_perimeter_m=Decimal("29.3"),
        regime_depth_m=Decimal("2.2"), regime_velocity_mps=Decimal("1.55"),
        afflux_m=Decimal("0.15"), max_afflux_allowable_m=Decimal("0.30"),
        water_source_type=WaterSourceType.RIVER_PERENNIAL,
        river_bed_slope_m_per_km=Decimal("0.35"),
        catchment_area_sqkm=Decimal("1875.0"),
        return_period_yr=FloodReturnPeriodDesign.Q100_NHAI_NATIONAL_CORRIDOR,
        any_regime_equation_not_applied_flag=False, highest_recorded_flood_year=2005,
    ),
    materials=Materials(
        concrete_superstructure=ConcreteGrade.M40,
        concrete_substructure=ConcreteGrade.M30,
        concrete_foundation=ConcreteGrade.M25,
        reinforcement_steel_grade=SteelGrade.Fe500D,
        prestressing_steel=PrestressGrade.G1860,
        bearing_type=BearingType.POT_PTFE,
        expansion_joint_type=ExpansionJointType.STRIP_SEAL,
        wearing_coat_material_type=WearingCoatType.BITUMINOUS_CONCRETE_BC,
        wearing_coat_grade=WearingCoatGrade.BC_GRADE_1_MARSHALL_30_6,
    ),
    bearings_joints=BearingsJoints(
        bearing_schedule=[
            BearingScheduleRow(
                location="A1-Abutment-B1",
                bearing_type=BearingType.ELASTOMERIC_NEOPRENE,
                size_x_mm=450, size_y_mm=450,
                design_load_kn=Decimal("650.0"), fixed_or_guide_or_free="FREE",
                elastomeric_layers_count=6, steel_back_bool=True, quantity=4,
            ),
            BearingScheduleRow(
                location="P1-Pier-B1", bearing_type=BearingType.POT_PTFE,
                size_x_mm=550, size_y_mm=550,
                design_load_kn=Decimal("820.0"), fixed_or_guide_or_free="FIXED",
                pot_pressure_mpa=Decimal("27.5"), ptfe_sliding_surface_flag=True,
                quantity=4,
            ),
        ],
        expansion_joint_schedule=[
            ExpansionJointScheduleRow(
                location="A1-Deck-End", joint_type=ExpansionJointType.STRIP_SEAL,
                width_mm=80, movement_range_mm=50, gap_mm=25,
                transverse_length_m=Decimal("11.50"), quantity=1,
            ),
            ExpansionJointScheduleRow(
                location="A2-Deck-End", joint_type=ExpansionJointType.STRIP_SEAL,
                width_mm=80, movement_range_mm=50, gap_mm=25,
                transverse_length_m=Decimal("11.50"), quantity=1,
            ),
        ],
    ),
    components_lib=ComponentsLib(
        standard_pier_tag="PIER-WALL-H8.5m-CAP11.5x2.0",
        standard_abutment_tag="ABUT-CANTILEVER-H3.2m-L11.8m",
        standard_foundation_tag="FOUND-PILE-1200mm-L18m-2x3",
        typical_girder_library_key="PSC-IGIRDER-D1200-SPAN12m",
        standard_parapet_id="PARAPET-RCC-H1150",
        standard_railing_id="RAILING-SS304-PIPE-3RAIL",
        standard_kerb_id="KERB-MOUNTAIN-H220",
        standard_crash_barrier_id="CRASH-WB2-METAL-BEAM",
        standard_bearing_typical_pair_id="BEAR-PAIR-POT+ELAST-450",
        standard_expansion_joint_id="EXPJ-STRIPSEAL-80mm",
        standard_drainage_outlet_id="DRAIN-SCUPPER-150DIA",
        standard_pile_group_template_id="PILE-GRP-2x3-@2400",
        standard_wing_wall_id="WING-SPLAY-45DEG-L3m",
        standard_return_wall_id="RETURN-CANT-L4m-H3m",
        standard_approach_slab_id="APP-SLAB-L5000-T250",
    ),
    drawing_control=DrawingControl(
        output_formats=[OutputFormat.DXF, OutputFormat.PDF],
        autocad_version=AcadVersion.R2018, sheet_size=SheetSize.A1,
        drawing_scale=DrawingScale.S100,
        gen_plan_sheet=True, gen_long_section_sheet=True,
        gen_cross_section_sheet=True, gen_foundation_sheet=True,
        gen_reinforcement_sheet=True, gen_pier_details_sheet=True,
        gen_abutment_details_sheet=True, gen_bearings_joints_sheet=True,
        gen_boq_sheet=True, gen_cover_sheet=True, gen_legends_sheet=True,
        gen_hydraulics_sheet=True, layer_standard=LayerStandard.IRC,
        title_block_style=TitleBlockStyle.STANDARD, dimension_precision_mm=1,
        text_height_scale_factor=Decimal("1.00"),
        lineweight_scale_factor=Decimal("1.00"),
        drawing_border_inside_mm=10, revision_block_count=6,
        legend_sheet_required=True,
    ),
    calculations=Calculations(
        total_length_m=Decimal("12.000"), span_count=1,
        span_depth_ratio=Decimal("15.0"), deck_area_sqm=Decimal("138.0"),
        overall_width_check_ok=True,
        concrete_volume_superstructure_cum=Decimal("58.5"),
        concrete_volume_substructure_cum=Decimal("92.3"),
        concrete_volume_foundation_cum=Decimal("148.7"),
        rebar_weight_tonnes_approx=Decimal("28.4"),
        prestress_tonnes_approx=Decimal("4.2"), bearing_count=8,
        expansion_joint_count=2,
        total_estimated_quantity_cost_inr=Decimal("187500000"),
        design_scour_vs_foundation_cover_ok=True, waterway_check_pass=True,
        afflux_ok=True, freeboard_actual_m=Decimal("2.25"),
        minimum_vertical_clearance_m=Decimal("6.50"),
        horizontal_clearance_m=Decimal("1.25"),
    ),
    validation=ValidationModel(
        overall_status="OK_PASS", critical_fail_count=0,
        warning_count=2, info_count=5, score_0_to_100=Decimal("95.60"),
        score_irc05=Decimal("98.0"), score_irc21=Decimal("94.0"),
        score_ircsp55=Decimal("96.0"), score_structural=Decimal("97.0"),
        score_hydraulic=Decimal("99.0"), score_drawing_standards=Decimal("92.0"),
        report_html_or_pdf_generated_flag=True, check_version_tag="1.0.0-day4",
    ),
)


def run_checks() -> int:
    sep = "=" * 72
    print(); print(sep)
    print("  M1 WEEK 1 -- DAY 4 ACCEPTANCE CHECKS")
    print(sep)
    results: dict[str, bool] = {}

    # D4-C1 ── plan geometry: deck_corners == 4 ---------------------------
    try:
        plan = compute_plan_geometry(SAMPLE)
        ok = len(plan.deck_corners) == 4
        results["D4C1"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D4-C1: deck_corners == 4  (got {len(plan.deck_corners)})")
    except Exception:
        results["D4C1"] = False
        print("  [FAIL] D4-C1: compute_plan_geometry raised"); traceback.print_exc()

    # D4-C2 ── plan geometry: 0 piers for single span ---------------------
    try:
        ok = len(plan.pier_centrelines) == 0
        results["D4C2"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D4-C2: pier_centrelines == 0 for span_count=1  (got {len(plan.pier_centrelines)})")
    except Exception:
        results["D4C2"] = False; print("  [FAIL] D4-C2")

    # D4-C3 ── long section: soffit > scour level -------------------------
    try:
        ls = compute_long_section_geometry(SAMPLE)
        ok = ls.soffit_rl > ls.scour_level_rl
        results["D4C3"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D4-C3: soffit_rl {ls.soffit_rl:.3f} > scour_rl {ls.scour_level_rl:.3f}")
    except Exception:
        results["D4C3"] = False
        print("  [FAIL] D4-C3: compute_long_section raised"); traceback.print_exc()

    # D4-C4 ── long section: HFL < soffit ---------------------------------
    try:
        ok = ls.hfl_rl < ls.soffit_rl
        results["D4C4"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D4-C4: hfl_rl {ls.hfl_rl:.3f} < soffit_rl {ls.soffit_rl:.3f}  freeboard={ls.freeboard_m:.3f} m")
    except Exception:
        results["D4C4"] = False; print("  [FAIL] D4-C4")

    # D4-C5 ── cross section: camber peak at CL == 30 mm ------------------
    try:
        cs = compute_cross_section_geometry(SAMPLE)
        peak = cs.camber_y_at_x(0.0)
        ok = abs(peak - 30.0) < 0.001
        results["D4C5"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D4-C5: camber_y_at_x(0.0) == 30.0 mm  (got {peak:.4f} mm)")
    except Exception:
        results["D4C5"] = False
        print("  [FAIL] D4-C5: compute_cross_section raised"); traceback.print_exc()

    # D4-C6 ── foundation: pile count == piles_per_pier -------------------
    try:
        fd = compute_pile_group_layout(SAMPLE)
        expected = int(SAMPLE.foundation_details.piles_per_pier)
        got = len(fd.pile_positions)
        ok = got == expected
        results["D4C6"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D4-C6: pile_positions == {expected}  (got {got}, grid {fd.pile_rows}×{fd.pile_cols})")
    except Exception:
        results["D4C6"] = False
        print("  [FAIL] D4-C6: compute_pile_group_layout raised"); traceback.print_exc()

    # D4-C7 ── validation: 0 critical failures ----------------------------
    try:
        report = run_all(SAMPLE)
        ok = report.critical_fail_count == 0
        results["D4C7"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D4-C7: critical_fails={report.critical_fail_count}  warnings={report.warning_fail_count}  score={report.score}")
        for f in report.failed_findings():
            if f.severity is ValidationSeverity.CRITICAL:
                print(f"    ✗ [{f.check_id}] {f.message}")
    except Exception:
        results["D4C7"] = False
        print("  [FAIL] D4-C7: run_all raised"); traceback.print_exc()

    # D4-C8 ── validation: score >= 60 ------------------------------------
    try:
        ok = report.score >= 60
        results["D4C8"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D4-C8: score {report.score} >= 60")
    except Exception:
        results["D4C8"] = False; print("  [FAIL] D4-C8")

    # ── Verdict -----------------------------------------------------------
    passed = sum(1 for v in results.values() if v)
    total  = len(results)
    all_ok = passed == total
    print(); print(sep); print("  FINAL DAY 4 VERDICT"); print(sep)
    print(f"  Checks run : {total}")
    print(f"  Passed     : {passed}")
    print(f"  Failed     : {total - passed}")
    print(f"  VERDICT    : {'★ ACCEPTED ★' if all_ok else 'REJECTED'}")
    print(sep)
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(run_checks())
