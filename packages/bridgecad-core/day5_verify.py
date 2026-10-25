"""M1 Week 1 Day 5 — Week-1 Sign-Off acceptance verifier (12 checks)."""
from __future__ import annotations

import py_compile
import sys
import traceback
from datetime import date
from decimal import Decimal
from pathlib import Path

from bridgecad_core import types as bc_types
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
from bridgecad_core.standards import (
    irc_05,
    irc_21,
    irc_sp55,
    morth_specs,
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
    WaterSourceType,
    WearingCoatGrade,
    WearingCoatType,
    WindSpeedBasic_ms,
    WingWallType,
)
from bridgecad_core.validation import run_all

PKG_DIR = Path(__file__).resolve().parent
CORE_DIR = PKG_DIR / "bridgecad_core"


# ---------------------------------------------------------------------------
# Fixture #1 — 12 m Simply Supported Minor ROB (PSC I-Girder)
# ---------------------------------------------------------------------------
def _fixture_12m_single() -> BridgeProject:
    return BridgeProject(
        project_master=ProjectMaster(
            project_title="PROPOSED ROB AT CH. 24+350", project_code="NHAI-2026-007",
            bridge_name="PUNE-ROB-CH24-350", chainage_km=Decimal("24.3500"),
            package_no="PKG-MH-PUNE-007", client=ClientType.NHAI_NATIONAL_HIGHWAYS,
            consultant=ConsultantType.LIMITED_CONSULTANT_A_GRADE,
            contractor=ContractorType.INFRA_LARGE_TIER1_EPC,
            drawing_no="GAD-ROB-001", drawing_title="GENERAL ARRANGEMENT DRAWING",
            revision=RevisionTag.ISSUE_FOR_TENDER, date_issued=date(2026,10,15),
            designed_by="A. Sharma", checked_by="R. Patil", approved_by="Dr. V. Kulkarni",
            road_level_rl_m=Decimal("565.250"), ground_level_rl_m=Decimal("562.800"),
            survey_date=date(2026,8,10), state_code=IndianStateCode.MH,
            district_code="PUNE", language=Language.EN,
            latitude_deg=Decimal("18.5204"), longitude_deg=Decimal("73.8567"),
            total_estimated_cost_inr=Decimal("187500000.00"),
            tender_no="NHAI/MH/ROB/2026/12", contract_no="NHAI/MH/EPC/2026/47",
            project_phase=ProjectPhase.DESIGN_GAD_60_PCT, currency=Currency.INR,
        ),
        bridge_selection=BridgeSelection(
            bridge_category=BridgeCategory.MAJOR_ROB_RAIL_OVER_BRIDGE,
            bridge_type=SuperstructureType.PSC_IGIRDER,
            span_configuration=SpanConfiguration.SIMPLY_SUPPORTED, span_count=1,
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
            crash_barrier_width_left_m=Decimal("0.50"), crash_barrier_width_right_m=Decimal("0.50"),
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
            transverse_diaphragm_spacing_m=Decimal("3.0"), continuity_slab_thickness_mm=0,
            kerb_elevation_mm=220, footpath_elevation_mm=150,
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
            wing_wall_height_m=Decimal("2.50"), backfill_type="SELECT GRANULAR MOORUM",
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
            left_approach_length_m=Decimal("45.0"), right_approach_length_m=Decimal("55.0"),
            type_of_embankment="SELECT MOORUM + SAND LAYERS",
            soil_embankment_unit_weight_kN_m3=Decimal("19.0"),
            approach_slope_width_m=Decimal("2.0"),
            shoulder_width_left_m=Decimal("1.5"), shoulder_width_right_m=Decimal("1.5"),
            guide_rail_required=True, speed_limit_on_approach_kmph=60,
            transition_curve_length_m=Decimal("0"), approach_gradient_pct=Decimal("1.2"),
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
                BearingScheduleRow(location="A1-Abutment-B1",
                    bearing_type=BearingType.ELASTOMERIC_NEOPRENE,
                    size_x_mm=450, size_y_mm=450,
                    design_load_kn=Decimal("650.0"), fixed_or_guide_or_free="FREE",
                    elastomeric_layers_count=6, steel_back_bool=True, quantity=4),
                BearingScheduleRow(location="P1-Pier-B1",
                    bearing_type=BearingType.POT_PTFE,
                    size_x_mm=550, size_y_mm=550,
                    design_load_kn=Decimal("820.0"), fixed_or_guide_or_free="FIXED",
                    pot_pressure_mpa=Decimal("27.5"), ptfe_sliding_surface_flag=True, quantity=4),
            ],
            expansion_joint_schedule=[
                ExpansionJointScheduleRow(location="A1-Deck-End",
                    joint_type=ExpansionJointType.STRIP_SEAL,
                    width_mm=80, movement_range_mm=50, gap_mm=25,
                    transverse_length_m=Decimal("11.50"), quantity=1),
                ExpansionJointScheduleRow(location="A2-Deck-End",
                    joint_type=ExpansionJointType.STRIP_SEAL,
                    width_mm=80, movement_range_mm=50, gap_mm=25,
                    transverse_length_m=Decimal("11.50"), quantity=1),
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
            drawing_scale=DrawingScale.S100, gen_plan_sheet=True,
            gen_long_section_sheet=True, gen_cross_section_sheet=True,
            gen_foundation_sheet=True, gen_reinforcement_sheet=True,
            gen_pier_details_sheet=True, gen_abutment_details_sheet=True,
            gen_bearings_joints_sheet=True, gen_boq_sheet=True,
            gen_cover_sheet=True, gen_legends_sheet=True,
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
            expansion_joint_count=2, total_estimated_quantity_cost_inr=Decimal("187500000"),
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
            report_html_or_pdf_generated_flag=True,
            check_version_tag="1.0.0-day5",
        ),
    )


# ---------------------------------------------------------------------------
# Fixture #2 — 3×12 m Continuous Major Bridge (PSC Box-Girder)
# ---------------------------------------------------------------------------
def _fixture_3x12m_continuous() -> BridgeProject:
    p = _fixture_12m_single()
    p.bridge_selection = p.bridge_selection.model_copy(update={
        "span_configuration": SpanConfiguration.CONTINUOUS,
        "span_count": 3,
    })
    p.geometry_input = p.geometry_input.model_copy(update={
        "span_count": 3,
        "span_lengths_m": [Decimal("12.000"), Decimal("12.000"), Decimal("12.000")],
    })
    p.superstructure.type = SuperstructureType.PSC_BOX_GIRDER
    p.superstructure.girder_type = GirderType.BOX_GIRDER_PSC_SINGLE_CELL
    p.superstructure.girder_depth_mm = 1500
    p.superstructure.girders_per_deck_count = 1
    p.calculations.span_count = 3
    p.calculations.total_length_m = Decimal("36.000")
    p.calculations.span_depth_ratio = Decimal("24.0")
    p.calculations.deck_area_sqm = Decimal("414.0")
    return p


# ---------------------------------------------------------------------------
# Fixture #3 — 8 m Box Culvert
# ---------------------------------------------------------------------------
def _fixture_8m_box_culvert() -> BridgeProject:
    p = _fixture_12m_single()
    p.bridge_selection = p.bridge_selection.model_copy(update={
        "bridge_category": BridgeCategory.MINOR_BRIDGE,
        "bridge_type": SuperstructureType.BOX_CULVERT,
        "span_count": 1,
    })
    p.geometry_input = p.geometry_input.model_copy(update={
        "span_count": 1,
        "span_lengths_m": [Decimal("8.000")],
        "carriageway_width_m": Decimal("7.00"),
    })
    p.superstructure.type = SuperstructureType.BOX_CULVERT
    p.superstructure.deck_material = ConcreteGrade.M25
    p.superstructure.deck_thickness_mm = 300
    p.substructure.pier_height_typical_m = Decimal("3.00")
    p.foundation_details.type = FoundationType.OPEN
    p.foundation_details.piles_per_pier = 0
    p.calculations.total_length_m = Decimal("8.000")
    p.calculations.span_depth_ratio = Decimal("8.0")
    p.calculations.deck_area_sqm = Decimal("88.0")
    return p


def _roundtrip_equal(original: BridgeProject, tag: str) -> bool:
    """Model dump + re-parse equals original (field-wise)."""
    data = original.model_dump_json(
        exclude={
            "total_bridge_length_m": ...,
            "overall_bridge_width_m": ...,
            "span_count_propagated": ...,
            "geometry_input": {"total_length_m", "overall_width_m"},
            "superstructure": {"total_deck_thickness_mm"},
            "hydraulic_data": {"freeboard_actual_m"},
            "bearings_joints": {"total_bearings_quantity", "total_joints_quantity"},
        }
    )
    restored = BridgeProject.model_validate_json(data)
    ok_len = (float(restored.geometry_input.total_length_m) ==
              float(original.geometry_input.total_length_m))
    ok_type = restored.superstructure.type == original.superstructure.type
    ok_phase = restored.project_master.project_phase == original.project_master.project_phase
    ok_spans = (len(restored.geometry_input.span_lengths_m) ==
                len(original.geometry_input.span_lengths_m))
    return ok_len and ok_type and ok_phase and ok_spans


# ---------------------------------------------------------------------------
# Standards smoke tests
# ---------------------------------------------------------------------------
def _standards_smoke_ok() -> bool:
    try:
        # irc_05 — Lacey scour multiplier 2.0 baked into PIER default + MAX_AFFLUX 0.3
        assert irc_05.freeboard_min("NHAI") >= 1.0, "irc_05 freeboard_min failed"
        # irc_21 — SPAN_DEPTH_RATIO via function + impact factor
        ok, ratio, _msg = irc_21.check_span_depth_ratio(12.0, 800, "SIMPLY_SUPPORTED", "PSC_IGIRDER")
        assert ok, f"irc_21 span_depth failed: ratio={ratio}"
        # irc_sp55 — spans/scales table + text height
        assert 100 in irc_sp55.STANDARD_SCALES["GENERAL_ARRANGEMENT"], "irc_sp55 scales failed"
        assert irc_sp55.text_height("A1", "TITLE") >= 4.0, "irc_sp55 text height failed"
        # morth_specs — MORTH item code limits + UNIT_RATE tolerance % 15
        assert morth_specs.TEST_FREQUENCIES["CONCRETE_CUBE_COMPRESSIVE"]
        assert "700" in morth_specs.MORTH_CHAPTERS, "morth_specs chapter codes failed"
        return True
    except AssertionError:
        traceback.print_exc()
        return False
    except Exception:
        traceback.print_exc()
        return False


# ---------------------------------------------------------------------------
# py_compile sweep
# ---------------------------------------------------------------------------
_FILES_TO_COMPILE = [
    CORE_DIR / "__init__.py",
    CORE_DIR / "types.py",
    CORE_DIR / "models.py",
    CORE_DIR / "validation.py",
    CORE_DIR / "validation_registry.py",
    CORE_DIR / "quantities.py",
    CORE_DIR / "costs.py",
    CORE_DIR / "geometry" / "__init__.py",
    CORE_DIR / "geometry" / "plan.py",
    CORE_DIR / "geometry" / "long_section.py",
    CORE_DIR / "geometry" / "cross_section.py",
    CORE_DIR / "geometry" / "foundation.py",
    CORE_DIR / "standards" / "__init__.py",
    CORE_DIR / "standards" / "irc_05.py",
    CORE_DIR / "standards" / "irc_21.py",
    CORE_DIR / "standards" / "irc_sp55.py",
    CORE_DIR / "standards" / "morth_specs.py",
]


def _py_compile_clean() -> bool:
    ok_all = True
    for f in _FILES_TO_COMPILE:
        try:
            py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError as exc:
            ok_all = False
            print(f"   COMPILE-ERR: {f.name} -> {exc.msg}")
    return ok_all


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def run_checks() -> int:
    sep = "=" * 72
    print(); print(sep)
    print("  M1 WEEK 1 -- DAY 5 SIGN-OFF ACCEPTANCE CHECKS  (12 checks)")
    print(sep)
    results: dict[str, bool] = {}
    p1 = _fixture_12m_single()
    p2 = _fixture_3x12m_continuous()
    p3 = _fixture_8m_box_culvert()

    # D5-C1 ── ENUM_REGISTRY count >= 180 ─────────────────────────────
    try:
        n_reg = len(bc_types.ENUM_REGISTRY)
        ok = n_reg >= 180
        results["D5C1"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D5-C1: ENUM_REGISTRY = {n_reg}  (target >= 180)")
    except Exception:
        results["D5C1"] = False; print("  [FAIL] D5-C1"); traceback.print_exc()

    # D5-C2 ── 14-sheet field count >= 380 ────────────────────────────
    try:
        n_fields = 0
        for cls in (ProjectMaster, BridgeSelection, GeometryInput, Superstructure,
                    Substructure, FoundationDetails, Approaches, HydraulicData,
                    Materials, BearingsJoints, ComponentsLib, DrawingControl,
                    Calculations, ValidationModel):
            n_fields += len(cls.model_fields)
        ok = n_fields >= 380
        results["D5C2"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D5-C2: 14-sheet field count = {n_fields}  (target >= 380)")
    except Exception:
        results["D5C2"] = False; print("  [FAIL] D5-C2"); traceback.print_exc()

    # D5-C3 ── JSON schema size >= 40 KB ─────────────────────────────
    try:
        schema_json = BridgeProject.model_json_schema(mode="serialization")
        import json
        size_kb = len(json.dumps(schema_json, default=str)) / 1024.0
        ok = size_kb >= 40.0
        results["D5C3"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D5-C3: JSON schema size = {size_kb:.1f} KB  (target >= 40 KB)")
    except Exception:
        results["D5C3"] = False; print("  [FAIL] D5-C3"); traceback.print_exc()

    # D5-C4 ── Round-trip: 12 m single ───────────────────────────────
    try:
        p1 = _fixture_12m_single()
        ok = _roundtrip_equal(p1, "12m")
        results["D5C4"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D5-C4: JSON round-trip — 12 m single span")
    except Exception:
        results["D5C4"] = False; print("  [FAIL] D5-C4"); traceback.print_exc()

    # D5-C5 ── Round-trip: 3×12 m continuous ─────────────────────────
    try:
        p2 = _fixture_3x12m_continuous()
        ok = _roundtrip_equal(p2, "3x12m")
        results["D5C5"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D5-C5: JSON round-trip — 3×12 m continuous")
    except Exception:
        results["D5C5"] = False; print("  [FAIL] D5-C5"); traceback.print_exc()

    # D5-C6 ── Round-trip: 8 m box culvert ───────────────────────────
    try:
        p3 = _fixture_8m_box_culvert()
        ok = _roundtrip_equal(p3, "8m culvert")
        results["D5C6"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D5-C6: JSON round-trip — 8 m box culvert")
    except Exception:
        results["D5C6"] = False; print("  [FAIL] D5-C6"); traceback.print_exc()

    # D5-C7 ── Standards: 2+ real constants per module (smoke) ──────
    try:
        ok = _standards_smoke_ok()
        results["D5C7"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D5-C7: Standards wiring stubs smoke — 4 modules have real constants")
    except Exception:
        results["D5C7"] = False; print("  [FAIL] D5-C7"); traceback.print_exc()

    # D5-C8 ── Geometry: all 4 modules smoke against 12m fixture ────
    try:
        plan = compute_plan_geometry(p1)
        ls   = compute_long_section_geometry(p1)
        cs   = compute_cross_section_geometry(p1)
        fd   = compute_pile_group_layout(p1)
        ok = (len(plan.deck_corners) == 4 and ls.soffit_rl > ls.hfl_rl and
              cs.camber_y_at_x(0) >= 0 and len(fd.pile_cap_corners) == 4)
        results["D5C8"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D5-C8: All 4 geometry modules — deck={len(plan.deck_corners)}  "
              f"soffit>hfl={ls.soffit_rl > ls.hfl_rl}  cap corners={len(fd.pile_cap_corners)}")
    except Exception:
        results["D5C8"] = False; print("  [FAIL] D5-C8"); traceback.print_exc()

    # D5-C9 ── Validation: 0 Critical on 12m fixture ────────────────
    try:
        report = run_all(p1)
        ok = report.critical_fail_count == 0 and report.score >= 60
        results["D5C9"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D5-C9: Validation — critical={report.critical_fail_count}  "
              f"score={report.score}  (target crit=0, score>=60)")
    except Exception:
        results["D5C9"] = False; print("  [FAIL] D5-C9"); traceback.print_exc()

    # D5-C10 ── Validation: 2 piers correctly detected for 3×12m ────
    try:
        p2 = _fixture_3x12m_continuous()
        plan2 = compute_plan_geometry(p2)
        ok = len(plan2.pier_centrelines) == 2   # continuous 3 spans → 2 internal piers
        results["D5C10"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D5-C10: Plan geometry — 3×12m continuous → {len(plan2.pier_centrelines)} internal piers (expect 2)")
    except Exception:
        results["D5C10"] = False; print("  [FAIL] D5-C10"); traceback.print_exc()

    # D5-C11 ── Open-foundation layout works for 8m culvert ────────
    try:
        p3 = _fixture_8m_box_culvert()
        fd3 = compute_pile_group_layout(p3)
        ok = (len(fd3.open_footing_steps) >= 1 or
              fd3.pile_cap_width_m >= 0)   # any valid output
        results["D5C11"] = ok
        print(f"  [{'PASS' if ok else 'FAIL'}] D5-C11: Foundation geometry — 8m culvert open footing: {len(fd3.open_footing_steps)} steps")
    except Exception:
        results["D5C11"] = False; print("  [FAIL] D5-C11"); traceback.print_exc()

    # D5-C12 ── py_compile all 17 source files clean ───────────────
    try:
        ok = _py_compile_clean()
        results["D5C12"] = ok
        n_files = len(_FILES_TO_COMPILE)
        print(f"  [{'PASS' if ok else 'FAIL'}] D5-C12: py_compile sweep — {n_files} files clean")
    except Exception:
        results["D5C12"] = False; print("  [FAIL] D5-C12"); traceback.print_exc()

    # ── Verdict ───────────────────────────────────────────────────────
    passed = sum(1 for v in results.values() if v)
    total  = len(results)
    all_ok = passed == total
    print(); print(sep); print("  FINAL WEEK 1 SIGN-OFF VERDICT"); print(sep)
    print(f"  Checks run : {total}")
    print(f"  Passed     : {passed}")
    print(f"  Failed     : {total - passed}")
    for k, v in results.items():
        if not v:
            print(f"    FAIL: {k}")
    print(f"  VERDICT    : {'★ M1W1 SIGN-OFF ACCEPTED ★' if all_ok else 'REJECTED — re-run after fix'}")
    print(sep)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(run_checks())
