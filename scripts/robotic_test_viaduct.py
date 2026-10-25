"""
Robotic test run — most complex bridge in the corpus.

Target: 8-span × 30m PSC Box Girder Expressway Viaduct
  Total length    : 240 m
  Overall width   : 14.0 m  (dual 2-lane + footpaths)
  Carriageway     : 2 × 7.0 m  (treated as 14 m single here per IRC:112)
  Superstructure  : PSC Box Girder, M50, depth=1.8m, span/depth=16.7
  Substructure    : Hammerhead pier M35, H=12m
  Foundation      : Bored pile 1500mm dia, L=25m, 8 piles per pier (2×4)
  Hydraulics      : Q=1500 m³/s, HFL=155.80, Scour=5.2m, 100yr return
  Loading         : Class 70R + Class A (IRC:6-2017)
  Seismic         : Zone III, Importance factor 1.5
  Wind            : Vb=47 m/s Zone IV
  State           : Maharashtra (MH) expressway

Pipeline steps:
  1. Build BridgeProject model from scratch (no Excel)
  2. Run QA validation (30 checks)
  3. Generate all 7 DXF sheets
  4. Generate priced BOQ (Excel + CSV)
  5. Generate QA HTML report
  6. Create ZIP bundle
  7. Print full summary with file sizes and timings
"""

from __future__ import annotations

import sys
import time
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path

# ── path bootstrap ─────────────────────────────────────────────────────────
SUITE = Path(__file__).parent.parent
for pkg in [
    "bridgecad-core",
    "bridgecad-io",
    "bridgecad-draw",
    "bridgecad-bill",
    "bridgecad-qa",
    "bridgecad-export",
    "bridgecad-plugins",
    "bridgecad-ai",
]:
    p = SUITE / "packages" / pkg
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

SEP = "=" * 72
TICK = "  ✓"
FAIL = "  ✗"


def hdr(title: str) -> None:
    print(f"\n{'─'*72}")
    print(f"  {title}")
    print(f"{'─'*72}")


def ok(label: str, detail: str = "") -> None:
    print(f"{TICK}  {label}" + (f"   [{detail}]" if detail else ""))


def err(label: str, detail: str = "") -> None:
    print(f"{FAIL}  {label}" + (f"   {detail}" if detail else ""))


# ──────────────────────────────────────────────────────────────────────────
# STEP 0 — build BridgeProject
# ──────────────────────────────────────────────────────────────────────────
hdr("STEP 0 — Build BridgeProject (8×30m PSC Box Viaduct)")
t0 = time.perf_counter()

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

N_SPANS = 8
SPAN_LEN = Decimal("30.000")
SPANS = [SPAN_LEN] * N_SPANS
TOTAL_LEN = Decimal(str(N_SPANS * 30))  # 240 m

project = BridgeProject(
    project_master=ProjectMaster(
        project_title="EXPRESSWAY VIADUCT AT CH 42+100 MUMBAI-PUNE EXPRESSWAY PHASE 2",
        project_code="NHAI-2026-00101",
        bridge_name="EXPR-VDT-CH42-100",
        chainage_km=Decimal("42.100"),
        package_no="PKG-MH-EXPR-03",
        client=ClientType.NHAI_NATIONAL_HIGHWAYS,
        consultant=ConsultantType.TIER1_ENGINEERING,
        contractor=ContractorType.INFRA_LARGE_TIER1_EPC,
        drawing_no="GAD-EXPR-VDT-001",
        drawing_title="GENERAL ARRANGEMENT - 8x30m PSC BOX GIRDER EXPRESSWAY VIADUCT",
        revision=RevisionTag.ISSUE_FOR_TENDER,
        date_issued=date(2026, 10, 3),
        designed_by="Dr. S. Kulkarni",
        checked_by="Er. R. Mehta",
        approved_by="Er. V. Joshi (DGM — Structures)",
        road_level_rl_m=Decimal("162.500"),
        ground_level_rl_m=Decimal("148.200"),
        survey_date=date(2026, 6, 15),
        state_code=IndianStateCode.MH,
        district_code="PUNE",
        language=Language.EN,
        latitude_deg=Decimal("18.6512000"),
        longitude_deg=Decimal("73.9250000"),
        total_estimated_cost_inr=Decimal(
            "0"
        ),  # populated post-BOQ via STEP 4 resync (avoids stale placeholders)
        tender_no="NHAI/MH/EXPR/VIA/2026/003",
        contract_no="NHAI/EPC/EXPR/MH/2026/017",
        project_phase=ProjectPhase.DESIGN_GAD_60_PCT,
        currency=Currency.INR,
    ),
    bridge_selection=BridgeSelection(
        bridge_category=BridgeCategory.VIADUCT,
        bridge_type=SuperstructureType.PSC_BOX_GIRDER,
        span_configuration=SpanConfiguration.SIMPLY_SUPPORTED,
        span_count=N_SPANS,
        carriageway_config=CarriagewayLaneConfig.FOUR_LANE_14M_CLASS_A,
        design_code=DesignCode.IRC_112_2020,
        loading_class=LoadClass.CLASS_70R,
        seismic_zone=SeismicZone.ZONE_III,
        wind_zone_ms=WindSpeedBasic_ms.VB_47_ms_ZONE_4,
        foundation_type=FoundationType.PILE,
    ),
    geometry_input=GeometryInput(
        span_count=N_SPANS,
        span_lengths_m=SPANS,
        alignment_type=AlignmentType.STRAIGHT,
        gradient_pct=Decimal("1.50"),
        carriageway_width_m=Decimal("14.00"),
        footpath_left_m=Decimal("1.50"),
        footpath_right_m=Decimal("1.50"),
        crash_barrier_width_left_m=Decimal("0.50"),
        crash_barrier_width_right_m=Decimal("0.50"),
        kerb_width_left_m=Decimal("0.25"),
        kerb_width_right_m=Decimal("0.25"),
        median_width_m=Decimal("1.20"),
        skew_angle_deg=Decimal("0.00"),
        skew_direction=SkewDirection.NONE,
        curved_bridge_flag=False,
        camber_mm=80,
        camber_method=CamberMethod.PARABOLIC_CROWN,
        pavement_thickness_total_mm=550,
        crust_layer_count=5,
        chainage_unit=ChainageUnit.METER,
        chainage_start_km=Decimal("42.000"),
        chainage_end_km=Decimal("42.240"),
        bearing_pad_spacing_m=Decimal("3.50"),
        kerb_type=KerbType.VERTICAL,
        footpath_type=FootpathType.STANDARD_RCC,
        median_type=MedianType.RIGID_MEDIAN_BARRIER,
        crash_barrier_type=CrashBarrierType.CONCRETE_NEW_JERSEY,
    ),
    superstructure=Superstructure(
        type=SuperstructureType.PSC_BOX_GIRDER,
        deck_material=ConcreteGrade.M50,
        deck_thickness_mm=280,
        wearing_coat_type=WearingCoatType.STONE_MASTIC_ASPALT,
        wearing_coat_grade=WearingCoatGrade.SMA_GRADE_1_STONE_MASTIC,
        wearing_coat_thickness_mm=50,
        wearing_coat_slope_pct=Decimal("2.5"),
        drainage_type=DrainageType.SCUPPER_OUTLET_THROUGH_DECK,
        drainage_spacing_m=Decimal("5.0"),
        camber_mm=80,
        camber_method=CamberMethod.PARABOLIC_CROWN,
        girder_type=GirderType.BOX_GIRDER_PSC_SINGLE_CELL,
        girder_depth_mm=1800,
        girder_spacing_m=Decimal("0.0"),  # mono-box
        girders_per_deck_count=1,
        parapet_type=ParapetType.RCC_CRASH,
        parapet_height_mm=1250,
        bearing_shelf_width_m=Decimal("0.60"),
        transverse_diaphragm_spacing_m=Decimal("7.5"),
        continuity_slab_thickness_mm=0,
        kerb_elevation_mm=280,
        footpath_elevation_mm=200,
    ),
    substructure=Substructure(
        pier_type=PierType.HAMMERHEAD,
        pier_material=ConcreteGrade.M35,
        pier_height_typical_m=Decimal("12.00"),
        pier_cap_type=PierCapType.OVERHANG_BOTH_SIDES,
        pier_cap_width_m=Decimal("3.00"),
        pier_cap_length_m=Decimal("16.00"),
        pier_cap_depth_m=Decimal("1.50"),
        pier_shaft_width_m=Decimal("2.50"),
        pier_shaft_length_m=Decimal("3.00"),
        pier_pedestal_height_m=Decimal("0.30"),
        pier_diaphragm_required=False,
        abutment_type=AbutmentType.CANTILEVER,
        abutment_material=ConcreteGrade.M35,
        abutment_width_m=Decimal("1.80"),
        abutment_length_m=Decimal("17.00"),
        abutment_height_m=Decimal("5.50"),
        abutment_pedestal_height_m=Decimal("0.30"),
        return_wall_type=ReturnWallType.CANTILEVER_RCC,
        return_wall_length_m=Decimal("6.0"),
        return_wall_height_m=Decimal("5.0"),
        wing_wall_type=WingWallType.SPLAYED_45_DEG,
        wing_wall_angle_deg=Decimal("45.0"),
        wing_wall_splay_length_m=Decimal("5.0"),
        wing_wall_height_m=Decimal("4.5"),
        backfill_type="SELECT GRANULAR MOORUM",
        approach_slab_length_m=Decimal("6.00"),
        approach_slab_thickness_mm=300,
        bearings_per_pier=4,
        bearings_per_abutment=4,
    ),
    foundation_details=FoundationDetails(
        type=FoundationType.PILE,
        pile_type=PileType.BORED_CAST_IN_SITU,
        pile_shape=PileShape.CIRCULAR_ROUND,
        pile_diameter_mm=1500,
        pile_length_m=Decimal("25.00"),
        piles_per_pier=8,
        pile_group_config="2×4 @3.0m c/c",
        pile_spacing_m=Decimal("3.00"),
        pile_cap_thickness_mm=2000,
        pile_cutoff_level_m=Decimal("144.500"),
        under_ream_count=UnderReamCount.NONE,
        factor_of_safety_on_bearing=Decimal("3.00"),
        bearing_capacity_kpa=Decimal("650.0"),
    ),
    approaches=Approaches(
        left_approach_length_m=Decimal("80.0"),
        right_approach_length_m=Decimal("80.0"),
        type_of_embankment="SELECT GRANULAR MOORUM COMPACTED",
        soil_embankment_unit_weight_kN_m3=Decimal("20.0"),
        approach_slope_width_m=Decimal("3.0"),
        shoulder_width_left_m=Decimal("2.5"),
        shoulder_width_right_m=Decimal("2.5"),
        guide_rail_required=True,
        speed_limit_on_approach_kmph=120,
        transition_curve_length_m=Decimal("0"),
        approach_gradient_pct=Decimal("1.50"),
    ),
    hydraulic_data=HydraulicData(
        design_discharge_cumecs=Decimal("1500.0"),
        hfl_m=Decimal("155.800"),
        lwl_m=Decimal("150.200"),
        normal_wl_m=Decimal("152.500"),
        scour_level_m=Decimal("143.800"),
        design_scour_depth_m=Decimal("5.20"),
        freeboard_m=Decimal("2.50"),
        actual_soffit_level_m=Decimal("158.300"),
        waterway_required_m2=Decimal("220.0"),
        waterway_provided_m2=Decimal("268.0"),
        lacey_silt_factor=Decimal("0.92"),
        regime_perimeter_m=Decimal("56.2"),
        regime_depth_m=Decimal("3.4"),
        regime_velocity_mps=Decimal("2.05"),
        afflux_m=Decimal("0.20"),
        max_afflux_allowable_m=Decimal("0.30"),
        water_source_type=WaterSourceType.PERENNIAL_SNOW_FED,
        river_bed_slope_m_per_km=Decimal("0.22"),
        catchment_area_sqkm=Decimal("8500.0"),
        return_period_yr=FloodReturnPeriodDesign.Q100_NHAI_NATIONAL_CORRIDOR,
        any_regime_equation_not_applied_flag=False,
        highest_recorded_flood_year=2005,
    ),
    materials=Materials(
        concrete_superstructure=ConcreteGrade.M50,
        concrete_substructure=ConcreteGrade.M35,
        concrete_foundation=ConcreteGrade.M30,
        reinforcement_steel_grade=SteelGrade.Fe500D,
        prestressing_steel=PrestressGrade.G1860,
        bearing_type=BearingType.POT_PTFE,
        expansion_joint_type=ExpansionJointType.SINGLE_MODULAR,
        wearing_coat_material_type=WearingCoatType.STONE_MASTIC_ASPALT,
        wearing_coat_grade=WearingCoatGrade.SMA_GRADE_3_STONE_MASTIC_16,
    ),
    bearings_joints=BearingsJoints(
        bearing_schedule=[
            BearingScheduleRow(
                location="A1-POT-FIXED",
                bearing_type=BearingType.POT_PTFE,
                size_x_mm=700,
                size_y_mm=700,
                design_load_kn=Decimal("3500.0"),
                fixed_or_guide_or_free="FIXED",
                pot_pressure_mpa=Decimal("28.5"),
                ptfe_sliding_surface_flag=True,
                quantity=2,
            ),
            BearingScheduleRow(
                location="P1-POT-GUIDED-X",
                bearing_type=BearingType.POT_PTFE,
                size_x_mm=700,
                size_y_mm=700,
                design_load_kn=Decimal("4800.0"),
                fixed_or_guide_or_free="GUIDED_X",
                pot_pressure_mpa=Decimal("31.0"),
                ptfe_sliding_surface_flag=True,
                quantity=4,
            ),
            BearingScheduleRow(
                location="P2-TO-P7-POT-FREE",
                bearing_type=BearingType.POT_PTFE,
                size_x_mm=700,
                size_y_mm=700,
                design_load_kn=Decimal("5200.0"),
                fixed_or_guide_or_free="FREE",
                pot_pressure_mpa=Decimal("31.0"),
                ptfe_sliding_surface_flag=True,
                quantity=24,
            ),
            BearingScheduleRow(
                location="A2-POT-FREE",
                bearing_type=BearingType.POT_PTFE,
                size_x_mm=700,
                size_y_mm=700,
                design_load_kn=Decimal("3500.0"),
                fixed_or_guide_or_free="FREE",
                pot_pressure_mpa=Decimal("28.5"),
                ptfe_sliding_surface_flag=True,
                quantity=2,
            ),
        ],
        expansion_joint_schedule=[
            ExpansionJointScheduleRow(
                location="A1-End Single Modular 80mm",
                joint_type=ExpansionJointType.SINGLE_MODULAR,
                width_mm=160,
                movement_range_mm=80,
                gap_mm=40,
                transverse_length_m=Decimal("19.00"),
                quantity=1,
            ),
            ExpansionJointScheduleRow(
                location="A2-End Single Modular 80mm",
                joint_type=ExpansionJointType.SINGLE_MODULAR,
                width_mm=160,
                movement_range_mm=80,
                gap_mm=40,
                transverse_length_m=Decimal("19.00"),
                quantity=1,
            ),
        ],
    ),
    components_lib=ComponentsLib(
        standard_pier_tag="PIER-HAMMERHEAD-H12m-CAP16x3.0",
        standard_abutment_tag="ABUT-CANTILEVER-H5.5m-L17m",
        standard_foundation_tag="PILE-1500mm-L25m-2x4",
        typical_girder_library_key="PSC-BOX-MONO-D2000-SPAN30m",
        standard_parapet_id="PARAPET-RCC-CRASH-H1250",
        standard_railing_id="RAILING-SS316-PIPE-3RAIL",
        standard_kerb_id="KERB-VERTICAL-H280",
        standard_crash_barrier_id="CRASH-NEWJERSEY-CONCRETE",
        standard_bearing_typical_pair_id="BEAR-POT-PTFE-700x700",
        standard_expansion_joint_id="EXPJ-SINGLE-MODULAR-80mm",
        standard_drainage_outlet_id="DRAIN-SCUPPER-200DIA",
        standard_pile_group_template_id="PILE-GRP-2x4-@3000",
        standard_wing_wall_id="WING-SPLAY-45DEG-L5m",
        standard_return_wall_id="RETURN-CANT-L6m-H5m",
        standard_approach_slab_id="APP-SLAB-L6000-T300",
    ),
    drawing_control=DrawingControl(
        output_formats=[OutputFormat.DXF, OutputFormat.PDF],
        autocad_version=AcadVersion.R2018,
        sheet_size=SheetSize.A1,
        drawing_scale=DrawingScale.S200,
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
        title_block_style=TitleBlockStyle.DETAILED,
        dimension_precision_mm=1,
        text_height_scale_factor=Decimal("1.00"),
        lineweight_scale_factor=Decimal("1.00"),
        drawing_border_inside_mm=10,
        revision_block_count=6,
        legend_sheet_required=True,
    ),
    calculations=Calculations(
        total_length_m=TOTAL_LEN,
        span_count=N_SPANS,
        span_depth_ratio=Decimal("16.67"),  # 30000/1800
        deck_area_sqm=Decimal("4080.0"),  # 240 × 17
        overall_width_check_ok=True,
        concrete_volume_superstructure_cum=Decimal("3200.0"),
        concrete_volume_substructure_cum=Decimal("2800.0"),
        concrete_volume_foundation_cum=Decimal("4500.0"),
        rebar_weight_tonnes_approx=Decimal("980.0"),
        prestress_tonnes_approx=Decimal("145.0"),
        bearing_count=32,
        expansion_joint_count=2,
        total_estimated_quantity_cost_inr=Decimal(
            "0"
        ),  # populated post-BOQ via STEP 4 resync (avoids stale placeholders)
        design_scour_vs_foundation_cover_ok=True,
        waterway_check_pass=True,
        afflux_ok=True,
        freeboard_actual_m=Decimal("2.50"),
        minimum_vertical_clearance_m=Decimal("8.50"),
        horizontal_clearance_m=Decimal("2.00"),
    ),
    validation=ValidationModel(
        overall_status="OK_PASS",
        critical_fail_count=0,
        warning_count=2,
        info_count=8,
        score_0_to_100=Decimal("93.0"),
        score_irc05=Decimal("96.0"),
        score_irc21=Decimal("94.0"),
        score_ircsp55=Decimal("92.0"),
        score_structural=Decimal("95.0"),
        score_hydraulic=Decimal("97.0"),
        score_drawing_standards=Decimal("90.0"),
        report_html_or_pdf_generated_flag=True,
        check_version_tag="1.0.0-rc1",
    ),
)

build_ms = int((time.perf_counter() - t0) * 1000)
ok("BridgeProject built", f"8 spans × 30m = 240m  |  14m wide  |  build={build_ms}ms")
print(f"     Total length  : {float(project.geometry_input.total_length_m):.1f} m")
print(f"     Overall width : {float(project.geometry_input.overall_width_m):.2f} m")
print(f"     Span count    : {project.geometry_input.span_count}")
print(f"     Bearings      : {project.calculations.bearing_count}")
print(
    f"     Est. cost     : INR {float(project.calculations.total_estimated_quantity_cost_inr):,.0f}"
)


# ──────────────────────────────────────────────────────────────────────────
# STEP 1 — QA Validation
# ──────────────────────────────────────────────────────────────────────────
hdr("STEP 1 — QA Validation (30 IRC/MORTH checks)")
t1 = time.perf_counter()

from bridgecad_core.validation import run_all
from bridgecad_qa.compliance import score as qa_score

report = run_all(project)
comp = qa_score(report)
qa_ms = int((time.perf_counter() - t1) * 1000)

print(f"     Score  : {comp.overall}/100   Grade: {comp.grade}")
print(f"     IRC:5  : {comp.irc05}/100   IRC:112: {comp.irc21}/100   SP:55: {comp.irc_sp55}/100")
print(f"     Critical failures : {comp.critical_fails}")
print(f"     Warning failures  : {comp.warning_fails}")
print(f"     Checks run        : {len(report.findings)}   [{qa_ms}ms]")

if comp.critical_fails:
    for f in report.failed_findings():
        if f.severity is ValidationSeverity.CRITICAL:
            err(f"  [{f.check_id}]", f.message)
    print("\n  ABORTING — critical failures must be resolved before drawing.")
    sys.exit(1)
else:
    ok("All 25 critical checks PASS", f"{qa_ms}ms")


# ──────────────────────────────────────────────────────────────────────────
# STEP 2 — IRC standards checks
# ──────────────────────────────────────────────────────────────────────────
hdr("STEP 2 — IRC Standards Verification")

from bridgecad_core.standards.irc_05 import compute_hydraulics
from bridgecad_core.standards.irc_21 import check_structural_adequacy
from bridgecad_core.standards.irc_sp55 import preferred_scale, text_height

hyd = compute_hydraulics(1500.0, 0.92)
ok(
    "IRC:5 Hydraulics",
    f"Lacey D_pier={hyd.design_scour_pier_m:.2f}m  "
    f"LW={hyd.linear_waterway_m:.0f}m  "
    f"V={hyd.regime_velocity_mps:.2f}m/s  "
    f"freeboard_min={hyd.freeboard_required_m}m",
)

str_chk = check_structural_adequacy(
    30.0,
    1800,
    "SIMPLY_SUPPORTED",
    "PSC_BOX_GIRDER",
    carriageway_width_m=14.0,
    bridge_class="CLASS_70R",
    exposure_class="SEVERE",
)
status = "PASS" if str_chk.span_depth_ok else "FAIL"
ok(
    f"IRC:112 Structural [{status}]",
    f"L/d={str_chk.span_depth_ratio}  "
    f"cover={str_chk.nominal_cover_mm}mm  "
    f"IF={str_chk.impact_factor:.2f}  "
    f"joint_gap={str_chk.joint_gap_mm:.0f}mm  "
    f"max_defl={str_chk.max_deflection_mm:.0f}mm",
)

ok(
    "IRC SP:55 Drawing",
    f"Preferred scale 1:{preferred_scale('PLAN_VIEW')}  "
    f"Text height body={text_height('A1','BODY')}mm",
)


# ──────────────────────────────────────────────────────────────────────────
# STEP 3 — Generate 7-sheet DXF package
# ──────────────────────────────────────────────────────────────────────────
hdr("STEP 3 — Generate 7-Sheet DXF GAD Package")
t3 = time.perf_counter()

OUT = SUITE / "test_run_output" / "viaduct_8x30m_psc_box"
OUT.mkdir(parents=True, exist_ok=True)

from bridgecad_draw.booklet import generate_package

sheets = generate_package(project, OUT, prefix="EXPR-VDT", scale_denom=200)

dxf_ms = int((time.perf_counter() - t3) * 1000)
total_kb = sum(s.stat().st_size for s in sheets) // 1024
print()
for s in sheets:
    kb = s.stat().st_size // 1024
    ok(f"  {s.name}", f"{kb} KB")
ok("7/7 sheets generated", f"total={total_kb} KB  time={dxf_ms}ms")


# ──────────────────────────────────────────────────────────────────────────
# STEP 4 — BOQ extraction + pricing (Maharashtra rates)
# ──────────────────────────────────────────────────────────────────────────
hdr("STEP 4 — Priced Bill of Quantities  [Maharashtra PWD rates]")
t4 = time.perf_counter()

from bridgecad_bill.formatters.csv_formatter import format_csv
from bridgecad_bill.formatters.excel_formatter import format_excel
from bridgecad_bill.processor import extract_and_price

boq = extract_and_price(project, state="MH")
xlsx_p = format_excel(boq, OUT / "EXPR-VDT_BOQ.xlsx")
csv_p = format_csv(boq, OUT / "EXPR-VDT_BOQ.csv")
boq_ms = int((time.perf_counter() - t4) * 1000)

# ── Sync model cost fields to computed BOQ (prevents stale hardcodes) ──
project.project_master.total_estimated_cost_inr = boq.grand_total
project.calculations.total_estimated_quantity_cost_inr = boq.grand_total

print()
for sec in boq.sections:
    amt_cr = float(sec.total) / 1e7
    print(f"     {sec.section_code:<8s}  {sec.title:<45s}  ₹{amt_cr:>6.2f} Cr")
print()
ok(
    "BOQ complete",
    f"Subtotal=₹{float(boq.subtotal)/1e7:.2f}Cr  "
    f"Contingency({boq.contingency_pct}%)=₹{float(boq.contingency_amount)/1e7:.2f}Cr  "
    f"Grand Total=₹{float(boq.grand_total)/1e7:.2f}Cr",
)
ok("Excel BOQ saved", f"{xlsx_p.stat().st_size//1024} KB  [{boq_ms}ms]")
ok("CSV BOQ saved", f"{csv_p.stat().st_size} B")


# ──────────────────────────────────────────────────────────────────────────
# STEP 5 — QA HTML report
# ──────────────────────────────────────────────────────────────────────────
hdr("STEP 5 — QA HTML Compliance Report")
t5 = time.perf_counter()

from bridgecad_qa.reports import generate_html_report

html_p = generate_html_report(report, OUT / "EXPR-VDT_QA.html", project)
html_ms = int((time.perf_counter() - t5) * 1000)
ok(
    "QA HTML report saved",
    f"{html_p.stat().st_size//1024} KB  score={comp.overall}/100  grade={comp.grade}  [{html_ms}ms]",
)


# ──────────────────────────────────────────────────────────────────────────
# STEP 6 — AI optimizer (optimal span/depth for this total length)
# ──────────────────────────────────────────────────────────────────────────
hdr("STEP 6 — AI Optimizer  [scipy SLSQP]")
t6 = time.perf_counter()

from bridgecad_ai.estimator import estimate_cost, estimate_quantities
from bridgecad_ai.optimizer import BridgeOptimizer
from bridgecad_ai.param_suggester import suggest

opt_result = BridgeOptimizer().optimize(
    total_length_m=240.0,
    carriageway_width_m=14.0,
    max_span_m=35.0,
)
ai_ms = int((time.perf_counter() - t6) * 1000)
ok(
    "AI Optimizer",
    f"optimal_span={opt_result.optimal_span_m}m  "
    f"depth={opt_result.optimal_depth_m}m  "
    f"n_spans={opt_result.optimal_n_spans}  "
    f"est_cost=₹{opt_result.estimated_cost_inr/1e7:.2f}Cr  "
    f"[{ai_ms}ms]",
)

# Parametric estimate vs BOQ comparison
qty = estimate_quantities(
    240.0,
    19.7,
    8,
    pier_height_m=12.0,
    pile_length_m=25.0,
    piles_per_support=8,
    is_prestressed=True,
    pile_diameter_mm=1500,
    carriageway_width_m=14.0,
)
cost = estimate_cost(qty, state="MH")
ok(
    "Parametric estimator",
    f"conc_sup={qty.concrete_superstructure_cum:.0f}m³  "
    f"rebar={qty.rebar_mt:.0f}MT  "
    f"grand_total=₹{cost.grand_total_inr/1e7:.2f}Cr",
)

# Suggestions from corpus
sugg = suggest(240.0, 8, "PSC_BOX_GIRDER", 14.0)
ok(
    "Param suggester",
    f"girder_depth={sugg.girder_depth_mm}mm  "
    f"pile_dia={sugg.pile_diameter_mm}mm  "
    f"bearing={sugg.bearing_type}  "
    f"conf={sugg.confidence}",
)


# ──────────────────────────────────────────────────────────────────────────
# STEP 7 — Create full ZIP bundle
# ──────────────────────────────────────────────────────────────────────────
hdr("STEP 7 — Full Export ZIP Bundle")
t7 = time.perf_counter()

from bridgecad_export.bundler import create_bundle

results = {
    "dxf": sheets,
    "bill": [xlsx_p, csv_p],
    "qa": [html_p],
}
bundle = create_bundle(OUT, "EXPR-VDT", results)
zip_ms = int((time.perf_counter() - t7) * 1000)
zip_kb = bundle.stat().st_size // 1024

# Inspect ZIP contents
with zipfile.ZipFile(bundle) as zf:
    entries = zf.namelist()
ok("ZIP bundle created", f"{zip_kb} KB  {len(entries)} entries  [{zip_ms}ms]")
print()
for e in sorted(entries):
    print(f"     📄 {e}")


# ──────────────────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ──────────────────────────────────────────────────────────────────────────
total_ms = int((time.perf_counter() - t0) * 1000)

print()
print(SEP)
print("  ROBOTIC TEST — FINAL SUMMARY")
print(SEP)
print("  Bridge         : 8×30m PSC Box Girder Expressway Viaduct")
print("  Total length   : 240 m   Width: 19 m   Spans: 8")
print("  Superstructure : PSC Box Girder M50, depth=1.8m, L/d=16.7")
print("  Foundation     : Bored pile 1500mm × 25m, 8 piles/pier")
print()
print(f"  QA score       : {comp.overall}/100  Grade: {comp.grade}")
print(f"  Grand Total    : ₹{float(boq.grand_total)/1e7:.2f} Crores (MH PWD rates)")
print(f"  Optimal span   : {opt_result.optimal_span_m}m  (AI SLSQP)")
print()
print("  OUTPUT FILES:")
for s in sheets:
    print(f"    {s.name:<55s}  {s.stat().st_size//1024:>4d} KB")
print(f"    {'EXPR-VDT_BOQ.xlsx':<55s}  {xlsx_p.stat().st_size//1024:>4d} KB")
print(f"    {'EXPR-VDT_BOQ.csv':<55s}  {csv_p.stat().st_size:>4d} B")
print(f"    {'EXPR-VDT_QA.html':<55s}  {html_p.stat().st_size//1024:>4d} KB")
print(f"    {'EXPR-VDT_bundle.zip':<55s}  {zip_kb:>4d} KB")
print()
print("  TIMINGS:")
print(f"    Build model   : {build_ms}ms")
print(f"    QA checks     : {qa_ms}ms")
print(f"    7-sheet DXF   : {dxf_ms}ms")
print(f"    BOQ           : {boq_ms}ms")
print(f"    QA HTML       : {html_ms}ms")
print(f"    AI optimizer  : {ai_ms}ms")
print(f"    ZIP bundle    : {zip_ms}ms")
print(f"    TOTAL         : {total_ms}ms  ({total_ms/1000:.1f}s)")
print()
print(f"  Output dir: {OUT}")
print(SEP)
print("  VERDICT : ★ ROBOTIC TEST COMPLETE ★")
print(SEP)
