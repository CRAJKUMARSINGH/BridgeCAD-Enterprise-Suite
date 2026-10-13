"""
Project fixtures for M1 Week 2 validation + geometry + round-trip tests.
Three scenarios:
  * SAMPLE_MINOR_12M_VALID      — 12 m single-span minor RCC solid-slab bridge
  * SAMPLE_MINOR_12M_WITH_BUGS  — seeded failures so Warning/Info checks fire
  * SAMPLE_MAJOR_3X12M          — 3-span 36 m continuous PSC I-Girder major
  * SAMPLE_CULVERT_8M_BOX       — 8 m single-cell box culvert
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from bridgecad_core.models import (
    Approaches,
    BearingsJoints,
    BridgeProject,
    BridgeSelection,
    Calculations,
    ComponentsLib,
    DrawingControl,
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
    BearingMaterial,
    BearingType,
    BridgeCategory,
    CarriagewayLaneConfig,
    ClientType,
    ConcreteGrade,
    DesignCode,
    DrawingScale,
    ExpansionJointType,
    FoundationType,
    IndianStateCode,
    Language,
    PierType,
    PrestressGrade,
    ProjectPhase,
    RevisionTag,
    SeismicZone,
    SheetSize,
    SpanConfiguration,
    SteelGrade,
    SuperstructureMaterial,
    SuperstructureType,
    TitleBlockStyle,
    WindSpeedBasic_ms,
)


# ==========================================================================
# Shared helpers — every field must match actual Pydantic schema exactly
# ==========================================================================

def _common_project_master(**overrides) -> ProjectMaster:
    base = dict(
        project_title="Minor Bridge across Nala at KM 24+350",
        project_code="PWD-2026-007",
        bridge_name="Nala Bridge KM 24.350",
        chainage_km=Decimal("24.350000"),
        package_no="PKG-III-A",
        client=ClientType.STATE_PWD,
        revision=RevisionTag.R1,
        date_issued=date(2026, 3, 15),
        designed_by="Er. A. Kumar",
        checked_by="Er. S. Patil",
        approved_by="Er. M. Desai",
        road_level_rl_m=Decimal("104.2500"),
        ground_level_rl_m=Decimal("100.0000"),
        survey_date=date(2026, 1, 10),
        state_code=IndianStateCode.MH,
        district_code="PUNE",
        language=Language.EN,
        latitude_deg=Decimal("18.5204000"),
        longitude_deg=Decimal("73.8567000"),
        total_estimated_cost_inr=Decimal("8500000.00"),
        tender_no="PWD/PUNE/2025-26/112",
        contract_no="PWD-CON-2026-018",
        project_phase=ProjectPhase.DESIGN_GAD_60_PCT,
    )
    base.update(overrides)
    return ProjectMaster(**base)


def _common_bridge_selection(**overrides) -> BridgeSelection:
    base = dict(
        bridge_category=BridgeCategory.MINOR_BRIDGE,
        bridge_type=SuperstructureType.SOLID_SLAB,
        span_configuration=SpanConfiguration.SIMPLY_SUPPORTED,
        span_count=1,
        carriageway_config=CarriagewayLaneConfig.LANE_2,
        design_code=DesignCode.IRC_SP_55_2019,
        loading_class="IRC_CLASS_A",
        seismic_zone=SeismicZone.ZONE_III,
        wind_zone_ms=WindSpeedBasic_ms.VB_39_ms_ZONE_2,
        foundation_type=FoundationType.WELL,
    )
    base.update(overrides)
    return BridgeSelection(**base)


def _common_geometry_input(**overrides) -> GeometryInput:
    base = dict(
        span_count=1,
        span_lengths_m=[Decimal("12.0")],
        carriageway_width_m=Decimal("7.00"),
        footpath_left_m=Decimal("1.25"),
        footpath_right_m=Decimal("1.25"),
        skew_angle_deg=Decimal("0"),
    )
    base.update(overrides)
    return GeometryInput(**base)


def _common_superstructure(**overrides) -> Superstructure:
    base = dict(
        type=SuperstructureType.SOLID_SLAB,
        deck_material=ConcreteGrade.M30,
        deck_thickness_mm=350,
        wearing_coat_thickness_mm=40,
        girder_depth_mm=1200,
        girder_spacing_m=Decimal("2.5"),
        girders_per_deck_count=4,
    )
    base.update(overrides)
    return Superstructure(**base)


def _common_substructure(**overrides) -> Substructure:
    base = dict(
        pier_type=PierType.WALL,
        pier_material=ConcreteGrade.M25,
        abutment_type=AbutmentType.CANTILEVER,
        abutment_material=ConcreteGrade.M25,
        pier_height_typical_m=Decimal("4.0"),
    )
    base.update(overrides)
    return Substructure(**base)


def _common_foundation(**overrides) -> FoundationDetails:
    base = dict(
        type=FoundationType.WELL,
    )
    base.update(overrides)
    return FoundationDetails(**base)


def _common_materials(**overrides) -> Materials:
    base = dict(
        concrete_superstructure=ConcreteGrade.M30,
        concrete_substructure=ConcreteGrade.M25,
        concrete_foundation=ConcreteGrade.M20,
        reinforcement_steel_grade=SteelGrade.Fe415,
        prestressing_steel=PrestressGrade.G1860,
        bearing_type=BearingType.ELASTOMERIC_NEOPRENE,
        expansion_joint_type=ExpansionJointType.STRIP_SEAL,
        bearing_material=BearingMaterial.CR_NEOPRENE_CHLOROPRENE,
    )
    base.update(overrides)
    return Materials(**base)


def _common_drawing_control(**overrides) -> DrawingControl:
    base = dict(
        sheet_size=SheetSize.A1,
        drawing_scale=DrawingScale.S200,
        title_block_style=TitleBlockStyle.STANDARD,
    )
    base.update(overrides)
    return DrawingControl(**base)


# ==========================================================================
# Fixture 1 — 12 m valid minor bridge
# ==========================================================================

def build_sample_minor_12m_valid() -> BridgeProject:
    return BridgeProject(
        project_master=_common_project_master(),
        bridge_selection=_common_bridge_selection(),
        geometry_input=_common_geometry_input(),
        superstructure=_common_superstructure(),
        substructure=_common_substructure(),
        foundation_details=_common_foundation(),
        approaches=Approaches(),
        hydraulic_data=HydraulicData(
            return_period_yr="Q50_MAJOR_BRIDGE_STANDARD_2pct_MORTH",
            design_discharge_cumecs=Decimal("120.0"),
            hfl_m=Decimal("102.000"),
            lwl_m=Decimal("98.000"),
            lacey_silt_factor=Decimal("1.0"),
        ),
        materials=_common_materials(),
        bearings_joints=BearingsJoints(),
        components_lib=ComponentsLib(),
        drawing_control=_common_drawing_control(),
        calculations=Calculations(),
        validation=ValidationModel(),
    )


SAMPLE_MINOR_12M_VALID: BridgeProject = build_sample_minor_12m_valid()


# ==========================================================================
# Fixture 2 — 12 m minor bridge with seeded failures for Warning/Info tests
# ==========================================================================

def build_sample_minor_12m_with_bugs() -> BridgeProject:
    return BridgeProject(
        project_master=_common_project_master(
            project_phase=ProjectPhase.CONCEPT,
        ),
        bridge_selection=_common_bridge_selection(
            bridge_type=SuperstructureType.STEEL_PLATE_GIRDER,
            span_count=3,
        ),
        geometry_input=_common_geometry_input(
            span_count=3,
            span_lengths_m=[Decimal("12"), Decimal("12"), Decimal("12")],
            carriageway_width_m=Decimal("16.5"),
            skew_angle_deg=Decimal("35"),
        ),
        superstructure=_common_superstructure(
            type=SuperstructureType.STEEL_PLATE_GIRDER,
            deck_material=ConcreteGrade.M35,
        ),
        substructure=_common_substructure(
            pier_type=PierType.ROUND,
            pier_height_typical_m=Decimal("25.0"),
        ),
        foundation_details=_common_foundation(
            type=FoundationType.PILE,
        ),
        approaches=Approaches(),
        hydraulic_data=HydraulicData(
            return_period_yr="Q10_STANDARD_MINOR_BRIDGE_CULVERT_10pct",
            design_discharge_cumecs=Decimal("200.0"),
            hfl_m=Decimal("103.800"),
            lwl_m=Decimal("96.000"),
            lacey_silt_factor=Decimal("1.2"),
        ),
        materials=_common_materials(
            concrete_superstructure=ConcreteGrade.M65,
            reinforcement_steel_grade=SteelGrade.Fe500,
            bearing_type=BearingType.ELASTOMERIC_NEOPRENE,
        ),
        bearings_joints=BearingsJoints(),
        components_lib=ComponentsLib(),
        drawing_control=_common_drawing_control(
            sheet_size=SheetSize.A0,
        ),
        calculations=Calculations(),
        validation=ValidationModel(),
    )


SAMPLE_MINOR_12M_WITH_BUGS: BridgeProject = build_sample_minor_12m_with_bugs()


# ==========================================================================
# Fixture 3 — 3 × 12 m = 36 m continuous PSC I-Girder major bridge
# ==========================================================================

def build_sample_major_3x12m() -> BridgeProject:
    return BridgeProject(
        project_master=_common_project_master(
            project_title="3-Span 36m Major Bridge across River X",
            project_code="NHAI-2026-112",
            client=ClientType.NHAI,
            bridge_name="River X Bridge @ CH 42+150",
            chainage_km=Decimal("42.150000"),
            total_estimated_cost_inr=Decimal("45000000.00"),
        ),
        bridge_selection=_common_bridge_selection(
            bridge_category=BridgeCategory.MAJOR_BRIDGE,
            bridge_type=SuperstructureType.PSC_IGIRDER,
            span_configuration=SpanConfiguration.CONTINUOUS,
            span_count=3,
            carriageway_config=CarriagewayLaneConfig.LANE_4,
            loading_class="IRC_CLASS_70R",
            foundation_type=FoundationType.PILE,
        ),
        geometry_input=_common_geometry_input(
            span_count=3,
            span_lengths_m=[Decimal("12"), Decimal("12"), Decimal("12")],
            carriageway_width_m=Decimal("14.0"),
            footpath_left_m=Decimal("0.75"),
            footpath_right_m=Decimal("0.75"),
        ),
        superstructure=_common_superstructure(
            type=SuperstructureType.PSC_IGIRDER,
            deck_material=ConcreteGrade.M40,
        ),
        substructure=_common_substructure(
            pier_type=PierType.HAMMERHEAD,
            pier_height_typical_m=Decimal("8.0"),
        ),
        foundation_details=_common_foundation(
            type=FoundationType.PILE,
        ),
        approaches=Approaches(),
        hydraulic_data=HydraulicData(
            return_period_yr="Q100_NHAI_NATIONAL_CORRIDOR_1pct",
            design_discharge_cumecs=Decimal("850.0"),
            hfl_m=Decimal("101.500"),
            lwl_m=Decimal("96.000"),
            lacey_silt_factor=Decimal("0.9"),
        ),
        materials=_common_materials(
            concrete_superstructure=ConcreteGrade.M40,
        ),
        bearings_joints=BearingsJoints(),
        components_lib=ComponentsLib(),
        drawing_control=_common_drawing_control(),
        calculations=Calculations(),
        validation=ValidationModel(),
    )


SAMPLE_MAJOR_3X12M: BridgeProject = build_sample_major_3x12m()


# ==========================================================================
# Fixture 4 — 8 m Box Culvert
# ==========================================================================

def build_sample_culvert_8m_box() -> BridgeProject:
    return BridgeProject(
        project_master=_common_project_master(
            project_title="8 m Single-Cell Box Culvert",
            project_code="PWD-2026-221",
            bridge_name="Culvert CH 12+200",
            chainage_km=Decimal("12.200000"),
            total_estimated_cost_inr=Decimal("3200000.00"),
        ),
        bridge_selection=_common_bridge_selection(
            bridge_category=BridgeCategory.CULVERT,
            bridge_type=SuperstructureType.BOX_CULVERT,
            span_configuration=SpanConfiguration.SIMPLY_SUPPORTED,
            span_count=1,
            carriageway_config=CarriagewayLaneConfig.LANE_2,
            foundation_type=FoundationType.OPEN,
        ),
        geometry_input=_common_geometry_input(
            span_count=1,
            span_lengths_m=[Decimal("8.0")],
            carriageway_width_m=Decimal("7.0"),
            footpath_left_m=Decimal("1.0"),
            footpath_right_m=Decimal("1.0"),
        ),
        superstructure=_common_superstructure(
            type=SuperstructureType.BOX_CULVERT,
            deck_material=ConcreteGrade.M25,
            deck_thickness_mm=400,
        ),
        substructure=_common_substructure(
            abutment_type=AbutmentType.GRAVITY,
            pier_type=PierType.WALL,
            pier_material=ConcreteGrade.M20,
            abutment_material=ConcreteGrade.M20,
        ),
        foundation_details=_common_foundation(
            type=FoundationType.OPEN,
        ),
        approaches=Approaches(),
        hydraulic_data=HydraulicData(
            return_period_yr="Q25_INTERMEDIATE_CULVERT_4pct",
            design_discharge_cumecs=Decimal("60.0"),
            hfl_m=Decimal("101.0"),
            lwl_m=Decimal("99.0"),
            lacey_silt_factor=Decimal("1.1"),
        ),
        materials=_common_materials(
            concrete_superstructure=ConcreteGrade.M25,
        ),
        bearings_joints=BearingsJoints(),
        components_lib=ComponentsLib(),
        drawing_control=_common_drawing_control(
            sheet_size=SheetSize.A2,
            drawing_scale=DrawingScale.S100,
        ),
        calculations=Calculations(),
        validation=ValidationModel(),
    )


SAMPLE_CULVERT_8M_BOX: BridgeProject = build_sample_culvert_8m_box()


# ==========================================================================
# Convenience tuple for parametrized geometry/round-trip tests
# ==========================================================================

THREE_SCENARIOS: tuple[BridgeProject, BridgeProject, BridgeProject] = (
    SAMPLE_MINOR_12M_VALID,
    SAMPLE_MAJOR_3X12M,
    SAMPLE_CULVERT_8M_BOX,
)


__all__ = [
    "SAMPLE_MINOR_12M_VALID",
    "SAMPLE_MINOR_12M_WITH_BUGS",
    "SAMPLE_MAJOR_3X12M",
    "SAMPLE_CULVERT_8M_BOX",
    "THREE_SCENARIOS",
    "build_sample_minor_12m_valid",
    "build_sample_minor_12m_with_bugs",
    "build_sample_major_3x12m",
    "build_sample_culvert_8m_box",
]
