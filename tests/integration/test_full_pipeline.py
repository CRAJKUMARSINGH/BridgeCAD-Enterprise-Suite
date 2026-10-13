"""
Integration smoke test: Excel template → BridgeProject → 7-sheet DXF + BOQ + ZIP bundle.

Run:
    cd "BridgeCAD Enterprise Suite"
    python tests/integration/test_full_pipeline.py
"""
from __future__ import annotations

import sys
import json
import zipfile
import tempfile
import traceback
from decimal import Decimal
from pathlib import Path
from datetime import date

# ── package path bootstrap ─────────────────────────────────────────────────
_SUITE = Path(__file__).parents[2]
for _pkg in ["bridgecad-core", "bridgecad-io", "bridgecad-draw",
             "bridgecad-bill", "bridgecad-qa", "bridgecad-export",
             "bridgecad-plugins"]:
    _p = _SUITE / "packages" / _pkg
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


# ===========================================================================
# Helpers
# ===========================================================================
SEP  = "=" * 72
PASS = "  [PASS]"
FAIL = "  [FAIL]"

def _ok(label: str, detail: str = "") -> tuple[str, bool]:
    print(f"{PASS} {label}" + (f"  ({detail})" if detail else ""))
    return label, True

def _fail(label: str, msg: str) -> tuple[str, bool]:
    print(f"{FAIL} {label}  →  {msg}")
    return label, False


# ===========================================================================
# Build a minimal valid BridgeProject in-process (no Excel needed for step 1)
# ===========================================================================

def _build_project():
    """Build the Day-3 SAMPLE project programmatically."""
    from bridgecad_core.models import (
        BridgeProject, ProjectMaster, BridgeSelection, GeometryInput,
        Superstructure, Substructure, FoundationDetails, Approaches,
        HydraulicData, Materials, BearingsJoints, BearingScheduleRow,
        ExpansionJointScheduleRow, ComponentsLib, DrawingControl,
        Calculations, ValidationModel,
    )
    from bridgecad_core.types import (
        ClientType, ConsultantType, ContractorType, ProjectPhase, RevisionTag,
        Currency, IndianStateCode, Language, BridgeCategory, SuperstructureType,
        SpanConfiguration, CarriagewayLaneConfig, DesignCode, LoadClass,
        SeismicZone, WindSpeedBasic_ms, FoundationType, SkewDirection,
        ConcreteGrade, SteelGrade, PrestressGrade, BearingType, ExpansionJointType,
        OutputFormat, AcadVersion, SheetSize, DrawingScale, LayerStandard,
        TitleBlockStyle, KerbType, FootpathType, MedianType, CrashBarrierType,
        ChainageUnit, AlignmentType, GirderType, WearingCoatType, DrainageType,
        ParapetType, CamberMethod, PierType, PierCapType, AbutmentType,
        ReturnWallType, WingWallType, PileType, PileShape, UnderReamCount,
        WaterSourceType, FloodReturnPeriodDesign, WearingCoatGrade,
    )
    return BridgeProject(
        project_master=ProjectMaster(
            project_title="INTEGRATION SMOKE TEST BRIDGE",
            project_code="TEST-2026-001",
            bridge_name="SMOKE-TEST-12M",
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
            span_count=1, span_lengths_m=[Decimal("12.000")],
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
            wearing_coat_grade=WearingCoatGrade.BC_GRADE_1_MARSHALL_30_6,
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
            bearings_per_pier=4, bearings_per_abutment=4,
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
            wearing_coat_grade=WearingCoatGrade.BC_GRADE_1_MARSHALL_30_6,
        ),
        bearings_joints=BearingsJoints(
            bearing_schedule=[
                BearingScheduleRow(
                    location="A1-Bearing",
                    bearing_type=BearingType.ELASTOMERIC_NEOPRENE,
                    size_x_mm=350, size_y_mm=350,
                    design_load_kn=Decimal("350.0"),
                    fixed_or_guide_or_free="FREE", quantity=4,
                ),
                BearingScheduleRow(
                    location="A2-Bearing",
                    bearing_type=BearingType.ELASTOMERIC_NEOPRENE,
                    size_x_mm=350, size_y_mm=350,
                    design_load_kn=Decimal("350.0"),
                    fixed_or_guide_or_free="FREE", quantity=4,
                ),
            ],
            expansion_joint_schedule=[
                ExpansionJointScheduleRow(
                    location="A1-End",
                    joint_type=ExpansionJointType.COMPRESSION_SEAL,
                    width_mm=40, movement_range_mm=20, gap_mm=12,
                    transverse_length_m=Decimal("8.90"), quantity=1,
                ),
                ExpansionJointScheduleRow(
                    location="A2-End",
                    joint_type=ExpansionJointType.COMPRESSION_SEAL,
                    width_mm=40, movement_range_mm=20, gap_mm=12,
                    transverse_length_m=Decimal("8.90"), quantity=1,
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
            gen_plan_sheet=True, gen_long_section_sheet=True,
            gen_cross_section_sheet=True, gen_foundation_sheet=True,
            gen_reinforcement_sheet=False, gen_pier_details_sheet=True,
            gen_abutment_details_sheet=True, gen_bearings_joints_sheet=True,
            gen_boq_sheet=True, gen_cover_sheet=True,
            gen_legends_sheet=True, gen_hydraulics_sheet=True,
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
            total_length_m=Decimal("12.000"), span_count=1,
            span_depth_ratio=Decimal("13.3"),
            deck_area_sqm=Decimal("105.0"),
            overall_width_check_ok=True,
            concrete_volume_superstructure_cum=Decimal("32.5"),
            concrete_volume_substructure_cum=Decimal("58.0"),
            concrete_volume_foundation_cum=Decimal("78.0"),
            rebar_weight_tonnes_approx=Decimal("18.5"),
            bearing_count=8, expansion_joint_count=2,
            total_estimated_quantity_cost_inr=Decimal("9500000"),
            design_scour_vs_foundation_cover_ok=True,
            waterway_check_pass=True, afflux_ok=True,
            freeboard_actual_m=Decimal("1.80"),
            minimum_vertical_clearance_m=Decimal("4.50"),
            horizontal_clearance_m=Decimal("1.00"),
        ),
        validation=ValidationModel(
            overall_status="OK_PASS", critical_fail_count=0,
            warning_count=0, info_count=3,
            score_0_to_100=Decimal("96.0"),
            check_version_tag="1.0.0-integration",
        ),
    )


# ===========================================================================
# Test runner
# ===========================================================================

def run_integration_smoke() -> int:
    results: list[tuple[str, bool]] = []
    print()
    print(SEP)
    print("  BRIDGECAD ENTERPRISE — INTEGRATION SMOKE TEST")
    print(SEP)

    # ── T01: BridgeProject constructs ────────────────────────────────────
    try:
        project = _build_project()
        results.append(_ok("T01", "BridgeProject constructed"))
    except Exception as exc:
        results.append(_fail("T01", f"BridgeProject failed: {exc}"))
        print("  Cannot continue without a valid project."); return 1

    # ── T02: Validation engine (30 checks, 0 critical fails) ─────────────
    try:
        from bridgecad_core.validation import run_all
        from bridgecad_qa.compliance   import score as _score
        report = run_all(project)
        comp   = _score(report)
        ok = report.critical_fail_count == 0 and comp.overall >= 60
        results.append(
            _ok("T02", f"score={comp.overall}  grade={comp.grade}  critical_fails={report.critical_fail_count}")
            if ok else
            _fail("T02", f"score={comp.overall}  critical_fails={report.critical_fail_count}")
        )
    except Exception as exc:
        results.append(_fail("T02", str(exc))); traceback.print_exc()

    # ── T03: Excel template generation ───────────────────────────────────
    try:
        from bridgecad_io.excel_template import generate_template
        with tempfile.TemporaryDirectory() as td:
            p = generate_template(Path(td) / "template.xlsx")
            sz = p.stat().st_size
        ok = sz > 20_000
        results.append(
            _ok("T03", f"template.xlsx = {sz//1024} KB")
            if ok else _fail("T03", f"template too small: {sz} B")
        )
    except Exception as exc:
        results.append(_fail("T03", str(exc)))

    # ── T04: 7-sheet DXF package ─────────────────────────────────────────
    dxf_sheets: list[Path] = []
    try:
        from bridgecad_draw.booklet import generate_package
        with tempfile.TemporaryDirectory() as td:
            sheets = generate_package(project, Path(td),
                                      prefix="SMOKE", scale_denom=100)
            # copy to persistent temp dir
            import shutil
            tmp_draw = Path(tempfile.mkdtemp())
            for s in sheets:
                dest = tmp_draw / s.name
                shutil.copy(s, dest)
                dxf_sheets.append(dest)
        total_kb = sum(s.stat().st_size for s in dxf_sheets) // 1024
        ok = len(dxf_sheets) == 7 and total_kb > 50
        results.append(
            _ok("T04", f"{len(dxf_sheets)}/7 sheets  total {total_kb} KB")
            if ok else _fail("T04", f"only {len(dxf_sheets)}/7 sheets or too small")
        )
    except Exception as exc:
        results.append(_fail("T04", str(exc))); traceback.print_exc()

    # ── T05: DXF files each > 10 KB ──────────────────────────────────────
    try:
        small = [s.name for s in dxf_sheets if s.stat().st_size < 10_000]
        ok = len(small) == 0
        results.append(
            _ok("T05", "all sheets > 10 KB")
            if ok else _fail("T05", f"small sheets: {small}")
        )
    except Exception as exc:
        results.append(_fail("T05", str(exc)))

    # ── T06: BOQ extraction + pricing ────────────────────────────────────
    try:
        from bridgecad_bill.processor import extract_and_price
        boq = extract_and_price(project, state="MH")
        ok  = boq.grand_total > 0 and len(boq.all_items()) >= 10
        results.append(
            _ok("T06", f"grand_total=INR {float(boq.grand_total):,.0f}  items={len(boq.all_items())}")
            if ok else _fail("T06", f"grand_total={boq.grand_total}  items={len(boq.all_items())}")
        )
    except Exception as exc:
        results.append(_fail("T06", str(exc))); traceback.print_exc()

    # ── T07: BOQ Excel + CSV formatters ──────────────────────────────────
    try:
        from bridgecad_bill.processor                  import extract_and_price
        from bridgecad_bill.formatters.excel_formatter import format_excel
        from bridgecad_bill.formatters.csv_formatter   import format_csv
        with tempfile.TemporaryDirectory() as td:
            boq2      = extract_and_price(project)
            xlsx_path = format_excel(boq2, Path(td) / "BOQ.xlsx")
            csv_path  = format_csv(boq2,   Path(td) / "BOQ.csv")
            xlsx_sz   = xlsx_path.stat().st_size
            csv_sz    = csv_path.stat().st_size
        ok = xlsx_sz > 5_000 and csv_sz > 500
        results.append(
            _ok("T07", f"xlsx={xlsx_sz//1024}KB  csv={csv_sz}B")
            if ok else _fail("T07", f"xlsx={xlsx_sz}B  csv={csv_sz}B too small")
        )
    except Exception as exc:
        results.append(_fail("T07", str(exc))); traceback.print_exc()

    # ── T08: QA HTML report ───────────────────────────────────────────────
    try:
        from bridgecad_core.validation import run_all
        from bridgecad_qa.reports       import generate_html_report
        report2 = run_all(project)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tf:
            tmp = Path(tf.name)
        generate_html_report(report2, tmp, project)
        html_sz = tmp.stat().st_size
        html    = tmp.read_text(encoding="utf-8")
        tmp.unlink(missing_ok=True)
        ok = html_sz > 3_000 and "<table" in html
        results.append(
            _ok("T08", f"QA HTML = {html_sz//1024} KB")
            if ok else _fail("T08", f"html too small or missing table: {html_sz}B")
        )
    except Exception as exc:
        results.append(_fail("T08", str(exc))); traceback.print_exc()

    # ── T09: Plugin registry ─────────────────────────────────────────────
    try:
        from bridgecad_plugins.registry import get_registry
        reg = get_registry()
        ok  = len(reg) >= 3
        plugin_ids = [p.plugin_id for p in reg.all()]
        results.append(
            _ok("T09", f"plugins={plugin_ids}")
            if ok else _fail("T09", f"expected >= 3 plugins, got {len(reg)}")
        )
    except Exception as exc:
        results.append(_fail("T09", str(exc)))

    # ── T10: Full export → ZIP bundle ─────────────────────────────────────
    try:
        from bridgecad_export.orchestrator import export_all
        with tempfile.TemporaryDirectory() as td:
            bundle = export_all(project, Path(td), prefix="SMOKE_INT")
            bundle_sz = bundle.stat().st_size
            # Inspect ZIP contents
            with zipfile.ZipFile(bundle) as zf:
                entries = zf.namelist()
                has_manifest = any("manifest.json" in e for e in entries)
                has_dxf      = any(e.endswith(".dxf") for e in entries)
                has_excel    = any(e.endswith(".xlsx") for e in entries)
                has_html     = any(e.endswith(".html") for e in entries)
        ok = bundle_sz > 50_000 and has_manifest and has_dxf and has_excel
        results.append(
            _ok("T10", f"bundle={bundle_sz//1024}KB  dxf={has_dxf}  xlsx={has_excel}  html={has_html}  manifest={has_manifest}")
            if ok else _fail("T10", f"bundle={bundle_sz}B  dxf={has_dxf}  xlsx={has_excel}")
        )
    except Exception as exc:
        results.append(_fail("T10", str(exc))); traceback.print_exc()

    # ── T11: CLI health command compiles + runs ───────────────────────────
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0,str(__import__('pathlib').Path('apps/cli-console').resolve()));"
             "from bridgecad_cli.main import app; print('CLI_IMPORT_OK')"],
            capture_output=True, text=True,
            cwd=str(_SUITE),
        )
        ok = "CLI_IMPORT_OK" in result.stdout or result.returncode == 0
        results.append(
            _ok("T11", "CLI module imports cleanly")
            if ok else _fail("T11", result.stderr[:100])
        )
    except Exception as exc:
        results.append(_fail("T11", str(exc)))

    # ── T12: FastAPI app constructs ───────────────────────────────────────
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "bridgecad_api.main",
            _SUITE / "apps" / "api-gateway" / "bridgecad_api" / "main.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)    # type: ignore[union-attr]
        has_app = hasattr(mod, "app")
        ok = has_app
        results.append(
            _ok("T12", "FastAPI app object found")
            if ok else _fail("T12", "no 'app' in api main.py")
        )
    except Exception as exc:
        results.append(_fail("T12", str(exc)[:120]))

    # ── Summary ───────────────────────────────────────────────────────────
    passed = sum(1 for _, ok in results if ok)
    total  = len(results)
    all_ok = passed == total

    print()
    print(SEP)
    print("  INTEGRATION SMOKE RESULTS")
    print(SEP)
    print(f"  Tests run   : {total}")
    print(f"  Passed      : {passed}")
    print(f"  Failed      : {total - passed}")

    if not all_ok:
        print("\n  FAILED TESTS:")
        for label, ok in results:
            if not ok:
                print(f"    ✗ {label}")

    verdict = "★ ACCEPTED ★" if all_ok else "REJECTED (see failures above)"
    print(f"\n  VERDICT     : {verdict}")
    print(SEP)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(run_integration_smoke())
