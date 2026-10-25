"""
bridgecad_core.models — Pydantic V2 aggregate (14 sheets -> BridgeProject).
M1 Week 1 Day 3: 100% field coverage with typed constraints.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_validator,
)

from .types import (
    AbutmentBackfillSpecificationType,
    AbutmentPedestalType,
    AbutmentType,
    AcadVersion,
    AdmixtureType,
    AffluxEstimationFormulaType,
    # --- S3 Geometry ---
    AlignmentType,
    AntiCorrosionProtectionType,
    ArchShapeType,
    ArrowStyle,
    BankErosionCategoryClass,
    BankProtectionMethodType,
    BearingCapacitySoilType,
    BearingMaterial,
    BearingType,
    # --- S2 Bridge Selection ---
    BridgeCategory,
    BridgeHydraulicOpeningType,
    BridgeSubcategory,
    CableStayingSystemClass,
    CamberMethod,
    CantileverOverhangType,
    CarriagewayLaneConfig,
    CementType,
    ChainageUnit,
    # --- S1 Project / Client ---
    ClientType,
    ConcreteAggregateType,
    ConcreteCoverNominalClass,
    ConcreteCuringMethodType,
    # --- S8 Materials ---
    ConcreteGrade,
    ConcreteSlumpClass,
    ConcreteSurfaceFinishClass,
    ConsultantType,
    ContractorType,
    ContractPackageType,
    CrashBarrierType,
    CreepShrinkageFactorClass,
    CrossSectionViewTypeCode,
    Currency,
    DampingRatioTypeEnum,
    DeckJointSpacing,
    DeckPourSequenceMethod,
    DesignCode,
    DesignFirmCategoryClass,
    DimensionStyleClass,
    DischargeMeasurementMethod,
    DrainageCrossfallType,
    DrainageType,
    DrawingScale,
    DuctilityClassLink,
    ExpansionJointType,
    FatigueDetailCategorySteel,
    FloodFrequencyAnalysisMethodType,
    FloodReturnPeriodDesign,
    FlowVelocityCategory,
    FontStyle,
    FootpathType,
    FormworkPanelType,
    FormworkReleaseAgentType,
    FoundationType,
    FreeboardAdditionFactorType,
    FrictionCoeffBearingPadType,
    FundingSourceType,
    GirderType,
    GradeControlStructureType,
    GroundImprovementType,
    HatchPatternCode,
    HorizontalCurveTransitionType,
    HydrographShapeType,
    IceLoadType,
    ImpactFactorCoeff,
    IndianStateCode,
    InterchangeGradeSeparationType,
    JointSealantType,
    KerbType,
    LaceyRegimeFactorType,
    Language,
    LayerStandard,
    LineStyleCode,
    LineWeightCode,
    LoadClass,
    LoadCombination,
    MedianType,
    OpenFoundationDepth,
    # --- S9 Drawing ---
    OutputFormat,
    PaintCoatSystemType,
    ParapetType,
    PavementCrustComposition,
    PierCapType,
    PierShaftShape,
    PierTieBeamLocationType,
    # --- S5 Substructure ---
    PierType,
    PileBaseType,
    PileInstallationMethodType,
    PileShape,
    # --- S6 Foundation ---
    PileType,
    PlotterPaperClass,
    PrecastSegmentJointType,
    PrestressGrade,
    PrestressLossTypeEnum,
    ProjectPhase,
    RaftMatType,
    RailingType,
    RebarCouplerType,
    RegimeConstantKValue,
    ReinforcementBarType,
    ResponseSpectrumCategory,
    RetainingWallModeType,
    ReturnWallType,
    RevisionTag,
    RiverBankType,
    RiverBedMaterialSizeType,
    RiverCrossingClass,
    RiverGeomorphologyType,
    RiverTrainingWorkType,
    RotationDirection,
    ScaleDenominatorSet,
    ScourMeasurementMethod,
    ScourProtectionSubtype,
    ScourRegimeType,
    SedimentLoadTransportType,
    SedimentYieldClassification,
    # --- S10 Load / Seismic / Wind ---
    SeismicZone,
    SettlementCriterionCategoryType,
    SheetPileType,
    SheetSize,
    SightDistanceCategory,
    SkewDirection,
    SlabType,
    SoilClass,
    SpanConfiguration,
    SteelGrade,
    SuperelevationRotationAxis,
    SuperstructureSegmentation,
    # --- S4 Superstructure ---
    SuperstructureType,
    SurveyAgency,
    TemperatureLoadDeltaT,
    TenderType,
    TitleBlockRevisionClass,
    TitleBlockStyle,
    TransitionCurveType,
    TrussConfigurationClass,
    UnderReamCount,
    UsageIntensityType,
    # --- Legacy / Validation ---
    ValidationSeverity,
    VerticalAlignmentType,
    ViewTypeClassification,
    WaterproofingMembraneType,
    WaterQualityAggressiveType,
    # --- S7 Hydraulic ---
    WaterSourceType,
    WaterSurfaceProfileType,
    WaterwayCrossingType,
    WearingCoatGrade,
    WearingCoatType,
    WebOpenCutoutType,
    WeldType,
    WellCurbType,
    WellCuttingEdgeShape,
    WellSteiningType,
    WideningTypeOnCurve,
    WindSpeedBasic_ms,
    WingWallType,
    WorkStatusType,
)

# ===========================================================================
# Helper: Pydantic typing shortcuts
# ===========================================================================

def DField(desc=None, ge=None, le=None, dp=3, md=12,
           description=None, decimal_places=None, max_digits=None, **_kw):
    """``Decimal`` :class:`~pydantic.Field` for engineering measurements.

    Parameters
    ----------
    desc / description : str
        Human-readable field description (appears in JSON schema / docs).
    ge, le : number | str | None
        Inclusive lower / upper bounds.  Converted to :class:`Decimal` so
        string inputs (``"0.001"``) avoid float round-trip errors.
    dp / decimal_places : int
        Pydantic ``decimal_places`` constraint (default 3 → mm precision).
    md / max_digits : int
        Pydantic ``max_digits`` constraint (default 12).
    """
    _desc = description if description is not None else desc
    _dp = decimal_places if decimal_places is not None else dp
    _md = max_digits if max_digits is not None else md
    return Field(
        default=None,
        max_digits=_md,
        decimal_places=_dp,
        ge=Decimal(str(ge)) if ge is not None else None,
        le=Decimal(str(le)) if le is not None else None,
        description=_desc,
    )


def IField(desc=None, ge=None, le=None, description=None, **_kw):
    """``int`` :class:`~pydantic.Field` for counts / ordinals / discrete codes.

    Parameters
    ----------
    desc / description : str
        Human-readable field description.
    ge, le : int | None
        Inclusive lower / upper integer bounds.
    """
    _desc = description if description is not None else desc
    return Field(
        default=None,
        ge=ge,
        le=le,
        description=_desc,
    )


def SField(desc=None, maxlen=255, pattern=None, default=None,
           description=None, max_length=None, **_kw):
    """``str`` :class:`~pydantic.Field` for identifiers / freeform text.

    Parameters
    ----------
    desc / description : str
        Human-readable field description.
    maxlen / max_length : int
        Maximum string length (default 255).
    pattern : str | None
        Optional regex pattern for strict code formats.
    default : Any
        Default value when the field is omitted (default ``None``).
    """
    _desc = description if description is not None else desc
    _maxlen = max_length if max_length is not None else maxlen
    return Field(
        default=default,
        max_length=_maxlen,
        pattern=pattern,
        description=_desc,
    )


def BField(desc=None, description=None, **_kw):
    """``bool`` :class:`~pydantic.Field` for boolean flags (default ``False``).

    Parameters
    ----------
    desc / description : str
        Human-readable field description.
    """
    _desc = description if description is not None else desc
    return Field(default=False, description=_desc)


def LField(desc=None, inner_cls=None, description=None, **_kw):
    """``list[inner_cls]`` :class:`~pydantic.Field` with ``default_factory=list``.

    Parameters
    ----------
    desc / description : str
        Human-readable field description.
    inner_cls : type
        Element type for the list (appears in schema / typed consumers).
    """
    _desc = description if description is not None else desc
    return Field(default_factory=list, description=_desc)


# Shorthand aliases — 500+ call sites use these 2-letter names.
# Positional + legacy keywords (dp / md / maxlen) are identical to the
# original lambda signatures to preserve 100 % backward compatibility.
DM = DField
DI = IField
DS = SField
DB = BField
DL = LField


# ===========================================================================
# Sheet 1: PROJECT_MASTER
# ===========================================================================
class ProjectMaster(BaseModel):
    """Sheet 1: PROJECT_MASTER — project identity, stakeholders, metadata."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    project_title: str = DS(
        "Official project title as per tender/contract document",
        maxlen=150,
    )
    project_code: str = DS(
        "Project code format: CLIENT-YYYY-### e.g. NHAI-2026-007",
        maxlen=30,
        pattern=r"^[A-Z][A-Z0-9_]{1,10}-\d{4}-\d{1,5}$",
    )
    bridge_name: str = DS(
        "Bridge / ROB / Culvert official name",
        maxlen=120,
    )
    chainage_km: Decimal | None = DM(
        "Central bridge chainage in kilometres (e.g. 24.350)",
        ge=0, le=9999, dp=6,
    )
    package_no: str | None = DS(
        "Contract package number from tender",
        maxlen=40,
    )
    client: ClientType = Field(
        description="Primary client / employer organisation type",
    )
    consultant: ConsultantType | None = Field(
        default=None,
        description="Detailed design consultant class",
    )
    contractor: ContractorType | None = Field(
        default=None,
        description="EPC / item-rate main contractor class",
    )
    drawing_no: str | None = DS(
        "Parent GAD drawing number as per title block",
        maxlen=50,
    )
    drawing_title: str | None = DS(
        "Drawing title appearing on title block",
        maxlen=150,
    )
    revision: RevisionTag = Field(
        description="Revision tag for this GAD iteration",
    )
    date_issued: date | None = Field(
        default=None,
        description="Date the drawing package is issued for review",
    )
    designed_by: str | None = DS(
        "Name of design engineer responsible",
        maxlen=80,
    )
    checked_by: str | None = DS(
        "Name of checker / senior engineer",
        maxlen=80,
    )
    approved_by: str | None = DS(
        "Name of approving authority / Engineer-in-Charge",
        maxlen=80,
    )
    road_level_rl_m: Decimal | None = DM(
        "Formation / road level Reduced Level at bridge centreline, m",
        ge=-100, le=9000, dp=4,
    )
    ground_level_rl_m: Decimal | None = DM(
        "Existing ground level Reduced Level at abutment, m",
        ge=-100, le=9000, dp=4,
    )
    survey_date: date | None = Field(
        default=None,
        description="Date of topographic / total-station site survey",
    )
    state_code: IndianStateCode = Field(
        description="India state / UT code per project location",
    )
    district_code: str | None = DS(
        "District name or short code (3-4 chars typical)",
        maxlen=40,
    )
    language: Language = Field(
        description="Primary drawing annotation language",
    )
    latitude_deg: Decimal | None = DM(
        "Site centre latitude, decimal degrees (WGS-84)",
        ge=Decimal("6.0"), le=Decimal("36.0"), dp=7,
    )
    longitude_deg: Decimal | None = DM(
        "Site centre longitude, decimal degrees (WGS-84)",
        ge=Decimal("68.0"), le=Decimal("98.0"), dp=7,
    )
    total_estimated_cost_inr: Decimal | None = DM(
        "Total project (works) estimated cost, INR",
        ge=0, le=Decimal("1E12"), dp=2, md=18,
    )
    tender_no: str | None = DS(
        "Tender reference identifier / RFP number",
        maxlen=60,
    )
    contract_no: str | None = DS(
        "Executed contract / agreement number",
        maxlen=60,
    )
    project_phase: ProjectPhase = Field(
        description="Current project delivery phase",
    )
    currency: Currency = Field(
        default=Currency.INR,
        description="Reporting currency for all cost / BOQ fields",
    )
    funding_source: FundingSourceType | None = Field(
        default=None,
        description="Primary funding authority / program",
    )
    tender_type: TenderType | None = Field(
        default=None,
        description="Procurement route (open / limited / single / EPC)",
    )
    contract_package: ContractPackageType | None = Field(
        default=None,
        description="Deliverable package phase (DPR/GAD/Detail/AsBuilt)",
    )
    survey_agency: SurveyAgency | None = Field(
        default=None,
        description="Agency that carried out site survey works",
    )
    work_status: WorkStatusType | None = Field(
        default=None,
        description="Physical project progress status class",
    )
    design_firm_class: DesignFirmCategoryClass | None = Field(
        default=None,
        description="Design office capacity class per COE rules",
    )


# ===========================================================================
# Sheet 2: BRIDGE_SELECTION
# ===========================================================================
class BridgeSelection(BaseModel):
    """Sheet 2: BRIDGE_SELECTION — type, category, loads, code selection."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    bridge_category: BridgeCategory = Field(
        description="Minor / Major / ROB / Culvert / FOB class",
    )
    bridge_type: SuperstructureType = Field(
        description="Primary superstructure framing system",
    )
    span_configuration: SpanConfiguration = Field(
        description="Simply supported / continuous / cantilever / cable-stayed etc.",
    )
    span_count: int = Field(
        default=1, ge=1, le=100,
        description="Total number of spans in the bridge",
    )
    carriageway_config: CarriagewayLaneConfig = Field(
        description="Number of through carriageway lanes (each direction)",
    )
    design_code: DesignCode = Field(
        description="Primary governing design code set for the structure",
    )
    loading_class: LoadClass = Field(
        description="Vehicular live load class per IRC:6 (Class A / 70R / AA / etc.)",
    )
    seismic_zone: SeismicZone = Field(
        description="Seismic zone of site per IS:1893 Part 1 (2016)",
    )
    wind_zone_ms: WindSpeedBasic_ms = Field(
        description="Basic wind speed zone Vb per IS:875 Part 3 (2015)",
    )
    foundation_type: FoundationType = Field(
        description="Primary foundation system adopted",
    )
    subcategory_tag: BridgeSubcategory | None = Field(
        default=None,
        description="Optional BridgeSubcategory tag for quick classification",
    )
    hydraulic_opening_type: BridgeHydraulicOpeningType | None = Field(
        default=None,
        description="Opening classification (Bridge/Culvert/Aqueduct/Underpass)",
    )
    custom_superstructure_note: str | None = DS(
        "Free-form note for unusual superstructure materials or methods",
        maxlen=400,
    )
    custom_substructure_note: str | None = DS(
        "Free-form note on substructure constraints (historic, aesthetic)",
        maxlen=400,
    )
    climate_zone: str | None = DS(
        "Climate classification (e.g. Tropical Wet/Dry, Arid, Mountain)",
        maxlen=60,
    )
    terrain_category: str | None = DS(
        "IS:875 terrain category (1/2/3/4) for wind height factor k1",
        maxlen=40,
    )
    corridor_type: UsageIntensityType | None = Field(
        default=None,
        description="Traffic usage intensity class along this corridor",
    )
    grade_separation: InterchangeGradeSeparationType | None = Field(
        default=None,
        description="Grade separation type (ROB/RUB/Flyover/Interchange)",
    )


# ===========================================================================
# Sheet 3: GEOMETRY_INPUT
# ===========================================================================
class GeometryInput(BaseModel):
    """Sheet 3: GEOMETRY_INPUT — alignment, widths, spans, curves, slopes."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    # --- Spans ---
    span_count: int = Field(
        default=1, ge=1, le=100,
        description="Number of spans (matches len(span_lengths_m))",
    )
    span_lengths_m: list[Decimal] = Field(
        default_factory=lambda: [Decimal("12.0")],
        description="Individual span lengths, metres (order from Abutment-1 to Abutment-2)",
    )
    # --- Alignment ---
    alignment_type: AlignmentType = Field(
        default=AlignmentType.STRAIGHT,
        description="Horizontal alignment type (Straight/Circular/Spiral/Compound)",
    )
    horizontal_curve_transition: HorizontalCurveTransitionType | None = Field(
        default=None,
        description="Transition curve method before/after circular arc",
    )
    transition_curve_type: TransitionCurveType | None = Field(
        default=None,
        description="Spiral / clothoid transition shape class",
    )
    horizontal_curve_R_m: Decimal | None = DM(
        "Horizontal circular curve radius, m (None = straight)",
        ge=Decimal("15"), le=Decimal("30000"), dp=3,
    )
    gradient_pct: Decimal | None = DM(
        "Longitudinal gradient, % (+ = rise, - = fall)",
        ge=Decimal("-8"), le=Decimal("8"), dp=3,
    )
    vertical_alignment: VerticalAlignmentType | None = Field(
        default=None,
        description="Sag / Crest / Straight vertical profile",
    )
    vertical_curve_passing_R_m: Decimal | None = DM(
        "Passing vertical curve radius (crest) for OSD, m",
        ge=Decimal("50"), le=Decimal("100000"), dp=3,
    )
    # --- Cross-section widths ---
    carriageway_width_m: Decimal = DM(
        "Through carriageway width, metres (curb-face to curb-face)",
        ge=Decimal("3.5"), le=Decimal("30"), dp=3,
    )
    footpath_left_m: Decimal | None = DM(
        "Left (CH-increasing) footpath width, m",
        ge=0, le=Decimal("10"), dp=3,
    )
    footpath_right_m: Decimal | None = DM(
        "Right (CH-decreasing) footpath width, m",
        ge=0, le=Decimal("10"), dp=3,
    )
    crash_barrier_width_left_m: Decimal | None = DM(
        "Left crash barrier system width, m",
        ge=0, le=Decimal("2"), dp=3,
    )
    crash_barrier_width_right_m: Decimal | None = DM(
        "Right crash barrier system width, m",
        ge=0, le=Decimal("2"), dp=3,
    )
    kerb_width_left_m: Decimal | None = DM(
        "Left kerb / channeliser width, m",
        ge=0, le=Decimal("2"), dp=3,
    )
    kerb_width_right_m: Decimal | None = DM(
        "Right kerb / channeliser width, m",
        ge=0, le=Decimal("2"), dp=3,
    )
    median_width_m: Decimal | None = DM(
        "Central median width, m (0 = undivided)",
        ge=0, le=Decimal("12"), dp=3,
    )
    median_barrier_width_m: Decimal | None = DM(
        "Median barrier width, m (0 = no barrier on median)",
        ge=0, le=Decimal("2"), dp=3,
    )
    left_ditch_width_m: Decimal | None = DM(
        "Left roadside drain / side-ditch width, m",
        ge=0, le=Decimal("6"), dp=3,
    )
    right_ditch_width_m: Decimal | None = DM(
        "Right roadside drain / side-ditch width, m",
        ge=0, le=Decimal("6"), dp=3,
    )
    service_road_left_m: Decimal | None = DM(
        "Left frontage / service road carriageway width, m",
        ge=0, le=Decimal("15"), dp=3,
    )
    service_road_right_m: Decimal | None = DM(
        "Right frontage / service road carriageway width, m",
        ge=0, le=Decimal("15"), dp=3,
    )
    # --- Skew & curve ---
    skew_angle_deg: Decimal = Field(
        default=Decimal("0.0"), ge=0, le=Decimal("60"), max_digits=5, decimal_places=2,
        description="Angle between normal to alignment and pier line, degrees (0..60 IRC limit)",
    )
    skew_direction: SkewDirection = Field(
        default=SkewDirection.NONE,
        description="Skew side (LEFT_ACUTE / RIGHT_ACUTE / NONE)",
    )
    curved_bridge_flag: bool = DB(
        "True if bridge lies on horizontal circular / spiral curve (not tangent)",
    )
    curve_radius_m: Decimal | None = DM(
        "Radius of curve at deck centroid if curved_bridge_flag = True",
        ge=Decimal("30"), le=Decimal("30000"), dp=3,
    )
    widening_on_curve: WideningTypeOnCurve | None = Field(
        default=None,
        description="Inner/outer/none widening class on curved alignments",
    )
    # --- Camber / Superelevation ---
    camber_mm: int | None = DI(
        "Design pre-camber (crown) height at deck centreline, millimetres",
        ge=0, le=500,
    )
    camber_method: CamberMethod | None = Field(
        default=None,
        description="Camber shape (parabolic/linear/precamber)",
    )
    superelevation_pct: Decimal | None = DM(
        "Applied superelevation cross-slope, % (max 7% urban, 10% rural IRC:73)",
        ge=Decimal("-10"), le=Decimal("10"), dp=3,
    )
    superelevation_rotation_axis: SuperelevationRotationAxis | None = Field(
        default=None,
        description="Rotation axis for superelevation transition (centre/inner-edge)",
    )
    # --- Pavement crust ---
    pavement_thickness_total_mm: int | None = DI(
        "Total crust (bituminous + granular sub-base) thickness, mm",
        ge=0, le=1500,
    )
    crust_layer_count: int | None = DI(
        "Number of distinct crust layers in pavement cross-section",
        ge=0, le=10,
    )
    pavement_crust_composition: PavementCrustComposition | None = Field(
        default=None,
        description="Crust recipe / type classification",
    )
    # --- Chainage ---
    chainage_unit: ChainageUnit = Field(
        default=ChainageUnit.METRE,
        description="Input chainage unit (METRE / KILOMETRE)",
    )
    chainage_start_km: Decimal | None = DM(
        "Starting chainage of abutment-1, km",
        ge=0, le=Decimal("9999"), dp=6,
    )
    chainage_end_km: Decimal | None = DM(
        "Ending chainage of abutment-2, km",
        ge=0, le=Decimal("9999"), dp=6,
    )
    # --- Bearing pad spacing ---
    bearing_pad_spacing_m: Decimal | None = DM(
        "Clear spacing between bearing pads (on one pier cap), m",
        ge=Decimal("0.5"), le=Decimal("20"), dp=3,
    )
    # --- Sight distance ---
    minimum_curve_speed_check_required: bool = DB(
        "Flag: compute min curve speed & sight-distance envelope as part of geometry report",
    )
    sight_distance_category: SightDistanceCategory | None = Field(
        default=None,
        description="Stopping/Passing/Overtaking sight-distance class for design",
    )
    kerb_type: KerbType | None = Field(
        default=None,
        description="Kerb cross-section shape type",
    )
    footpath_type: FootpathType | None = Field(
        default=None,
        description="Footpath / cycle-track / none",
    )
    median_type: MedianType | None = Field(
        default=None,
        description="Central median type (rigid/flexible/none)",
    )
    crash_barrier_type: CrashBarrierType | None = Field(
        default=None,
        description="Metal beam / RCC wall / semi-rigid",
    )
    rotation_direction: RotationDirection | None = Field(
        default=None,
        description="Clockwise / Counter-clockwise (annotation / layout convention)",
    )

    # --- Computed ------------------------------------------------------------
    @computed_field
    @property
    def total_length_m(self) -> Decimal:
        return Decimal(sum(Decimal(str(x)) for x in self.span_lengths_m))

    @computed_field
    @property
    def overall_width_m(self) -> Decimal:
        parts = [self.carriageway_width_m]
        for w in [self.footpath_left_m, self.footpath_right_m,
                  self.crash_barrier_width_left_m, self.crash_barrier_width_right_m,
                  self.kerb_width_left_m, self.kerb_width_right_m,
                  self.median_width_m, self.median_barrier_width_m,
                  self.left_ditch_width_m, self.right_ditch_width_m,
                  self.service_road_left_m, self.service_road_right_m]:
            parts.append(w if w is not None else Decimal("0"))
        return Decimal(sum(Decimal(str(p)) for p in parts))

    @model_validator(mode="after")
    def _span_count_matches_lengths(self):
        if len(self.span_lengths_m) != self.span_count:
            raise ValueError(
                f"span_count ({self.span_count}) must equal len(span_lengths_m) ({len(self.span_lengths_m)})"
            )
        for i, L in enumerate(self.span_lengths_m, 1):
            if not (Decimal("1") <= L <= Decimal("150")):
                raise ValueError(
                    f"span_lengths_m[{i}]={L} out of IRC allowed range [1m, 150m]"
                )
        return self


# ===========================================================================
# Sheet 4: SUPERSTRUCTURE
# ===========================================================================
class Superstructure(BaseModel):
    """Sheet 4: SUPERSTRUCTURE — deck, girders, wearing coat, parapet, drainage."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    type: SuperstructureType = Field(description="Primary framing system")
    deck_material: ConcreteGrade = Field(description="Deck slab concrete grade")
    deck_thickness_mm: int = Field(
        default=220, ge=100, le=1500,
        description="Deck slab nominal thickness mm (excluding wearing coat). Solid-slab decks commonly 200–1200 mm.",
    )
    wearing_coat_type: WearingCoatType | None = Field(
        default=None,
        description="Type of wearing surface (BC / SMA / MS / DBST / AC)",
    )
    wearing_coat_grade: WearingCoatGrade | None = Field(
        default=None,
        description="Wearing coat mix-grade class (MorTH Clause 500 series)",
    )
    wearing_coat_thickness_mm: int | None = DI(
        "Wearing coat compacted thickness, millimetres",
        ge=0, le=500,
    )
    wearing_coat_slope_pct: Decimal | None = DM(
        "Cross-fall slope on carriageway wearing coat, % (typically 2.0)",
        ge=Decimal("-4"), le=Decimal("4"), dp=3,
    )
    drainage_type: DrainageType | None = Field(
        default=None,
        description="Deck drainage outlet type (Scupper / InletPipe / EdgeChannel)",
    )
    drainage_spacing_m: Decimal | None = DM(
        "Longitudinal spacing of deck drainage outlets, metres",
        ge=Decimal("3"), le=Decimal("50"), dp=3,
    )
    drainage_crossfall: DrainageCrossfallType | None = Field(
        default=None,
        description="Deck crossfall direction convention",
    )
    camber_mm: int | None = DI(
        "Parabolic deck camber height at centreline, millimetres",
        ge=0, le=600,
    )
    camber_method: CamberMethod | None = Field(
        default=None,
        description="Camber application method",
    )
    girder_type: GirderType | None = Field(
        default=None,
        description="Girder shape family (I / Box / T / Delta / Plate / Truss)",
    )
    girder_depth_mm: int | None = DI(
        "Nominal girder depth (excluding deck), millimetres (0 = NA for slab/culvert)",
        ge=0, le=8000,
    )
    girder_spacing_m: Decimal | None = DM(
        "Centre-to-centre girder spacing, m (0 = NA for box/slab/culvert)",
        ge=0, le=Decimal("10"), dp=3,
    )
    girders_per_deck_count: int | None = DI(
        "Number of longitudinal girders per deck (cross-section count, 0 = NA)",
        ge=0, le=30,
    )
    slab_type: SlabType | None = Field(
        default=None,
        description="Deck slab structural behaviour (Solid / Voided / Ribbed / HollowCore)",
    )
    slab_effective_flange_width_check: bool = DB(
        "Flag: effective flange width check performed and recorded",
    )
    parapet_type: ParapetType | None = Field(
        default=None,
        description="Edge parapet / roadside barrier class",
    )
    parapet_height_mm: int | None = DI(
        "Parapet top-to-deck height, millimetres (min 1100 for pedestrian)",
        ge=600, le=2500,
    )
    railing_type: RailingType | None = Field(
        default=None,
        description="Footpath / median railing sub-type",
    )
    cantilever_overhang_type: CantileverOverhangType | None = Field(
        default=None,
        description="Cantilever deck slab overhang class",
    )
    cantilever_overhang_left_m: Decimal | None = DM(
        "Left cantilever overhang (from girder CL to deck edge), m",
        ge=0, le=Decimal("5"), dp=3,
    )
    cantilever_overhang_right_m: Decimal | None = DM(
        "Right cantilever overhang (from girder CL to deck edge), m",
        ge=0, le=Decimal("5"), dp=3,
    )
    bearing_shelf_width_m: Decimal | None = DM(
        "Minimum bearing shelf width on diaphragm, m",
        ge=Decimal("0.2"), le=Decimal("3"), dp=3,
    )
    kerb_elevation_mm: int | None = DI(
        "Raised kerb mount height above deck, millimetres",
        ge=0, le=600,
    )
    footpath_elevation_mm: int | None = DI(
        "Footpath top elevation above deck wearing coat, millimetres",
        ge=0, le=500,
    )
    crash_barrier_reinforcement_required: bool = DB(
        "True = crash barrier has dedicated reinforcement cage separate from deck slab",
    )
    transverse_diaphragm_spacing_m: Decimal | None = DM(
        "Longitudinal spacing between transverse diaphragms, m",
        ge=Decimal("1"), le=Decimal("30"), dp=3,
    )
    continuity_slab_thickness_mm: int | None = DI(
        "Continuity slab topping over pier, millimetres (for continuous systems)",
        ge=0, le=1000,
    )
    haunch_height_mm: int | None = DI(
        "Girder-deck haunch depth (initial bedding layer), millimetres",
        ge=0, le=400,
    )
    cable_duct_required: bool = DB(
        "True = embed cable / service ducts through deck slab (electrical / telecom)",
    )
    stay_sag_ratio_for_cable: Decimal | None = DM(
        "Cable-stayed: f/L sag ratio for stay cables",
        ge=Decimal("0.001"), le=Decimal("0.3"), dp=4,
    )
    superstructure_segmentation: SuperstructureSegmentation | None = Field(
        default=None,
        description="Cast-in-place / Precast-balanced-cantilever / Precast-span-by-span",
    )
    precast_segment_joint_type: PrecastSegmentJointType | None = Field(
        default=None,
        description="Precast segmental joint match-cast class",
    )
    deck_joint_spacing: DeckJointSpacing | None = Field(
        default=None,
        description="Longitudinal deck expansion joint spacing class",
    )
    deck_pour_sequence_method: DeckPourSequenceMethod | None = Field(
        default=None,
        description="Concrete deck pour phasing (symmetric/balanced cantilever)",
    )
    web_open_cutout_type: WebOpenCutoutType | None = Field(
        default=None,
        description="Service opening / cutout shape class in girder web",
    )
    cable_staying_system: CableStayingSystemClass | None = Field(
        default=None,
        description="Cable stay arrangement class (Harp/Fan/Modified)",
    )
    arch_shape_type: ArchShapeType | None = Field(
        default=None,
        description="Arch rib shape type (Parabolic/Circular/Tied/Deck/Through)",
    )
    truss_configuration: TrussConfigurationClass | None = Field(
        default=None,
        description="Truss configuration (Warren/Pratt/Howe/Baltimore)",
    )
    waterproofing_membrane: WaterproofingMembraneType | None = Field(
        default=None,
        description="Deck waterproofing membrane product type",
    )
    anti_corrosion_protection: AntiCorrosionProtectionType | None = Field(
        default=None,
        description="Steel / rebar anti-corrosion system",
    )

    # --- Computed ------------------------------------------------------------
    @computed_field
    @property
    def total_deck_thickness_mm(self) -> int:
        """Deck + wearing coat total thickness (mm)."""
        wc = self.wearing_coat_thickness_mm or 0
        return self.deck_thickness_mm + wc

    # --- Conditional validators --------------------------------------------
    _GIRDER_SST = frozenset({
        "RCC_TBEAM", "PSC_IGIRDER", "PSC_U_GIRDER", "PSC_I_GIRDER_COMPOSITE",
        "STEEL_PLATE_GIRDER", "STEEL_TRUSS", "STEEL_COMPOSITE",
        "BALANCED_CANTILEVER", "INCREMENTALLY_LAUNCHED",
    })
    _BOX_SST = frozenset({
        "PSC_BOX_GIRDER", "STEEL_BOX_GIRDER",
    })
    _CULVERT_SST = frozenset({
        "BOX_CULVERT", "PIPE_CULVERT_SINGLE", "PIPE_CULVERT_MULTI",
        "SLAB_CULVERT", "ARCH_CULVERT", "RCC_FRAME_CULVERT",
    })

    @model_validator(mode="after")
    def _conditional_girder_floors(self):
        sst = self.type.name if hasattr(self.type, "name") else str(self.type)
        # Girder-bearing superstructures must have positive girder params
        if sst in self._GIRDER_SST:
            if self.girder_depth_mm is None or self.girder_depth_mm < 200:
                raise ValueError(
                    f"superstructure.type={sst} requires girder_depth_mm >= 200 (got {self.girder_depth_mm})"
                )
            if self.girder_spacing_m is None or self.girder_spacing_m < Decimal("1"):
                raise ValueError(
                    f"superstructure.type={sst} requires girder_spacing_m >= 1.0 (got {self.girder_spacing_m})"
                )
            if self.girders_per_deck_count is None or self.girders_per_deck_count < 1:
                raise ValueError(
                    f"superstructure.type={sst} requires girders_per_deck_count >= 1 (got {self.girders_per_deck_count})"
                )
        # Culverts / slab-only systems: 0 values accepted as N/A
        return self


# ===========================================================================
# Sheet 5: SUBSTRUCTURE
# ===========================================================================
class Substructure(BaseModel):
    """Sheet 5: SUBSTRUCTURE — piers, abutments, wings, returns, backfill."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    # --- Piers ---
    pier_type: PierType = Field(description="Pier family (Wall/Hammerhead/Round/Octagonal)")
    pier_material: ConcreteGrade = Field(description="Pier concrete grade")
    pier_height_typical_m: Decimal | None = DM(
        "Typical pier height (GL to bearing base), m (range 2..50 IRC)",
        ge=Decimal("2"), le=Decimal("50"), dp=3,
    )
    pier_cap_type: PierCapType | None = Field(
        default=None,
        description="Pier cap: drop / non-drop / flared",
    )
    pier_cap_width_m: Decimal | None = DM(
        "Pier cap width (along bridge), m",
        ge=Decimal("0.5"), le=Decimal("20"), dp=3,
    )
    pier_cap_length_m: Decimal | None = DM(
        "Pier cap length (transverse to alignment), m",
        ge=Decimal("1"), le=Decimal("50"), dp=3,
    )
    pier_cap_depth_m: Decimal | None = DM(
        "Pier cap vertical depth, m",
        ge=Decimal("0.3"), le=Decimal("6"), dp=3,
    )
    pier_shaft_shape: PierShaftShape | None = Field(
        default=None,
        description="Pier shaft cross-section shape",
    )
    pier_shaft_width_m: Decimal | None = DM(
        "Pier shaft width (along bridge), m",
        ge=Decimal("0.3"), le=Decimal("10"), dp=3,
    )
    pier_shaft_length_m: Decimal | None = DM(
        "Pier shaft cross-section length (transverse), m",
        ge=Decimal("0.3"), le=Decimal("15"), dp=3,
    )
    pier_diameter_m: Decimal | None = DM(
        "For round/octagonal piers: shaft diameter, m",
        ge=Decimal("0.5"), le=Decimal("10"), dp=3,
    )
    pier_pedestal_height_m: Decimal | None = DM(
        "Pier pedestal (height from cap soffit to bearing plate), m",
        ge=Decimal("0.05"), le=Decimal("3"), dp=3,
    )
    pier_tie_beam_location: PierTieBeamLocationType | None = Field(
        default=None,
        description="Multi-column: tie-beam location (mid-height/top/bottom)",
    )
    pier_diaphragm_required: bool = DB(
        "True = pier diaphragm / cross-beam between shafts constructed",
    )
    pier_hammerhead_overhang_m: Decimal | None = DM(
        "Hammerhead cantilever overhang beyond shaft face, m",
        ge=0, le=Decimal("8"), dp=3,
    )
    bearings_per_pier: int | None = DI(
        "Number of bearings supported on a single pier",
        ge=1, le=60,
    )
    well_cap_width_m: Decimal | None = DM(
        "Well / Caisson top cap (steining cover) width, m",
        ge=Decimal("1"), le=Decimal("15"), dp=3,
    )
    pile_cap_thickness_mm: int | None = DI(
        "Pile cap thickness, millimetres",
        ge=300, le=6000,
    )
    # --- Abutments ---
    abutment_type: AbutmentType = Field(
        description="Abutment system: Cantilever / Counterfort / Wing-wall / Gravity",
    )
    abutment_material: ConcreteGrade = Field(description="Abutment concrete grade")
    abutment_width_m: Decimal | None = DM(
        "Abutment width (along alignment direction), m",
        ge=Decimal("0.3"), le=Decimal("20"), dp=3,
    )
    abutment_length_m: Decimal | None = DM(
        "Abutment transverse length (road width +), m",
        ge=Decimal("3"), le=Decimal("60"), dp=3,
    )
    abutment_height_m: Decimal | None = DM(
        "Abutment height (GL to deck soffit), m",
        ge=Decimal("0.5"), le=Decimal("25"), dp=3,
    )
    abutment_pedestal_type: AbutmentPedestalType | None = Field(
        default=None,
        description="Abutment bearing pedestal sub-class",
    )
    abutment_pedestal_height_m: Decimal | None = DM(
        "Abutment pedestal height (abutment top to bearing plate bottom), m",
        ge=Decimal("0.05"), le=Decimal("2"), dp=3,
    )
    bearings_per_abutment: int | None = DI(
        "Number of bearings at a single abutment",
        ge=1, le=60,
    )
    # --- Wings / Returns ---
    return_wall_type: ReturnWallType | None = Field(
        default=None,
        description="Return (rear) wall at abutment: Cantilever / Buttress / None",
    )
    return_wall_length_m: Decimal | None = DM(
        "Return wall length along embankment, m",
        ge=0, le=Decimal("20"), dp=3,
    )
    return_wall_height_m: Decimal | None = DM(
        "Return wall height (top to base), m",
        ge=0, le=Decimal("12"), dp=3,
    )
    wing_wall_type: WingWallType | None = Field(
        default=None,
        description="Wing-wall arrangement: Parallel / Perpendicular / Splayed / Tapered",
    )
    wing_wall_angle_deg: Decimal | None = DM(
        "Splay angle of wing walls relative to abutment face, degrees",
        ge=0, le=Decimal("90"), dp=2,
    )
    wing_wall_splay_length_m: Decimal | None = DM(
        "Wing wall splay run-out length, m",
        ge=0, le=Decimal("25"), dp=3,
    )
    wing_wall_height_m: Decimal | None = DM(
        "Wing wall max height, m",
        ge=0, le=Decimal("12"), dp=3,
    )
    # --- Backfill / Approach slab ---
    abutment_backfill_spec: AbutmentBackfillSpecificationType | None = Field(
        default=None,
        description="Backfill material gradation class behind abutment",
    )
    backfill_type: str | None = DS(
        "Free-form: selected backfill material (Moorum / Sand / Gravel / Crusher dust)",
        maxlen=120,
    )
    approach_slab_length_m: Decimal | None = DM(
        "Approach / transition slab length, m (typically 3m, 5m or 6m)",
        ge=0, le=Decimal("15"), dp=3,
    )
    approach_slab_thickness_mm: int | None = DI(
        "Approach slab thickness, mm (typical 200-250)",
        ge=0, le=600,
    )


# ===========================================================================
# Sheet 6: FOUNDATION_DETAILS
# ===========================================================================
class FoundationDetails(BaseModel):
    """Sheet 6: FOUNDATION_DETAILS — piles, wells, open, raft, combined footing."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    type: FoundationType = Field(description="Primary foundation system")
    # --- Piles ---
    pile_type: PileType | None = Field(
        default=None,
        description="Pile installation family (Bored/Driven/Under-reamed/Micro/Compaction)",
    )
    pile_shape: PileShape | None = Field(
        default=None,
        description="Pile cross-section shape: Circular / Square / Octagonal",
    )
    pile_base_type: PileBaseType | None = Field(
        default=None,
        description="Pile toe / base detail class",
    )
    pile_installation_method: PileInstallationMethodType | None = Field(
        default=None,
        description="Installation method sub-type",
    )
    pile_diameter_mm: int | None = DI(
        "Pile shaft diameter, millimetres (range 400..2000 IRC typical; 0 = NA for open/well)",
        ge=0, le=3000,
    )
    pile_length_m: Decimal | None = DM(
        "Pile length (cut-off to tip), m (5..60 m range IRC; 0 = NA for open/well)",
        ge=0, le=Decimal("120"), dp=3,
    )
    piles_per_pier: int | None = DI(
        "Number of piles supporting a single pier cap (0 = NA for open/well)",
        ge=0, le=100,
    )
    pile_group_config: str | None = DS(
        "Pile group layout string e.g. 3x3, 4x2, 6x2@2.5m c/c",
        maxlen=80,
    )
    pile_spacing_m: Decimal | None = DM(
        "Centre-to-centre pile spacing (typically 2.5 x diameter), m",
        ge=0, le=Decimal("10"), dp=3,
    )
    pile_cap_thickness_mm: int | None = DI(
        "Pile cap thickness, millimetres (>= 1.5x pile_diameter; 0 = NA)",
        ge=0, le=6000,
    )
    pile_cutoff_level_m: Decimal | None = DM(
        "Pile cut-off level (RL), m",
        ge=Decimal("-100"), le=Decimal("9000"), dp=4,
    )
    under_ream_count: UnderReamCount | None = Field(
        default=None,
        description="Number of under-ream bulbs (0/1/2/3) for under-reamed piles",
    )
    # --- Wells / Caissons ---
    well_diameter_m: Decimal | None = DM(
        "Well (Caisson) outer diameter, m",
        ge=Decimal("1"), le=Decimal("20"), dp=3,
    )
    well_steining_type: WellSteiningType | None = Field(
        default=None,
        description="Well steining material / construction type",
    )
    well_steining_tmm: int | None = DI(
        "Well steining wall thickness, millimetres",
        ge=200, le=2500,
    )
    well_depth_below_bed_m: Decimal | None = DM(
        "Depth of well founding below river bed level, m",
        ge=Decimal("0.5"), le=Decimal("80"), dp=3,
    )
    well_curb_type: WellCurbType | None = Field(
        default=None,
        description="Well cutting curb: RCC / steel-shod",
    )
    well_curb_height_m: Decimal | None = DM(
        "Cutting curb section height, m",
        ge=Decimal("0.3"), le=Decimal("3"), dp=3,
    )
    well_cutting_edge_shape: WellCuttingEdgeShape | None = Field(
        default=None,
        description="Cutting edge: straight chamfer / conical",
    )
    well_sump_depth_m: Decimal | None = DM(
        "Well plug / sump depth inside curb, m",
        ge=0, le=Decimal("10"), dp=3,
    )
    well_cap_width_m: Decimal | None = DM(
        "Well top cap (steining cover block) width, m",
        ge=Decimal("1"), le=Decimal("20"), dp=3,
    )
    # --- Open foundation ---
    open_foundation_depth: OpenFoundationDepth | None = Field(
        default=None,
        description="Open foundation depth category (Shallow / Deep / Stepped)",
    )
    open_width_m: Decimal | None = DM(
        "Open footing width (transverse), m",
        ge=Decimal("0.5"), le=Decimal("30"), dp=3,
    )
    open_length_m: Decimal | None = DM(
        "Open footing length (along alignment), m",
        ge=Decimal("0.5"), le=Decimal("30"), dp=3,
    )
    open_depth_m: Decimal | None = DM(
        "Open footing founding depth below GL, m",
        ge=Decimal("0.5"), le=Decimal("15"), dp=3,
    )
    open_stepped_flag: bool = DB(
        "True = stepped open footing on sloping rock",
    )
    # --- Raft ---
    raft_type: RaftMatType | None = Field(
        default=None,
        description="Raft / mat foundation class (solid/ribbed/piled-raft)",
    )
    raft_thickness_mm: int | None = DI(
        "Raft slab thickness, millimetres",
        ge=300, le=6000,
    )
    raft_reinforcement_dia_mm: int | None = DI(
        "Principal raft reinforcement bar diameter, mm",
        ge=8, le=50,
    )
    # --- Combined footing ---
    combined_footing_length_m: Decimal | None = DM(
        "Combined footing length (along), m",
        ge=Decimal("0.5"), le=Decimal("40"), dp=3,
    )
    combined_footing_width_m: Decimal | None = DM(
        "Combined footing width (transverse), m",
        ge=Decimal("0.5"), le=Decimal("40"), dp=3,
    )
    sheet_pile_type: SheetPileType | None = Field(
        default=None,
        description="Sheet pile temporary / permanent type",
    )
    # --- Bearing capacity ---
    factor_of_safety_on_bearing: Decimal | None = DM(
        "Factor of safety against bearing failure (>=2.5 IRC)",
        ge=Decimal("1.0"), le=Decimal("10"), dp=3,
    )
    bearing_capacity_kpa: Decimal | None = DM(
        "Allowable bearing pressure at founding level, kPa",
        ge=0, le=Decimal("20000"), dp=2,
    )
    bearing_capacity_soil_class: BearingCapacitySoilType | None = Field(
        default=None,
        description="Soil classification for bearing purpose",
    )
    ground_improvement: GroundImprovementType | None = Field(
        default=None,
        description="Ground improvement method if adopted",
    )
    settlement_criterion: SettlementCriterionCategoryType | None = Field(
        default=None,
        description="Settlement limitation class adopted",
    )


# ===========================================================================
# Sheet 7: APPROACHES
# ===========================================================================
class Approaches(BaseModel):
    """Sheet 7: APPROACHES — embankment, retaining walls, shoulders, transitions."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    left_approach_length_m: Decimal | None = DM(
        "Left (A1-side) approach length from abutment toe, m",
        ge=0, le=Decimal("1000"), dp=3,
    )
    right_approach_length_m: Decimal | None = DM(
        "Right (A2-side) approach length from abutment toe, m",
        ge=0, le=Decimal("1000"), dp=3,
    )
    retaining_wall_type: RetainingWallModeType | None = Field(
        default=None,
        description="Retaining wall: Gravity / Cantilever / Counterfort / Mechanically Stabilised Earth",
    )
    retaining_wall_height_m: Decimal | None = DM(
        "Retaining wall retained height, m",
        ge=0, le=Decimal("20"), dp=3,
    )
    type_of_embankment: str | None = DS(
        "Embankment fill type description e.g. 'Granular Moorum / Sand / Select / Boulders'",
        maxlen=120,
    )
    soil_embankment_unit_weight_kN_m3: Decimal | None = DM(
        "Design unit weight of embankment, kN/m^3 (usually 18-22)",
        ge=Decimal("10"), le=Decimal("30"), dp=3,
    )
    approach_slope_width_m: Decimal | None = DM(
        "Embankment side slope run (1V:2H -> 2.0) for a 1 m drop, m/m",
        ge=Decimal("1"), le=Decimal("6"), dp=3,
    )
    shoulder_width_left_m: Decimal | None = DM(
        "Left paved / unpaved shoulder width, m",
        ge=0, le=Decimal("6"), dp=3,
    )
    shoulder_width_right_m: Decimal | None = DM(
        "Right paved / unpaved shoulder width, m",
        ge=0, le=Decimal("6"), dp=3,
    )
    guide_rail_required: bool = DB(
        "Flag: approach guide / safety rail installed on embankment top edge",
    )
    sign_gantry_required: bool = DB(
        "Flag: overhead sign gantry installed on approaches",
    )
    speed_limit_on_approach_kmph: int | None = DI(
        "Posted regulatory speed limit, km/h (0 = no signage)",
        ge=0, le=180,
    )
    transition_curve_length_m: Decimal | None = DM(
        "Length of superelevation / widening transition on approach, m",
        ge=0, le=Decimal("500"), dp=3,
    )
    vertical_alignment_type: VerticalAlignmentType | None = Field(
        default=None,
        description="Approach road vertical alignment type",
    )
    approach_gradient_pct: Decimal | None = DM(
        "Approach longitudinal gradient, % (abs <= 6 MORTH)",
        ge=Decimal("-10"), le=Decimal("10"), dp=3,
    )
    pavement_thickness_mm: int | None = DI(
        "Approach carriageway crust thickness, mm",
        ge=0, le=2000,
    )
    approach_wearing_coat_grade: WearingCoatGrade | None = Field(
        default=None,
        description="Approach wearing coat mix-grade",
    )
    approach_kerb_type: KerbType | None = Field(
        default=None,
        description="Approach kerb shape type",
    )
    approach_drainage_type: DrainageType | None = Field(
        default=None,
        description="Approach carriageway drainage method",
    )
    approach_median_type: MedianType | None = Field(
        default=None,
        description="Approach median type (if divided)",
    )


# ===========================================================================
# Sheet 8: HYDRAULIC_DATA
# ===========================================================================
class HydraulicData(BaseModel):
    """Sheet 8: HYDRAULIC_DATA — flood, scour, waterway, afflux, water quality."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    # --- Discharge ---
    design_discharge_cumecs: Decimal | None = DM(
        "Design flood discharge Q, m3/s (at chosen return period)",
        ge=0, le=Decimal("500000"), dp=3,
    )
    discharge_measurement_method: DischargeMeasurementMethod | None = Field(
        default=None,
        description="How Q was obtained (rating-curve / Gumbel / Rational / 1D model / 2D)",
    )
    # --- Water levels ---
    hfl_m: Decimal | None = DM(
        "High Flood Level (RL), m",
        ge=Decimal("-100"), le=Decimal("9000"), dp=4,
    )
    lwl_m: Decimal | None = DM(
        "Low / Summer Water Level (RL), m",
        ge=Decimal("-100"), le=Decimal("9000"), dp=4,
    )
    normal_wl_m: Decimal | None = DM(
        "Normal / Average annual water level (RL), m",
        ge=Decimal("-100"), le=Decimal("9000"), dp=4,
    )
    scour_level_m: Decimal | None = DM(
        "Design scour level (RL) after applying safety margin, m",
        ge=Decimal("-100"), le=Decimal("9000"), dp=4,
    )
    design_scour_depth_m: Decimal | None = DM(
        "Computed design scour depth (below bed), m",
        ge=0, le=Decimal("30"), dp=3,
    )
    scour_regime: ScourRegimeType | None = Field(
        default=None,
        description="Scour analysis model: Lacey / Regime / USGS / Pelton",
    )
    scour_measurement_method: ScourMeasurementMethod | None = Field(
        default=None,
        description="Scour method on site / in report",
    )
    scour_protection: ScourProtectionSubtype | None = Field(
        default=None,
        description="Scour countermeasure adopted (Launching apron / Rip-rap / Mattress etc.)",
    )
    freeboard_m: Decimal = Field(
        default=Decimal("2.0"),
        max_digits=8, decimal_places=3, ge=Decimal("0.3"), le=Decimal("10"),
        description="Freeboard to be maintained above HFL to deck soffit (m)",
    )
    actual_soffit_level_m: Decimal | None = DM(
        "Actual deck soffit RL at minimum span, m",
        ge=Decimal("-100"), le=Decimal("9000"), dp=4,
    )
    freeboard_addition_factor: FreeboardAdditionFactorType | None = Field(
        default=None,
        description="Extra freeboard factor applied (wave / boat / wind setup)",
    )
    # --- Waterway ---
    waterway_required_m2: Decimal | None = DM(
        "Required (Lacey regime) waterway area, m^2",
        ge=0, le=Decimal("100000"), dp=3,
    )
    waterway_provided_m2: Decimal | None = DM(
        "Provided clear waterway area between abutments, m^2",
        ge=0, le=Decimal("100000"), dp=3,
    )
    regime_waterway_coeff: LaceyRegimeFactorType | None = Field(
        default=None,
        description="Lacey regime waterway coefficient category",
    )
    regime_constant_k: RegimeConstantKValue | None = Field(
        default=None,
        description="Lacey's regime constant K (depends on silt factor)",
    )
    lacey_silt_factor: Decimal | None = DM(
        "Lacey silt factor f = 1.76 sqrt(d50 mm)",
        ge=Decimal("0.1"), le=Decimal("10"), dp=4,
    )
    regime_perimeter_m: Decimal | None = DM(
        "Lacey regime wetted perimeter P = 4.75 sqrt(Q) (m)",
        ge=0, le=Decimal("5000"), dp=3,
    )
    regime_depth_m: Decimal | None = DM(
        "Lacey regime depth R = 0.478 (Q/f^2)^(1/3) metres",
        ge=0, le=Decimal("50"), dp=3,
    )
    regime_velocity_mps: Decimal | None = DM(
        "Regime mean flow velocity V = 10.8 R^(2/3) S^(1/3) ??? or Lacey V = (Q f^2 / 140)^(1/6), m/s",
        ge=0, le=Decimal("10"), dp=4,
    )
    # --- Afflux ---
    afflux_m: Decimal | None = DM(
        "Computed afflux (heading-up) at bridge, m",
        ge=0, le=Decimal("5"), dp=4,
    )
    max_afflux_allowable_m: Decimal | None = DM(
        "Maximum allowable afflux per IRC:5, m (typical 0.3 m)",
        ge=0, le=Decimal("3"), dp=3,
    )
    afflux_formula_type: AffluxEstimationFormulaType | None = Field(
        default=None,
        description="Afflux formula: Kindsvater-Carter / Yarnell / Mavis",
    )
    # --- Site properties ---
    water_source_type: WaterSourceType | None = Field(
        default=None,
        description="Water source: River / Nala / Drain / Culvert / Rainfall / Tidal",
    )
    soil_class_bed: SoilClass | None = Field(
        default=None,
        description="Dominant river-bed soil classification",
    )
    river_bank_type: RiverBankType | None = Field(
        default=None,
        description="River bank protection / geotechnical class",
    )
    river_bed_slope_m_per_km: Decimal | None = DM(
        "Longitudinal bed slope, m/km",
        ge=0, le=Decimal("500"), dp=4,
    )
    catchment_area_sqkm: Decimal | None = DM(
        "Catchment / drainage area up to site, km^2",
        ge=0, le=Decimal("1000000"), dp=3,
    )
    return_period_yr: FloodReturnPeriodDesign | None = Field(
        default=None,
        description="Return period used for design flood (25 / 50 / 100 / PMF)",
    )
    flood_analysis_method: FloodFrequencyAnalysisMethodType | None = Field(
        default=None,
        description="Flood frequency analysis technique",
    )
    hydrograph_shape: HydrographShapeType | None = Field(
        default=None,
        description="Design hydrograph shape / unit hydrograph class",
    )
    any_regime_equation_not_applied_flag: bool = DB(
        "Flag: True = site conditions cause regime equations to not apply; justify in notes",
    )
    highest_recorded_flood_year: int | None = DI(
        "Year of highest recorded flood in historical data",
        ge=1800, le=2200,
    )
    river_geomorphology: RiverGeomorphologyType | None = Field(
        default=None,
        description="River reach geomorphology type (straight/meandering/braided/anastomosing)",
    )
    river_crossing_class: RiverCrossingClass | None = Field(
        default=None,
        description="Major / Medium / Minor river crossing class",
    )
    river_bed_material: RiverBedMaterialSizeType | None = Field(
        default=None,
        description="Bed material size class",
    )
    river_training_work: RiverTrainingWorkType | None = Field(
        default=None,
        description="River training / bank protection works class",
    )
    bank_protection_method: BankProtectionMethodType | None = Field(
        default=None,
        description="Bank protection method adopted (riprap/geo-bag/CC block)",
    )
    bank_erosion_category: BankErosionCategoryClass | None = Field(
        default=None,
        description="Bank erosion hazard class",
    )
    waterway_crossing_type: WaterwayCrossingType | None = Field(
        default=None,
        description="Crossing mode (through over / under / aqueduct)",
    )
    flow_velocity_category: FlowVelocityCategory | None = Field(
        default=None,
        description="Design velocity magnitude class",
    )
    grade_control_structure: GradeControlStructureType | None = Field(
        default=None,
        description="Grade control structure (check dam / weir / sill) if any",
    )
    sediment_load_transport: SedimentLoadTransportType | None = Field(
        default=None,
        description="Sediment load class (wash/bed/suspended)",
    )
    sediment_yield_class: SedimentYieldClassification | None = Field(
        default=None,
        description="Annual sediment yield classification",
    )
    water_surface_profile: WaterSurfaceProfileType | None = Field(
        default=None,
        description="Gradually-varied flow profile class",
    )
    water_quality_aggressive_class: WaterQualityAggressiveType | None = Field(
        default=None,
        description="Concrete aggressivity classification of water",
    )
    ice_load_type: IceLoadType | None = Field(
        default=None,
        description="Ice / floe load class if applicable (hilly terrain)",
    )

    # --- Computed ------------------------------------------------------------
    @computed_field
    @property
    def freeboard_actual_m(self) -> Decimal | None:
        if self.actual_soffit_level_m is None or self.hfl_m is None:
            return None
        return Decimal(self.actual_soffit_level_m) - Decimal(self.hfl_m)

    @model_validator(mode="after")
    def _hfl_exceeds_lwl_when_set(self):
        if (
            self.hfl_m is not None
            and self.lwl_m is not None
            and Decimal(self.hfl_m) < Decimal(self.lwl_m)
        ):
            raise ValueError(f"hfl_m ({self.hfl_m}) must be >= lwl_m ({self.lwl_m})")
        return self


# ===========================================================================
# Sheet 9: MATERIALS
# ===========================================================================
class Materials(BaseModel):
    """Sheet 9: MATERIALS — concrete, rebar, prestress, bearings, joints, coatings."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    # --- Concrete ---
    concrete_superstructure: ConcreteGrade = Field(description="Superstructure concrete grade")
    concrete_substructure: ConcreteGrade = Field(description="Pier / abutment concrete grade")
    concrete_foundation: ConcreteGrade = Field(description="Pile / well / open-footing concrete grade")
    concrete_aggregate: ConcreteAggregateType | None = Field(
        default=None,
        description="Aggregate source / rock type",
    )
    concrete_cover_superstructure_mm: ConcreteCoverNominalClass | None = Field(
        default=None,
        description="Nominal cover class for deck / superstructure",
    )
    concrete_cover_substructure_mm: ConcreteCoverNominalClass | None = Field(
        default=None,
        description="Nominal cover class for substructure",
    )
    concrete_cover_foundation_mm: ConcreteCoverNominalClass | None = Field(
        default=None,
        description="Nominal cover class for foundation",
    )
    concrete_slump_class: ConcreteSlumpClass | None = Field(
        default=None,
        description="Workability / slump class (S1..S5)",
    )
    concrete_curing_method: ConcreteCuringMethodType | None = Field(
        default=None,
        description="Post-pour curing method class",
    )
    concrete_surface_finish: ConcreteSurfaceFinishClass | None = Field(
        default=None,
        description="Fair-faced / Plastered / Paint-grade finish",
    )
    # --- Cement / Admixtures ---
    cement_type: CementType | None = Field(
        default=None,
        description="Cement type (OPC/PPC/PSC/SRC/RHPC etc.)",
    )
    admixture_required: AdmixtureType | None = Field(
        default=None,
        description="Primary concrete admixture (water-reducer / retarder / accelerator)",
    )
    # --- Reinforcement ---
    reinforcement_bar_type: ReinforcementBarType | None = Field(
        default=None,
        description="Rebar family (HYSD Fe415 / TMT Fe500 / Fe500D / Epoxy / Galv)",
    )
    reinforcement_steel_grade: SteelGrade = Field(description="Rebar strength grade (Fe415/500/550)")
    rebar_coupler_type: RebarCouplerType | None = Field(
        default=None,
        description="Mechanical splice / coupler type if used",
    )
    # --- Prestress ---
    prestressing_steel: PrestressGrade = Field(description="Prestress strand / wire grade class")
    prestress_loss_class: PrestressLossTypeEnum | None = Field(
        default=None,
        description="Prestress loss estimation class",
    )
    creep_shrinkage_class: CreepShrinkageFactorClass | None = Field(
        default=None,
        description="Creep & shrinkage factor environment class",
    )
    # --- Bearings / Expansion joints ---
    bearing_type: BearingType = Field(description="Primary bearing type class")
    bearing_material: BearingMaterial | None = Field(
        default=None,
        description="Elastomer / pad material type",
    )
    bearing_friction_pad_class: FrictionCoeffBearingPadType | None = Field(
        default=None,
        description="PTFE / Stainless / Elastomeric friction class",
    )
    expansion_joint_type: ExpansionJointType = Field(description="Expansion joint system class")
    joint_sealant_type: JointSealantType | None = Field(
        default=None,
        description="Expansion joint sealant substance type",
    )
    # --- Wearing coat ---
    wearing_coat_material_type: WearingCoatType | None = Field(
        default=None,
        description="Wearing coat surfacing type",
    )
    wearing_coat_grade: WearingCoatGrade | None = Field(
        default=None,
        description="Wearing coat mix-design grade",
    )
    # --- Welding & metal ---
    weld_type_for_steel: WeldType | None = Field(
        default=None,
        description="Principal weld process for steel components",
    )
    paint_coat_system: PaintCoatSystemType | None = Field(
        default=None,
        description="Paint / coating system class",
    )
    anti_corrosion_protection: AntiCorrosionProtectionType | None = Field(
        default=None,
        description="Corrosion protection system (HDG / Paint / Metalized / Duplex)",
    )
    # --- Misc ---
    brick_type_for_return_walls: str | None = DS(
        "Brick / block type for return / wing wall masonry",
        maxlen=80,
    )
    mortar_type: str | None = DS(
        "Mortar mix ratio (e.g. 1:4 CM, 1:6 CM) for non-structural masonry",
        maxlen=40,
    )
    backfill_material: str | None = DS(
        "Backfill gradation / material spec",
        maxlen=80,
    )
    metal_parapet_finish: str | None = DS(
        "Metal parapet finish description (Hot-dip galvanized + paint / powder coated)",
        maxlen=120,
    )
    formwork_panel_type: FormworkPanelType | None = Field(
        default=None,
        description="Formwork panel face material (Plywood / Steel / Plastic / Aluminium)",
    )
    formwork_release_agent: FormworkReleaseAgentType | None = Field(
        default=None,
        description="Formwork release agent / barrier class",
    )
    waterproofing_membrane: WaterproofingMembraneType | None = Field(
        default=None,
        description="Deck / substructure waterproofing product",
    )


# ===========================================================================
# Sheet 10: BEARINGS_JOINTS — typed schedule rows
# ===========================================================================
class BearingScheduleRow(BaseModel):
    """One row in a bearing schedule (N rows per bridge)."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    location: str = Field(
        description="Bearing location label (P1-A, A1-BEAR-1, etc.)",
        max_length=40,
    )
    bearing_type: BearingType = Field(description="Bearing system used")
    size_x_mm: int | None = DI("Bearing pad / pot dimension X, mm", ge=50, le=5000)
    size_y_mm: int | None = DI("Bearing pad / pot dimension Y, mm", ge=50, le=5000)
    design_load_kn: Decimal | None = DM(
        "Design vertical load (Serviceability), kN",
        ge=0, le=Decimal("100000"), dp=2,
    )
    fixed_or_guide_or_free: str | None = DS(
        "Movement constraint flag: FIXED / GUIDED_X / GUIDED_Y / FREE / POT_FIX / POT_GUIDE",
        maxlen=30,
    )
    elastomeric_layers_count: int | None = DI(
        "Number of rubber layers for elastomeric pad",
        ge=1, le=30,
    )
    steel_back_bool: bool = DB(
        "True = steel-backed elastomeric bearing plate",
    )
    pot_pressure_mpa: Decimal | None = DM(
        "For POT bearing: elastomer compressive pressure, MPa",
        ge=Decimal("10"), le=Decimal("60"), dp=2,
    )
    spherical_rotation_rad: Decimal | None = DM(
        "Spherical bearing design rotation magnitude, rad",
        ge=0, le=Decimal("0.1"), dp=5,
    )
    ptfe_sliding_surface_flag: bool = DB(
        "True = sliding plane PTFE / UHMWPE against stainless steel",
    )
    quantity: int = Field(
        default=1, ge=1, le=1000,
        description="Number of identical bearings in this row location",
    )


class ExpansionJointScheduleRow(BaseModel):
    """One row in an expansion-joint schedule."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    location: str = DS(
        "Expansion joint location string (A1 deck end, P3 mid-span, etc.)",
        maxlen=40,
    )
    joint_type: ExpansionJointType = Field(description="Expansion joint system class")
    width_mm: int | None = DI(
        "Joint finished open width (along deck), mm",
        ge=10, le=2000,
    )
    movement_range_mm: int | None = DI(
        "± total movement capacity, mm",
        ge=0, le=3000,
    )
    gap_mm: int | None = DI(
        "Initial installation gap between deck ends, mm",
        ge=0, le=1000,
    )
    sealant_type: JointSealantType | None = Field(
        default=None,
        description="Joint sealant material class",
    )
    anchor_spacing_mm: int | None = DI(
        "Edge anchor bar centre-to-centre spacing along joint, mm",
        ge=50, le=2000,
    )
    transverse_length_m: Decimal | None = DM(
        "Total joint length (full road width), m",
        ge=Decimal("0.5"), le=Decimal("100"), dp=3,
    )
    quantity: int = Field(
        default=1, ge=1, le=100,
        description="Number of identical joints with this configuration",
    )


class BearingsJoints(BaseModel):
    """Sheet 10: BEARINGS_JOINTS — bearing schedule + expansion joint schedule."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    bearing_schedule: list[BearingScheduleRow] = Field(
        default_factory=list,
        description="One entry per distinct bearing group in the bridge",
    )
    expansion_joint_schedule: list[ExpansionJointScheduleRow] = Field(
        default_factory=list,
        description="One entry per distinct expansion joint location",
    )
    notes_bearings: str | None = DS(
        "General notes on bearing selection, maintenance, installation",
        maxlen=600,
    )
    notes_joints: str | None = DS(
        "General notes on expansion joint sequencing, sealing type",
        maxlen=600,
    )

    # --- Computed ------------------------------------------------------------
    @computed_field
    @property
    def total_bearings_quantity(self) -> int:
        return int(sum(row.quantity for row in self.bearing_schedule))

    @computed_field
    @property
    def total_joints_quantity(self) -> int:
        return int(sum(row.quantity for row in self.expansion_joint_schedule))


# ===========================================================================
# Sheet 11: COMPONENTS_LIB — references to standard / catalogued components
# ===========================================================================
class ComponentsLib(BaseModel):
    """Sheet 11: COMPONENTS_LIB — library keys used by Excel template generator."""

    model_config = ConfigDict(validate_assignment=True, extra="allow")

    standard_pier_tag: str | None = DS(
        "Catalogued pier key from pier library",
        maxlen=60,
    )
    standard_abutment_tag: str | None = DS(
        "Catalogued abutment key from abutment library",
        maxlen=60,
    )
    standard_foundation_tag: str | None = DS(
        "Foundation template identifier",
        maxlen=60,
    )
    typical_girder_library_key: str | None = DS(
        "Girder / superstructure standard library key",
        maxlen=60,
    )
    standard_parapet_id: str | None = DS(
        "Parapet assembly standard ID",
        maxlen=60,
    )
    standard_railing_id: str | None = DS(
        "Railing system standard ID (pedestrian / cycle)",
        maxlen=60,
    )
    standard_retaining_wall_id: str | None = DS(
        "Retaining wall type key from standards library",
        maxlen=60,
    )
    standard_kerb_id: str | None = DS(
        "Kerb cross-section standard ID",
        maxlen=60,
    )
    standard_crash_barrier_id: str | None = DS(
        "Road safety crash barrier standard ID (WB1/WB2/H1/H2 etc.)",
        maxlen=60,
    )
    standard_bearing_typical_pair_id: str | None = DS(
        "Standard pair (fixed + free) bearing ID",
        maxlen=60,
    )
    standard_expansion_joint_id: str | None = DS(
        "Expansion joint standard product / catalog ID",
        maxlen=60,
    )
    standard_drainage_outlet_id: str | None = DS(
        "Deck scupper / drainage outlet standard ID",
        maxlen=60,
    )
    standard_pile_group_template_id: str | None = DS(
        "Pile-group standard arrangement key (e.g. 3x3-PIER, 4x2-ABUT)",
        maxlen=60,
    )
    standard_wing_wall_id: str | None = DS(
        "Wing wall standard assembly key",
        maxlen=60,
    )
    standard_return_wall_id: str | None = DS(
        "Return wall standard assembly key",
        maxlen=60,
    )
    standard_approach_slab_id: str | None = DS(
        "Approach / transition slab standard key",
        maxlen=60,
    )
    standard_drawing_sheet_template_id: str | None = DS(
        "CAD sheet border / title block template ID",
        maxlen=60,
    )
    standard_bill_of_quantities_template_id: str | None = DS(
        "BOQ standard schedule template key",
        maxlen=60,
    )

    # --- Additional component drawing references (added for E2E fixture compatibility) ---
    crash_barrier_drawing_no: str | None = DS(
        "Crash barrier drawing number",
        maxlen=60,
    )
    wearing_coat_drawing_no: str | None = DS(
        "Wearing coat drawing number",
        maxlen=60,
    )
    expansion_joint_drawing_no: str | None = DS(
        "Expansion joint drawing number",
        maxlen=60,
    )
    drainage_spout_type: str | None = DS(
        "Drainage spout type",
        maxlen=60,
    )
    drainage_spout_spacing_m: Decimal | None = DM(
        "Drainage spout spacing in metres",
        ge=Decimal("0"), le=Decimal("1000"), dp=3,
    )
    railing_type: str | None = DS(
        "Railing type",
        maxlen=60,
    )


    # --- Additional standard component drawing references (added for E2E fixture compatibility) ---
    standard_crash_barrier_drawing_no: str | None = DS(
        "Crash barrier drawing number",
        maxlen=60,
    )
    standard_wearing_coat_drawing_no: str | None = DS(
        "Wearing coat drawing number",
        maxlen=60,
    )
    standard_expansion_joint_drawing_no: str | None = DS(
        "Expansion joint drawing number",
        maxlen=60,
    )
    standard_drainage_spout_type: str | None = DS(
        "Drainage spout type",
        maxlen=60,
    )
    standard_drainage_spout_spacing_m: Decimal | None = DM(
        "Drainage spout spacing in metres",
        ge=Decimal("0"), le=Decimal("1000"), dp=3,
    )
    standard_railing_type: str | None = DS(
        "Railing type",
        maxlen=60,
    )



# ===========================================================================
# Sheet 12: DRAWING_CONTROL
# ===========================================================================
class DrawingControl(BaseModel):
    """Sheet 12: DRAWING_CONTROL — formats, sheets, scales, layer/line/font params."""

    model_config = ConfigDict(validate_assignment=True, extra="allow")

    output_formats: list[OutputFormat] = Field(
        default_factory=lambda: [OutputFormat.DXF, OutputFormat.PDF],
        description="Required deliverable file formats (DXF / PDF / DGN / DWG)",
    )
    autocad_version: AcadVersion = Field(
        default=AcadVersion.R2018,
        description="DXF/DWG writing version for CAD interoperability",
    )
    sheet_size: SheetSize = Field(description="ISO / ANSI sheet size selection")
    drawing_scale: DrawingScale = Field(description="Default nominal plotting scale")
    scale_denominator_set: ScaleDenominatorSet | None = Field(
        default=None,
        description="Alternate scale set identifier for drawing series",
    )
    # --- Boolean generate sheet flags ---
    gen_plan_sheet: bool = DB("Generate General Arrangement (PLAN) sheet")
    gen_long_section_sheet: bool = DB("Generate Longitudinal Section / Elevation sheet")
    gen_cross_section_sheet: bool = DB("Generate Typical Cross Sections sheet")
    gen_foundation_sheet: bool = DB("Generate Foundation Layout sheet")
    gen_reinforcement_sheet: bool = DB("Generate Reinforcement Details sheet")
    gen_pier_details_sheet: bool = DB("Generate Pier Details sheet")
    gen_abutment_details_sheet: bool = DB("Generate Abutment Details sheet")
    gen_bearings_joints_sheet: bool = DB("Generate Bearings & Expansion Joints sheet")
    gen_boq_sheet: bool = DB("Generate Bill of Quantities / Schedule sheet")
    gen_cover_sheet: bool = DB("Generate Title / Cover sheet")
    gen_legends_sheet: bool = DB("Generate Legends / Abbreviations / Symbols sheet")
    gen_hydraulics_sheet: bool = DB("Generate Hydraulics & Scour Details sheet")
    gen_retaining_wall_sheet: bool = DB("Generate Retaining Wall / Wing Wall Details sheet")
    gen_approach_road_sheet: bool = DB("Generate Approach Road typicals sheet")
    # --- Transformation ---
    drawing_rotation_deg: Decimal = Field(
        default=Decimal("0.0"), max_digits=6, decimal_places=2,
        ge=Decimal("-180"), le=Decimal("180"),
        description="Plot rotation angle (degrees, CCW positive)",
    )
    north_arrow_size_mm: int | None = DI(
        "North arrow symbol plot size, mm",
        ge=3, le=300,
    )
    scale_bar_length_mm: int | None = DI(
        "Graphic scale bar length, mm",
        ge=20, le=800,
    )
    # --- Standards ---
    layer_standard: LayerStandard = Field(
        default=LayerStandard.IRC,
        description="Layer naming standard (IRC / BS-1192 / ISO-19650)",
    )
    title_block_style: TitleBlockStyle = Field(
        description="Title block frame style",
    )
    title_block_revision_class: TitleBlockRevisionClass | None = Field(
        default=None,
        description="Revision history block class (A/B/C issue vs tender / construction)",
    )
    dimension_precision_mm: int | None = DI(
        "Dimension decimal / rounding precision, millimetres (e.g. 1, 5, 10)",
        ge=0, le=100,
    )
    dimension_style: DimensionStyleClass | None = Field(
        default=None,
        description="Dimension line / arrow / text style class",
    )
    text_height_scale_factor: Decimal | None = DM(
        "Plot-scale multiplier applied to text height table (e.g. 1.2 = 20% larger)",
        ge=Decimal("0.5"), le=Decimal("3"), dp=3,
    )
    lineweight_scale_factor: Decimal | None = DM(
        "Lineweight scale multiplier across all layers",
        ge=Decimal("0.5"), le=Decimal("3"), dp=3,
    )
    line_weight_default: LineWeightCode | None = Field(
        default=None,
        description="Default contour / line weight code (0.25/0.35/0.5 mm)",
    )
    line_style_default: LineStyleCode | None = Field(
        default=None,
        description="Default line style (Continuous / Dashed / Center / Phantom)",
    )
    hatch_pattern_standard: HatchPatternCode | None = Field(
        default=None,
        description="Default hatch pattern for concrete/earth/steel sections",
    )
    font_style: FontStyle | None = Field(
        default=None,
        description="Annotation font family style (ISOCP / ROMANS / etc.)",
    )
    arrow_style: ArrowStyle | None = Field(
        default=None,
        description="Dimension / leader arrow head class",
    )
    plot_style_used: str | None = DS(
        "CTB/STB plot style table name for monochrome or colour plots",
        maxlen=60,
    )
    plotter_paper_class: PlotterPaperClass | None = Field(
        default=None,
        description="Plotter paper type / size class",
    )
    drawing_border_inside_mm: int | None = DI(
        "Inside margin (frame to content border), mm",
        ge=0, le=200,
    )
    revision_block_count: int | None = DI(
        "Max number of revision rows rendered in title block",
        ge=0, le=20,
    )
    legend_sheet_required: bool = DB(
        "Legends / symbols / abbreviations sheet is mandatory for tender issue",
    )
    default_view_type: ViewTypeClassification | None = Field(
        default=None,
        description="Primary view category on first sheet (Plan / Elevation / 3D)",
    )
    default_cross_section_view: CrossSectionViewTypeCode | None = Field(
        default=None,
        description="Cross-section rendering class (Half-symmetric / Full / Cut / Staged)",
    )


# ===========================================================================
# Sheet 13: CALCULATIONS — auto-derived summary outputs
# ===========================================================================
class Calculations(BaseModel):
    """Sheet 13: CALCULATIONS — summary quantities & check outputs derived by engine."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    total_length_m: Decimal | None = DM(
        "Total bridge length = sum of spans, m",
        ge=0, le=Decimal("10000"), dp=3,
    )
    span_count: int | None = DI(
        "Span count (repeated here for cross-check with GI)",
        ge=1, le=100,
    )
    span_depth_ratio: Decimal | None = DM(
        "Span / girder-depth ratio check value (e.g. 20 for T-beam, 30 for PSC Box)",
        ge=Decimal("5"), le=Decimal("80"), dp=3,
    )
    deck_area_sqm: Decimal | None = DM(
        "Deck plan area (overall width x length), m^2",
        ge=0, le=Decimal("100000"), dp=3,
    )
    overall_width_check_ok: bool | None = DB(
        "Overall width >= carriageway + kerbs + barriers + footpaths check passed"
    )
    concrete_volume_superstructure_cum: Decimal | None = DM(
        "Estimated superstructure concrete volume (deck + girders + diaphragms), m^3",
        ge=0, le=Decimal("100000"), dp=3,
    )
    concrete_volume_substructure_cum: Decimal | None = DM(
        "Estimated pier + abutment concrete volume, m^3",
        ge=0, le=Decimal("100000"), dp=3,
    )
    concrete_volume_foundation_cum: Decimal | None = DM(
        "Estimated pile / well / open / raft concrete, m^3",
        ge=0, le=Decimal("100000"), dp=3,
    )
    rebar_weight_tonnes_approx: Decimal | None = DM(
        "Approx total reinforcement tonnage (super+sub+found), tonnes",
        ge=0, le=Decimal("100000"), dp=3,
    )
    prestress_tonnes_approx: Decimal | None = DM(
        "Approx total prestress steel (strands + ducts, tonnes)",
        ge=0, le=Decimal("10000"), dp=3,
    )
    bearing_count: int | None = DI(
        "Total bearings in the bridge",
        ge=0, le=10000,
    )
    expansion_joint_count: int | None = DI(
        "Total expansion joint assemblies",
        ge=0, le=200,
    )
    total_estimated_quantity_cost_inr: Decimal | None = DM(
        "Rough estimate: sum(vol × unit rates) works cost, INR",
        ge=0, le=Decimal("1E14"), dp=2, md=20,
    )
    design_scour_vs_foundation_cover_ok: bool | None = DB(
        "Foundation founding level safely below design scour + margin"
    )
    waterway_check_pass: bool | None = DB(
        "Provided waterway >= required regime waterway"
    )
    afflux_ok: bool | None = DB(
        "Computed afflux <= allowable afflux"
    )
    freeboard_actual_m: Decimal | None = DM(
        "Achieved freeboard = (soffit - HFL), m",
        ge=Decimal("-5"), le=Decimal("30"), dp=4,
    )
    minimum_vertical_clearance_m: Decimal | None = DM(
        "Minimum vertical clearance under deck, m (rail/navigable/road)",
        ge=0, le=Decimal("80"), dp=3,
    )
    horizontal_clearance_m: Decimal | None = DM(
        "Horizontal clearance from edge carriageway to pier face, m",
        ge=0, le=Decimal("30"), dp=3,
    )
    impact_factor_applied: ImpactFactorCoeff | None = Field(
        default=None,
        description="Impact factor I class applied for governing span",
    )
    seismic_coeff_applied: Decimal | None = DM(
        "Seismic zone factor / base shear coefficient used, Ah",
        ge=0, le=Decimal("1"), dp=5,
    )
    deflection_check_ratio_live_load: Decimal | None = DM(
        "Actual / allowable live-load deflection ratio (<= 1 PASS)",
        ge=0, le=Decimal("5"), dp=4,
    )
    load_combination_set: LoadCombination | None = Field(
        default=None,
        description="Governing analysis load-combination identifier",
    )
    temperature_load_delta: TemperatureLoadDeltaT | None = Field(
        default=None,
        description="Temperature rise/fall load case class used",
    )
    damping_ratio_class: DampingRatioTypeEnum | None = Field(
        default=None,
        description="Damping ratio class used in seismic analysis",
    )
    response_spectrum_category: ResponseSpectrumCategory | None = Field(
        default=None,
        description="Site response spectrum (soil) category used",
    )
    fatigue_detail_category_steel: FatigueDetailCategorySteel | None = Field(
        default=None,
        description="Fatigue detail curve category for steel joints",
    )
    ductility_class_link: DuctilityClassLink | None = Field(
        default=None,
        description="Ductility class (OMF/IMF/SMF ductility demand) at piers",
    )


# ===========================================================================
# Sheet 14: VALIDATION_MODEL — engine outputs
# ===========================================================================
class ValidationModel(BaseModel):
    """Sheet 14: VALIDATION — validation engine status & scoring."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    overall_status: ValidationSeverity = Field(
        default=ValidationSeverity.OK_PASS,
        description="Worst severity across all triggered rules",
    )
    critical_fail_count: int = Field(
        default=0, ge=0, le=10000,
        description="Number of CRITICAL / BLOCKER rules fired",
    )
    warning_count: int = Field(
        default=0, ge=0, le=10000,
        description="Number of WARNING / HIGH rules fired",
    )
    info_count: int = Field(
        default=0, ge=0, le=10000,
        description="Number of INFO / SUGGESTION / HINT rules fired",
    )
    score_0_to_100: Decimal = Field(
        default=Decimal("100.0"),
        max_digits=6, decimal_places=2, ge=0, le=100,
        description="Composite quality score 0..100 (100 = perfect)",
    )
    score_irc05: Decimal | None = DM(
        "IRC:5 Hydrology / Scour sub-score, 0..100",
        ge=0, le=100, dp=2,
    )
    score_irc21: Decimal | None = DM(
        "IRC:21 Concrete sub-structure sub-score, 0..100",
        ge=0, le=100, dp=2,
    )
    score_ircsp55: Decimal | None = DM(
        "IRC:SP:55 GAD Drawing Standards sub-score, 0..100",
        ge=0, le=100, dp=2,
    )
    score_structural: Decimal | None = DM(
        "Structural adequacy sub-score, 0..100",
        ge=0, le=100, dp=2,
    )
    score_hydraulic: Decimal | None = DM(
        "Hydraulic adequacy sub-score, 0..100",
        ge=0, le=100, dp=2,
    )
    score_drawing_standards: Decimal | None = DM(
        "Drawing / CAD standards conformance sub-score, 0..100",
        ge=0, le=100, dp=2,
    )
    report_html_or_pdf_generated_flag: bool = DB(
        "True = validation report artefact generated as HTML or PDF file"
    )
    last_validated_at_iso_datetime: datetime | None = Field(
        default=None,
        description="ISO-8601 UTC timestamp of last validation engine run",
    )
    check_version_tag: str | None = DS(
        "Validation rule-set semantic version tag (e.g. 1.4.2-day3)",
        maxlen=40,
    )
    rules_run_count: int | None = DI(
        "Number of rule checks actually executed in last run",
        ge=0, le=100000,
    )
    rules_skipped_count: int | None = DI(
        "Number of checks skipped due to pre-condition / missing data",
        ge=0, le=100000,
    )
    score_materials: Decimal | None = DM(
        "Materials spec conformance sub-score, 0..100",
        ge=0, le=100, dp=2,
    )
    score_geometry: Decimal | None = DM(
        "Geometry & alignment conformance sub-score, 0..100",
        ge=0, le=100, dp=2,
    )


# ===========================================================================
# Aggregate: BRIDGE_PROJECT
# ===========================================================================
class BridgeProject(BaseModel):
    """Top-level aggregate — 14 sheets unified into one validation-scoped root."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    project_master: ProjectMaster = Field(default_factory=ProjectMaster)
    bridge_selection: BridgeSelection = Field(default_factory=BridgeSelection)
    geometry_input: GeometryInput = Field(default_factory=GeometryInput)
    superstructure: Superstructure = Field(default_factory=Superstructure)
    substructure: Substructure = Field(default_factory=Substructure)
    foundation_details: FoundationDetails = Field(default_factory=FoundationDetails)
    approaches: Approaches = Field(default_factory=Approaches)
    hydraulic_data: HydraulicData = Field(default_factory=HydraulicData)
    materials: Materials = Field(default_factory=Materials)
    bearings_joints: BearingsJoints = Field(default_factory=BearingsJoints)
    components_lib: ComponentsLib = Field(default_factory=ComponentsLib)
    drawing_control: DrawingControl = Field(default_factory=DrawingControl)
    calculations: Calculations = Field(default_factory=Calculations)
    validation: ValidationModel = Field(default_factory=ValidationModel)

    # --- Top-level computed aliases for templates ---------------------------
    @computed_field
    @property
    def total_bridge_length_m(self) -> Decimal:
        return self.geometry_input.total_length_m

    @computed_field
    @property
    def overall_bridge_width_m(self) -> Decimal:
        return self.geometry_input.overall_width_m

    @computed_field
    @property
    def span_count_propagated(self) -> int:
        return self.geometry_input.span_count


__all__ = [
    "ProjectMaster", "BridgeSelection", "GeometryInput", "Superstructure",
    "Substructure", "FoundationDetails", "Approaches", "HydraulicData",
    "Materials", "BearingScheduleRow", "ExpansionJointScheduleRow",
    "BearingsJoints", "ComponentsLib", "DrawingControl",
    "Calculations", "ValidationModel", "BridgeProject",
]
