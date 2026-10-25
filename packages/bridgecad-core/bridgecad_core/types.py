"""
bridgecad_core.types — 200+ Enums.
M1 Week 1 Day 1: Mixins + Sections 1–6 (Project/Client → Bridge Selection →
Geometry → Superstructure → Substructure → Foundation). 86+ enum classes today.
M1 Week 1 Day 2: Sections 7–10 (Hydraulic, Materials, Drawing, Load/Seismic/Wind).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any

# ===========================================================================
# Fuzzy normalisation for enum name/value matching
# ===========================================================================

_SEP_RE = re.compile(r"[\s_\-:/]+")


def _fuzzy_norm(s: str) -> str:
    """Normalise a string so underscores / hyphens / colons / slashes / spaces
    all become a single underscore, then uppercase, for tolerant matching
    (e.g. ``IRC_112_2020`` ``IRC:112-2020`` ``IRC 112 / 2020`` all match)."""
    return _SEP_RE.sub("_", s.strip()).upper()


# ===========================================================================
# Mixin base classes
# ===========================================================================


class StrEnum(str, Enum):
    """String-valued enum base (backwards-compat with all existing consumers).

    Pydantic deserialisation accepts three forms (case-insensitive, fuzzy):
      1. exact Enum.value match
      2. exact Enum.name match
      3. normalised match (``_`` / ``-`` / ``:`` / ``/`` / whitespace interchangeable)
    """

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> Any:
        from pydantic_core import core_schema

        def _coerce(v: Any) -> StrEnum:
            if isinstance(v, cls):
                return v
            if v is None:
                raise TypeError("expected a string, got None")
            if isinstance(v, str):
                s = v
            else:
                try:
                    s = str(v)
                except Exception as exc:  # pragma: no cover - unlikely
                    raise TypeError(f"cannot convert {type(v).__name__} to {cls.__name__}") from exc

            if s in cls._value2member_map_:
                return cls(s)

            # Exact name match (case-insensitive)
            su = s.strip()
            for m in cls:
                if m.name.upper() == su.upper():
                    return m
            # Exact value match (case-insensitive)
            for m in cls:
                if str(m.value).strip().upper() == su.upper():
                    return m

            # Fuzzy normalised match
            fuzzy = _fuzzy_norm(s)
            for m in cls:
                if _fuzzy_norm(m.name) == fuzzy or _fuzzy_norm(str(m.value)) == fuzzy:
                    return m

            # Build helpful error
            names = [m.name for m in cls]
            values = [str(m.value) for m in cls]
            raise ValueError(
                f"{s!r} is not a valid {cls.__name__}. "
                f"Accepted names={names[:25]}{'...' if len(names) > 25 else ''}; "
                f"accepted values={values[:25]}{'...' if len(values) > 25 else ''}"
            )

        enum_values = [str(m.value) for m in cls]

        # Use Pydantic's standard Enum handling: preserves Enum member objects
        # in Python mode + correctly serialises StrEnum to the raw string value
        # in JSON mode (str(StrEnum.x) -> the value, thanks to __str__ override
        # defined just above).
        try:
            base_schema = handler(source_type)
        except Exception:
            base_schema = core_schema.any_schema()

        validated = core_schema.no_info_before_validator_function(_coerce, base_schema)
        validated["metadata"] = {"enum": enum_values} if enum_values else {}
        return validated

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema_: Any, handler: Any) -> Any:
        from pydantic.json_schema import JsonSchemaValue

        schema: JsonSchemaValue = handler(core_schema_)
        # Normative enum declaration — FastAPI / Swagger / TypeScript generators
        # see a real enum instead of a plain string with metadata-only hints.
        schema["type"] = "string"
        schema["enum"] = [str(m.value) for m in cls]
        return schema


class IntEnumStrict(IntEnum):
    """Strict int enum base with explicit OpenAPI serialization contract.

    Serialises to the raw :class:`int` value so FastAPI / Swagger / OpenAPI
    generators see an ``integer`` type with a normative ``enum`` list rather
    than an opaque object.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> Any:
        from pydantic_core import core_schema

        def _coerce(v: Any) -> IntEnumStrict:
            if isinstance(v, cls):
                return v
            try:
                iv = int(v)
            except Exception as exc:
                raise TypeError(f"expected int for {cls.__name__}, got {type(v).__name__}") from exc
            if iv in cls._value2member_map_:
                return cls(iv)
            names = [m.name for m in cls]
            vals = [m.value for m in cls]
            raise ValueError(f"{iv!r} is not a valid {cls.__name__}. Names={names}; Values={vals}")

        enum_values = [int(m.value) for m in cls]

        # Use Pydantic's native IntEnum handling: keeps Enum member objects in
        # Python mode and emits plain ints in JSON mode.
        try:
            base_schema = handler(source_type)
        except Exception:
            base_schema = core_schema.any_schema()

        validated = core_schema.no_info_before_validator_function(_coerce, base_schema)
        validated["metadata"] = {"enum": enum_values} if enum_values else {}
        return validated

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema_: Any, handler: Any) -> Any:
        from pydantic.json_schema import JsonSchemaValue

        schema: JsonSchemaValue = handler(core_schema_)
        # Normative OpenAPI-friendly enum + type declaration
        schema["type"] = "integer"
        schema["enum"] = [int(m.value) for m in cls]
        return schema


@dataclass(frozen=True)
class _Range:
    min: float
    max: float
    unit: str | None = None


class LabeledEnum(StrEnum):
    """Enum base where every member has a human-friendly `.label` attribute."""

    @property
    def label(self) -> str:
        """Return a human-friendly display label. Falls back to name if not overridden."""
        return self.name.replace("_", " ").title()


class UnitHaverEnum(LabeledEnum):
    """Enum base whose members also declare a unit string (m, mm, kN, MPa, ...)."""

    unit: str

    def __new__(cls, value: str, unit: str | None = None) -> UnitHaverEnum:
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.unit = unit or ""
        return obj


class RangeBoundedEnum(LabeledEnum):
    """Enum base whose members also declare a numeric (min, max) range."""

    bounds: _Range

    def __new__(
        cls,
        value: str,
        min_v: float | None = None,
        max_v: float | None = None,
        unit: str | None = None,
    ) -> RangeBoundedEnum:
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.bounds = _Range(
            min=float(min_v if min_v is not None else float("-inf")),
            max=float(max_v if max_v is not None else float("inf")),
            unit=unit,
        )
        return obj

    @property
    def range_min(self) -> float:
        return self.bounds.min

    @property
    def range_max(self) -> float:
        return self.bounds.max

    @property
    def unit(self) -> str | None:
        return self.bounds.unit

    def contains(self, x: float) -> bool:
        return self.range_min <= x <= self.range_max


# ===========================================================================
# SECTION 1 — PROJECT / CLIENT
# ===========================================================================


class ClientType(LabeledEnum):
    NHAI = "NHAI"
    NHAI_NATIONAL_HIGHWAYS = "NHAI_NATIONAL_HIGHWAYS"
    STATE_PWD = "STATE_PWD"
    RAILWAYS = "RAILWAYS"
    MUNICIPAL_CORPORATION = "MUNICIPAL_CORPORATION"
    NHAIDC = "NHAIDC"
    MORTH = "MORTH"
    BRO = "BRO"
    PVT_DEVELOPER = "PVT_DEVELOPER"
    PORT_AUTHORITY = "PORT_AUTHORITY"
    AIRPORTS_AUTHORITY = "AIRPORTS_AUTHORITY"
    IRRIGATION_DEPT = "IRRIGATION_DEPT"
    OTHER = "OTHER"


class ConsultantType(LabeledEnum):
    IN_HOUSE = "IN_HOUSE"
    TIER1_ENGINEERING = "TIER1_ENGINEERING"
    TIER2_ENGINEERING = "TIER2_ENGINEERING"
    LIMITED_CONSULTANT_A_GRADE = "LIMITED_CONSULTANT_A_GRADE"
    SITE_SUPERVISION = "SITE_SUPERVISION"
    DPR_CONSULTANT = "DPR_CONSULTANT"
    PMC = "PMC"
    LENDER_IPC = "LENDER_IPC"
    OTHER = "OTHER"


class ContractorType(LabeledEnum):
    MAIN_CONTRACTOR = "MAIN_CONTRACTOR"
    SUBCONTRACTOR_FOUNDATION = "SUBCONTRACTOR_FOUNDATION"
    SUBCONTRACTOR_SUPERSTRUCTURE = "SUBCONTRACTOR_SUPERSTRUCTURE"
    SUBCONTRACTOR_EARTHWORK = "SUBCONTRACTOR_EARTHWORK"
    EPC = "EPC"
    INFRA_LARGE_TIER1_EPC = "INFRA_LARGE_TIER1_EPC"
    TURNKEY = "TURNKEY"
    DESIGN_BUILD = "DESIGN_BUILD"
    OTHER = "OTHER"


class ProjectPhase(LabeledEnum):
    CONCEPT = "CONCEPT"
    PROPOSED = "PROPOSED"
    DPR = "DPR"
    DESIGN_GAD_30_PCT = "DESIGN_GAD_30_PCT"
    DESIGN_GAD_60_PCT = "DESIGN_GAD_60_PCT"
    DESIGN_GAD_90_PCT = "DESIGN_GAD_90_PCT"
    DESIGN_GAD_100_PCT_IFC = "DESIGN_GAD_100_PCT_IFC"
    TENDER = "TENDER"
    AWARDED = "AWARDED"
    UNDER_CONSTRUCTION = "UNDER_CONSTRUCTION"
    COMMISSIONED = "COMMISSIONED"
    MAINTENANCE = "MAINTENANCE"
    REHAB = "REHABILITATION"
    DEMOLITION = "DEMOLITION"


class Currency(LabeledEnum):
    INR = "INR"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    AED = "AED"
    SGD = "SGD"
    AUD = "AUD"


class RevisionTag(LabeledEnum):
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    R5 = "R5"
    R6 = "R6"
    R7 = "R7"
    R8 = "R8"
    R9 = "R9"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    ISSUE_FOR_TENDER = "IFT"
    ISSUE_FOR_CONSTRUCTION = "IFC"
    ISSUE_FOR_APPROVAL = "IFA"


class Language(LabeledEnum):
    EN = "EN"
    HI = "HI"
    BILINGUAL_EN_HI = "EN_HI"
    MR = "MR"
    GU = "GU"
    TA = "TA"
    TE = "TE"
    KN = "KN"
    ML = "ML"
    BN = "BN"
    OR = "OR"
    RJ = "RJ"
    UP = "UP"
    PJ = "PB"
    AS = "AS"


class IndianStateCode(LabeledEnum):
    MH = "MH"
    GJ = "GJ"
    RJ = "RJ"
    MP = "MP"
    CG = "CG"
    UP = "UP"
    UK = "UK"
    DL = "DL"
    HR = "HR"
    PB = "PB"
    HP = "HP"
    JK = "JK"
    LA = "LA"
    BR = "BR"
    JH = "JH"
    BH = "BH"
    WB = "WB"
    OR = "OR"
    AS = "AS"
    TR = "TR"
    ML = "ML"
    MZ = "MZ"
    MN = "MN"
    NL = "NL"
    AR = "AR"
    SK = "SK"
    KA = "KA"
    TN = "TN"
    KL = "KL"
    AP = "AP"
    TS = "TS"
    GA = "GA"
    PY = "PY"
    DN = "DN_DD"
    DD = "DD"
    LD = "LD"
    AN = "AN_NI"
    CH = "CH"
    DL_NCT = "NCT_DELHI"


class SurveyAgency(LabeledEnum):
    SOI = "SOI"
    GSI = "GSI"
    PWD = "PWD"
    NHAI = "NHAI"
    PRIVATE = "PRIVATE"
    IN_HOUSE = "IN_HOUSE"
    CPCB = "CPCB"
    SPCB = "SPCB"
    OTHER = "OTHER"


class TenderType(LabeledEnum):
    OPEN = "OPEN_TENDER"
    LIMITED = "LIMITED_TENDER"
    SINGLE_TENDER = "SINGLE_TENDER"
    EPC = "EPC"
    DESIGN_BUILD = "DESIGN_BUILD"
    PPP_BOT = "PPP_BOT"
    PPP_TOLL = "PPP_TOLL"
    PPP_HAM = "PPP_HAM"
    PPP_DBFOT = "PPP_DBFOT"
    OTHER = "OTHER"


# ===========================================================================
# SECTION 2 — BRIDGE CATEGORY / SELECTION
# ===========================================================================


class BridgeCategory(LabeledEnum):
    MAJOR_BRIDGE = "MAJOR_BRIDGE"
    MAJOR_ROB_RAIL_OVER_BRIDGE = "MAJOR_ROB_RAIL_OVER_BRIDGE"
    MINOR_BRIDGE = "MINOR_BRIDGE"
    VIADUCT = "VIADUCT"
    ROB = "ROB"
    RUB = "RUB"
    FOB = "FOB"
    CULVERT = "CULVERT"
    SUBWAY = "SUBWAY"
    PEDESTRIAN_UNDERPASS = "PED_UNDERPASS"
    ANIMAL_OVERPASS = "ANIMAL_OVERPASS"
    FLYOVER = "FLYOVER"
    INTERCHANGE_RAMP = "INTERCHANGE_RAMP"
    CAUSEWAY = "CAUSEWAY"
    SUBMERSIBLE_BRIDGE = "SUBMERSIBLE_BRIDGE"
    BAILEY_BRIDGE = "BAILEY_BRIDGE"
    PONTOON_BRIDGE = "PONTOON_BRIDGE"


class SuperstructureType(LabeledEnum):
    RCC_TBEAM = "RCC_TBEAM"
    PSC_IGIRDER = "PSC_IGIRDER"
    PSC_BOX_GIRDER = "PSC_BOX_GIRDER"
    PSC_U_GIRDER = "PSC_U_GIRDER"
    PSC_I_GIRDER_COMPOSITE = "PSC_I_GIRDER_COMPOSITE"
    SOLID_SLAB = "SOLID_SLAB"
    VOIDED_SLAB = "VOIDED_SLAB"
    BALANCED_CANTILEVER = "BALANCED_CANTILEVER"
    CABLE_STAYED = "CABLE_STAYED"
    SUSPENSION = "SUSPENSION"
    EXTRADOSED = "EXTRADOSED"
    STEEL_PLATE_GIRDER = "STEEL_PLATE_GIRDER"
    STEEL_TRUSS = "STEEL_TRUSS"
    STEEL_COMPOSITE = "STEEL_COMPOSITE"
    STEEL_BOX_GIRDER = "STEEL_BOX_GIRDER"
    STEEL_ARCH = "STEEL_ARCH"
    CONCRETE_ARCH_THROUGH = "CONCRETE_ARCH_THROUGH"
    CONCRETE_ARCH_DECK = "CONCRETE_ARCH_DECK"
    MASONRY_ARCH = "MASONRY_ARCH"
    BOX_CULVERT = "BOX_CULVERT"
    PIPE_CULVERT_SINGLE = "PIPE_CULVERT_SINGLE"
    PIPE_CULVERT_MULTI = "PIPE_CULVERT_MULTI"
    SLAB_CULVERT = "SLAB_CULVERT"
    ARCH_CULVERT = "ARCH_CULVERT"
    RCC_FRAME_CULVERT = "RCC_FRAME_CULVERT"
    BAILEY_PANEL = "BAILEY_PANEL"
    PREFAB_PSC_SLAB = "PREFAB_PSC_SLAB"
    HYBRID_STEEL_CONCRETE = "HYBRID_STEEL_CONCRETE"
    MOVABLE_BRIDGE_BASCULE = "MOVABLE_BRIDGE_BASCULE"
    MOVABLE_BRIDGE_SWING = "MOVABLE_BRIDGE_SWING"
    MOVABLE_BRIDGE_LIFT = "MOVABLE_BRIDGE_LIFT"


class SpanConfiguration(LabeledEnum):
    SIMPLY_SUPPORTED = "SIMPLY_SUPPORTED"
    CONTINUOUS = "CONTINUOUS"
    CANTILEVER_SUSPENDED = "CANTILEVER_SUSPENDED"
    BALANCED_CANTILEVER = "BALANCED_CANTILEVER"
    INCREMENTALLY_LAUNCHED = "INCREMENTALLY_LAUNCHED"
    CABLE_STAYED_STIFFENING_GIRDER = "CABLE_STAYED_SG"
    SUSPENSION_SG = "SUSPENSION_SG"
    EXTRADOSED = "EXTRADOSED"
    ARCH_FILLED = "ARCH_FILLED"
    ARCH_OPEN = "ARCH_OPEN_SPANDREL"
    FIXED_FIXED = "FIXED_FIXED"
    RIGID_FRAME = "RIGID_FRAME"
    BOWSTRING_ARCH = "BOWSTRING_ARCH"


class CarriagewayLaneConfig(LabeledEnum):
    LANE_1 = "1_LANE"
    LANE_1_PLUS_SHOULDER = "1_LANE_WIDE"
    LANE_2 = "2_LANE"
    LANE_3 = "3_LANE"
    LANE_4 = "4_LANE"
    LANE_5 = "5_LANE"
    LANE_6 = "6_LANE"
    LANE_8 = "8_LANE"
    TWO_LANE_7M5_CLASS_A = "TWO_LANE_7M5_CLASS_A"
    FOUR_LANE_14M_CLASS_A = "FOUR_LANE_14M_CLASS_A"
    MULTI_LEVEL_STACKED = "MULTI_LEVEL_STACKED"
    DUAL_CARRIAGEWAY_4 = "DUAL_CW_4_LANE"
    DUAL_CARRIAGEWAY_6 = "DUAL_CW_6_LANE"
    DUAL_CARRIAGEWAY_8 = "DUAL_CW_8_LANE"


class BridgeSubcategory(LabeledEnum):
    MINOR_12M = "MINOR_12M"
    MINOR_15M = "MINOR_15M"
    MINOR_18M = "MINOR_18M"
    MAJOR_3X12M = "MAJOR_3X12M"
    MAJOR_4X15M = "MAJOR_4X15M"
    MAJOR_5X20M = "MAJOR_5X20M"
    MAJOR_6X25M = "MAJOR_6X25M"
    MAJOR_7X30M = "MAJOR_7X30M"
    VIADUCT_10X30M = "VIADUCT_10X30M"
    VIADUCT_20X35M = "VIADUCT_20X35M"
    VIADUCT_CURVED = "VIADUCT_CURVED"
    ROB_SINGLE_TRACK = "ROB_SINGLE_RAIL"
    ROB_DOUBLE_TRACK = "ROB_DOUBLE_RAIL"
    RUB_SINGLE_TRACK = "RUB_SINGLE_RAIL"
    RUB_DOUBLE_TRACK = "RUB_DOUBLE_RAIL"
    FOB_SINGLE_SPAN = "FOB_SINGLE_SPAN"
    FOB_MULTI_SPAN = "FOB_MULTI_SPAN"
    FOB_WITH_ESCALATOR = "FOB_W_ESCALATOR"
    FOB_WITH_LIFT = "FOB_W_LIFT"
    BOX_CULVERT_6X4M = "BOX_CULVERT_6X4M"
    BOX_CULVERT_8X5M = "BOX_CULVERT_8X5M"
    BOX_CULVERT_12X6M = "BOX_CULVERT_12X6M"
    BOX_CULVERT_2CELL = "BOX_CULVERT_2CELL"
    BOX_CULVERT_3CELL = "BOX_CULVERT_3CELL"
    BOX_CULVERT_4CELL = "BOX_CULVERT_4CELL"
    PIPE_CULVERT_1200 = "PIPE_CULVERT_1200"
    PIPE_CULVERT_1500 = "PIPE_CULVERT_1500"
    PIPE_CULVERT_1800 = "PIPE_CULVERT_1800"
    PIPE_CULVERT_DOUBLE_1200 = "PIPE_CULVERT_DBL_1200"
    SLAB_CULVERT_5M = "SLAB_CULVERT_5M"
    SLAB_CULVERT_8M = "SLAB_CULVERT_8M"
    ARCH_CULVERT_12M = "ARCH_CULVERT_12M"
    ARCH_CULVERT_18M = "ARCH_CULVERT_18M"
    ARCH_CULVERT_24M = "ARCH_CULVERT_24M"
    CUSTOM = "CUSTOM"


class CarriagewaySkewConfig(LabeledEnum):
    STRAIGHT_NO_SKEW = "STRAIGHT_0_DEG"
    LOW_SKEW_0_TO_15 = "LOW_SKEW_0_15"
    MEDIUM_SKEW_15_TO_30 = "MEDIUM_SKEW_15_30"
    HIGH_SKEW_30_TO_45 = "HIGH_SKEW_30_45"
    EXTREME_SKEW_45_TO_60 = "EXTREME_SKEW_45_60"
    CURVED_STRAIGHT_SKEW_MIXED = "CURVED_MIXED"


# ===========================================================================
# SECTION 3 — GEOMETRY
# ===========================================================================


class SkewDirection(LabeledEnum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    NONE = "NONE"
    ALTERNATING = "ALTERNATING"


class AlignmentType(LabeledEnum):
    STRAIGHT = "STRAIGHT"
    CIRCULAR_CURVE = "CIRCULAR_CURVE"
    SPIRAL_TRANSITION = "SPIRAL_TRANSITION"
    COMPOUND_CURVE = "COMPOUND_CURVE"
    REVERSE_CURVE = "REVERSE_CURVE"
    STRAIGHT_PLUS_CURVES = "STRAIGHT_PLUS_CURVES"
    FULL_CURLINEAR = "FULL_CURLINEAR"


class KerbType(LabeledEnum):
    MOUNTAIN = "MOUNTAIN"
    MOUNTAIN_TALL = "MOUNTAIN_TALL"
    VERTICAL = "VERTICAL"
    SLOPED_BATTERED = "SLOPED_BATTERED"
    SEMI_MOUNTAIN = "SEMI_MOUNTAIN"
    FLUSH_KERB = "FLUSH"
    RAISED_TABLE_TOP = "RAISED_TABLE_TOP"
    NO_KERB = "NO_KERB"


class FootpathType(LabeledEnum):
    NONE = "NONE"
    STANDARD_RCC = "STANDARD_RCC"
    FOOTPATH_2M_PLUS = "FOOTPATH_2M_PLUS"
    PAVER_BLOCK = "PAVER_BLOCK"
    CYCLE_TRACK_ONLY = "CYCLE_TRACK_ONLY"
    FOOTPATH_PLUS_CYCLE_TRACK = "FOOTPATH_PLUS_CYCLE_TRACK"
    SERVICE_ROAD = "SERVICE_ROAD"
    COMBINED_SHOULDER_FOOTPATH = "COMBINED_SHOULDER"


class MedianType(LabeledEnum):
    NONE = "NONE"
    NONE_UNDIVIDED = "NONE_UNDIVIDED"
    FLEXIBLE_PAINT = "FLEXIBLE_PAINT"
    RIGID_MEDIAN_BARRIER = "RIGID_MEDIAN_BARRIER"
    RCC_MEDIAN_BLOCK = "RCC_MEDIAN_BLOCK"
    BEAM_MEDIAN_BARRIER = "BEAM_MEDIAN_BARRIER"
    CABLE_MEDIAN_BARRIER = "CABLE_MEDIAN_BARRIER"
    GREEN_LANDSCAPED = "GREEN_LANDSCAPED"
    RAISED_KERBED = "RAISED_KERBED"


class CrashBarrierType(LabeledEnum):
    METAL_W_BEAM = "METAL_W_BEAM"
    METAL_TH_BEAM = "METAL_TH_BEAM"
    RCC_VERTICAL = "RCC_VERTICAL"
    RCC_WALL_PARAPET = "RCC_WALL_PARAPET"
    RCC_CRASH_PROOF = "RCC_CRASH_PROOF"
    SEMI_RIGID_DOUBLE_BEAM = "SEMI_RIGID_DOUBLE_BEAM"
    CABLE_ROPE = "CABLE_ROPE"
    STAINLESS_STEEL_PIPE = "SS_PIPE"
    CONCRETE_NEW_JERSEY = "NEW_JERSEY_BARRIER"
    CONCRETE_F_SHAPE = "F_SHAPE_BARRIER"
    PEDESTRIAN_METAL = "PEDESTRIAN_METAL"
    COMBINATION_VEHICLE_PED = "COMBINED_VEHICLE_PED"
    NONE = "NONE"


class ChainageUnit(LabeledEnum):
    METER = "m"
    METRE = "m"
    KILOMETER = "km"
    MILE = "mi"
    FEET = "ft"


class RotationDirection(LabeledEnum):
    CLOCKWISE = "CW"
    COUNTER_CLOCKWISE = "CCW"


class PavementCrustComposition(LabeledEnum):
    FLEXIBLE_BITUMINOUS = "FLEXIBLE_BITUMINOUS"
    RIGID_CC_PAVEMENT = "RIGID_CC_PAVEMENT"
    SEMI_RIGID_COMPOSITE = "SEMI_RIGID_COMPOSITE"
    INTERLOCKING_PAVER = "INTERLOCKING_PAVER"
    CEMENT_STABILISED = "CEMENT_STABILISED_BASE"
    WET_MIX_MACADAM = "WMM_DBM_BC"


class TransitionCurveType(LabeledEnum):
    NONE = "NONE"
    SPIRAL_CLOTHOID = "SPIRAL_CLOTHOID"
    LEMNISCATE = "LEMNISCATE"
    CUBIC_PARABOLA = "CUBIC_PARABOLA"
    BIQUADRATIC_PARABOLA = "BIQUADRATIC_PARABOLA"
    SINE_HALF_VERSA = "SINE_HALF_VERSA_SINE"


class VerticalAlignmentType(LabeledEnum):
    SUMMIT_CURVE = "SUMMIT_CURVE"
    VALLEY_CURVE = "VALLEY_CURVE"
    UNIFORM_GRADIENT = "UNIFORM_GRADIENT"
    BROKEN_BACK = "BROKEN_BACK"
    FLAT_LEVEL = "FLAT_LEVEL"
    STEEP_GRADIENT = "STEEP_GRADIENT"


class DrainageCrossfallType(LabeledEnum):
    SYMMETRIC_CROWN = "SYMMETRIC_CROWN"
    SINGLE_SLOPE = "SINGLE_SLOPE_LEFT"
    SINGLE_SLOPE_RIGHT = "SINGLE_SLOPE_RIGHT"
    COMBINED_CROWN_SUPER_ELEVATION = "CROWN_PLUS_SUPERELEVATION"
    V_SHAPED_TRENCH = "V_SHAPED_TRENCH"


# ===========================================================================
# SECTION 4 — SUPERSTRUCTURE
# ===========================================================================


class WearingCoatType(LabeledEnum):
    BITUMINOUS_CONCRETE = "BC"
    BITUMINOUS_CONCRETE_BC = "BITUMINOUS_CONCRETE_BC"
    STONE_MASTIC_ASPALT = "SMA"
    MARSHALL_SURFACE = "MS"
    DENSE_BITUMINOUS_MACADAM = "DBM"
    OPEN_GRADED_FRICTION_COURSE = "OGFC"
    ASPHALTIC_CONCRETE = "AC"
    SEMI_DENSE_BITUMINOUS_CONCRETE = "SDBC"
    SURFACE_DRESSING = "SURFACE_DRESSING"
    RCC_DECK_ONLY = "NO_WEARING_COAT_RCC_BARE"
    EPOXY_TOPPING = "EPOXY_TOPPING"
    POLYMER_MODIFIED_CONCRETE = "PMC"
    GRANITE_SETTS = "GRANITE_SETTS"
    INTERLOCKING_PAVER = "INTERLOCKING_PAVER"
    RUBBER_MODIFIED_ASPHALT = "RMA"
    MASTIC_ASPALT = "MASTIC_ASPALT"
    WARM_MIX_ASPALT = "WMA"


class ParapetType(LabeledEnum):
    RCC_VERTICAL = "RCC_VERTICAL"
    RCC_PARAPET_FULL_HEIGHT = "RCC_PARAPET_FULL_HEIGHT"
    RCC_CRASH = "RCC_CRASH_PROOF"
    METAL_CRASH_BARRIER = "METAL_CRASH_BARRIER"
    SS_304_PIPE_RAILING = "SS304_PIPE_RAILING"
    SS_316_PIPE_RAILING = "SS316_PIPE_RAILING"
    CAST_IRON = "CAST_IRON"
    WROUGHT_IRON = "WROUGHT_IRON"
    WOODEN = "WOODEN"
    GLASS_PANEL = "GLASS_PANEL"
    ALUMINIUM = "ALUMINIUM"
    COMBINED_RCC_AND_METAL = "COMBINED_RCC_METAL"
    PEDESTRIAN_ONLY = "PEDESTRIAN_ONLY_LOW"
    NONE = "NONE"


class RailingType(LabeledEnum):
    THREE_RAIL_PIPE = "THREE_RAIL_PIPE"
    TWO_RAIL_PIPE = "TWO_RAIL_PIPE"
    HORIZONTAL_BAR = "HORIZONTAL_BAR"
    VERTICAL_BALUSTER = "VERTICAL_BALUSTER"
    PANELLED = "PANELLED"
    CABLE = "CABLE"
    MESH_WIRE = "MESH_WIRE"
    PERFORATED = "PERFORATED"
    DECORATIVE = "DECORATIVE"
    BRIDGE_ART_MURAL = "BRIDGE_ART_MURAL"
    SOLID_PANEL = "SOLID_PANEL"
    NONE = "NONE"


class DrainageType(LabeledEnum):
    SCUPPER = "DECK_SCUPPER"
    SCUPPER_OUTLET_THROUGH_DECK = "SCUPPER_OUTLET_THROUGH_DECK"
    INLET_PIPE = "INLET_PIPE_DOWN"
    EDGE_CHANNEL = "EDGE_CHANNEL_CENTRAL"
    GULLY_POT_AND_DOWNTAKE = "GULLY_POT_DOWNTAKE"
    CENTRAL_FOUNTAIN_DRAIN = "CENTRAL_FOUNTAIN_DRAIN"
    SIDE_BURDEN_DRAIN = "SIDE_BURDEN_DRAIN"
    SLOTTED_DRAIN = "SLOTTED_LINE_DRAIN"
    NO_DRAINAGE_FLAT_DECK = "NO_DRAINAGE_FLAT_DECK"
    COMBINED_SCUPER_CHANNEL = "COMBINED_SCUPER_CHANNEL"


class GirderType(LabeledEnum):
    T_BEAM_RCC = "T_BEAM_RCC"
    I_GIRDER_PSC = "I_GIRDER_PSC"
    I_GIRDER_PS_PRECAST_OR_INSITU = "I_GIRDER_PS_PRECAST_OR_INSITU"
    BOX_GIRDER_PSC_SINGLE_CELL = "BOX_PSC_SINGLE_CELL"
    BOX_GIRDER_PSC_MULTI_CELL = "BOX_PSC_MULTI_CELL"
    BOX_STEEL_ORTHOTROPIC = "BOX_STEEL_ORTHOTROPIC"
    I_STEEL_PLATE = "I_STEEL_PLATE_GIRDER"
    U_GIRDER_PSC = "U_GIRDER_PSC"
    DOUBLE_TEE_PSC = "DOUBLE_TEE_PSC"
    DELTA_PSC = "DELTA_PSC"
    TRUSS_WARREN = "TRUSS_WARREN"
    TRUSS_PRATT = "TRUSS_PRATT"
    TRUSS_HOWE = "TRUSS_HOWE"
    TRUSS_BALTIMORE = "TRUSS_BALTIMORE"
    TRUSS_PENNEY = "TRUSS_PENNEY"
    BOWSTRING_TIE = "BOWSTRING_TIE_BEAM"
    PLATE_GIRDER_COMPOSITE = "PLATE_GIRDER_COMPOSITE"
    PRECAST_I = "PRECAST_I"
    PREFABRICATED_BOX = "PREFABRICATED_BOX"
    SEGMENTAL_PSC = "SEGMENTAL_PSC"
    BALANCED_CANTILEVER_BOX = "BALANCED_CANTILEVER_BOX"


class SlabType(LabeledEnum):
    SOLID_MONOLITHIC = "SOLID_MONOLITHIC"
    VOIDED_CORE = "VOIDED_CORE"
    HOLLOW_BOX_CORE = "HOLLOW_BOX_CORE"
    PROFILED_SHEET_DECKING = "PROFILED_SHEET_DECKING_COMPOSITE"
    PRECAST_PSC_SLAB_UNIT = "PRECAST_PSC_SLAB_UNIT"
    RIBBED_WAFFLE = "RIBBED_WAFFLE"
    TWO_WAY_SOLID = "TWO_WAY_SOLID"
    FLAT_SLAB_WITH_DROP_PANELS = "FLAT_SLAB_DROP_PANELS"
    STRESSED_SLAB = "POST_TENSIONED_SOLID_SLAB"
    LAYERED_COMPOSITE_SLAB = "LAYERED_COMPOSITE_SLAB"


class CamberMethod(LabeledEnum):
    PARABOLIC = "PARABOLIC"
    PARABOLIC_CROWN = "PARABOLIC_CROWN"
    LINEAR_BROKEN = "LINEAR_BROKEN_BACK"
    PRE_CAMBER_COLD = "PRE_CAMBER_COLD"
    CAMBER_PLUS_DEFLECTION_COMPENSATION = "CAMBER_PLUS_DEFLECTION_COMPENSATION"
    CROWN_ONLY = "CROWN_ONLY_NO_CAMBER"
    REVERSE_SAG_CURVE = "REVERSE_SAG_CURVE"
    SEGMENTAL_BOX_LIFT = "SEGMENTAL_BOX_LIFT_SCHEDULE"


class CantileverOverhangType(LabeledEnum):
    UNIFORM = "UNIFORM_OVERHANG"
    TAPERED_HAUNCHED = "TAPERED_HAUNCHED"
    STEPPED = "STEPPED"
    FLARED_AT_PIERS = "FLARED_AT_PIERS"
    VARIABLE_CANTILEVER_CURVE = "VARIABLE_CANTILEVER_CURVE"
    NARROW_ABUTMENT_WIDE_PIER = "NARROW_ABUTMENT_WIDE_PIER"


class SuperstructureSegmentation(LabeledEnum):
    CAST_IN_SITU_SINGLE = "CAST_IN_SITU_SINGLE"
    PRECAST_SPANS = "PRECAST_SPANS"
    SPAN_BY_SPAN_LAUNCHING = "SPAN_BY_SPAN_LAUNCHING"
    BALANCED_CANTILEVER = "BALANCED_CANTILEVER_SEGMENTS"
    INCREMENTAL_LAUNCHING = "INCREMENTAL_LAUNCHING"
    FREE_CANTILEVER = "FREE_CANTILEVER_ERECTION"
    PUSHING_METHOD = "PUSHING_METHOD"


class DeckJointSpacing(LabeledEnum):
    EVERY_SPAN = "EVERY_SPAN"
    EVERY_TWO_SPANS = "EVERY_2_SPANS"
    EVERY_THREE_SPANS = "EVERY_3_SPANS"
    CONTINUOUS_LONG_DECK = "LONG_CONTINUOUS_DECK"
    SEMI_INTEGRAL = "SEMI_INTEGRAL"
    FULLY_INTEGRAL_NO_JOINTS = "FULLY_INTEGRAL_NO_JOINTS"


class ArchShapeType(LabeledEnum):
    PARABOLIC_ARCH = "PARABOLIC_ARCH"
    CIRCULAR_ARCH = "CIRCULAR_ARCH"
    ELLIPTICAL_ARCH = "ELLIPTICAL_ARCH"
    TIED_ARCH_BOWSTRING = "TIED_ARCH_BOWSTRING"
    DECK_ARCH = "DECK_ARCH_SPANDREL"
    THROUGH_ARCH = "THROUGH_ARCH"
    HALF_THROUGH_ARCH = "HALF_THROUGH_ARCH"
    OPEN_SPANDREL_DECK = "OPEN_SPANDREL_DECK_ARCH"
    FILLED_SPANDREL = "FILLED_SPANDREL_ARCH"
    MULTI_CENTERED_GOTHIC = "MULTI_CENTERED_GOTHIC"
    SEGMENTAL = "SEGMENTAL_FLAT_ARCH"
    THREE_HINGED = "THREE_HINGED_ARCH"
    TWO_HINGED = "TWO_HINGED_ARCH"
    FIXED_FIXED_ARCH = "FIXED_FIXED_RIGID_ARCH"


class CableStayingSystemClass(LabeledEnum):
    HARP_PARALLEL_STAYS = "HARP_PARALLEL_STAYS"
    FAN_RADIAL_STAYS = "FAN_RADIAL_STAYS"
    MODIFIED_HARP_FAN = "MODIFIED_HARP_FAN_HYBRID"
    STAR_PATTERN = "STAR_PATTERN_VERY_FEW_STAYS"
    MULTI_STAY_PLANE = "MULTI_PLANE_3_OR_4_PLANES"
    CABLE_STAYED_EXTRADOSED = "EXTRADOSED_LOW_PYLON"
    SINGLE_PYLON_CENTER = "SINGLE_PYLON_CENTERLINE"
    TWIN_PYLON_SIDE = "TWIN_PYLON_LATERAL"
    INVERTED_Y_PYLON = "INVERTED_Y_PYLON"
    A_FRAME_PYLON = "A_FRAME_PYLON"
    H_FRAME_PYLON = "H_FRAME_PYLON"
    DIAMOND_PYLON = "DIAMOND_PYLON"


class TrussConfigurationClass(LabeledEnum):
    WARREN_TRUSS = "WARREN_TRUSS_VERTICALS_OPTIONAL"
    WARREN_TRUSS_WITH_VERTICALS = "WARREN_WITH_VERTICAL_POSTS"
    PRATT_TRUSS = "PRATT_TRUSS_CLASSICAL"
    MODIFIED_PRATT = "MODIFIED_PRATT_CAMELBACK"
    HOWE_TRUSS = "HOWE_TRUSS"
    BALTIMORE_TRUSS = "BALTIMORE_TRUSS_WITH_SUBPANELS"
    PENNSYLVANIA_PETIT = "PENNSYLVANIA_PETIT_TRUSS"
    PARKER_TRUSS = "PARKER_CAMBERED_PRATT"
    K_TRUSS = "K_TRUSS_BRACING"
    X_BRACING_CROSS = "X_BRACING_CROSS_DIAGONALS"
    THROUGH_TRUSS = "THROUGH_TRUSS_DECK_BETWEEN"
    DECK_TRUSS = "DECK_TRUSS_TOP_CHORD_DECK"
    HALF_THROUGH_TRUSS = "HALF_THROUGH_PONY_TRUSS"
    BOWSTRING_TRUSS = "BOWSTRING_TRUSS_CURVED_TOP"
    LENTICULAR_TRUSS = "LENTICULAR_LENS_SHAPED"
    WARREN_WEBBED_PLATE = "WARREN_WEBBED_PLATE_GIRDER"
    NORTH_LIGHT = "NORTH_LIGHT_ROOF_TRUSS"


# ===========================================================================
# SECTION 5 — SUBSTRUCTURE
# ===========================================================================


class PierType(LabeledEnum):
    WALL = "WALL"
    HAMMERHEAD = "HAMMERHEAD"
    ROUND = "ROUND_SHAFT"
    OCTAGONAL = "OCTAGONAL_SHAFT"
    SQUARE = "SQUARE_SHAFT"
    RECTANGULAR = "RECTANGULAR_SHAFT"
    HEXAGONAL = "HEXAGONAL_SHAFT"
    MULTI_COLUMN_2 = "MULTI_COLUMN_2"
    MULTI_COLUMN_3 = "MULTI_COLUMN_3"
    MULTI_COLUMN_4 = "MULTI_COLUMN_4"
    FRAME = "PIER_FRAME_WITH_TIE_BEAM"
    FAN_COLUMN_PIER = "FAN_COLUMN_PIER"
    V_SHAPED_PIER = "V_SHAPED_PIER"
    Y_SHAPED_PIER = "Y_SHAPED_PIER"
    A_SHAPED_PIER = "A_SHAPED_PIER"
    INTEGRAL_PIER = "INTEGRAL_PIER"
    SEMI_INTEGRAL_PIER = "SEMI_INTEGRAL_PIER"
    BENT_PIER = "BENT_PIER"
    TRESTLE_BENT = "TRESTLE_BENT"
    ARCH_PIER = "ARCH_PIER"
    CABLE_STAYED_PYLON = "CABLE_STAYED_PYLON_H"
    CABLE_STAYED_PYLON_DIAMOND = "CABLE_STAYED_PYLON_DIAMOND"
    CABLE_STAYED_PYLON_A = "CABLE_STAYED_PYLON_A"
    CABLE_STAYED_PYLON_HARP = "CABLE_STAYED_PYLON_HARP"
    SUSPENSION_TOWER = "SUSPENSION_TOWER"
    TWIN_WALL = "TWIN_WALL"
    TWIN_ROUND = "TWIN_ROUND"
    DUMB_BELL = "DUMB_BELL"
    FISH_BELLY = "FISH_BELLY"
    PYLON_SINGLE_COLUMN = "PYLON_SINGLE_COLUMN"


class PierCapType(LabeledEnum):
    NON_DROP_FLAT = "NON_DROP_FLAT"
    NON_DROP_FLUSH_PIERSHAFT = "NON_DROP_FLUSH_PIERSHAFT"
    DROP_PANEL = "DROP_PANEL"
    FLARED = "FLARED"
    OVERHANG_BOTH_SIDES = "OVERHANG_BOTH_SIDES"
    OVERHANG_CANTILEVER = "OVERHANG_CANTILEVER_ONE_SIDE"
    WIDENED_AT_EXPANSION_JOINT = "WIDENED_AT_EXPANSION_JOINT"
    HAUNCHED = "HAUNCHED_TOP_AND_BOTTOM"
    RECESSED_FOR_BEARING_POCKETS = "RECESSED_BEARING_POCKETS"


class PierShaftShape(LabeledEnum):
    RECTANGULAR = "RECTANGULAR"
    SQUARE = "SQUARE"
    CIRCULAR = "CIRCULAR"
    OCTAGONAL = "OCTAGONAL"
    HEXAGONAL = "HEXAGONAL"
    DUMBBELL = "DUMBBELL"
    ELLIPTICAL = "ELLIPTICAL"
    TAPERED_TUBULAR = "TAPERED_TUBULAR"
    FLANGED = "FLANGED"
    VARIABLE_TAPER = "VARIABLE_TAPER"


class AbutmentType(LabeledEnum):
    CANTILEVER = "CANTILEVER"
    COUNTERFORT = "COUNTERFORT"
    GRAVITY = "GRAVITY"
    SPILL_THROUGH = "SPILL_THROUGH_OPEN"
    STUB = "STUB_ABUTMENT"
    SEMI_GRAVITY = "SEMI_GRAVITY"
    BUTTRESSED = "BUTTRESSED"
    CANTILEVER_WITH_WING_WALLS = "CANTILEVER_WITH_WING_WALLS"
    FULL_HEIGHT_WALL = "FULL_HEIGHT_WALL"
    PILE_ABUTMENT = "PILE_ABUTMENT"
    WELL_ABUTMENT = "WELL_ABUTMENT"
    OPEN_FOUNDATION_ABUTMENT = "OPEN_FOUNDATION_ABUTMENT"
    TRESTLE_APPROACH_ABUTMENT = "TRESTLE_APPROACH_ABUTMENT"
    INTEGRAL_ABUTMENT = "INTEGRAL_ABUTMENT"
    SEMI_INTEGRAL_ABUTMENT = "SEMI_INTEGRAL_ABUTMENT"
    MECHANICALLY_STABILISED = "MECHANICALLY_STABILISED_MSE"
    GRS_ABUTMENT = "GRS_GEO_REINFORCED_SOIL"
    CONCRETE_BLOCK_ABUTMENT = "CONCRETE_BLOCK_ABUTMENT"
    ARCH_ABUTMENT = "ARCH_ABUTMENT"
    SKEW_BACK_ABUTMENT = "SKEW_BACK_ABUTMENT"
    WINGLESS = "WINGLESS_WALL_ABUTMENT"
    VERTICAL_WALL_W_TIE_BACK = "VERTICAL_WALL_W_TIE_BACK"
    QUAY_WALL_TYPE = "QUAY_WALL_TYPE"


class ReturnWallType(LabeledEnum):
    NONE = "NONE"
    CANTILEVER_RCC = "CANTILEVER_RCC"
    BUTTRESSED_RCC = "BUTTRESSED_RCC"
    GRAVITY_STONE = "GRAVITY_STONE_MASONRY"
    COUNTERFORT = "COUNTERFORT"
    MSE_GRID = "MSE_GRID"
    GRS_GEOSYNTHETIC = "GRS_GEOSYNTHETIC"
    CAPPED_PILE_WALL = "CAPPED_PILE_WALL"
    DIAPHRAGM_WALL = "DIAPHRAGM_WALL"
    SECANT_PILE = "SECANT_PILE_WALL"
    SHEET_PILE = "SHEET_PILE_WALL"
    DRILLED_SHAFT_WALL = "DRILLED_SHAFT_WALL"


class WingWallType(LabeledEnum):
    NONE = "NONE"
    PARALLEL = "PARALLEL_TO_CARRIAGEWAY"
    PERPENDICULAR = "PERPENDICULAR_TO_CARRIAGEWAY"
    SPAYED_30 = "SPLAYED_30_DEG"
    SPAYED_45 = "SPLAYED_45_DEG"
    SPAYED_60 = "SPLAYED_60_DEG"
    SPAYED_VARIABLE = "SPLAYED_VARIABLE"
    SPLAYED_30 = "SPLAYED_30_DEG"
    SPLAYED_45_DEG = "SPLAYED_45_DEG"
    SPLAYED_60 = "SPLAYED_60_DEG"
    SPLAYED_VARIABLE = "SPLAYED_VARIABLE"
    TAPERED = "TAPERED_HEIGHT"
    U_SHAPED = "U_SHAPED_WING"
    FLARED_CURVED = "FLARED_CURVED"
    APPROACH_RAMP = "APPROACH_RAMP_WALL"
    BRIDLE_PATH = "BRIDLE_PATH_WING"
    PARAPET_INTEGRATED = "PARAPET_INTEGRATED"


class AbutmentPedestalType(LabeledEnum):
    NONE = "NONE"
    SOLID_RCC_PEDESTAL = "SOLID_RCC_PEDESTAL"
    STEPPED_PEDESTAL = "STEPPED_PEDESTAL"
    H_PEDESTAL = "H_PEDESTAL"
    T_PEDESTAL = "T_PEDESTAL"
    I_PEDESTAL = "I_PEDESTAL"
    RECESSED_BEARING_PEDESTAL = "RECESSED_BEARING_PEDESTAL"


class WellSteiningType(LabeledEnum):
    RCC_SINGLE_SKIN = "RCC_SINGLE_SKIN"
    RCC_DOUBLE_SKIN = "RCC_DOUBLE_SKIN"
    BRICK_STEINING = "BRICK_STEINING"
    STONE_MASONRY = "STONE_MASONRY_STEINING"
    COMPOSITE_RCC_BRICK = "COMPOSITE_RCC_BRICK"
    STEEL_CAISSON = "STEEL_CAISSON"
    PNEUMATIC_CAISSON = "PNEUMATIC_CAISSON"
    OPEN_CAISSON = "OPEN_CAISSON"
    BOX_CAISSON = "BOX_CAISSON"


# ===========================================================================
# SECTION 6 — FOUNDATION
# ===========================================================================


class FoundationType(LabeledEnum):
    OPEN = "OPEN_FOUNDATION"
    PILE = "PILE_FOUNDATION"
    WELL = "WELL_CAISSON"
    RAFT = "RAFT_FOUNDATION"
    COMBINED = "COMBINED_FOOTING"
    STRIP = "STRIP_FOOTING"
    ISOLATED = "ISOLATED_FOOTING"
    PILE_CAPPED = "PILE_CAPPED"
    MICRO_PILE = "MICRO_PILE"
    UNDER_REAMED_PILE = "UNDER_REAMED_PILE"
    COMPACTION_PILE = "COMPACTION_PILE"
    STONE_COLUMN = "STONE_COLUMN"
    JET_GROUTING = "JET_GROUTING_COLUMN"
    DIAPHRAGM_WALL_FOUNDATION = "DIAPHRAGM_WALL_FOUNDATION"
    SECANT_PILE_WALL_FOUNDATION = "SECANT_PILE_WALL_FOUNDATION"
    GROUND_IMPROVEMENT_GRUBS = "GROUND_IMPROVEMENT_GRUBS"
    GEOPILE_REINFORCED = "GEOPILE_REINFORCED_EARTH"
    PILE_PLUS_RAFT = "PILE_PLUS_RAFT"
    WELL_PLUS_PILE = "WELL_PLUS_PILE_HYBRID"
    BOX_FOUNDATION = "BOX_FOUNDATION"
    FLOATING_FOUNDATION = "FLOATING_FOUNDATION"
    PILE_WITH_ISOLATED_CAPS = "PILE_WITH_ISOLATED_CAPS"
    PILE_WITH_STRIP_CAP = "PILE_WITH_STRIP_CAP"
    PILE_WITH_RAFT = "PILE_WITH_RAFT"
    RING_FOUNDATION = "RING_FOUNDATION"
    INVERTED_ARCH_FOUNDATION = "INVERTED_ARCH_FOUNDATION"
    GRILLAGE_FOUNDATION = "GRILLAGE_FOUNDATION"
    ECCENTRIC_FOUNDATION = "ECCENTRIC_FOUNDATION"
    SLAB_ON_GRADE = "SLAB_ON_GRADE"


class PileType(LabeledEnum):
    BORED_CAST_IN_SITU = "BORED_CAST_IN_SITU"
    DRIVEN_DISPLACEMENT = "DRIVEN_DISPLACEMENT"
    DRIVEN_CAST_IN_SITU = "DRIVEN_CAST_IN_SITU"
    PRECAST_CONCRETE = "PRECAST_CONCRETE"
    PRESTRESSED_CONCRETE_PSC = "PSC_PILE"
    STEEL_H_PILE = "STEEL_H_PILE"
    STEEL_PIPE_PILE = "STEEL_PIPE_PILE"
    STEEL_SHEET_PILE = "STEEL_SHEET_PILE"
    COMPOSITE_PILE = "COMPOSITE_PILE"
    TIMBER_PILE = "TIMBER_PILE"
    MICRO_PILE_MINIPILE = "MICRO_PILE_MINIPILE"
    UNDER_REAMED = "UNDER_REAMED"
    COMPACTION_GRAVEL = "COMPACTION_GRAVEL"
    COMPACTION_SAND = "COMPACTION_SAND"
    FRICTION_PILE = "FRICTION_PILE"
    END_BEARING_PILE = "END_BEARING_PILE"
    FLOATING_FRICTION = "FLOATING_FRICTION"
    TENSION_PILE = "TENSION_PILE"
    COMPRESSION_PILE = "COMPRESSION_PILE"
    LATERAL_LOAD_PILE = "LATERAL_LOAD_PILE"
    BATTER_PILE = "BATTER_PILE"
    VERTICAL_PILE = "VERTICAL_PILE"
    STEPPED_TAPER_PILE = "STEPPED_TAPER_PILE"
    JET_GROUT_PILE = "JET_GROUT_PILE"
    SAND_CEMENT_COLUMN = "SAND_CEMENT_COLUMN"
    DEEP_MIXING = "DEEP_MIXING_COLUMN"
    CFG_PILE = "CFG_PILE_CEMENT_FLYASH_GRAVEL"


class PileShape(LabeledEnum):
    CIRCULAR = "CIRCULAR"
    CIRCULAR_ROUND = "CIRCULAR_ROUND"
    SQUARE = "SQUARE"
    RECTANGULAR = "RECTANGULAR"
    OCTAGONAL = "OCTAGONAL"
    HEXAGONAL = "HEXAGONAL"
    TAPERED_CIRCULAR = "TAPERED_CIRCULAR"
    STEPPED_CIRCULAR = "STEPPED_CIRCULAR"
    UNDER_REAMED_ENLARGED_BASE = "UNDER_REAMED_ENLARGED_BASE"
    H_SHAPE = "H_SHAPE"
    I_SHAPE = "I_SHAPE"
    TUBULAR = "TUBULAR"
    SPIRAL_WELDED_TUBE = "SPIRAL_WELDED_TUBE"
    LONGITUDINAL_WELDED_TUBE = "LONGITUDINAL_WELDED_TUBE"
    CORROGATED_TUBE = "CORROGATED_TUBE"


class PileBaseType(LabeledEnum):
    FLAT_CUT = "FLAT_CUT"
    BULB_ENLARGED = "BULB_ENLARGED"
    UNDER_REAMED_SINGLE = "UNDER_REAMED_SINGLE"
    UNDER_REAMED_DOUBLE = "UNDER_REAMED_DOUBLE"
    UNDER_REAMED_TRIPLE = "UNDER_REAMED_TRIPLE"
    CONICAL_POINT = "CONICAL_POINT"
    ROCK_SOCKETED = "ROCK_SOCKETED"
    STEEL_TOE_PLATE = "STEEL_TOE_PLATE"
    SHOE_CAST_IRON = "SHOE_CAST_IRON"
    AGGLOMERATED = "AGGLOMERATED"


class WellCurbType(LabeledEnum):
    RCC_REINFORCED = "RCC_REINFORCED"
    PLAIN_CEMENT_CONCRETE = "PCC"
    STEEL_CUTTING_EDGE_CUM_CURB = "STEEL_CUTTING_EDGE_CUM_CURB"
    COMPOSITE_STEEL_RCC = "COMPOSITE_STEEL_RCC"
    MASONRY = "MASONRY_BRICK_OR_STONE"
    CAST_IRON_CUTTING_EDGE = "CAST_IRON_CUTTING_EDGE"


class WellCuttingEdgeShape(LabeledEnum):
    STRAIGHT_CHAMFERED = "STRAIGHT_CHAMFERED"
    CONICAL_POINTED = "CONICAL_POINTED"
    WEDGE_SHAPED = "WEDGE_SHAPED"
    BULL_NOSE = "BULL_NOSE_ROUNDED"
    KNIFE_EDGE = "KNIFE_EDGE_THIN"
    REINFORCED_SHIELD = "REINFORCED_SHIELD"
    BOTTOM_SLOPING = "BOTTOM_SLOPING"
    STEPPED = "STEPPED"
    ANGULAR_INWARDS = "ANGULAR_INWARDS"


class UnderReamCount(IntEnumStrict):
    NONE = 0
    SINGLE = 1
    DOUBLE = 2
    TRIPLE = 3
    QUAD = 4


class RaftMatType(LabeledEnum):
    FLAT_PLATE = "FLAT_PLATE"
    FLAT_PLATE_WITH_THICKENED_COLUMNS = "FLAT_PLATE_THICKENED_COLUMN_STRIPS"
    PLATE_BEAM = "PLATE_BEAM"
    CELLULAR = "CELLULAR_BOX_RAFT"
    PILED_RAFT = "PILED_RAFT"
    RIBBED = "RIBBED_RAFT"
    THICKENED_EDGE = "THICKENED_EDGE"
    WAFFLE = "WAFFLE"
    BASMENT_FLOOR = "BASEMENT_FLOOR_INTEGRATED"
    SLAB_WITH_DROP_PANELS = "SLAB_WITH_DROP_PANELS"


class OpenFoundationDepth(LabeledEnum):
    SHALLOW_LESS_1_5M = "SHALLOW_LT_1P5M"
    SHALLOW_1_5_TO_3M = "SHALLOW_1P5_3M"
    DEEP_3_TO_6M = "DEEP_3_6M"
    VERY_DEEP_GT_6M = "VERY_DEEP_GT_6M"
    STEPPED = "STEPPED_MULTI_LEVEL"


class SheetPileType(LabeledEnum):
    NONE = "NONE"
    LARSSEN_U = "LARSSEN_U"
    LARSSEN_Z = "LARSSEN_Z"
    LARSSEN_S = "LARSSEN_S"
    HOESCH = "HOESCH"
    STRAIGHT_WEB = "STRAIGHT_WEB"
    PANEL = "PANEL"
    STEEL_TUBULAR_COFFERDAM = "STEEL_TUBULAR_COFFERDAM"
    STEEL_BOX_COFFERDAM = "STEEL_BOX_COFFERDAM"
    DOUBLE_WALLED = "DOUBLE_WALLED"
    WOODEN_SHEET_PILE = "WOODEN_SHEET_PILE"
    VINYL_PVC = "VINYL_PVC"
    FIBERGLASS = "FIBERGLASS"
    CONCRETE_SHEET_PILE = "PRECAST_CONCRETE_SHEET_PILE"


class BearingCapacitySoilType(LabeledEnum):
    SOFT_CLAY = "SOFT_CLAY"
    STIFF_CLAY = "STIFF_CLAY"
    HARD_CLAY = "HARD_CLAY"
    SILT = "SILT"
    FINE_SAND = "FINE_SAND"
    MEDIUM_SAND = "MEDIUM_SAND"
    COARSE_SAND = "COARSE_SAND"
    SANDY_GRAVEL = "SANDY_GRAVEL"
    GRAVEL = "GRAVEL"
    BOULDER = "BOULDER"
    GRAVELLY_SAND = "GRAVELLY_SAND"
    ROCK_SOFT = "SOFT_ROCK"
    ROCK_MEDIUM = "MEDIUM_ROCK"
    ROCK_HARD = "HARD_ROCK"
    ORGANIC_PEAT = "ORGANIC_PEAT"
    MADE_UP_FILL = "MADE_UP_FILL"
    LATERITE = "LATERITE"
    CALCAREOUS = "CALCAREOUS"
    MARINE_CLAY = "MARINE_CLAY"
    BLACK_COTTON = "BLACK_COTTON_EXPANSIVE"
    LOESS = "LOESS"


class GroundImprovementType(LabeledEnum):
    NONE = "NONE"
    STONE_COLUMNS = "STONE_COLUMNS"
    VIBRO_COMPACTION = "VIBRO_COMPACTION"
    VIBRO_REPLACEMENT = "VIBRO_REPLACEMENT"
    DYNAMIC_COMPACTION = "DYNAMIC_COMPACTION"
    DEEP_SOIL_MIXING = "DEEP_SOIL_MIXING"
    JET_GROUTING = "JET_GROUTING"
    CEMENT_GROUTING = "CEMENT_GROUTING"
    CHEMICAL_GROUTING = "CHEMICAL_GROUTING"
    COMPACTION_GROUTING = "COMPACTION_GROUTING"
    GEOGRID_REINFORCEMENT = "GEOGRID_REINFORCEMENT"
    GEOTEXTILE_SEPARATION = "GEOTEXTILE_SEPARATION"
    PREFABRICATED_VERTICAL_DRAINS = "PVD"
    SURCHARGE_PRELOADING = "SURCHARGE_PRELOADING"
    VACUUM_PRELOADING = "VACUUM_PRELOADING"
    REPLACEMENT_WITH_GOOD_SOIL = "REPLACEMENT_WITH_GOOD_SOIL"
    GRANULAR_PILES = "GRANULAR_PILES"
    RIGID_INCLUSIONS = "RIGID_INCLUSIONS"
    MICRO_PILES_REINFORCEMENT = "MICRO_PILES_REINFORCEMENT"
    LIME_COLUMNS = "LIME_COLUMNS"
    LIME_CEMENT_COLUMNS = "LIME_CEMENT_COLUMNS"


class FundingSourceType(LabeledEnum):
    NHAI = "NHAI_CENTRAL"
    MORTH = "MORTH"
    STATE_PWD = "STATE_PWD"
    MUNICIPAL_CORPORATION = "MUNICIPAL_CORPORATION"
    WORLD_BANK_AIDED = "WORLD_BANK_AIDED"
    ADB_AIDED = "ASIAN_DEVELOPMENT_BANK"
    JICA_AIDED = "JICA_AIDED"
    KFW_AIDED = "KFW_GERMAN_AIDED"
    NEW_DEVELOPMENT_BANK = "NDB_BRICS"
    INFRASTRUCTURE_LEASING = "ILAND_FS_TOT"
    PUBLIC_PRIVATE_PARTNERSHIP = "PPP_BOT_BOOT"
    RAILWAY_RDSO = "INDIAN_RAILWAYS_RDSO"
    MINING_CORPORATION = "MINING_PSU"
    IRRIGATION_DEPT = "STATE_IRRIGATION_DEPT"
    POWER_GRID = "POWER_GRID_CROSSING"
    PORT_TRUST = "PORT_MARITIME_BOARD"


class WorkStatusType(LabeledEnum):
    CONCEPT_PROPOSED = "CONCEPT_PROPOSED"
    FEASIBILITY_STAGE = "FEASIBILITY_STAGE"
    DPR_PREPARATION = "DETAILED_PROJECT_REPORT"
    BID_DOCUMENT_STAGE = "BID_DOCUMENT_STAGE"
    TENDER_FLOATING = "TENDER_FLOATING"
    TENDER_EVALUATION = "TENDER_EVALUATION"
    AWARDED_LOA = "AWARDED_LOA_SIGNED"
    AGREEMENT_SIGNED = "AGREEMENT_SIGNED"
    MOBILISATION = "MOBILISATION_STAGE"
    FOUNDATION_EXECUTION = "FOUNDATION_EXECUTION"
    SUBSTRUCTURE_EXECUTION = "SUBSTRUCTURE_EXECUTION"
    SUPERSTRUCTURE_EXECUTION = "SUPERSTRUCTURE_EXECUTION"
    APPROACH_ROAD = "APPROACH_ROAD_WORKS"
    DRAWING_PRECONSTRUCTION = "PRECONSTRUCTION_DRAWING"
    SHOP_DRAWING = "SHOP_DRAWING_BBS"
    AS_BUILT_DRAWING = "AS_BUILT_DRAWING"
    TRIAL_LOAD_TEST = "TRIAL_LOAD_TESTING"
    COMMISSIONING = "COMMISSIONING_STAGE"
    DEFECT_LIABILITY = "DLP_OPERATION"
    OPERATION_MAINTENANCE = "O_AND_M_5YR"
    RECONSTRUCTION = "RECONSTRUCTION_REHABILITATION"


class ContractPackageType(LabeledEnum):
    PACKAGE_DPR_PREPARATION = "DPR_PREPARATION"
    PACKAGE_GAD_BASIC_DESIGN = "GAD_BASIC_DESIGN"
    PACKAGE_DETAILED_DESIGN = "DETAILED_ENGINEERING_DESIGN"
    PACKAGE_EPC_TURNKEY = "EPC_TURNKEY_FULL"
    PACKAGE_ITEM_RATE_WORKS = "ITEM_RATE_WORKS_CONTRACT"
    PACKAGE_FOUNDATION_ONLY = "FOUNDATION_PACKAGE_ONLY"
    PACKAGE_SUPERSTRUCTURE = "SUPERSTRUCTURE_SPECIALIST"
    PACKAGE_SUBSTRUCTURE = "SUBSTRUCTURE_CIVIL"
    PACKAGE_AS_BUILT = "AS_BUILT_SURVEY_DRAWINGS"
    PACKAGE_BILL_OF_QUANTITIES = "BOQ_AND_COSTING_ONLY"
    PACKAGE_CONSTRUCTION_SUPERVISION = "CONSTRUCTION_SUPERVISION_PMC"
    PACKAGE_LAB_TESTING = "LAB_TESTING_AND_QUALITY"
    PACKAGE_TOTAL_BRIDGE = "FULL_BRIDGE_DELIVERY"


class DesignFirmCategoryClass(LabeledEnum):
    SMALL_LOCAL_PRACTITIONER = "SMALL_LOCAL_FIRM_CLASS_D"
    MEDIUM_REGIONAL_FIRM = "MEDIUM_REGIONAL_FIRM_CLASS_C"
    LARGE_NATIONAL_FIRM = "LARGE_NATIONAL_FIRM_CLASS_B"
    TIER1_MULTINATIONAL = "TIER1_INTERNATIONAL_FIRM_CLASS_A"
    SPECIALIST_BRIDGE_FIRM = "BRIDGE_SPECIALIST_BOUTH_ASCE"
    GOVERNMENT_IN_HOUSE = "GOVERNMENT_DEPARTMENT_INHOUSE"
    PSU_CONSULTING_CELL = "PUBLIC_SECTOR_UNDERTAKING_CELL"
    ACADEMIC_RESEARCH_INSTITUTE = "ACADEMIC_IIT_NIT_RESEARCH"
    JOINT_VENTURE_MIXED = "JV_MIXED_CAPABILITY"


class UsageIntensityType(LabeledEnum):
    NATIONAL_HIGHWAY_CORRIDOR = "NH_CORRIDOR_4_6_LANE"
    EXPRESSWAY_ACCESS_CONTROLLED = "EXPRESSWAY_ACCESS_CONTROLLED"
    URBAN_ARTERIAL_ROAD = "URBAN_ARTERIAL_MASTER_PLAN"
    STATE_HIGHWAY = "STATE_HIGHWAY"
    MAJOR_DISTRICT_ROAD = "MAJOR_DISTRICT_ROAD_MDR"
    ORDINARY_DISTRICT_ROAD = "ORDINARY_DISTRICT_ROAD_ODR"
    VILLAGE_ROAD_CONNECTIVITY = "PMGSY_VILLAGE_CONNECTIVITY"
    RAILWAY_OVER_BRIDGE_ROB = "RAILWAY_OVER_BRIDGE_ROB"
    RAILWAY_UNDER_BRIDGE_RUB = "RAILWAY_UNDER_BRIDGE_RUB"
    FLYOVER_GRADE_SEPARATOR = "FLYOVER_GRADE_SEPARATOR"
    PEDESTRIAN_FOOT_OVER = "FOOT_OVER_BRIDGE_FOB"
    CYCLE_TRACK_SHARED = "CYCLE_TRACK_NON_MOTOR"
    LIGHT_RAIL_TRAMWAY = "LIGHT_RAIL_TRAM_CROSSING"
    METRO_GUIDEWAY = "METRO_RAIL_GUIDEWAY"
    HYDRO_CANAL_CROSSING = "HYDRO_CANAL_CROSSING"
    IRRIGATION_AQUEDUCT = "IRRIGATION_AQUEDUCT"
    INDUSTRIAL_PLANT_ACCESS = "INDUSTRIAL_PLANT_ACCESS_ROAD"
    MINING_HAUL_ROAD = "MINING_HAUL_ROAD_100T"
    DEFENCE_STRATEGIC_ROAD = "DEFENCE_STRATEGIC_BORDER_ROAD"
    TOLL_PLAZA_APPROACH = "TOLL_PLAZA_APPROACH_RAMP"


class WaterwayCrossingType(LabeledEnum):
    MAJOR_PERENNIAL_RIVER = "MAJOR_PERENNIAL_RIVER"
    MINOR_SEASONAL_RIVER = "MINOR_SEASONAL_RIVER"
    RIVER_CONFLUENCE = "RIVER_CONFLUENCE_SANGAM"
    NALA_STREAM = "NALA_RAIN_FED_STREAM"
    TORRENT_HILLY = "TORRENT_HILLY_FIRST_ORDER"
    CANAL_IRRIGATION = "CANAL_IRRIGATION_MAIN"
    CANAL_MINOR_DISTRIBUTORY = "CANAL_MINOR_DISTRIBUTORY"
    DRAIN_URBAN = "DRAIN_URBAN_STORM_WATER"
    VALLEY_NO_WATER = "VALLEY_DEPRESSION_NALA"
    RAILWAY_SINGLE_LINE = "RAILWAY_SINGLE_LINE_BG"
    RAILWAY_DOUBLE_LINE = "RAILWAY_DOUBLE_MULTI_LINE"
    RAILWAY_YARD = "RAILWAY_YARD_MARSHALLING"
    ROAD_NH_UNDERPASS = "ROAD_NH_UNDERPASS_CROSSING"
    ROAD_INTERCHANGE_LEVEL = "ROAD_INTERCHANGE_LEVEL_SEPARATION"
    POWER_TRANSMISSION_LINE = "POWER_220KV_400KV_LINE"
    PIPELINE_CROSSING_OIL_GAS = "OIL_GAS_PIPELINE_CROSSING"
    MARITIME_COASTAL = "MARITIME_BACKWATER_CREEK"
    FLOOD_ZONE_NO_FLOW = "FLOOD_PLAIN_ZONE_NO_FLOW"


class InterchangeGradeSeparationType(LabeledEnum):
    CLOVERLEAF_FOUR_LEG = "CLOVERLEAF_FOUR_LEG_STANDARD"
    TRUMPET_INTERCHANGE = "TRUMPET_TWO_THREE_LEG"
    DIAMOND_INTERCHANGE = "DIAMOND_SIGNAL_FREE"
    SINGLE_POINT_URBAN_SPUI = "SINGLE_POINT_URBAN_INTERCHANGE_SPUI"
    DOUBLE_DIAMOND_DDI = "DOUBLE_CROSSOVER_DIAMOND_DDI"
    PARTIAL_CLOVERLEAF_PARCLO_A2 = "PARTIAL_CLOVERLEAF_PARCLO_A2"
    PARTIAL_CLOVERLEAF_PARCLO_B2 = "PARTIAL_CLOVERLEAF_PARCLO_B2"
    MULTILEVEL_STACK_3TIER = "STACK_3TIER_MULTILEVEL"
    MULTILEVEL_STACK_4TIER = "STACK_4TIER_MULTILEVEL"
    ROUNDABOUT_GRADE_SEPARATED = "GRADE_SEPARATED_ROTARY"
    ONE_ROW_QUADRANT_PARCLO = "PARCLO_ONE_ROW_QUADRANT"
    TWO_QUADRANT_PARCLO = "PARCLO_TWO_QUADRANT_B1"
    THREE_QUADRANT_PARCLO = "PARCLO_THREE_QUADRANT_A4"
    FIVE_LEG_STAR_INTERCHANGE = "FIVE_LEG_STAR_INTERCHANGE"
    TURBINE_INTERCHANGE = "TURBINE_WINDMILL_INTERCHANGE"
    BASKET_HANDLE_INTERCHANGE = "BASKET_HANDLE_INTERCHANGE"


class SuperelevationRotationAxis(LabeledEnum):
    CENTRE_LINE_OF_CARRIAGEWAY = "ROTATE_ABOUT_CENTRE_LINE"
    INNER_EDGE_OF_CARRIAGEWAY = "ROTATE_ABOUT_INNER_EDGE"
    OUTER_EDGE_OF_CARRIAGEWAY = "ROTATE_ABOUT_OUTER_EDGE"
    MEDIAN_EDGE_DIVIDED = "ROTATE_ABOUT_MEDIAN_EDGE"
    OFFSET_PIVOT_3D = "OFFSET_PIVOT_THREE_DIMENSIONAL"


class WideningTypeOnCurve(LabeledEnum):
    INNER_SIDE_ONLY = "INNER_SIDE_ONLY_CLASSICAL"
    OUTER_SIDE_ONLY = "OUTER_SIDE_ONLY_MOUNTAINOUS"
    BOTH_SIDES_SYMMETRIC = "BOTH_SIDES_SYMMETRIC_DIVIDED"
    TRANSITION_TAPER_WIDENING = "TRANSITION_TAPER_WIDENING"
    FULL_SECTION_UNIFORM = "FULL_SECTION_UNIFORM_WIDENING"
    SHARP_CURVE_EXTRA = "SHARP_CURVE_EXTRA_WIDENING_PS2"
    MULTIPLE_BEND_SPIRAL = "MULTIPLE_BEND_SPIRAL_WIDENING"


class HorizontalCurveTransitionType(LabeledEnum):
    SPIRAL_CLOTHOID = "SPIRAL_CLOTHOID_IRC_STANDARD"
    CUBIC_PARABOLA = "CUBIC_PARABOLA_APPROXIMATE"
    LEMNISCATE_BERNOULLI = "LEMNISCATE_BERNOULLI_CURVE"
    S_CURVE_REVERSE = "S_CURVE_REVERSE_TRANSITION"
    COMPOUND_CURVE_MULTI_RADIUS = "COMPOUND_CURVE_MULTI_RADIUS"
    BROKEN_BACK_CURVE = "BROKEN_BACK_SHORT_TANGENT"
    COMBINATION_SPIRAL_SPIRAL = "SPIRAL_CIRCULAR_SPIRAL_SCS"
    COMBINATION_SPIRAL_CIRCULAR = "SPIRAL_CIRCULAR_SC_ONLY"


class SightDistanceCategory(LabeledEnum):
    STOPPING_SIGHT_DISTANCE_SSD = "SSD_STOPPING_SIGHT_DISTANCE"
    OVERTAKING_SIGHT_DISTANCE_OSD = "OSD_OVERTAKING_SIGHT_DISTANCE_PASSING"
    INTERMEDIATE_SIGHT_DISTANCE_ISD = "ISD_INTERMEDIATE_SIGHT_DISTANCE_2xSSD"
    HEADLIGHT_SIGHT_DISTANCE_HSD = "HSD_HEADLIGHT_NIGHT_SIGHT"
    SAFETY_STOPPING_DOWNGRADE = "SSD_DOWNGRADE_SAFETY_PLUS_20PCT"
    PEDESTRIAN_CROSSING_ZEBRA = "PEDESTRIAN_ZEBRA_SIGHT_DISTANCE"
    STOP_LINE_AT_SIGNAL = "SIGNAL_STOP_LINE_SIGHT"
    DECISION_SIGHT_DISTANCE_DSD = "DSD_DECISION_SIGHT_DISTANCE_URBAN"
    INTERSECTION_APPROACH_SIGHT = "INTERSECTION_APPROACH_SIGHT_TRIANGLE"


class WebOpenCutoutType(LabeledEnum):
    CIRCULAR_OPENING = "CIRCULAR_WEB_OPENING"
    RECTANGULAR_ROUNDED_CORNER = "RECTANGULAR_ROUNDED_CORNER_R100"
    SQUARE_ROUNDED = "SQUARE_ROUNDED_CORNER_R150"
    HEXAGONAL_SYMMETRIC = "HEXAGONAL_SYMMETRIC_OPENING"
    OCTAGONAL_SYMMETRIC = "OCTAGONAL_SYMMETRIC_OPENING"
    ELLIPTICAL_HORIZONTAL = "ELLIPTICAL_HORIZONTAL_OPENING"
    CASTELLATED_BEAM_HEX = "CASTELLATED_BEAM_HEXAGONAL_STD"
    CELLULAR_BEAM_CIRCULAR = "CELLULAR_BEAM_CIRCULAR_OPENING"
    VERTICAL_SLOT_ROUND_END = "VERTICAL_SLOT_ROUND_END"
    HORIZONTAL_SLOT_ROUND_END = "HORIZONTAL_SLOT_ROUND_END"


class PrecastSegmentJointType(LabeledEnum):
    EPOXY_DRY_JOINT_NHAI = "EPOXY_DRY_JOINT_NHAI_STANDARD"
    SHEAR_KEY_ONLY_DRY = "SHEAR_KEY_ONLY_DRY_JOINT"
    MATCH_CAST_EPOXY = "MATCH_CAST_EPOXY_ASSEMBLY"
    MATCH_CAST_DRY_NO_EPOXY = "MATCH_CAST_DRY_NO_EPOXY"
    WET_JOINT_CAST_IN_SITU = "WET_JOINT_CAST_IN_SITU_M40"
    POST_TENSIONED_STITCH_POUR = "POST_TENSIONED_STITCH_POUR"
    ULTRA_HIGH_PERF_UHPFRC = "JOINT_UHPFRC_STITCH_120MPa"
    INTERNAL_DOWEL_BAR = "INTERNAL_DOWEL_BAR_REINFORCEMENT"
    EXTERNAL_STIFFENER_PLATE = "EXTERNAL_STIFFENER_PLATE_STEEL"
    HYBRID_KEY_EPOXY_DOWEL = "HYBRID_KEY_EPOXY_DOWEL"


class DeckPourSequenceMethod(LabeledEnum):
    BALANCED_CANTILEVER_METHOD = "BALANCED_CANTILEVER_CAST_IN_SITU"
    SPAN_BY_SPAN_METHOD = "SPAN_BY_SPAN_TRUSSEL_GANTRY"
    INCREMENTAL_LAUNCHING_METHOD = "INCREMENTAL_LAUNCHING_METHOD_STATIC"
    FULL_SPAN_SCAFFOLDING_SHORING = "FULL_SPAN_SCAFFOLDING_SHORING"
    FORM_TRAVELLER_CARRIAGE = "FORM_TRAVELLER_CARRIAGE_WALKING"
    Movable_Scaffolding_System_MSS = "MOVABLE_SCAFFOLDING_SYSTEM_MSS"
    OVERHEAD_LAUNCHING_GANTRY = "OVERHEAD_LAUNCHING_GANTRY_BOX_GIRDER"
    BENEATH_SUPPORT_LAUNCHER = "BENEATH_SUPPORT_LAUNCHER_SSG"
    SEGMENTAL_PRECAST_ERECTION = "SEGMENTAL_PRECAST_ERECTION_CRANE"
    TOP_DOWN_ERECTION_SEQUENCE = "TOP_DOWN_ERECTION_SEQUENCE"
    CORE_SLAB_FIRST_FULL_WIDTH = "CORE_SLAB_FIRST_FULL_WIDTH_LATER"
    TWO_HALF_WIDTH_PHASED = "TWO_HALF_WIDTH_PHASED_CONSTRUCTION"


class PierTieBeamLocationType(LabeledEnum):
    AT_PIER_CAP_LEVEL = "TIE_BEAM_AT_PIER_CAP_LEVEL"
    HALF_HEIGHT_OF_SHAFT = "TIE_BEAM_HALF_HEIGHT_OF_SHAFT"
    ONE_THIRD_HEIGHT_FROM_TOP = "TIE_BEAM_1_3_HEIGHT_FROM_TOP"
    ONE_THIRD_HEIGHT_FROM_BOTTOM = "TIE_BEAM_1_3_HEIGHT_FROM_BOTTOM"
    AT_GROUND_LEVEL_PLOWINTH = "TIE_BEAM_AT_GROUND_LEVEL_PLOWINTH"
    AT_FINISHED_GROUND_LEVEL_FGL = "TIE_BEAM_AT_FINISHED_GROUND_LEVEL_FGL"
    MULTIPLE_LEVELS_MULTI_STRUT = "TIE_BEAM_MULTIPLE_LEVELS_MULTI_STRUT"
    BURIED_BELOW_GROUND_PILE_CAP = "TIE_BEAM_BURIED_BELOW_GROUND_PILE_CAP"
    INTEGRATED_WITH_PILE_CAP = "TIE_BEAM_INTEGRATED_WITH_PILE_CAP"
    DYNAMIC_LATERAL_SEISMIC_STRAP = "DYNAMIC_LATERAL_SEISMIC_STRAP"


class AbutmentBackfillSpecificationType(LabeledEnum):
    GRANULAR_MOORUM_MORTH = "GRANULAR_MOORUM_MORTH_CL_406"
    CRUSHED_STONE_SAND_BLENDED = "CRUSHED_STONE_SAND_BLENDED_60_40"
    RIVER_BED_SAND_CLEAN = "RIVER_BED_SAND_CLEAN_FREE_CLAY"
    BOULDER_CRUSHED_COARSE = "BOULDER_CRUSHED_COARSE_600MM"
    COHESIVE_SELECT_FILL = "COHESIVE_SELECT_FILL_PL_10"
    GSB_GRANULAR_SUB_BASE = "GSB_GRANULAR_SUB_BASE_IRC_SPEC"
    WMM_WET_MIX_MACADAM = "WMM_WET_MIX_MACADAM_00MORTH"
    PCC_CUT_OFF_PLUG = "PCC_CUT_OFF_PLUG_M10"
    GEOFOAM_EXPANDED_POLYSTYRENE = "GEOFOAM_EXPANDED_POLYSTYRENE_EPS"
    POND_ASH_BOTTOM_ASH_BLEND = "POND_ASH_BOTTOM_ASH_BLEND_80_20"
    LATERITIC_SOIL_SELECT = "LATERITIC_SOIL_SELECT_GRADE_A"
    RUBBER_MODIFIED_LIGHTWEIGHT = "RUBBER_MODIFIED_LIGHTWEIGHT_FILL"
    ENGINEERED_COMPOUND_MORTH = "ENGINEERED_COMPOUND_MORTH_CL_406_408"
    NO_BACKFILL_INTEGRAL = "NO_BACKFILL_INTEGRAL_ABUTMENT"


class PileInstallationMethodType(LabeledEnum):
    ROTARY_WASH_BORING = "ROTARY_WASH_BORING"
    CALYX_DRUM_AUGER_BORING = "CALYX_DRUM_AUGER_BORING"
    DIRECT_MUD_CIRCULATION_DMC = "DIRECT_MUD_CIRCULATION_DMC"
    REVERSE_CIRCULATION_DRilling_RCD = "REVERSE_CIRCULATION_DRILLING_RCD"
    AUGER_BORING_SHORT_FLIGHT = "AUGER_BORING_SHORT_FLIGHT_CFA"
    CONTINUOUS_FLIGHT_AUGER_CFA = "CONTINUOUS_FLIGHT_AUGER_CFA_LONG"
    DRIVEN_DROP_HAMMER = "DRIVEN_DROP_HAMMER_CAST_IN_SITU"
    DRIVEN_PNEUMATIC_HAMMER = "DRIVEN_PNEUMATIC_HAMMER_OPEN_CLOSED_END"
    DRIVEN_DIESEL_HAMMER = "DRIVEN_DIESEL_HAMMER_SINGLE_DOUBLE_ACTING"
    DRIVEN_VIBRATORY_HAMMER = "DRIVEN_VIBRATORY_HAMMER_SHEET_PILE"
    HYDRAULIC_JACKED_PILE = "HYDRAULIC_JACKED_PILE_PRESSED_IN"
    JETTING_ASSISTED_DRIVEN = "JETTING_ASSISTED_DRIVEN_SANDY_SOIL"
    MICRO_PILE_PERCUSSION_DTH = "MICRO_PILE_PERCUSSION_DTH_HAMMER"
    GRouted_HOLLOW_BAR = "GROUTED_HOLLOW_BAR_SELF_DRILLING_SDA"
    PRESSURE_GROUTED_STAGE = "PRESSURE_GROUTED_MULTI_STAGE_SINGLE_TUBE"


class SettlementCriterionCategoryType(LabeledEnum):
    TOTAL_MAXIMUM_SETTLEMENT = "TOTAL_MAXIMUM_SETTLEMENT_65MM"
    DIFFERENTIAL_ANGULAR_SETTLEMENT = "DIFFERENTIAL_ANGULAR_SETTLEMENT_1in500"
    TILT_ROTATION_RADIANS = "TILT_ROTATION_RADIANS_1in2500"
    LONG_TERM_CONSOLIDATION = "LONG_TERM_CONSOLIDATION_10YR_30YR"
    SHORT_TERM_IMMEDIATE_ELASTIC = "SHORT_TERM_IMMEDIATE_ELASTIC_SPRINGBACK"
    SECONDARY_COMPRESSION_CREEP = "SECONDARY_COMPRESSION_CREEP_C_ALPHA"
    END_BEARING_SETTLEMENT = "END_BEARING_SETTLEMENT_PILE_TIP"
    NEGATIVE_SKIN_FRICTION_DRAG = "NEGATIVE_SKIN_FRICTION_DRAG_DOWN"
    SEEPAGE_INDUCED_CONSOLIDATION = "SEEPAGE_INDUCED_CONSOLIDATION"
    CYCLIC_DYNAMIC_SETTLEMENT = "CYCLIC_DYNAMIC_SETTLEMENT_TRAFFIC_LOADING"
    RATE_OF_SETTLEMENT_PER_YEAR = "RATE_OF_SETTLEMENT_MM_PER_YEAR_5MM"
    POST_CONSTRUCTION_SETTLEMENT = "POST_CONSTRUCTION_SETTLEMENT_AFTER_3_MONTHS"


# ===========================================================================
# Section 7 — HYDRAULIC / SCOUR / FLOOD enums (IRC:5-2015, IRC:78, MORTH)
# ===========================================================================


class WaterSourceType(LabeledEnum):
    PERENNIAL_SNOW_FED = "PERENNIAL_SNOW_FED_HIMALAYAN"
    PERENNIAL_GROUND_WATER_BASE = "PERENNIAL_GROUND_WATER_BASE_FLOW"
    RIVER_PERENNIAL = "RIVER_PERENNIAL"
    SEASONAL_MONSOON = "SEASONAL_MONSOON_ONLY"
    FLASH_FLOOD_NALA = "FLASH_FLOOD_NALA_TORRENT"
    RAIN_FED_MINOR = "RAIN_FED_MINOR_STREAM"
    INTER_STATE_BASIN = "INTER_STATE_BASIN_RIVER"
    CANAL_IRRIGATION_MAIN = "CANAL_IRRIGATION_MAIN"
    CANAL_MINOR_DISTRIBUTORY = "CANAL_MINOR_DISTRIBUTORY_2ND_ORDER"
    STORM_WATER_DRAIN_URBAN = "STORM_WATER_DRAIN_URBAN_100YEAR"
    COASTAL_BACKWATER_CREEK = "COASTAL_BACKWATER_CREEK_TIDAL"
    ESTUARY_MIXED_FLOW = "ESTUARY_MIXED_FLOW_BRACKISH"
    RESERVOIR_BEHIND_DAM = "RESERVOIR_BEHIND_DAM_FRL_MDDL"
    LAGOON_CHILIKA_TYPE = "LAGOON_CHILIKA_TYPE_BRACKISH"
    ARTIFICIAL_INTERCEPTING_DRAIN = "ARTIFICIAL_INTERCEPTING_DRAIN"
    PIPE_CULVERT_OUTLET = "PIPE_CULVERT_OUTLET_CHANNEL"
    NALA_CASCADE_FIRST_ORDER = "NALA_CASCADE_FIRST_ORDER_HILLY"
    FLOOD_PLAIN_REJUVENATED = "FLOOD_PLAIN_REJUVENATED_FROM_BEFORE"


class ScourRegimeType(LabeledEnum):
    CLEAR_WATER_SCOUR = "CLEAR_WATER_SCOUR_BELOW_MOBILE"
    LIVE_BED_SCOUR = "LIVE_BED_SCOUR_WITH_TRANSPORT"
    GENERAL_SCOUR_RIVER = "GENERAL_SCOUR_RIVER_WIDE"
    LOCAL_SCOUR_AROUND_PIER = "LOCAL_SCOUR_AROUND_PIER_COLES_BHARGAVA"
    CONTRACTION_SCOUR = "CONTRACTION_SCOUR_BRIDGE_OPENING"
    DEGRADATIONAL_SCOUR = "DEGRADATIONAL_SCOUR_LONG_TERM"
    AGGRADATIONAL_SCOUR_NEGATIVE = "AGGRADATIONAL_SCOUR_NEGATIVE_SILTING"
    LACEYS_REGIME_DEPTH_SCOUR = "LACEYS_REGIME_DEPTH_R_SCOUR"
    SCOUR_DUE_TO_BEND_CURRENT = "SCOUR_DUE_TO_BEND_CURRENT_SECONDARY"
    TIDAL_SCOUR_REVERSIBLE = "TIDAL_SCOUR_REVERSIBLE_FLOOD_EBB"
    ICE_JAM_SCOUR_HIMALAYAN = "ICE_JAM_SCOUR_HIMALAYAN_RIVERS"
    MEANDER_SCOUR_OUTER_BANK = "MEANDER_SCOUR_OUTER_BANK_ATTACK"
    CONFLUENCE_SCOUR = "CONFLUENCE_SCOUR_RIVER_MEETING_POINT"
    MAXIMUM_DESIGN_SCOUR = "MAXIMUM_DESIGN_SCOUR_2x_GENERAL_LOCAL"
    SCOUR_CHECK_FRL_MINIMUM = "SCOUR_CHECK_FRL_MINIMUM_DEPTH"


class ScourMeasurementMethod(LabeledEnum):
    ECHO_SOUNDER_SINGLE_BEAM = "ECHO_SOUNDER_SINGLE_BEAM_200kHz"
    MULTI_BEAM_SONAR_SCAN = "MULTI_BEAM_SONAR_SCAN_BATHYMETRY"
    CROSS_SECTION_LEVELLING_SURVEY = "CROSS_SECTION_LEVELLING_SURVEY_THEODOLITE"
    FSL_HFL_MARKER_INSPECTION = "FSL_HFL_MARKER_INSPECTION_VISUAL"
    LACEYS_REGIME_FORMULA_IRC5 = "LACEYS_REGIME_FORMULA_IRC5_CL_24"
    BHARGAVA_PIER_SCOUR_METHOD = "BHARGAVA_PIER_SCOUR_METHOD"
    COLES_LOCAL_SCOUR_METHOD = "COLES_LOCAL_SCOUR_METHOD"
    INGLIS_CONTRACTION_SCOUR = "INGLIS_CONTRACTION_SCOUR_MORTH_CL_704"
    BLENCH_REGIME_MODIFIED = "BLENCH_REGIME_MODIFIED_IRI_G"
    HEC_RAS_1D_MODELLED = "HEC_RAS_1D_MODELLED_50YR"
    HEC_RAS_2D_MODELLED = "HEC_RAS_2D_MODELLED_FLOOD_MAP"
    MIKE11_HYDRAULIC_MODEL = "MIKE11_HYDRAULIC_MODEL_DHI"
    SWMM_URBAN_DRAIN_SCOUR = "SWMM_URBAN_DRAIN_SCOUR_EPA"
    INFRARED_BATHYMETRY_AERIAL = "INFRARED_BATHYMETRY_AERIAL_DRONE"
    ADCP_VELOCITY_INTEGRATED = "ADCP_VELOCITY_INTEGRATED_DEPTH"
    GPS_ROVER_BED_MAPPING = "GPS_ROVER_BED_MAPPING_RTK"


class HydrographShapeType(LabeledEnum):
    UNIT_HYDROGRAPH_1CM = "UNIT_HYDROGRAPH_1CM_EXCESS"
    S_CURVE_SUMMATION = "S_CURVE_SUMMATION_HYDROGRAPH"
    RATIONAL_METHOD_FORMULA = "RATIONAL_METHOD_FORMULA_CiA_360"
    SNYDER_SYNTHETIC_UH = "SNYDER_SYNTHETIC_UH_CT_CP"
    CLARK_IUH_TIME_AREA = "CLARK_IUH_TIME_AREA_HISTOGRAM"
    NAKAYASU_SYNTHETIC_HIROSHIMA = "NAKAYASU_SYNTHETIC_HIROSHIMA_UNIT"
    GAMMA_FUNCTION_2P_NASH = "GAMMA_FUNCTION_2P_NASH_SYNTHETIC"
    HEC_HMS_EVENT_MODELLING = "HEC_HMS_EVENT_MODELLING"
    SWMM_5_HYDROGRAPH_BLOCK = "SWMM_5_HYDROGRAPH_BLOCK_FUNCTION"
    CONTINUOUS_HYDROGRAPH_MONSOON = "CONTINUOUS_HYDROGRAPH_MONSOON_4_MONTH"
    SINGLE_PEAK_SYMMETRIC = "SINGLE_PEAK_SYMMETRIC_BELL_SHAPED"
    MULTI_PEAK_COMPOSITE = "MULTI_PEAK_COMPOSITE_SUCCESSIVE_RAINS"
    FLASH_FLOOD_RAPID_RISING = "FLASH_FLOOD_RAPID_RISING_TP_1H"
    SNOW_MELT_HYDROGRAPH = "SNOW_MELT_HYDROGRAPH_HR_DAY_SCALE"
    PMP_PMF_PROBABLE_MAX = "PMP_PMF_PROBABLE_MAX_FLOOD"
    DESIGNED_DREDGED_RETURN_FLOW = "DESIGNED_DREDGED_RETURN_FLOW"


class BankProtectionMethodType(LabeledEnum):
    BOULDER_RIPRAP_GRADED = "BOULDER_RIPRAP_GRADED_D50_200MM"
    STONE_PITCHING_RANDOM = "STONE_PITCHING_RANDOM_MORTH_CL_608"
    CEMENT_CONCRETE_PITCHING = "CEMENT_CONCRETE_PITCHING_M15_100MM"
    CC_PAVER_BLOCK_INTERLOCKING = "CC_PAVER_BLOCK_INTERLOCKING_80MM"
    GABION_BASKET_WIRE_MESH = "GABION_BASKET_WIRE_MESH_2x1x0_5M"
    GABION_MATTRESS_REVETMENT = "GABION_MATTRESS_REVETMENT_2X3X0_23M"
    RENNO_MATTRESS_GEOTEXTILE = "RENNO_MATTRESS_GEOTEXTILE_FILLED"
    GEO_BAG_SAND_FILLED = "GEO_BAG_SAND_FILLED_PP_WOVEN"
    GEO_TUBE_DEWATERING = "GEO_TUBE_DEWATERING_SHORELINE"
    LAUNCHING_APRON_GRADED = "LAUNCHING_APRON_GRADED_T_1_5m"
    SPUR_DYKE_PERMEABLE = "SPUR_DYKE_PERMEABLE_T_GROIN"
    GROYNE_IMPERMEABLE_STONE = "GROYNE_IMPERMEABLE_STONE_E_SMILE"
    GUIDE_BANK_MARGINAL_BUND = "GUIDE_BANK_MARGINAL_BUND_IRC5_15DEG"
    REVETMENT_WALL_GRAVITY = "REVETMENT_WALL_GRAVITY_MASONRY"
    GEOGRID_REINFORCED_BERM = "GEOGRID_REINFORCED_BERM_SLOPE_2H_1V"
    BAMBOO_FASCINE_SOFT = "BAMBOO_FASCINE_SOFT_PROTECTION"
    COIR_LOG_BIOENGINEERING = "COIR_LOG_BIOENGINEERING_VEGETATIVE"
    NO_PROTECTION_BEDROCK = "NO_PROTECTION_BEDROCK_NON_ERODIBLE"


class RiverTrainingWorkType(LabeledEnum):
    GUIDE_BANK_BELSUND = "GUIDE_BANK_BELSUND_FORMULA_IRC5"
    MARGINAL_BUND_FLOOD_CONTAINMENT = "MARGINAL_BUND_FLOOD_CONTAINMENT"
    CLOSING_DYKE_SLUICED = "CLOSING_DYKE_SLUICED_KHOR_SPILLED"
    GROYNE_FIELD_TRAINING = "GROYNE_FIELD_TRAINING_SPACING_2x_LENGTH"
    SPUR_TRAINING_EITHER_BANK = "SPUR_TRAINING_EITHER_BANK"
    FLOOD_WALL_URBAN_CONTAINMENT = "FLOOD_WALL_URBAN_CONTAINMENT"
    EMBANKMENT_LEVEE_PROTECTION = "EMBANKMENT_LEVEE_PROTECTION_HFL_PLUS"
    CUT_OFF_MEANDER_SHORTENING = "CUT_OFF_MEANDER_SHORTENING_CHUTE"
    ARTIFICIAL_CUTOFF_CONTROLLED = "ARTIFICIAL_CUTOFF_CONTROLLED_DREDGED"
    BENDWAY_POOL_CONTROL = "BENDWAY_POOL_CONTROL_VANE_DEFLECTOR"
    CHANNEL_RELINING_PAVING = "CHANNEL_RELINING_PAVING"
    ISLAND_CREATION_STABILISATION = "ISLAND_CREATION_STABILISATION_MID_CHANNEL"
    BARRAGE_REGULATION_FLOW = "BARRAGE_REGULATION_FLOW_POND_LEVEL"
    RESERVOIR_SEDIMENT_BYPASS = "RESERVOIR_SEDIMENT_BYPASS_TUNNEL"
    INLET_CONTROL_TRASH_RACK = "INLET_CONTROL_TRASH_RACK_300MM_CLEAR"
    RETARDING_BASIN_OFF_CHANNEL = "RETARDING_BASIN_OFF_CHANNEL_STORAGE"
    DREDGED_APPROACH_CHANNEL = "DREDGED_APPROACH_CHANNEL_NAVIGABLE_DEPTH"


class AffluxEstimationFormulaType(LabeledEnum):
    YARNELL_ORIGINAL_1934 = "YARNELL_ORIGINAL_1934_abUTMENT_K"
    CHATTAUD_MODIFIED_INDIA = "CHATTAUD_MODIFIED_INDIA_IRC5_CL_17"
    YARNELL_MODIFIED_MH_SADASHIVA = "YARNELL_MODIFIED_MH_SADASHIVA"
    BROAD_CRESTED_WEIR_IRC89 = "BROAD_CRESTED_WEIR_IRC89_FLOW_OVER"
    NARROW_CRESTED_OGEE_SHAPED = "NARROW_CRESTED_OGEE_SHAPED_SPILLWAY"
    ORIFICE_FLOW_LOW_OPENING = "ORIFICE_FLOW_LOW_OPENING_SUBMERGED"
    FREE_FLOW_DISCHARGE_AFFLUX = "FREE_FLOW_DISCHARGE_AFFLUX_HIGH_FROUDE"
    SUBMERGED_FLOW_AFFLUX = "SUBMERGED_FLOW_AFFLUX_MF_0_8"
    IRC_5_2015_CL_17_1_METHOD = "IRC_5_2015_CL_17_1_METHOD"
    MORTH_CL_704_ANNEXURE_METHOD = "MORTH_CL_704_ANNEXURE_METHOD"
    DENDY_LEHR_DELTA_METHOD = "DENDY_LEHR_DELTA_METHOD_BACKWATER"
    WSPRO_STANDARD_PROFILE = "WSPRO_STANDARD_PROFILE_USGS"
    HEC_RAS_GRADUALLY_VARIED = "HEC_RAS_GRADUALLY_VARIED_FLOW"
    ENERGY_EQUATION_ITERATIVE = "ENERGY_EQUATION_ITERATIVE_BERNOULLI"
    MOMENTUM_EQUATION_FORCE_BALANCE = "MOMENTUM_EQUATION_FORCE_BALANCE"
    AIR_INCLUDED_3D_CFD = "AIR_INCLUDED_3D_CFD_OPEN_FOAM"
    NO_AFFLUX_BEDROCK = "NO_AFFLUX_BEDROCK_WIDE_CHANNEL"


class FreeboardAdditionFactorType(LabeledEnum):
    NHAI_STANDARD_2_POINT_0M = "NHAI_STANDARD_2_POINT_0M_CLEAR_FREEBOARD"
    IRC_SP_13_1_POINT_5M = "IRC_SP_13_1_POINT_5M_URBAN_EXPRESSWAY"
    IRC5_MIN_1_POINT_0M = "IRC5_MIN_1_POINT_0M_MAJOR_BRIDGE"
    MORTH_0_POINT_75M_MINOR = "MORTH_0_POINT_75M_MINOR_BRIDGE_CULVERT"
    WAVE_RUN_UP_VON_KARMAN = "WAVE_RUN_UP_VON_KARMAN_IRREGULAR"
    WIND_SETUP_SURGE_EFFECT = "WIND_SETUP_SURGE_EFFECT_COASTAL"
    BANK_FREEBOARD_ADDITION = "BANK_FREEBOARD_ADDITION_EMBANKMENT"
    HFL_FENNEC_POST_2018_FLOOD = "HFL_FENNEC_POST_2018_FLOOD_HISTORIC_PLUS"
    SEA_LEVEL_RISE_PROJECTED_2100 = "SEA_LEVEL_RISE_PROJECTED_2100_1m"
    MONSOON_UNCERTAINTY_0_POINT_5M = "MONSOON_UNCERTAINTY_0_POINT_5M_SAFETY"
    TSUNAMI_MARINE_COASTAL = "TSUNAMI_MARINE_COASTAL_3M_PLUS"
    FLOOD_STAGE_PROJECTION_2050 = "FLOOD_STAGE_PROJECTION_2050_0_8m"
    SUPER_ELEVATION_CURVE_BANK = "SUPER_ELEVATION_CURVE_BANK_FLOW_HEEL"
    AGGRADE_SILTATION_RISK = "AGGRADE_SILTATION_RISK_HFL_UP_0_3M"
    SEICHE_WIND_OSCILLATION = "SEICHE_WIND_OSCILLATION_RESERVOIR"


class FloodFrequencyAnalysisMethodType(LabeledEnum):
    GUMBEL_EV1_DOUBLE_EXPONENTIAL = "GUMBEL_EV1_DOUBLE_EXPONENTIAL_GRINGERTON"
    LOG_PEARSON_TYPE_III_BULLETIN_17B = "LOG_PEARSON_TYPE_III_BULLETIN_17B"
    LOG_NORMAL_2PARAMETER = "LOG_NORMAL_2PARAMETER_GALTON"
    NORMAL_GAUSSIAN_LINEAR_MOMENT = "NORMAL_GAUSSIAN_LINEAR_MOMENT"
    GENERALIZED_EXTREME_VALUE_GEV_3P = "GENERALIZED_EXTREME_VALUE_GEV_3P"
    GENERALIZED_PARETO_GPD_POT = "GENERALIZED_PARETO_GPD_PEAK_OVER_THRESHOLD"
    WAKEBY_5PARAMETER_EMPRICAL = "WAKEBY_5PARAMETER_EMPRICAL_RANGE"
    WEIBULL_EXTREME_LOWER = "WEIBULL_EXTREME_LOWER_MINIMA_DROUGHT"
    PARTIAL_DURATION_SERIES_POT = "PARTIAL_DURATION_SERIES_POT_2x_AMAX"
    ANNUAL_MAXIMUM_SERIES_AMS = "ANNUAL_MAXIMUM_SERIES_AMS_N_30_YEARS"
    REGIONAL_FREQUENCY_ANALYSIS_INDEX = "REGIONAL_FREQUENCY_ANALYSIS_INDEX_FLOOD"
    BAYESIAN_MCMC_FREQUENCY = "BAYESIAN_MCMC_FREQUENCY_UNCERTAINTY"
    RFFE_GUIDELINE_AUSTRALIAN = "RFFE_GUIDELINE_AUSTRALIAN_2016"
    CWC_INDIA_MANUAL = "CWC_INDIA_MANUAL_GUMBEL_STANDARD"
    NO_FREQUENCY_DATA_HYDROGRAPH = "NO_FREQUENCY_DATA_HYDROGRAPH_RATIONAL_ONLY"
    PALAEOFLOOD_EXTENDED_SERIES = "PALAEOFLOOD_EXTENDED_SERIES_1000YEAR"


class FloodReturnPeriodDesign(LabeledEnum):
    Q2_BRIEF_RETURN = "Q2_BRIEF_RETURN_50pct_EXCEED"
    Q5_SHORT_TERM_DESIGN = "Q5_SHORT_TERM_DESIGN_20pct"
    Q10_STANDARD_MINOR = "Q10_STANDARD_MINOR_BRIDGE_CULVERT_10pct"
    Q25_INTERMEDIATE_CULVERT = "Q25_INTERMEDIATE_CULVERT_4pct"
    Q50_MAJOR_BRIDGE_STANDARD = "Q50_MAJOR_BRIDGE_STANDARD_2pct_MORTH"
    Q100_NHAI_NATIONAL_CORRIDOR = "Q100_NHAI_NATIONAL_CORRIDOR_1pct"
    Q200_EXPRESSWAY_ACCESS = "Q200_EXPRESSWAY_ACCESS_CONTROLLED_0_5pct"
    Q500_STRATEGIC_DEFENCE_SP = "Q500_STRATEGIC_DEFENCE_SP_0_2pct"
    Q1000_CRITICAL_INFRA_LIFELINE = "Q1000_CRITICAL_INFRA_LIFELINE_0_1pct"
    Q10000_ULTRA_EXTREME_HAZARD = "Q10000_ULTRA_EXTREME_HAZARD_0_01pct"
    PMF_PROBABLE_MAXIMUM_FLOOD = "PMF_PROBABLE_MAXIMUM_FLOOD_1_IN_NEVER"
    SPF_STANDARD_PROJECT_FLOOD = "SPF_STANDARD_PROJECT_FLOOD_NORM_1pct_PLUS"
    FLASH_FLOOD_2_HOUR_CRITICAL = "FLASH_FLOOD_2_HOUR_CRITICAL_URBAN_DRAIN"


class RainfallIntensityStormType(LabeledEnum):
    HFL_MONSOON_96HR_MAIN = "HFL_MONSOON_96HR_MAIN_SPELL"
    DESIGN_STORM_24HR_CWC = "DESIGN_STORM_24HR_CWC_EMDEN"
    POST_MONSOON_NORTH_EAST = "POST_MONSOON_NORTH_EAST_TN_KERALA"
    PRE_MONSOON_MANGO_SHOWER = "PRE_MONSOON_MANGO_SHOWER_KA"
    CYCLONIC_DEPR_SPEED_6HR = "CYCLONIC_DEPR_SPEED_6HR_LAND_FALL"
    CLOUD_BURST_VERY_HIGH_INTENSITY = "CLOUD_BURST_VERY_HIGH_INTENSITY_UT_JK"
    STORM_4HR_SHORT_SYNOPTIC = "4HR_SHORT_SYNOPTIC_STORM"
    STORM_1HR_URBAN_DRAIN = "1HR_URBAN_DRAIN_DESIGN_100YEAR"
    STORM_10MIN_FLASH_CULVERT = "10MIN_FLASH_CULVERT_PEAK"
    STORM_6HR_MESO_CONVECTIVE = "6HR_MESO_SCALE_CONVECTIVE"
    STORM_12HR_WESTERN_DISTURBANCE = "12HR_WESTERN_DISTURBANCE_NORTH"
    STORM_48HR_PERSISTENT_STATIONARY = "48HR_PERSISTENT_STATIONARY"
    MONSOON_WITHDRAWAL_OCTOBER = "MONSOON_WITHDRAWAL_OCTOBER_LOW"
    TROPICAL_WAVE_EQUATORIAL = "TROPICAL_WAVE_EQUATORIAL_30_60DAY_MJO"
    CONVECTIVE_CELL_ISOLATED = "CONVECTIVE_CELL_ISOLATED_AFTERNOON"
    THUNDERSTORM_DUST_STORM = "THUNDERSTORM_DUST_STORM_RAJASTHAN"


class RiverBedMaterialSizeType(LabeledEnum):
    HARD_BEDROCK_NON_ERODIBLE = "HARD_BEDROCK_NON_ERODIBLE_GNEISS_GRANITE"
    SOFT_BEDROCK_SHALE_SANDSTONE = "SOFT_BEDROCK_SHALE_SANDSTONE"
    LARGE_BOULDER_500MM_PLUS = "LARGE_BOULDER_500MM_PLUS"
    SMALL_BOULDER_256_500MM = "SMALL_BOULDER_256_500MM_WENTWORTH"
    LARGE_COBBLE_128_256MM = "LARGE_COBBLE_128_256MM"
    SMALL_COBBLE_64_128MM = "SMALL_COBBLE_64_128MM"
    VERY_COARSE_GRAVEL_32_64MM = "VERY_COARSE_GRAVEL_32_64MM"
    COARSE_GRAVEL_16_32MM = "COARSE_GRAVEL_16_32MM"
    MEDIUM_GRAVEL_8_16MM = "MEDIUM_GRAVEL_8_16MM"
    FINE_GRAVEL_4_8MM = "FINE_GRAVEL_4_8MM"
    GRANULE_2_4MM = "GRANULE_2_4MM"
    VERY_COARSE_SAND_1_2MM = "VERY_COARSE_SAND_1_2MM"
    COARSE_SAND_0_POINT_5_1MM = "COARSE_SAND_0_POINT_5_1MM"
    MEDIUM_SAND_0_POINT_25_0_POINT_5MM = "MEDIUM_SAND_0_POINT_25_0_POINT_5MM"
    FINE_SAND_0_POINT_125_0_POINT_25MM = "FINE_SAND_0_POINT_125_0_POINT_25MM"
    VERY_FINE_SAND_0_POINT_062_0_POINT_125MM = "VERY_FINE_SAND_0_POINT_062_0_POINT_125MM"
    SILT_0_POINT_004_0_POINT_062MM = "SILT_0_POINT_004_0_POINT_062MM"
    CLAY_LESS_0_POINT_004MM = "CLAY_LESS_0_POINT_004MM_COHESIVE"
    BLACK_COTTON_EXPANSIVE = "BLACK_COTTON_EXPANSIVE_VERTISOL"
    MIXED_ALLUVIAL_BRAIDED = "MIXED_ALLUVIAL_BRAIDED_MULTIMODAL"
    DUNE_SAND_ERODIBLE = "DUNE_SAND_ERODIBLE_0_POINT_2MM"
    SHELLED_CALCAREOUS = "SHELLED_CALCAREOUS_COASTAL"


class HydraulicDesignMethod(LabeledEnum):
    MANNINGS_N_EMPIRICAL = "MANNINGS_N_EMPIRICAL_STRICKLER_1_N"
    CHEZY_C_FORMULA = "CHEZY_C_FORMULA_V_C_sqrt_RS"
    DARCY_WEISBACH_f_PIPE_FULL = "DARCY_WEISBACH_f_PIPE_FULL_FLOW"
    LACEY_REGIME_DESIGN = "LACEY_REGIME_DESIGN_IRC5_R_V_P_Q_S_f"
    BLENCH_REGIME_DESIGN_MODIFIED = "BLENCH_REGIME_DESIGN_MODIFIED_IRI_GEO"
    INGLIS_FORMULA_DESIGN = "INGLIS_FORMULA_DESIGN_MORTH_CL_704"
    KENNEDY_NON_SILTING_CRITICAL = "KENNEDY_NON_SILTING_CRITICAL_V_0_55m_D_0_64"
    CRITICAL_FLOW_FROUDE_1 = "CRITICAL_FLOW_FROUDE_1_V_sqrt_gD"
    SUBCRITICAL_FROUDE_LESS_1 = "SUBCRITICAL_FROUDE_LESS_1_TRANQUIL"
    SUPERCRITICAL_FROUDE_GREATER_1 = "SUPERCRITICAL_FROUDE_GREATER_1_SHOOTING"
    HYDRAULIC_JUMP_ENERGY_DISSIPATOR = "HYDRAULIC_JUMP_ENERGY_DISSIPATOR_STILLING"
    GRADUALLY_VARIED_M1_TO_S2 = "GRADUALLY_VARIED_M1_TO_S2_PROFILE_WSPRO"
    RAPIDLY_VARIED_BORRE_WAVE = "RAPIDLY_VARIED_BORRE_WAVE_SURGE"
    UNSTEADY_FLOOD_ROUTING = "UNSTEADY_FLOOD_ROUTING_MUSKINGUM_CUNGE"
    UNSTEADY_DYNAMIC_SAINT_VENANT = "UNSTEADY_DYNAMIC_SAINT_VENANT_EQUATIONS"
    PRESSURE_FLOW_ECK = "PRESSURE_FLOW_ECK_INVERTED_SIPHON"
    OPEN_CHANNEL_GRAVITY = "OPEN_CHANNEL_GRAVITY_DEFAULT"


class DischargeMeasurementMethod(LabeledEnum):
    CURRENT_METER_PRICE_TYPE_A = "CURRENT_METER_PRICE_TYPE_A_USGS"
    ADCP_ACOUSTIC_DOPPLER_MOVINGBOAT = "ADCP_ACOUSTIC_DOPPLER_MOVINGBOAT"
    FLOAT_METHOD_WOOD_ORANGE = "FLOAT_METHOD_WOOD_ORANGE_CORRECTION_0_85"
    WEIR_CRESTED_V_NOTCH = "WEIR_CRESTED_V_NOTCH_90_DEG_REHBOCK"
    NOTCHED_RECTANGULAR_THOMSON = "NOTCHED_RECTANGULAR_THOMSON"
    VENTURI_METER_PIPE_FULL = "VENTURI_METER_PIPE_FULL_FLOW_C_D_0_985"
    PARSHALL_FLUME_TRAPEZOIDAL = "PARSHALL_FLUME_TRAPEZOIDAL_FREE_FLOW"
    CHEMICAL_GAUGING_SALT_DILUTION = "CHEMICAL_GAUGING_SALT_DILUTION_NACL"
    SLOPE_AREA_HIGH_FLOW = "SLOPE_AREA_HIGH_FLOW_POST_FLOOD"
    ULTRASONIC_DOPPLER_FIXED = "ULTRASONIC_DOPPLER_FIXED_BANK_MOUNT"
    ELECTROMAGNETIC_INDUCTIVE = "ELECTROMAGNETIC_INDUCTIVE_WATER_VELOCITY"
    STAGE_DISCHARGE_RATING_CURVE = "STAGE_DISCHARGE_RATING_CURVE_GAUGE_HEIGHT"
    EXTENDED_RATING_GAUGE_HEIGHT = "EXTENDED_RATING_GAUGE_HEIGHT_CONNEL"
    LSPIV_LARGE_SCALE_IMAGE = "LSPIV_LARGE_SCALE_IMAGE_VELOCITY"
    SATELLITE_ALTIMETRY_VIRTUAL = "SATELLITE_ALTIMETRY_VIRTUAL_STATION"
    REMOTE_SENSING_RADAR_SAR = "REMOTE_SENSING_RADAR_SAR_FLOOD_EXTENT"
    NO_GAUGE_ESTIMATE_FROM_FAB = "NO_GAUGE_ESTIMATE_FROM_FAB_CHANNEL"


class FlowVelocityCategory(LabeledEnum):
    MEAN_CROSS_SECTION_V = "MEAN_CROSS_SECTION_V_Q_BY_A"
    MAXIMUM_SURFACE_V = "MAXIMUM_SURFACE_V_MID_DEPTH_0_POINT_6"
    NEAR_BED_0_POINT_1D_V = "NEAR_BED_0_POINT_1D_V_BED_SHEAR"
    SCOUR_THRESHOLD_CRITICAL = "SCOUR_THRESHOLD_CRITICAL_SHIELDS_STRESS"
    SETTLING_FALL_VELOCITY_D50 = "SETTLING_FALL_VELOCITY_D50_STOKES"
    CRITICAL_V_FROUDE_1 = "CRITICAL_V_FROUDE_1_SQRT_gD"
    SHEAR_VELOCITY_U_STAR = "SHEAR_VELOCITY_U_STAR_SQRT_tau_BY_rho"
    FRICTION_VELOCITY_BOUNDARY = "FRICTION_VELOCITY_BOUNDARY_LAYER"
    SCOUR_ATTAINED_MAX_LOCAL = "SCOUR_ATTAINED_MAX_LOCAL_PIER"
    ALLOWABLE_V_EARTH_CHANNEL = "ALLOWABLE_V_EARTH_CHANNEL_1_0m_PER_SEC"
    MAX_PERMISSIBLE_V_NON_ERODIBLE = "MAX_PERMISSIBLE_V_NON_ERODIBLE_3_0m_PER_SEC"
    MIN_SELF_CLEANSING_V = "MIN_SELF_CLEANSING_V_0_POINT_6m_PER_SEC"
    LOW_FLOW_SUMMER_V = "LOW_FLOW_SUMMER_V_LESS_0_POINT_3"
    NAVIGABLE_MIN_V_DEPTH = "NAVIGABLE_MIN_V_DEPTH_2M_3M_PER_SEC"


class BridgeHydraulicOpeningType(LabeledEnum):
    DECK_SLAB_NO_GIRDER_OBSTRUCTION = "DECK_SLAB_NO_GIRDER_OBSTRUCTION_SOLID_DECK"
    T_GIRDER_UNDERSIDE_OBSTRUCTION = "T_GIRDER_UNDERSIDE_OBSTRUCTION_20pct_BLOCK"
    BOX_MULTI_CELLULAR_OBSTRUCTION = "BOX_MULTI_CELLULAR_OBSTRUCTION_30pct"
    I_GIRDER_PLATE_GIRDER_STEEL = "I_GIRDER_PLATE_GIRDER_STEEL_WARREN"
    THROUGH_GIRDER_BOTTOM_CHORD = "THROUGH_GIRDER_BOTTOM_CHORD_HIGH_BLOCK"
    HALF_THROUGH_GIRDER_HALF = "HALF_THROUGH_GIRDER_HALF_HEIGHT_WEB"
    TRUSS_BOTTOM_CHORD_BRACING = "TRUSS_BOTTOM_CHORD_BRACING_BLOCK_35pct"
    ARCH_BARREL_RIB_CROWN = "ARCH_BARREL_RIB_CROWN_UNDERSIDE"
    CABLE_STAYED_STIFFENING_GIRDER = "CABLE_STAYED_STIFFENING_GIRDER_AERODYNAMIC"
    SUSPENSION_HANGER_GIRDER_SLENDER = "SUSPENSION_HANGER_GIRDER_SLENDER"
    BALANCED_CANTILEVER_PIER_CAP = "BALANCED_CANTILEVER_PIER_CAP_HAMMERHEAD"
    BENT_PIER_OPEN_COLUMN = "BENT_PIER_OPEN_COLUMN_MIN_BLOCK"
    WELL_CAISSON_FOUNDATION_OBSTR = "WELL_CAISSON_FOUNDATION_OBSTR_D_2x_PILE"
    RCC_PILE_GROUP_OBSTRUCTION = "RCC_PILE_GROUP_OBSTRUCTION_3x_DIAMETER"
    INTEGRAL_NO_JOINT_SUPER = "INTEGRAL_NO_JOINT_SUPER_LOW_PROFILE"
    CULVERT_BOX_PIPE_FULL_CLOSED = "CULVERT_BOX_PIPE_FULL_CLOSED_ORIFICE"
    MULTI_SPAN_LONG_OPENING = "MULTI_SPAN_LONG_OPENING_VIADUCT_LOW_BLOCK"


class SedimentLoadTransportType(LabeledEnum):
    BED_LOAD_ROLLING_SLIDING = "BED_LOAD_ROLLING_SLIDING_CONTACT_LOAD"
    SUSPENDED_LOAD_COLLOIDAL_HIGHER = "SUSPENDED_LOAD_COLLOIDAL_HIGHER_0_POINT_062"
    WASH_LOAD_FINER_THAN_0_POINT_062 = "WASH_LOAD_FINER_THAN_0_POINT_062_SOURCE_EROSION"
    TOTAL_LOAD_BED_SUSPENDED_WASH = "TOTAL_LOAD_BED_SUSPENDED_WASH"
    BED_MATERIAL_LOAD_D50_FRACTION = "BED_MATERIAL_LOAD_D50_FRACTION_BED_PLUS_SUSPENDED"
    CONTACT_LOAD_SALTATION = "CONTACT_LOAD_SALTATION_BOUNCING"
    UNSTEADY_TRANSPORT_HYSTERESIS = "UNSTEADY_TRANSPORT_HYSTERESIS_RISING_FALLING"
    EINSTEIN_BED_LOAD_FUNCTION = "EINSTEIN_BED_LOAD_FUNCTION_INTEGRAL"
    MEYER_PETER_MULLER_BED_LOAD = "MEYER_PETER_MULLER_BED_LOAD_DIMENSIONLESS"
    ENGELUND_HANSEN_TOTAL_LOAD = "ENGELUND_HANSEN_TOTAL_LOAD_REGIME"
    ACKERS_WHITE_GRAIN_SIZE = "ACKERS_WHITE_GRAIN_SIZE_D_GR"
    VAN_RIJN_TRANSPORT_STAGES = "VAN_RIJN_TRANSPORT_STAGES_REFERENCE"
    WILCOCK_CROWE_MIXED_GRAIN = "WILCOCK_CROWE_MIXED_GRAIN_SURFACE"
    NO_SIGNIFICANT_TRANSPORT_BEDROCK = "NO_SIGNIFICANT_TRANSPORT_BEDROCK"
    COHESIVE_EROSION_FLUFF = "COHESIVE_EROSION_FLUFF_CONSOLIDATION"


class GradeControlStructureType(LabeledEnum):
    CHECK_DAM_LOW_HEAD = "CHECK_DAM_LOW_HEAD_RUBBLE_FILLED"
    DROP_STRUCTURE_VERTICAL = "DROP_STRUCTURE_VERTICAL_0_5_TO_3M"
    CASCADE_STEPPED = "CASCADE_STEPPED_GRAVITY_CHUTE"
    GRADE_STABILIZER_RIVER = "GRADE_STABILIZER_RIVER_LONG_PROFILE"
    WEIR_FIXED_CREST = "WEIR_FIXED_CREST_BROAD_CRESTED"
    BARRAGE_UNDER_SL_U_SLUICES = "BARRAGE_UNDER_SL_U_SLUICES_REGULATOR"
    RESERVOIR_FULL_LIFETIME = "RESERVOIR_FULL_LIFETIME_SEDIMENT_FILL"
    SEDIMENT_BYPASS_TUNNEL = "SEDIMENT_BYPASS_TUNNEL_FROM_HEAD_WORKS"
    SEDIMENT_TRAP_EFFICIENCY = "SEDIMENT_TRAP_EFFICIENCY_95pct"
    STILLING_BASIN_USBR_TYPE_II = "STILLING_BASIN_USBR_TYPE_II_III_IV"
    ROLLER_COMPACTED_CONCRETE_DROP = "ROLLER_COMPACTED_CONCRETE_DROP_GRADE"
    GABION_CHECK_DAM_SERIES = "GABION_CHECK_DAM_SERIES_RETARDING"
    CUTTOFF_TRENCH_KEY = "CUTTOFF_TRENCH_KEY_PILE_SHEET"
    RIVER_TRAINING_GROYNE_HEAD = "RIVER_TRAINING_GROYNE_HEAD"
    SCOUR_MATTRESS_FLEXIBLE = "SCOUR_MATTRESS_FLEXIBLE_GEOTEXTILE_ARMOUR"


class BankErosionCategoryClass(LabeledEnum):
    BEDROCK_NO_EROSION_0 = "BEDROCK_NO_EROSION_0_mm_PER_YR"
    SLIGHT_0_TO_1_M_PER_YR = "SLIGHT_0_TO_1_M_PER_YR_STABLE"
    LOW_RISK_STABILISED_VEG = "LOW_RISK_STABILISED_VEG_0_TO_0_5"
    MODERATE_1_TO_3_M_PER_YR = "MODERATE_1_TO_3_M_PER_YR_GABION_RECOMMEND"
    HIGH_3_TO_8_M_PER_YR = "HIGH_3_TO_8_M_PER_YR_HARD_PROTECTION_NEEDED"
    VERY_HIGH_8_TO_15_M_PER_YR = "VERY_HIGH_8_TO_15_M_PER_YR_BENDWAY_WORKS"
    SEVERE_15_TO_30_M_PER_YR = "SEVERE_15_TO_30_M_PER_YR_MARGINAL_BUND_NEED"
    EXTREME_GREATER_30_M_PER_YR = "EXTREME_GREATER_30_M_PER_YR_RIVER_RELOCATION"
    CATASTROPHIC_100m_SINGLE_EVENT = "CATASTROPHIC_100m_SINGLE_EVENT_AVULSION"
    CUT_BANK_MEANDER_ATTACK = "CUT_BANK_MEANDER_ATTACK_OUTER_BEND"
    SLUMP_BANK_COHESIVE_BLOCK = "SLUMP_BANK_COHESIVE_BLOCK_FAILURE"
    PIPE_SURFACE_EVASION = "PIPE_SURFACE_EVASION_INTERNAL_EROSION"
    WAVE_SCOUR_RESERVOIR_BANKS = "WAVE_SCOUR_RESERVOIR_BANKS"
    SHIP_WASH_VESSEL_PROPELLER = "SHIP_WASH_VESSEL_PROPELLER_INLAND_WATERWAY"


class LaceyRegimeFactorType(LabeledEnum):
    SILT_FACTOR_f = "SILT_FACTOR_f_1_POINT_76_SQROOT_mm"
    REGIME_WETTED_PERIMETER_P = "REGIME_WETTED_PERIMETER_P_4_POINT_8_SQROOT_Q"
    REGIME_HYDRAULIC_MEAN_DEPTH_R = "REGIME_HYDRAULIC_MEAN_DEPTH_R_0_POINT_477_Q_f_2_1_3"
    REGIME_MEAN_VELOCITY_V = "REGIME_MEAN_VELOCITY_V_10_8_R_2_3_S_1_3"
    REGIME_LONGITUDINAL_SLOPE_S = "REGIME_LONGITUDINAL_SLOPE_S_f_5_3_3340_Q_1_6"
    REGIME_DISCHARGE_Q = "REGIME_DISCHARGE_Q_V_A"
    REGIME_AREA_A_Q_BY_V = "REGIME_AREA_A_Q_BY_V"
    REGIME_TOP_WIDTH_T = "REGIME_TOP_WIDTH_T_FROM_P_SHAPE_FACTOR"
    LACEY_SCOUR_DEPTH_R_PRIME = "LACEY_SCOUR_DEPTH_R_PRIME_1_POINT_35_R"
    LACEY_MAX_SCOUR_AROUND_PIER = "LACEY_MAX_SCOUR_AROUND_PIER_2_POINT_0_x_D"
    LACEY_FLOODED_WIDTH_W = "LACEY_FLOODED_WIDTH_W_8_POARM_Q_1_2"
    SCOUR_LEVEL_BELOW_BED = "SCOUR_LEVEL_BELOW_BED_2_D_H_FL_PLUS_D"
    FOUNDATION_MIN_DEPTH_IRC5 = "FOUNDATION_MIN_DEPTH_IRC5_CL_24_2m_BELOW_SCOUR"


class IceLoadType(LabeledEnum):
    NO_ICE_LOAD_PENINSULAR = "NO_ICE_LOAD_PENINSULAR_INDIA"
    ICE_FLOE_IMPACT_HIMALAYAN_RIVER = "ICE_FLOE_IMPACT_HIMALAYAN_RIVER_ZANSKAR"
    ICE_JAM_STATIC_LOAD = "ICE_JAM_STATIC_LOAD_LEVEL_FORCE"
    STATIC_ICE_PRESSURE_PER_M = "STATIC_ICE_PRESSURE_PER_M_WIDTH_100_KN_PER_M"
    ICE_BREAKING_DYNAMIC = "ICE_BREAKING_DYNAMIC_COEFF_0_POINT_3"
    ICE_THRUST_FROM_SHEET = "ICE_THRUST_FROM_SHEET_EXPANSION_FROST"
    ICE_PERMAFROST_FOUNDATION = "ICE_PERMAFROST_FOUNDATION_THERMAL_PILE"
    GLACIAL_OUTBURST_GLOF_RISK = "GLACIAL_OUTBURST_GLOF_RISK_HIGH_ALTITUDE"
    AVALANCHE_IMPACT_LOAD = "AVALANCHE_IMPACT_LOAD_DEFENCE_GALLERY"
    SNOW_LOAD_ROOF_IRC_6 = "SNOW_LOAD_ROOF_IRC_6_ANNEX_D"
    FROST_HEAVE_SILT = "FROST_HEAVE_SILT_FOUNDATION_LIFT"
    THAW_SETTLEMENT = "THAW_SETTLEMENT_ACTIVE_LAYER_0_POINT_5_TO_3M"


class WaterQualityAggressiveType(LabeledEnum):
    NON_AGGRESSIVE_PURE_HIMALAYAN = "NON_AGGRESSIVE_PURE_HIMALAYAN_SNOW"
    MILDLY_AGGRESSIVE_MINERAL = "MILDLY_AGGRESSIVE_MINERAL_IRON"
    MODERATELY_AGGRESSIVE_ACIDIC = "MODERATELY_AGGRESSIVE_ACIDIC_PH_LESS_6"
    SEVERELY_AGGRESSIVE_SULPHATE = "SEVERELY_AGGRESSIVE_SULPHATE_IS_456_2000_TABLE_3"
    CHLORIDE_RICH_COASTAL_SEA = "CHLORIDE_RICH_COASTAL_SEA_5000_PPM"
    CHLORIDE_DEICING_SALT = "CHLORIDE_DEICING_SALT_HIMALAYAN_JAMMU_SRINAGAR"
    ACID_MINE_DRAINAGE_IRON = "ACID_MINE_DRAINAGE_IRON_COAL_AREA_CHHATTISGARH"
    INDUSTRIAL_EFFLUENT_DISCHARGE = "INDUSTRIAL_EFFLUENT_DISCHARGE_PH_3_TO_11"
    SEWAGE_POLLUTED_URBAN = "SEWAGE_POLLUTED_URBAN_BOD_100_PLUS"
    AGRICULTURAL_DRAINAGE_NITRATE = "AGRICULTURAL_DRAINAGE_NITRATE_PESTICIDE"
    SALINE_GROUND_WATER_RANN = "SALINE_GROUND_WATER_RANN_OF_KUTCHH"
    BRACKISH_BACKWATER_ESTUARY = "BRACKISH_BACKWATER_ESTUARY_5_TO_30_PSU"
    MARINE_TIDAL_FULL_SEA = "MARINE_TIDAL_FULL_SEA_35_PSU"
    HIGH_TURBIDITY_SUSPENDED = "HIGH_TURBIDITY_SUSPENDED_SILT_ABRASIVE"
    ALGAE_BIOLOGICAL_FOULING = "ALGAE_BIOLOGICAL_FOULING_DAMS_RESERVOIR"
    URANIUM_ARSENIC_FLUORIDE = "URANIUM_ARSENIC_FLUORIDE_GROUND_WATER_WB_BR"


class RiverBankType(LabeledEnum):
    NATURAL_EARTH_UNSTABILISED = "NATURAL_EARTH_UNSTABILISED"
    GRASS_TURFED_SLOPE = "GRASS_TURFED_SLOPE_3H_1V"
    STONE_PITCHING_RANDOM = "STONE_PITCHING_RANDOM_MORTH_CL608"
    CC_PITCHING_100MM = "CC_PITCHING_100MM_M15"
    GABION_BASKET_REVETMENT = "GABION_BASKET_REVETMENT_2x1x0_5"
    GABION_MATTRESS_230MM = "GABION_MATTRESS_230MM_DOUBLE_TWIST"
    RENNO_MATTRESS_GEOFILLED = "RENNO_MATTRESS_GEOFILLED_COIR"
    GEO_BAG_SAND_FILLED = "GEO_BAG_SAND_FILLED_PP_WOVEN"
    GEO_TEXTILE_REINFORCED = "GEO_TEXTILE_REINFORCED_SLOPE"
    RCC_REVETMENT_WALL = "RCC_REVETMENT_WALL_GRAVITY"
    BOULDER_RIPRAP_GRADED = "BOULDER_RIPRAP_GRADED_D50_300MM"
    CONCRETE_BLOCK_INTERLOCKING = "CONCRETE_BLOCK_INTERLOCKING_80MM"
    COIR_LOG_BIOENGINEERED = "COIR_LOG_BIOENGINEERED_VEGETATIVE"
    BAMBOO_FASCINE_SOFT = "BAMBOO_FASCINE_SOFT_PROTECTION"
    GROYNE_SPUR_FIELD = "GROYNE_SPUR_FIELD_PROTECTION"
    BEDROCK_NON_ERODIBLE = "BEDROCK_NON_ERODIBLE_NO_PROTECTION"


class SoilClass(LabeledEnum):
    CLAY_HIGH_COMPRESSIBILITY = "CH_CLAY_HIGH_CC_PI_GT_50"
    CLAY_MEDIUM_COMPRESSIBILITY = "CI_CLAY_MEDIUM_CC_PI_20_50"
    CLAY_LOW_COMPRESSIBILITY = "CL_CLAY_LOW_CC_PI_LT_20"
    SILT_HIGH_COMPRESSIBILITY = "MH_SILT_HIGH_MH_PI_GT_50"
    SILT_MEDIUM_COMPRESSIBILITY = "MI_SILT_MEDIUM_MI_PI_20_50"
    SILT_LOW_COMPRESSIBILITY = "ML_SILT_LOW_ML_PI_LT_20"
    SAND_POORLY_GRADED = "SP_SAND_POORLY_GRADED_UNIFORM"
    SAND_WELL_GRADED = "SW_SAND_WELL_GRADED_CU_GT_6"
    SAND_WITH_FINES_CLAYEY = "SC_SAND_CLAYEY_SAND_CGT_12"
    SAND_WITH_FINES_SILTY = "SM_SAND_SILTY_SAND_C5_12"
    GRAVEL_POORLY_GRADED = "GP_GRAVEL_POORLY_GRADED"
    GRAVEL_WELL_GRADED = "GW_GRAVEL_WELL_GRADED_CU_GT_4"
    GRAVEL_WITH_FINES_CLAYEY = "GC_GRAVEL_CLAYEY_GRAVEL"
    GRAVEL_WITH_FINES_SILTY = "GM_GRAVEL_SILTY_GRAVEL"
    ORGANIC_CLAY_SILT = "OL_ORGANIC_CLAY_SILT_LOW"
    ORGANIC_CLAY_HIGH = "OH_ORGANIC_CLAY_HIGH_CC"
    PEAT_HIGHLY_ORGANIC = "PT_PEAT_HIGHLY_ORGANIC_FIBROUS"
    ROCK_SOFT_SHALE_SANDSTONE = "R_SOFT_ROCK_SHALE_SANDSTONE_UCS_LT_1MPa"
    ROCK_MEDIUM_GRANITE_GNEISS = "RM_MEDIUM_ROCK_GRANITE_GNEISS_UCS_1_10MPa"
    ROCK_HARD_BASALT_QUARTZITE = "RH_HARD_ROCK_BASALT_QUARTZITE_UCS_GT_10MPa"
    BLACK_COTTON_SOIL_EXPANSIVE = "BC_BLACK_COTTON_VERTISOL_HIGH_SWELL"
    LATERITE_SOIL_ALUMINA_RICH = "LAT_LATERITE_SOIL_ALUMINA_IRON_RICH"
    MADE_UP_FILL_BORROWED = "MF_MADE_UP_FILL_BORROWED_UNCONSOLIDATED"
    ALLUVIAL_SOIL_MIXED = "AL_ALLUVIAL_SOIL_MIXED_RIVER_BASIN"
    MARINE_CLAY_SENSITIVE = "MC_MARINE_CLAY_SENSITIVE_QUICK_CLAY"
    LOESS_SILT_AEOLIAN = "LS_LOESS_SILT_AEOLIAN_COLLAPSIBLE"
    CALCAREOUS_SOIL_KANKAR = "CA_CALCAREOUS_SOIL_KANKAR_CEMENTED"


class RegimeConstantKValue(LabeledEnum):
    K_0_POINT_50_FINE_SILT = "K_0_50_FINE_SILT_D50_0_POINT_08mm"
    K_0_POINT_75_SILTY_CLAY = "K_0_75_SILTY_CLAY_D50_0_POINT_125mm"
    K_0_POINT_95_SANDY_SILT = "K_0_95_SANDY_SILT_D50_0_POINT_2mm"
    K_1_POINT_00_LACEY_DEFAULT = "K_1_00_LACEY_DEFAULT_SAND_D50_0_POINT_25mm"
    K_1_POINT_25_COARSE_SAND = "K_1_25_COARSE_SAND_D50_0_POINT_4mm"
    K_1_POINT_50_FINE_GRAVEL = "K_1_50_FINE_GRAVEL_D50_0_POINT_75mm"
    K_1_POINT_75_MEDIUM_GRAVEL = "K_1_75_MEDIUM_GRAVEL_D50_1_POINT_5mm"
    K_2_POINT_00_COARSE_GRAVEL = "K_2_00_COARSE_GRAVEL_D50_3mm"
    K_2_POINT_50_SMALL_COBBLE = "K_2_50_SMALL_COBBLE_D50_8mm"
    K_3_POINT_00_BEDROCK_CUP = "K_3_00_BEDROCK_CUP_D50_20mm"
    K_4_POINT_00_BOULDER_BED = "K_4_00_BOULDER_BED_D50_80mm"
    K_CUSTOM_MEASURED_D50 = "K_CUSTOM_FROM_MEASURED_D50_BED_SAMPLE"


class RiverGeomorphologyType(LabeledEnum):
    RIVER_BRAIDED_MULTI_CHANNEL = "RIVER_BRAIDED_MULTI_CHANNEL_COARSE_SAND_GRAVEL_BED"
    RIVER_MEANDERING_SINGLE_THREAD = "RIVER_MEANDERING_SINGLE_THREAD_SAND_SILT_ALLUVIAL"
    RIVER_STRAIGHT_POOL_RIFFLE = "RIVER_STRAIGHT_POOL_RIFFLE_BEDROCK_CONTROLLED"
    RIVER_ANASTOMOSING_SPLIT_BRAID = "RIVER_ANASTOMOSING_SPLIT_BRAID_FINE_GRAIN_FLOODPLAIN"
    RIVER_WANDERING_GRAVEL_BED = "RIVER_WANDERING_GRAVEL_BED_MID_SIZED_HIMALAYAN_TORRENT"
    RIVER_TORRENTIAL_STEEP_MOUNTAIN = "RIVER_TORRENTIAL_STEEP_MOUNTAIN_BEDROCK_BOULDER_COBBLE"
    RIVER_EPHEMERAL_MONSOONAL = "RIVER_EPHEMERAL_MONSOONAL_RAJASTHAN_ARID_RUN_OFF"
    RIVER_PERENNIAL_GLACIAL = "RIVER_PERENNIAL_GLACIAL_GANGA_BRAMHAPUTRA_SOURCE"
    RIVER_INTERMITTENT_SEASONAL = "RIVER_INTERMITTENT_SEASONAL_PENINSULAR_DECCAN_RIVERS"
    RIVER_DELTAIC_DISTRIBUTARY = "RIVER_DELTAIC_DISTRIBUTARY_SUNDERBANS_GODAVARI_DELTA"
    RIVER_TIDAL_ESTUARINE = "RIVER_TIDAL_ESTUARINE_SALT_WATER_INTRUSION_HOOGHLY"
    RIVER_ENDORHEIC_INLAND_BASIN = "RIVER_ENDORHEIC_INLAND_BASIN_RANN_OF_KUTCH_LUNI"
    RIVER_YOUTHFUL_V_SHAPED = "RIVER_YOUTHFUL_V_SHAPED_VALLEY_WESTERN_GHATS"
    RIVER_MATURE_U_SHAPED_FLOOD = "RIVER_MATURE_U_SHAPED_FLOOD_PLAIN_DEVELOPED"
    RIVER_OLD_AGE_BRAIDED_DELTA = "RIVER_OLD_AGE_BRAIDED_DELTA_FAN_SILT_DEPOSIT"


class WaterSurfaceProfileType(LabeledEnum):
    M1_MILD_BACKWATER_CURVE = "M1_MILD_BACKWATER_CURVE_DAM_RESERVOIR_UPSTREAM"
    M2_MILD_DRAWDOWN_CURVE = "M2_MILD_DRAWDOWN_CURVE_FREE_OVERFALL_BRIDGE_ABUTMENT"
    M3_MILD_RAPID_FLOW = "M3_MILD_RAPID_FLOW_SLUICE_GATE_DISCHARGE"
    S1_STEEP_BACKWATER = "S1_STEEP_BACKWATER_DOWNSTREAM_OF_BREAK_IN_GRADE"
    S2_STEEP_DRAWDOWN = "S2_STEEP_DRAWDOWN_TRANSITION_MILD_TO_STEEP"
    S3_STEEP_RAPID_FLOW = "S3_STEEP_RAPID_FLOW_FROM_GATE_ON_STEEP_CHUTE"
    C1_CRITICAL_BACKWATER = "C1_CRITICAL_BACKWATER_NEARLY_HORIZONTAL_SLIGHT_BACKUP"
    C3_CRITICAL_RAPID = "C3_CRITICAL_RAPID_CREST_OF_GATED_SPILLWAY"
    H1_HORIZONTAL_BACKWATER = "H1_HORIZONTAL_BACKWATER_RESERVOIR_POOL_LEVEL_BRIDGE_WEIR"
    H2_HORIZONTAL_DRAWDOWN = "H2_HORIZONTAL_DRAWDOWN_CULVERT_OUTLET"
    H3_HORIZONTAL_RAPID = "H3_HORIZONTAL_RAPID_FLAT_SLOPE_SUPERCRITICAL"
    A1_ADVERSE_BACKWATER = "A1_ADVERSE_BACKWATER_REVERSE_SLOPE_MILD_SURGE"
    A2_ADVERSE_DRAWDOWN = "A2_ADVERSE_DRAWDOWN_ADVERSE_GRADE_NEGATIVE_SLOPE"
    A3_ADVERSE_RAPID = "A3_ADVERSE_RAPID_ADVERSE_SLOPE_SUPERCRITICAL_OUTLET"
    JUMP_HYDRAULIC_S0_TO_SUBCRITICAL = "HYDRAULIC_JUMP_ENERGY_DISSPATOR_STILLING_BASIN"


class ScourProtectionSubtype(LabeledEnum):
    LAUNCHING_APRON_GABION = "LAUNCHING_APRON_GABION_TETRAPOD_FLEXIBLE"
    RIP_RAP_ARMOUR_GRADED = "RIP_RAP_ARMOUR_GRADED_D50_0_P6M_OVER_FILTER"
    CONCRETE_BLOCK_MATTRESS_ARTICULATED = "CONCRETE_BLOCK_MATTRESS_ARTICULATED_ACBM_REVETMENT"
    GROYNE_SPUR_TRAINING = "GROYNE_SPUR_TRAINING_IMPERMEABLE_TRANSVERSE"
    GUIDE_BUND_STREAMLINE = "GUIDE_BUND_STREAMLINE_APPROACH_KUMMEL_APPROACH"
    MARGINAL_BAND_EMBANKMENT = "MARGINAL_BAND_EMBANKMENT_FLOOD_PROTECTION_LEVEE"
    POROUS_CHECK_DAM = "POROUS_CHECK_DAM_GABION_BIOENGINEERED"
    INVERTED_FILTER_BLANKET = "INVERTED_FILTER_BLANKET_3_LAYER_GEO_SAND_GRAVEL"
    CEMENT_BAG_STACK_PROTECTION = "CEMENT_BAG_STACK_PROTECTION_EMERGENCY_EMBANKMENT_TOE"
    STONE_CANTELEVER_TIPPING = "STONE_CANTELEVER_TIPPING_ABUTMENT_SCOUR_REPAIR"
    SUBMERGED_VANE_FIELD = "SUBMERGED_VANE_FIELD_FLOW_DEFLECTOR_VORTEX_CONTROL"
    BED_SILL_GRADE_CONTROL = "BED_SILL_GRADE_CONTROL_RCC_STEPPED_CASCADE"
    SAND_CITATION_FILL = "SAND_CITATION_FILL_SCOUR_HOLE_BACKFILL_COMPACTION"
    SACRIFICIAL_PILE_SLEEVE = "SACRIFICIAL_PILE_SLEEVE_CORROSION_ABRASION_PROTECTION"
    SCOUR_MONITORING_SONAR_RADAR = "SCOUR_MONITORING_SONAR_RADAR_FLOAT_SENSOR_HOUSING"


class SedimentYieldClassification(LabeledEnum):
    SEDIMENT_YIELD_LOW_LT_100 = "SEDIMENT_YIELD_LOW_LT_100_TONNES_PER_SQ_KM_PER_YEAR"
    SEDIMENT_YIELD_MODERATE_100_500 = "SEDIMENT_YIELD_MODERATE_100_500_TONNES_PER_SQ_KM"
    SEDIMENT_YIELD_HIGH_500_2000 = "SEDIMENT_YIELD_HIGH_500_2000_TONNES_PER_SQ_KM"
    SEDIMENT_YIELD_VERY_HIGH_2000_5000 = "SEDIMENT_YIELD_VERY_HIGH_2000_5000_TONNES_HIMALAYA"
    SEDIMENT_YIELD_EXTREME_5000_PLUS = "SEDIMENT_YIELD_EXTREME_GT_5000_TONNES_GANGA_YAMUNA_BASIN"
    SEDIMENT_LOAD_SUSPENDED_DOMINATED = "SEDIMENT_LOAD_SUSPENDED_DOMINATED_80PCT_SUSPEND_ALLUVIAL"
    SEDIMENT_LOAD_BED_MATERIAL_DOMINATED = "SEDIMENT_LOAD_BED_MATERIAL_DOMINATED_COARSE_BRAIDED"
    SEDIMENT_LOAD_WASH_LOAD_FINE = "SEDIMENT_LOAD_WASH_LOAD_FINE_CLAY_SILT_0_POINT_0625mm"
    SEDIMENT_LOAD_DISSOLVED_FLUX = "SEDIMENT_LOAD_DISSOLVED_FLUX_SALINITY_IRON_MINERAL"
    BED_LOAD_MEYER_PETER_MULLER_FORMULA = "BED_LOAD_MEYER_PETER_MULLER_FORMULA_TRACTIVE_STRESS"
    BED_LOAD_ENGELUND_HANSEN = "BED_LOAD_ENGELUND_HANSEN_UNIT_STREAM_POWER_METHOD"
    TOTAL_LOAD_ACKERS_WHITE = "TOTAL_LOAD_ACKERS_WHITE_TRANSPORT_FUNCTION"
    TOTAL_LOAD_COLF_BY_STATE = "TOTAL_LOAD_COLF_BY_STATE_REGIONAL_CALIBRATED"
    FLUVIAL_PROCESS_DEGRADING = "FLUVIAL_PROCESS_DEGRADING_BED_ELEVATION_DECREASING_EROSION"
    FLUVIAL_PROCESS_AGGRADING = "FLUVIAL_PROCESS_AGGRADING_BED_ELEVATION_INCREASING_DEPOSITION"


class RiverCrossingClass(LabeledEnum):
    CROSSING_MINOR_CULVERT_LT_6M = "CROSSING_MINOR_CULVERT_LT_6M_SPAN_IR_SP_13"
    CROSSING_MINOR_BRIDGE_6M_30M = "CROSSING_MINOR_BRIDGE_6M_30M_SPAN_SLAB_PSC_GIRDER"
    CROSSING_MAJOR_BRIDGE_30M_60M = "CROSSING_MAJOR_BRIDGE_30M_60M_TOTAL_LEN_SPAN_LT_120M"
    CROSSING_LARGE_BRIDGE_60M_150M = "CROSSING_LARGE_BRIDGE_60M_150M_TOTAL_LEN_MULTI_SPAN"
    CROSSING_VERY_LARGE_GT_150M = "CROSSING_VERY_LARGE_GT_150M_VIADUCT_LONG_SPAN"
    CROSSING_VIADUCT_ELEVATED = "CROSSING_VIADUCT_ELEVATED_PIER_CAP_SUPERSTRUCTURE_METRO"
    CROSSING_CAUSEWAY_SUBMERSIBLE = "CROSSING_CAUSEWAY_SUBMERSIBLE_DURING_HFL_MONSOON_CROSSING"
    CROSSING_LOW_LEVEL_CAUSEWAY = "CROSSING_LOW_LEVEL_CAUSEWAY_FAIR_WEATHER_CROSSING_ONLY"
    CROSSING_NAVIGABLE_AIR_DRAFT = "CROSSING_NAVIGABLE_AIR_DRAFT_INLAND_WATERWAYS_I_W_A_10M_CLEAR"
    CROSSING_FOOT_OVER_BRIDGE_PEDESTRIAN = "CROSSING_FOOT_OVER_BRIDGE_PEDESTRIAN_ONLY_FOB"
    CROSSING_ROB_RAILWAY_OVER_BRIDGE = "CROSSING_ROB_RAILWAY_OVER_BRIDGE_ROAD_OVER_RAILWAY_IR"
    CROSSING_RUB_RAILWAY_UNDER_BRIDGE = "CROSSING_RUB_RAILWAY_UNDER_BRIDGE_RAIL_OVER_ROAD_BOX"
    CROSSING_RUB_BOX_CULVERT_RAIL = "CROSSING_RUB_BOX_CULVERT_RAIL_PUSHED_IN_RAILWAY_LINE"
    CROSSING_AQUEDUCT_CANAL_OVER = "CROSSING_AQUEDUCT_CANAL_OVER_RIVER_WATER_CROSS_DRAINAGE"
    CROSSING_PIPELINE_BRIDGE = "CROSSING_PIPELINE_BRIDGE_OIL_GAS_WATER_PIPE_CROSSING"


# ===========================================================================
# SECTION 8 — MATERIALS / CONSTRUCTION / COMPONENTS
# ===========================================================================


class ConcreteAggregateType(LabeledEnum):
    CRUSHED_GRANITE_HARD = "CRUSHED_GRANITE_HARD_MORTH_CL_1012"
    CRUSHED_BASALT_MAFIC = "CRUSHED_BASALT_MAFIC_DARK"
    CRUSHED_LIMESTONE_CALCAREOUS = "CRUSHED_LIMESTONE_CALCAREOUS"
    CRUSHED_GRAVEL_ALLUVIAL = "CRUSHED_GRAVEL_ALLUVIAL_RIVER_BORN"
    NATURAL_GRAVEL_RIVER_WASHED = "NATURAL_GRAVEL_RIVER_WASHED_40mm"
    BROKEN_STONE_METAL = "BROKEN_STONE_METAL_20mm_WMM"
    COARSE_SAND_CONCRETE = "COARSE_SAND_CONCRETE_ZONE_II_IS_383"
    FINE_SAND_MORTAR = "FINE_SAND_MORTAR_ZONE_III"
    MANUFACTURED_SAND_M_SAND = "MANUFACTURED_SAND_M_SAND_CRUSHED_ROCK"
    QUARTZITE_AGGREGATE_HARD = "QUARTZITE_AGGREGATE_HIGH_ABRASION"
    LIGHTWEIGHT_AGGREGATE_AAC = "LIGHTWEIGHT_AGGREGATE_AAC_CLAY_PUFFED"
    HEAVYWEIGHT_AGGREGATE_BARYTES = "HEAVYWEIGHT_AGGREGATE_BARYTES_RADIATION"
    RECYCLED_CONCRETE_AGGREGATE = "RECYCLED_CONCRETE_AGGREGATE_RCA_RCA_70PCT"
    COPPER_SLAG_AGGREGATE = "COPPER_SLAG_AGGREGATE_INDUSTRIAL_BYPRODUCT"
    STEEL_SLAG_AGGREGATE = "STEEL_SLAG_AGGREGATE_BOILED_STABILISED"
    PUMICE_STONE_LIGHTWEIGHT = "PUMICE_STONE_LIGHTWEIGHT_STRUCTURAL"
    VERMICULITE_AGGREGATE = "VERMICULITE_AGGREGATE_INSULATION"
    PERLITE_AGGREGATE = "PERLITE_AGGREGATE_LIGHTWEIGHT"
    BRICK_BALLAST_AGGREGATE = "BRICK_BALLAST_AGGREGATE_RECYCLED_CLINKER"
    COARSE_AGGREGATE_MAX_10mm = "CA_MAX_10mm_SINGLE_SIZE"
    COARSE_AGGREGATE_MAX_20mm = "CA_MAX_20mm_SINGLE_SIZE"
    COARSE_AGGREGATE_MAX_40mm = "CA_MAX_40mm_SINGLE_SIZE"
    COARSE_AGGREGATE_MAX_63mm = "CA_MAX_63mm_MASS_CONCRETE"
    GRADATION_SINGLE_SIZE = "GRADATION_SINGLE_SIZE_UNIFORM_CU_LT_2"
    GRADATION_WELL_GRADED = "GRADATION_WELL_GRADED_CU_GT_6_CC_1_3"
    GRADATION_GAP_GRADED = "GRADATION_GAP_GRADED_MISSING_SIEVES"


class CementType(LabeledEnum):
    OPC_33_GRADE_IS_269 = "OPC_33_GRADE_IS_269_GENERAL"
    OPC_43_GRADE_IS_8112 = "OPC_43_GRADE_IS_8112_STRUCTURAL_NORMAL"
    OPC_53_GRADE_IS_12269 = "OPC_53_GRADE_IS_12269_HIGH_STRENGTH_EARLY"
    PPC_PORTLAND_POZZOLANA_FLYASH = "PPC_PORTLAND_POZZOLANA_FLYASH_15_35PCT"
    PSC_PORTLAND_SLAG_CEMENT = "PSC_PORTLAND_SLAG_GGBS_25_70PCT"
    SRPC_SULPHATE_RESISTANT = "SRPC_SULPHATE_RESISTANT_IS_12330_SOIL"
    SRPC_SULPHATE_RESISTANT_TYPE_V = "SRPC_TYPE_V_HIGH_SULPHATE_SEVERE"
    LHPFC_LOW_HEAT_PORTLAND = "LHPFC_LOW_HEAT_MASS_CONCRETE_DAMS"
    RHPC_RAPID_HARDENING = "RHPC_RAPID_HARDENING_EARLY_STRENGTH"
    PHSR_PORTLAND_HIGH_SULPHATE_RESIST = "PHSR_PORTLAND_HIGH_SULPHATE_RESIST"
    PCC_COLOURED_WHITE = "PCC_WHITE_CEMENT_COLOURED_TILING"
    PCC_MASONRY_CEMENT = "PCC_MASONRY_CEMENT_NON_STRUCTURAL_WALLS"
    OIL_WELL_CEMENT_CLASS_A = "OIL_WELL_CEMENT_CLASS_A_API_10A"
    EXPANSIVE_CEMENT_K_TYPE = "EXPANSIVE_CEMENT_K_TYPE_SHRINKAGE_COMPENSATE"
    REFACTORY_CEMENT_CAC_ALUMINATE = "REFACTORY_CEMENT_CAC_HIGH_ALUMINATE_FURNACE"
    SUPER_SULPHATED_CEMENT = "SUPER_SULPHATED_CEMENT_LOW_HEAT_SLAG"
    MAGNESIUM_OXYCHLORIDE = "MAGNESIUM_OXYCHLORIDE_SOREL_FLOORING"
    GEOPOLYMER_CEMENT_ALKALI = "GEOPOLYMER_CEMENT_ALKALI_ACTIVATED_LOW_CO2"
    BINARY_BLEND_CEMENT = "BINARY_BLEND_CEMENT_OPC_GGBS_FLYASH"
    TERNARY_BLEND_CEMENT = "TERNARY_BLEND_CEMENT_OPC_GGBS_FLYASH_SILICA_FUME"


class AdmixtureType(LabeledEnum):
    PLASTICIZER_NORMAL_SNF = "PLASTICIZER_NORMAL_SNF_SULPHONATED_NAPTHALENE"
    PLASTICIZER_MELAMINE_SMF = "PLASTICIZER_MELAMINE_SMF_SULPHONATED_MELAMINE"
    SUPERPLASTICIZER_PCE_POLYCARBOXYLATE = "SUPERPLASTICIZER_PCE_POLYCARBOXYLATE_ETHER"
    SUPERPLASTICIZER_ACRYLIC_ETHER = "SUPERPLASTICIZER_ACRYLIC_ETHER_BASED"
    ACCELERATOR_CACL_CALCIUM_CHLORIDE = "ACCELERATOR_CACL_CALCIUM_CHLORIDE_NON_PRE_STRESS"
    ACCELERATOR_NON_CHLORIDE_NITRATE = "ACCELERATOR_NON_CHLORIDE_CALCIUM_NITRATE"
    RETARDER_LIGNOSULPHONATE = "RETARDER_LIGNOSULPHONATE_NORMAL_1_3_HR"
    RETARDER_GLUCONATE_SUGAR = "RETARDER_SODIUM_GLUCONATE_LONG_4_12_HR"
    ACCELERATING_RETARDING_SET_AIR = "AIR_ENTRAINING_AGENT_AEA_VINSOL_RESIN"
    AIR_ENTRAINING_AEA_STANDARD = "AIR_ENTRAINING_AEA_STANDARD_DURABILITY_FREEZE_THAW"
    WATER_REDUCING_WR_NORMAL = "WATER_REDUCING_WR_NORMAL_5_10PCT_WATER"
    HIGH_RANGE_WATER_REDUCER_HRWR = "HRWR_HIGH_RANGE_12_30PCT_WATER_REDUCE"
    SHRINKAGE_REDUCING_ADMIXTURE = "SRA_SHRINKAGE_REDUCING_GLYCOL_ETHER"
    CORROSION_INHIBITOR_SODIUM_NITRITE = "CORROSION_INHIBITOR_SODIUM_NITRITE_CN_104"
    CORROSION_INHIBITOR_AMINO_ESTER = "CORROSION_INHIBITOR_AMINO_ESTER_ORGANIC"
    INTEGRAL_WATERPROOFING = "INTEGRAL_WATERPROOFING_PENETRATING_CRYSTALLINE"
    INTEGRAL_WATERPROOFING_POLYMER = "INTEGRAL_WATERPROOFING_SBR_LATEX_POLYMER"
    DAMP_PROOFING_ADMIXTURE = "DAMP_PROOFING_ADMIXTURE_STEARATES"
    ANTI_FREEZING_AGENT = "ANTI_FREEZING_AGENT_CALCIUM_FORMATE_COLD"
    PUMPING_AID_BENTONITE = "PUMPING_AID_BENTONITE_CELLULOSE_ETHER"
    SEGREGATION_REDUCING_VISCOSITY = "VMA_VISCOSITY_MODIFYING_SEGREGATION_CONTROL"
    COLOURING_ADMIXTURE_MINERAL = "COLOURING_ADMIXTURE_MINERAL_OXIDE_PIGMENTS"
    EXPANSIVE_ADMIXTURE_ETTRINGITE = "EXPANSIVE_ADMIXTURE_ETTRINGITE_SHRINKAGE_COMP"
    FLASH_SET_ACCELERATOR_SHOTCRETE = "FLASH_SET_ACCELERATOR_SHOTCRETE_TUNNEL_ALKALI_FREE"
    HYDROPHOBING_ADMIXTURE = "HYDROPHOBING_ADMIXTURE_STEARIC_ACID"
    RHEOLOGY_STABILIZER = "RHEOLOGY_STABILIZER_WELAN_GUM_BIO_POLYSACCHARIDE"
    ALKALI_AGGREGATE_REACTION_SUPPRESSOR = "AAR_SUPPRESSOR_LITHIUM_NITRATE_SILICA_FUME"
    FIBER_REINFORCEMENT_MICRO_STEEL = "FIBER_REINFORCEMENT_MICRO_STEEL_0_POINT_2mm"
    FIBER_REINFORCEMENT_MACRO_POLYPROPYLENE = "FIBER_REINFORCEMENT_PP_MACRO_48mm"
    FIBER_REINFORCEMENT_GLASS_FIBER = "FIBER_REINFORCEMENT_GLASS_FIBER_ALKALI_RESISTANT"
    FIBER_REINFORCEMENT_NYLON = "FIBER_REINFORCEMENT_NYLON_FIBRILATED"


class WeldType(LabeledEnum):
    SMAW_MANUAL_ARC_SHIELDED = "SMAW_MANUAL_METAL_ARC_SHIELDED_ELECTRODE"
    GMAW_MIG_METAL_INERT_GAS = "GMAW_MIG_METAL_INERT_GAS_CO2_ARGON"
    GTAW_TIG_TUNGSTEN_INERT_GAS = "GTAW_TIG_TUNGSTEN_INERT_ARGON_PRECISE"
    FCAW_FLUX_CORED_ARC = "FCAW_FLUX_CORED_ARC_CONTINUOUS_WIRE"
    SAW_SUBMERGED_ARC_AUTOMATIC = "SAW_SUBMERGED_ARC_AUTOMATIC_HIGH_DEP_DEPOSITION"
    EGW_ELECTRO_GAS_WELDING = "EGW_ELECTRO_GAS_VERTICAL_WELD_STEEL_PLATE_GIRDER"
    ESW_ELECTRO_SLAB_WELDING = "ESW_ELECTRO_SLAB_WELDING_VERTICAL_THICK_PLATE"
    PW_PLASMA_ARC_PRECISE = "PW_PLASMA_ARC_PRECISE_THIN_STAINLESS"
    LBW_LASER_BEAM_HIGH_DENSITY = "LBW_LASER_BEAM_HIGH_DENSITY_DEEP_PENETRATION"
    EBW_ELECTRON_BEAM_VACUUM = "EBW_ELECTRON_BEAM_VACUUM_PRECISION"
    RW_SPOT_RESISTANCE = "RW_SPOT_RESISTANCE_SHEET_METAL"
    RW_SEAM_RESISTANCE_CONTINUOUS = "RW_SEAM_RESISTANCE_CONTINUOUS_WATER_TIGHT"
    FW_FLASH_BUTT_JOINT = "FW_FLASH_BUTT_JOINT_RAIL_END"
    FRW_FRICTION_STIR = "FRW_FRICTION_STIR_SOLID_STATE_ALUMINIUM"
    OFW_OXY_ACETYLENE_GAS = "OFW_OXY_ACETYLENE_GAS_GENERAL_CUT_WELD"
    BRAZING_FILLER_BRAZE_ALLOY = "BRAZING_FILLER_BRAZE_ALLOY_HIGH_STRENGTH"
    SOLDERING_SOFT_TIN_LEAD = "SOLDERING_SOFT_TIN_LEAD_ELECTRONIC"
    STUD_WELDING_SHEAR_CONNECTOR = "STUD_WELDING_SHEAR_CONNECTOR_COMPOSITE_DECK"
    SOCKET_WELD_PIPE_FITTING = "SOCKET_WELD_PIPE_FITTING_B16_11_3000#"
    BUTT_WELD_PIPE_FULL_PENETRATION = "BUTT_WELD_PIPE_FULL_PENETRATION_GROOVE_V"
    FILLET_WELD_SIZE_SPECIFIED = "FILLET_WELD_SIZE_SPECIFIED_THROAT_MIN_THICKNESS"
    PLUG_WELD_SLOT_CONNECTOR = "PLUG_WELD_SLOT_CONNECTOR_LAP_JOINT"
    TACK_WELD_TEMPORARY = "TACK_WELD_TEMPORARY_FIXTURE_ASSEMBLY"
    BACKING_WELD_CERAMIC_BACKING = "BACKING_WELD_CERAMIC_BACKING_FULL_PENETRATION"
    WELDMARK_INSPECTION_CLASS = "WELDMARK_INSPECTION_CLASS_1_B_EN_1090"


class BearingMaterial(LabeledEnum):
    NRB_NATURAL_RUBBER = "NRB_NATURAL_RUBBER_POLYISOPRENE_GENERAL_PURPOSE"
    NBR_NITRILE_RUBBER = "NBR_NITRILE_RUBBER_OIL_RESISTANT_FUEL"
    CR_NEOPRENE_CHLOROPRENE = "CR_NEOPRENE_CHLOROPRENE_WEATHER_OZONE"
    EPDM_ETHYLENE_PROPYLENE = "EPDM_ETHYLENE_PROPYLENE_DYENE_TERRACE_DIENE_MAIN_WEATHER"
    SILICONE_RUBBER_VMQ = "SILICONE_RUBBER_VMQ_HIGH_TEMP_RANGE_200C"
    VITON_FKM_FLUOROELASTOMER = "VITON_FKM_FLUOROELASTOMER_CHEMICAL_HIGH_TEMP"
    URETHANE_POLYURETHANE_PU = "URETHANE_POLYURETHANE_PU_HIGH_ABRASION_LOAD"
    PTFE_TEFLON_SLIDING_SURFACE = "PTFE_TEFLON_SLIDING_SURFACE_GLASS_FILLED_25PCT"
    PTFE_MODIFIED_GLASS_BRONZE = "PTFE_MODIFIED_GLASS_BRONZE_FILLED_LOW_FRICTION"
    STEEL_BACKING_PLATE_STRUCTURAL = "STEEL_BACKING_PLATE_STRUCTURAL_MILD_STEEL_IS_2062"
    STEEL_BACKING_STAINLESS_SS304 = "STEEL_BACKING_STAINLESS_SS304_NON_CORROSIVE"
    STEEL_BACKING_HIGH_STRENGTH_EN8 = "STEEL_BACKING_HIGH_STRENGTH_EN8_080M40"
    STEEL_BACKING_WEAR_RESISTANT_HARD_CHROME = "STEEL_BACKING_HARD_CHROME_PLATED_50UM"
    BRONZE_TIN_PB_BEARING_ALLOY = "BRONZE_TIN_PB_BEARING_ALLOY_LEADED_C93200"
    ALUMINIUM_BRONZE_C95400 = "ALUMINIUM_BRONZE_C95400_HIGH_LOAD_SLIDING"
    COPPER_LEAD_BIMETAL_STRIP = "COPPER_LEAD_BIMETAL_STRIP_POT_BEARING_LINER"
    WHITE_METAL_BABBITT_TIN_BASE = "WHITE_METAL_BABBITT_TIN_BASE_88TIN_8ANTIMONY"
    WHITE_METAL_BABBITT_LEAD_BASE = "WHITE_METAL_BABBITT_LEAD_BASE_75LEAD_15ANTIMONY"
    PHENOLIC_RESIN_LINEN_REINFORCED = "PHENOLIC_RESIN_LINEN_REINFORCED_LIGHT_LOAD_CIVIL"
    NYLON_66_REINFORCED_MOLY = "NYLON_66_REINFORCED_MOLY_DISULPHIDE_GEAR"
    PHOSPHOR_BRONZE_C51100 = "PHOSPHOR_BRONZE_C51100_SPRING_LOAD_BEARING_CUP"
    GRAPHITE_IMPREGNATED_CARBON = "GRAPHITE_IMPREGNATED_CARBON_SELF_LUBRICATING"
    CORK_COMPOSITE_BEARING_PAD = "CORK_COMPOSITE_BEARING_PAD_VIBRATION_DAMPING"
    LAMINATED_RUBBER_STEEL_SANDWICH = "LAMINATED_RUBBER_STEEL_SANDWICH_STANDARD_ELASTOMERIC"
    HIGH_DAMPING_RUBBER_HDR_LRB = "HIGH_DAMPING_RUBBER_HDR_SEISMIC_ISOLATOR_LRB"


class JointSealantType(LabeledEnum):
    POLYSULPHIDE_PS_TWO_PART = "POLYSULPHIDE_PS_TWO_PART_ASTM_C920_MOVEMENT_25PCT"
    POLYURETHANE_PU_TWO_PART = "POLYURETHANE_PU_TWO_PART_ASTM_C920_MODULUS"
    POLYURETHANE_PU_ONE_PART_MOISTURE_CURE = "POLYURETHANE_PU_ONE_PART_MOISTURE_CURE"
    SILICONE_SR_NEUTRAL_CURE = "SILICONE_SR_NEUTRAL_CURE_HIGH_PERFORMANCE_ASTM_C920"
    SILICONE_SR_ACETIC_CURING = "SILICONE_SR_ACETIC_CURING_GENERAL_PURPOSE_GLAZING"
    SILICONE_SR_LOW_MODULUS = "SILICONE_SR_LOW_MODULUS_JOINT_MOVEMENT_50PCT"
    MS_POLYMER_MODIFIED_SILANE = "MS_POLYMER_MODIFIED_SILANE_HYBRID_LOW_MODULUS"
    BUTYL_RUBBER_PREFORMED_TAPE = "BUTYL_RUBBER_PREFORMED_TAPE_VULCANIZED_COMPRESSION"
    NEOPRENE_GASKET_PREFORMED = "NEOPRENE_GASKET_PREFORMED_DENDRITIC_NITRILE"
    NITRILE_RUBBER_CORD_BACKING = "NITRILE_RUBBER_CORD_BACKING_ROD_CLOSED_CELL_ETHAPROP"
    COMPRESSIBLE_IMPERVIOUS_FABRIC = "COMPRESSIBLE_IMPERVIOUS_FABRIC_VINYL_FOAM_BUTYL"
    HOT_APPLIED_BITUMINOUS_RUBBER = "HOT_APPLIED_BITUMINOUS_RUBBER_HMA_JOINT_FILLER_ROAD"
    COLD_APPLIED_BITUMINOUS_EMULSION = "COLD_APPLIED_BITUMINOUS_EMULSION_CUT_BACK_MINOR_JOINT"
    EPOXY_JOINT_FILLER_RIGID = "EPOXY_JOINT_FILLER_RIGID_STRUCTURAL_BONDING"
    FIBRE_BOARD_IMPREGNATED_BITUMEN = "FIBRE_BOARD_IMPREGNATED_BITUMEN_EXPANSION_JOINT_FILLER_20mm"
    CORK_EXPANSION_JOINT_FILLER = "CORK_EXPANSION_JOINT_FILLER_COMPRESSIBLE_SLAB_JOINT"
    STYROFOAM_XPS_CLOSED_CELL = "STYROFOAM_XPS_CLOSED_CELL_EXPANSION_JOINT_FILLER_25_50mm"
    PVC_WATERSTOP_EXTERNAL = "PVC_WATERSTOP_EXTERNAL_RIBBED_HYDROPHILIC_150x8mm"
    PVC_WATERSTOP_INTERNAL_CENTRE_BULB = "PVC_WATERSTOP_INTERNAL_CENTRE_BULB_200x10mm"
    RUBBER_WATERSTOP_EMBEDDED = "RUBBER_WATERSTOP_EMBEDDED_DUMBBELL_EPDM_NR"
    HYDROPHILIC_BENTONITE_SWELLED = "HYDROPHILIC_SWELLED_BENTONITE_PUTTY_TYPE_400PCT_SWELL"
    HYDROPHILIC_SWELLED_TAPE = "HYDROPHILIC_SWELLED_TAPE_PREFORMED_NAIL_ON_SLAB_JOINT"
    COPPER_STOP_WATER_SHEET = "COPPER_STOP_WATER_SHEET_1mm_T_150mm_W_DAM_SEALANT"
    LEAD_WOOL_CAULKING_HISTORIC = "LEAD_WOOL_CAULKING_HISTORIC_BRIDGE_RESTORATION"
    MASTIC_ASPALTE_COMPRESSIBLE = "MASTIC_ASPALTE_COMPRESSIBLE_ARKOAL_TYPE_PAVEMENT"


class WearingCoatGrade(LabeledEnum):
    BC_GRADE_1_MARSHALL_30_6 = "BC_GRADE_1_MARSHALL_30_6_BITUMEN_VG30"
    BC_GRADE_2_MARSHALL_45_75 = "BC_GRADE_2_MARSHALL_45_75_HEAVY_TRAFFIC_MORTH"
    BC_GRADE_3_MARSHALL_60_100 = "BC_GRADE_3_MARSHALL_60_100_VERY_HEAVY_EXPRESSWAY"
    SMA_GRADE_1_STONE_MASTIC = "SMA_GRADE_1_STONE_MASTIC_8MM_NOMINAL"
    SMA_GRADE_2_STONE_MASTIC_13 = "SMA_GRADE_2_STONE_MASTIC_13MM_NOMINAL_MORTH_CL_509"
    SMA_GRADE_3_STONE_MASTIC_16 = "SMA_GRADE_3_STONE_MASTIC_16MM_EXPRESSWAY"
    MS_GRADE_MARSHALL_SURFACE = "MS_GRADE_MARSHALL_SURFACE_DENSE_BITUMINOUS_MACADAM"
    DBM_GRADE_1_DENSE_BITUMINOUS = "DBM_GRADE_1_DENSE_BITUMINOUS_MACADAM_GRADATION_1"
    DBM_GRADE_2_BINDER_COURSE = "DBM_GRADE_2_BINDER_COURSE_19_26mm_MORTH_CL_504"
    OGFC_OPEN_GRADED_FRICTION = "OGFC_OPEN_GRADED_FRICTION_COURSE_13MM_DRAINAGE_LAYER"
    SDBC_SEMI_DENSE_BITUMINOUS = "SDBC_SEMI_DENSE_BITUMINOUS_CONCRETE_10MM"
    PMC_POLYMER_MODIFIED_BITUMEN = "PMC_POLYMER_MODIFIED_BITUMEN_SBS_STYRENE_BUTADIENE"
    CRMB_CRUMB_RUBBER_MODIFIED = "CRMB_CRUMB_RUBBER_MODIFIED_BITUMEN_15PCT_RUBBER_MORTH"
    MULTIGRADE_BITUMEN_MV_70 = "MULTIGRADE_BITUMEN_MV_70_MULTIPLE_VISCOSITY"
    VG10_BITUMEN_VERY_SOFT = "VG10_BITUMEN_VERY_SOFT_CLIMATE_TROPICAL_LOW"
    VG20_BITUMEN_NORMAL = "VG20_BITUMEN_NORMAL_PEN_60_70"
    VG30_BITUMEN_HARD = "VG30_BITUMEN_HARD_PEN_50_60_HIGH_TEMP_CLIMATE"
    VG40_BITUMEN_VERY_HARD = "VG40_BITUMEN_VERY_HARD_PEN_40_50_EXTREME_HEAVY_LOAD"
    WMA_WARM_MIX_ASPALT_FOAMED = "WMA_WARM_MIX_ASPALT_FOAMED_ZEOCLITE_120C_LAY_TEMP"
    MASTIC_ASPALTE_GUSSTYPE = "MASTIC_ASPALTE_GUSSTYPE_FILLED_92_5PCT_AGGREGATE_DENSE"
    AC_ASPALTE_CONCRETE = "AC_ASPALTE_CONCRETE_DENSE_GRADATION_AIR_VOIDS_3_6PCT"
    EPOXY_OVERLAY_RESIN_SYSTEM = "EPOXY_OVERLAY_RESIN_SYSTEM_ANTI_SKID_BRIDGE_DECK"
    PMB_POLYMER_MODIFIED_SBS = "PMB_POLYMER_MODIFIED_BITUMEN_SBS_ELASTOMERIC_ELASTOMER"
    EMA_EPOXY_MODIFIED_ASPALT = "EMA_EPOXY_MODIFIED_ASPALT_CHEMICAL_BRIDGE_WEARING"
    RUBBER_MODIFIED_ASPALT_RMA = "RUBBER_MODIFIED_ASPALT_RMA_SURFACE_DRESSING"


class ConcreteCoverNominalClass(LabeledEnum):
    COVER_20MM_SLIGHT_EXPOSURE = "20mm_NOMINAL_MILD_M1"
    COVER_25MM_MODERATE_M2 = "25mm_NOMINAL_MODERATE_M2_IRC21_CL16_2"
    COVER_30MM_SEVERE_M3 = "30mm_NOMINAL_SEVERE_M3_IRC21_CL16_2"
    COVER_35MM_VERY_SEVERE_M4 = "35mm_NOMINAL_VERY_SEVERE_M4_IRC21"
    COVER_40MM_EXTREME_M5 = "40mm_NOMINAL_EXTREME_M5_IRC21_CL16_2_1"
    COVER_45MM_MARINE_SPLASH = "45mm_NOMINAL_MARINE_SPLASH_ZONE"
    COVER_50MM_SUBMERGED_OR_SOIL = "50mm_NOMINAL_SUBMERGED_OR_SOIL_CONTACT"
    COVER_55MM_FOUNDRY_SAND_AGG = "55mm_NOMINAL_FOUNDRY_SAND_AGG_M2_M3"
    COVER_60MM_HIGH_CHLORIDE_SULPHATE = "60mm_NOMINAL_HIGH_CHLORIDE_SULPHATE_ENV"
    COVER_75MM_EXTREME_MARINE_INTERTIDAL = "75mm_NOMINAL_EXTREME_MARINE_INTERTIDAL"


class ConcreteSlumpClass(LabeledEnum):
    SLUMP_0_10_NO_SLUMP = "0_10mm_NO_SLUMP_ROLLER_COMPACTED_NO_FINING"
    SLUMP_10_40_VERY_DRY = "10_40mm_VERY_DRY_ABUTMENT_PIERS_MASS_CONCRETE"
    SLUMP_25_75_LOW_PLASTIC = "25_75mm_LOW_PLASTIC_FOUNDATIONS_RCC_MASS_MORTH_602"
    SLUMP_50_100_MEDIUM = "50_100mm_MEDIUM_PLAIN_RCC_BEAMS_SLIGHTLY_REINFORCED_MORTH_602"
    SLUMP_75_125_HIGH_HEAVY_REINFORCED = (
        "75_125mm_HIGH_HEAVY_REINFORCED_BOX_GIRDERS_PIERS_MORTH_CL_602_3"
    )
    SLUMP_100_150_VERY_HIGH_PUMPED = "100_150mm_VERY_HIGH_PUMPED_SEGMENTAL_CONCRETE_SCC_BASE"
    SLUMP_150_225_FLOWING_SCC_BASE = "150_225mm_FLOWING_SCC_BASE_SELF_COMPACTING_BRIDGE_DECK"
    SLUMP_FLOW_CLASS_SF1_SCC = "SCC_SF1_MINI_SLUMP_FLOW_550mm_SELF_COMPACTING_NARROW_SECTIONS"
    SLUMP_FLOW_CLASS_SF2_SCC = "SCC_SF2_SLUMP_FLOW_660mm_SELF_COMPACTING_STANDARD_BRIDGE"
    SLUMP_FLOW_CLASS_SF3_SCC = "SCC_SF3_SLUMP_FLOW_760mm_SELF_COMPACTING_HEAVILY_CONGESTED"


class ConcreteCuringMethodType(LabeledEnum):
    PONDING_WATER_SUBMERGED = "PONDING_WATER_SUBMERGED_FLAT_DECK_SLIGHT_SLOPE"
    WET_SACKS_GUNNY_BAGS = "WET_SACKS_GUNNY_BAGS_MOIST_HORIZONTAL_MEMBER_7DAYS"
    SPRINKLING_MISTING_CONTINUOUS = "SPRINKLING_MISTING_CONTINUOUS_VERTICAL_COLUMNS_PIERS"
    CURING_COMPOUND_MEMBRANE_LIQUID = (
        "CURING_COMPOUND_MEMBRANE_LIQUID_SBR_BASED_IRC_21_MIN_0_2KG_M2"
    )
    CURING_COMPOUND_WHITE_PIGMENTED = "CURING_COMPOUND_WHITE_PIGMENTED_HOT_SUNNY_DECK_SURFACE"
    POLYETHYLENE_SHEET_200_MICRON = "POLYETHYLENE_SHEET_200_MICRON_MIN_BLACK_LDPE_HEAVY_DUTY"
    WET_HESSIAN_BURLAP_OVERLAY = "WET_HESSIAN_BURLAP_OVERLAY_GUNNY_BAG_MOISTURE_7_14_DAYS"
    INSULATED_BLANKET_COLD_WEATHER = (
        "INSULATED_BLANKET_COLD_WEATHER_MIN_5DEG_C_FOR_7DAYS_MORTH_CL_610"
    )
    ELECTRICAL_RESISTANCE_HEATING = "ELECTRICAL_RESISTANCE_HEATING_LOW_TEMPERATURE_CONSTRUCTION"
    STEAM_CURING_PRESTRESSING_BEDS = (
        "STEAM_CURING_PRESTRESSING_BEDS_60DEG_C_95RH_PRECAST_I_BOX_GIRDERS"
    )
    AUTOCLAVE_HIGH_PRESSURE_STEAM = "AUTOCLAVE_HIGH_PRESSURE_STEAM_AAC_ELEMENTS_SPECIAL"
    CURING_WATER_RETAINING_ADMIX = "CURING_WATER_RETAINING_ADMIX_SUPER_ABSORBENT_POLYMERS_INTERNAL"
    FULL_HEIGHT_STAIR_WETTING = (
        "FULL_HEIGHT_STAIR_WETTING_MARINE_STRUCTURE_28_DAYS_SULPHATE_RESISTING"
    )


class ReinforcementBarType(LabeledEnum):
    HYSD_FE415_THERMEX = "HYSD_FE415_THERMEX_DEFORMED_BAR_415MPa"
    HYSD_FE500_TMT = "HYSD_FE500_TMT_THERMO_MECHANICAL_TREATED"
    HYSD_FE500D_DUCTILE = "HYSD_FE500D_DUCTILE_CEQ_ELONGATION_16PCT"
    HYSD_FE500S_SEISMIC = "HYSD_FE500S_SEISMIC_DUCTILE_IRC_112_ELONGATION"
    HYSD_FE550_HIGH_STRENGTH = "HYSD_FE550_HIGH_STRENGTH_TMT"
    HYSD_FE550D_DUCTILE_HIGH = "HYSD_FE550D_DUCTILE_HIGH_STRENGTH"
    HYSD_FE600_ULTRA_STRENGTH = "HYSD_FE600_ULTRA_STRENGTH_TMT_600MPa"
    MILD_STEEL_FE250_PLAIN = "MILD_STEEL_FE250_PLAIN_ROUND_BAR_SMOOTH"
    CRS_COLD_WORKED_STEEL = "CRS_COLD_WORKED_STEEL_TWISTED_DEFORMED"
    SD400_ASTM_G60_EQUIVALENT = "SD400_ASTM_G60_DEFORMED_400MPa"
    SD500_ASTM_G75_EQUIVALENT = "SD500_ASTM_G75_DEFORMED_500MPa"
    STAINLESS_STEEL_REBAR_304 = "STAINLESS_STEEL_REBAR_304_CORROSION_RESISTANT"
    STAINLESS_STEEL_REBAR_2205_DUPLEX = "STAINLESS_STEEL_REBAR_2205_DUPLEX_MARINE"
    GALVANISED_HOT_DIP_ZINC_REBAR = "GALVANISED_HOT_DIP_ZINC_REBAR_85UM_MIN_COAT"
    EPOXY_COATED_FBE_REBAR = "EPOXY_COATED_FBE_REBAR_FUSION_BONDED_POWDER"
    GFRP_GLASS_FIBER_REBAR = "GFRP_GLASS_FIBER_REINFORCED_POLYMER"
    CFRP_CARBON_FIBER_REBAR = "CFRP_CARBON_FIBER_REINFORCED_POLYMER_TENDON"
    BASALT_FIBER_REBAR_BFRP = "BASALT_FIBER_REBAR_BFRP_NON_MAGNETIC"
    PRESTRESSING_STRAND_7_WIRE_12_POINT_7mm = "PRESTRESSING_STRAND_7_WIRE_12_POINT_7mm_GRADE_270"
    PRESTRESSING_WIRE_DRAWN_HIGH_TENSILE = "PRESTRESSING_WIRE_DRAWN_HIGH_TENSILE_5mm_7mm"


class RebarCouplerType(LabeledEnum):
    THREADED_TAPER_THREAD_COUPLER = "THREADED_TAPER_THREAD_COUPLER_NPT_ISO"
    PARALLEL_THREAD_COUPLER_STANDARD = "PARALLEL_THREAD_COUPLER_STANDARD_COARSE_THREAD"
    UPSSET_FORGED_PARALLEL_COUPLER = "UPSSET_FORGED_PARALLEL_COUPLER_BAR_END_SWAGED"
    ROLL_THREADED_COLD_FORGED_COUPLER = "ROLL_THREADED_COLD_FORGED_COUPLER_CONTINUOUS_THREAD"
    MACHINE_THREADED_COUPLER_HIGH_TORQUE = "MACHINE_THREADED_COUPLER_HIGH_TORQUE_SPEC_150PCT"
    GRIP_COUPLER_COMPRESSION_SWAGING = "GRIP_COUPLER_COMPRESSION_SWAGING_HYDRAULIC_DIE"
    WELDABLE_COUPLER_BUTT_WELD = "WELDABLE_COUPLER_BUTT_WELD_SITE_WELDING"
    SLEEVE_COUPLER_MORTAR_GROUT_FILLED = "SLEEVE_COUPLER_MORTAR_GROUT_FILLED_NON_SHRINK_GROUT"
    COUPLER_BOLTED_CLAMP_ON = "COUPLER_BOLTED_CLAMP_ON_TEMPORARY_CONSTRUCTION"
    SHEAR_KEY_COUPLER_PRECAST_SLAB = "SHEAR_KEY_COUPLER_PRECAST_SLAB_DECK_CONNECTOR"
    STANDARD_TRANSITION_COUPLER = "STANDARD_TRANSITION_COUPLER_BAR_SIZE_REDUCER"
    LOCKING_COUPLER_POSITION_HOLDER = "LOCKING_COUPLER_POSITION_HOLDER_END_LOCK_NUT"
    COUPLER_LEFT_HAND_THREAD_SPECIAL = "COUPLER_LEFT_HAND_THREAD_SPECIAL_SKEWED"
    CORROSION_RESISTANT_DUPLEX_COUPLER = "CORROSION_RESISTANT_DUPLEX_COUPLER_MARINE_FOULING"
    INSULATING_COUPLER_GALVANIC_SEPARATION = "INSULATING_COUPLER_GALVANIC_SEPARATION_RAILWAY"


class ConcreteSurfaceFinishClass(LabeledEnum):
    F1_ROUGH_AS_CAST = "F1_ROUGH_AS_CAST_FOUNDATION_FOOTING_FILL"
    F2_ORDINARY_PLANE_FINISH = "F2_ORDINARY_PLANE_FINISH_ABUTMENT_BACK_FACE"
    F3_NORMAL_SMOOTH_FLOAT = "F3_NORMAL_SMOOTH_FLOAT_PIER_SUBSTRUCTURE_VISIBLE"
    F4_GOOD_SMOOTH_TROWELED = "F4_GOOD_SMOOTH_TROWELED_DECK_SOFFIT_SUPERSTRUCTURE"
    F5_VERY_SMOOTH_PRECAST_FACTORY = "F5_VERY_SMOOTH_PRECAST_FACTORY_PSC_GIRDER"
    F6_ULTRA_SMOOTH_OFF_SHUTTER = "F6_ULTRA_SMOOTH_OFF_SHUTTER_ARCHITECTURAL_EXPOSED"
    F7_POLISHED_TERRAZZO_3MM = "F7_POLISHED_TERRAZZO_3MM_STONE_FLOORING"
    F8_EPOXY_COATED_WEAR_RESISTANT = "F8_EPOXY_COATED_WEAR_RESISTANT_INDUSTRIAL"
    F9_PU_POLYURETHANE_FINISH = "F9_PU_POLYURETHANE_FINISH_FOOTPATH"
    F10_ACRYLIC_COATED_FACADE = "F10_ACRYLIC_COATED_FACADE_AESTHETIC_PAINT"
    F11_PS_PLASTER_CEMENT = "F11_PS_PLASTER_CEMENT_MORTAR_12MM_THICK"
    F12_RM_RAIN_COAT_PUTTY = "F12_RM_RAIN_COAT_PUTTY_EXTERNAL_WEATHER_PROOF"
    F13_TEXTURED_STAMPED_CONCRETE = "F13_TEXTURED_STAMPED_CONCRETE_PATTERN"
    F14_EXPOSED_AGGREGATE_PEBBLE = "F14_EXPOSED_AGGREGATE_PEBBLE_WASHED_SURFACE"
    F15_GRIT_BLASTED_NON_SKID = "F15_GRIT_BLASTED_NON_SKID_PEDESTRIAN_FOOTPATH"


class FormworkPanelType(LabeledEnum):
    SHUTTERING_PLYWOOD_BWR_12mm = "SHUTTERING_PLYWOOD_BWR_12mm_BOILING_WATER_RESISTANT"
    SHUTTERING_PLYWOOD_FILM_FACED_18mm = "SHUTTERING_PLYWOOD_FILM_FACED_18mm_FINNISH_BIRCH"
    SHUTTERING_TIMBER_PLANK_50x200 = "SHUTTERING_TIMBER_PLANK_50x200_SAL_TEAK_WOOD"
    STEEL_SHUTTERING_PANEL_1250x500 = "STEEL_SHUTTERING_PANEL_1250x500_3mm_THICK_ANGLE_FRAME"
    STEEL_PLATE_FORMWORK_CUP_LOCK = "STEEL_PLATE_FORMWORK_CUP_LOCK_MODULAR_SYSTEM"
    ALUMINIUM_ALUFORM_SYSTEM = "ALUMINIUM_ALUFORM_SYSTEM_6061_T6_LIGHT_WEIGHT"
    ALUMINIUM_FORMWORK_MIVAN = "ALUMINIUM_FORMWORK_MIVAN_RIBBED_PANEL_SYSTEM"
    PERI_FORMWORK_MODULAR = "PERI_FORMWORK_MODULAR_UP_RIGHT_FRAME_SYSTEM"
    DOKA_FORMWORK_FRAME = "DOKA_FORMWORK_FRAME_SYSTEM_GERMAN_TECH"
    MEVA_FORMWORK_ALU_PANEL = "MEVA_FORMWORK_ALU_PANEL_QUICK_LOCK"
    COFFER_FORMWORK_PLASTIC_MODULAR = "COFFER_FORMWORK_PLASTIC_MODULAR_HOLLOW_BLOCK"
    GFRP_GLASS_FIBER_PANEL_FORMWORK = "GFRP_GLASS_FIBER_PANEL_FORMWORK_CORROSION_RESIST"
    PRECAST_CONCRETE_LOST_FORMWORK = "PRECAST_CONCRETE_LOST_FORMWORK_PERMANENT_RETAIN"
    BRICK_WALL_LOST_FORMWORK = "BRICK_WALL_LOST_FORMWORK_FOUNDATION_PIT"
    FLEXIBLE_PLYWOOD_CURVED_FORMWORK = "FLEXIBLE_PLYWOOD_CURVED_FORMWORK_CURVED_PIER_ARCH"


class FormworkReleaseAgentType(LabeledEnum):
    RELEASE_AGENT_MINERAL_OIL_BASED = "RELEASE_AGENT_MINERAL_OIL_BASED_GENERAL_PURPOSE"
    RELEASE_AGENT_NEAT_ENGINE_OIL = "RELEASE_AGENT_NEAT_ENGINE_OIL_CHEAP_COMMON"
    RELEASE_AGENT_CASTOR_OIL_EMULSION = "RELEASE_AGENT_CASTOR_OIL_EMULSION_SMOOTH_FINISH"
    RELEASE_AGENT_MOLYBDENUM_DISULPHIDE = "RELEASE_AGENT_MOLYBDENUM_DISULPHIDE_STEEL_PANEL"
    RELEASE_AGENT_WAX_BASED_CAR_NAUBA = "RELEASE_AGENT_WAX_BASED_CAR_NAUBA_POLISH"
    RELEASE_AGENT_SILICONE_EMULSION = "RELEASE_AGENT_SILICONE_EMULSION_ARCHITECTURAL_QUALITY"
    RELEASE_AGENT_CHEMICAL_CALCIUM_STEARATE = "RELEASE_AGENT_CHEMICAL_CALCIUM_STEARATE_EMULSION"
    RELEASE_AGENT_POLYVINYL_ALCOHOL_PVA = "RELEASE_AGENT_PVA_POLYVINYL_ALCOHOL_PLYWOOD_SHUTTER"
    RELEASE_AGENT_FATTY_ACID_METHYL_ESTER = (
        "RELEASE_AGENT_FAME_FATTY_ACID_METHYL_ESTER_BIODEGRADABLE"
    )
    RELEASE_AGENT_GRAPHITE_POWDER_OIL = "RELEASE_AGENT_GRAPHITE_POWDER_OIL_DARK_FINISH_STEEL"
    RELEASE_AGENT_LIME_WASH_PASTE = "RELEASE_AGENT_LIME_WASH_PASTE_TRADITIONAL_TIMBER_FORM"
    RELEASE_AGENT_WATER_BASED_ACRYLIC = "RELEASE_AGENT_WATER_BASED_ACRYLIC_NON_STAINING_ALUM"
    RELEASE_AGENT_ANTI_BUBBLE_DEFOAMER = "RELEASE_AGENT_ANTI_BUBBLE_DEFOAMER_AIR_PIN_HOLE"
    RELEASE_AGENT_HIGH_TEMP_EPOXY = "RELEASE_AGENT_HIGH_TEMP_EPOXY_GROUT_PRESTRESS_BED"
    RELEASE_AGENT_BOND_BREAKER_PU = "RELEASE_AGENT_BOND_BREAKER_PU_JOINT_SEPARATOR_PU_MEMBRANE"


class WaterproofingMembraneType(LabeledEnum):
    BITUMEN_FELT_3K_GRADIENT_15KG = "BITUMEN_FELT_3K_GRADIENT_15KG_3_PLY_ROOFING"
    APP_ATACTIC_POLYPROPYLENE_MODIFIED = "APP_ATACTIC_POLYPROPYLENE_MODIFIED_BITUMEN_MEMBRANE_TORCH"
    SBS_STYRENE_BUTADIENE_STYRENE_MODIFIED = (
        "SBS_STYRENE_BUTADIENE_STYRENE_MODIFIED_BITUMEN_MEMBRANE_ELASTOMERIC"
    )
    SELF_ADHESIVE_BITUMEN_MEMBRANE_ALU_FOIL = "SELF_ADHESIVE_BITUMEN_MEMBRANE_ALU_FOIL_1_POINT_5mm"
    EPDM_ETHYLENE_PROPYLENE_DYENE = "EPDM_ETHYLENE_PROPYLENE_DYENE_RUBBER_SHEET_2mm"
    TPO_THERMOPLASTIC_POLYOLEFIN = "TPO_THERMOPLASTIC_POLYOLEFIN_ROOF_SHEET"
    PVC_POLYVINYL_CHLORIDE_MEMBRANE = "PVC_POLYVINYL_CHLORIDE_MEMBRANE_SINGLE_PLY"
    HDPE_HIGH_DENSITY_POLYETHYLENE_GEOMEMBRANE = (
        "HDPE_HIGH_DENSITY_POLYETHYLENE_GEOMEMBRANE_1_POINT_5mm"
    )
    LDPE_LOW_DENSITY_POLYETHYLENE_SHEET = "LDPE_LOW_DENSITY_POLYETHYLENE_SHEET_500_GAUGE"
    PU_POLYURETHANE_LIQUID_COATING = "PU_POLYURETHANE_LIQUID_COATING_ELASTOMERIC_1_POINT_2mm_DFT"
    CRACK_BRIDGING_ACRYLIC_POLYMER = "CRACK_BRIDGING_ACRYLIC_POLYMER_COATING_ELASTIC"
    CEMENTITIOUS_CRYSTALLINE_WATERPROOFING = "CEMENTITIOUS_CRYSTALLINE_WATERPROOFING_PENETRON_XYPEX"
    POLYMER_MODIFIED_CEMENT_SBR_BRUSHABLE = "POLYMER_MODIFIED_CEMENT_SBR_BRUSHABLE_COAT_DRUM"
    POLYSULPHIDE_BASED_JOINT_SEALER_PRIMER = "POLYSULPHIDE_BASED_JOINT_SEALER_PRIMER_TWO_PART"
    INTEGRAL_WATERPROOFING_POWDER_ADMIX = "INTEGRAL_WATERPROOFING_POWDER_ADMIX_CICO_WATERGUARD"


class AntiCorrosionProtectionType(LabeledEnum):
    GALVANISING_HOT_DIP_ZINC_85UM = "GALVANISING_HOT_DIP_ZINC_85UM_MIN_IS_4759"
    GALVANISING_MECHANICAL_ZINC_SHERARDIZE = "GALVANISING_MECHANICAL_ZINC_SHERARDIZE_SMALL_FASTENER"
    ZINC_RICH_PRIMER_EPOXY_92PCT = "ZINC_RICH_PRIMER_EPOXY_92PCT_ZINC_DUST_IN_DRY_FILM"
    SHOP_PRIMER_INORGANIC_ZINC_SILICATE = "SHOP_PRIMER_INORGANIC_ZINC_SILICATE_60um_AUTO_BLAST"
    RED_OXIDE_PRIMER_CONVENTIONAL = "RED_OXIDE_PRIMER_CONVENTIONAL_OIL_BASED"
    CHROME_ZINC_PHOSPHATE_PRIMER = "CHROME_ZINC_PHOSPHATE_PRIMER_CONVERSION_COATING"
    EPOXY_POLYAMIDE_COATING_MID_COAT = "EPOXY_POLYAMIDE_COATING_MID_COAT_300um_DFT"
    POLYURETHANE_PU_TOP_COAT_ALIPHATIC = "POLYURETHANE_PU_TOP_COAT_ALIPHATIC_UV_RESISTANT"
    FLUOROPOLYMER_PVDF_COATING = "FLUOROPOLYMER_PVDF_COATING_KYNAR_500_ARCHITECTURAL"
    POLYSILOXANE_HYBRID_COATING = "POLYSILOXANE_HYBRID_COATING_DUPONT_BAYER_20YR"
    COAL_TAR_EPOXY_COATING_UNDERGROUND = "COAL_TAR_EPOXY_COATING_UNDERGROUND_PIPE_PILE"
    METALLISING_ZINC_SPRAY_100um = "METALLISING_ZINC_SPRAY_100um_ARCH_ARC_BRIDGE_DECK"
    METALLISING_ALUMINIUM_150um = "METALLISING_ALUMINIUM_150um_MARINE_BRIDGE_PIER"
    METALLISING_ZINC_ALUMINIUM_85_15 = (
        "METALLISING_ZINC_ALUMINIUM_85_15_ALLOY_BRIDGE_SUPERSTRUCTURE"
    )
    CATHODIC_PROTECTION_IMPRESSED_CURRENT = (
        "CATHODIC_PROTECTION_IMPRESSED_CURRENT_ICCP_SUBSTRUCTURE_MARINE"
    )
    CATHODIC_PROTECTION_SACRIFICIAL_ANODE = "CATHODIC_PROTECTION_SACRIFICIAL_ANODE_MGO_ALLOY_ZINC"
    CONVERSION_COATING_CHROMATE_III = "CONVERSION_COATING_CHROMATE_III_ROHS_COMPLIANT"
    BLACKENING_PARKERIZING_PHOSPHATE = "BLACKENING_PARKERIZING_PHOSPHATE_TEMPORARY_STORAGE"
    VCI_VAPOUR_CORROSION_INHIBITOR = "VCI_VAPOUR_CORROSION_INHIBITOR_TEMPORARY_STORAGE_TRANSIT"
    RUST_STAINING_INHIBITOR_CALCIUM_NITRITE = "RUST_STAINING_INHIBITOR_CALCIUM_NITRITE_REBAR_ADMIX"


class PaintCoatSystemType(LabeledEnum):
    COAT_SYSTEM_1_ZINC_RICH_EPOXY_PU = "COAT_SYS_1_ZINC_RICH_EPOXY_PU_3COAT_25YR_BRIDGE"
    COAT_SYSTEM_2_EPOXY_POLYAMIDE_PU = "COAT_SYS_2_EPOXY_POLYAMIDE_PU_3COAT_15YR_MODERATE"
    COAT_SYSTEM_3_METALLISED_ZINC_AL_PU = (
        "COAT_SYS_3_METALLISED_ZINC_AL_PU_SEALER_25YR_SEVERE_MARINE"
    )
    COAT_SYSTEM_4_EPOXY_COAL_TAR_UNDERGROUND = "COAT_SYS_4_EPOXY_COAL_TAR_UNDERGROUND_20YR_PILE"
    COAT_SYSTEM_5_ALKYD_ENAMEL_ORDINARY = "COAT_SYS_5_ALKYD_ENAMEL_ORDINARY_7YR_INTERIOR"
    COAT_SYSTEM_6_CHLORINATED_RUBBER = "COAT_SYS_6_CHLORINATED_RUBBER_10YR_MODERATE_WATER_TANK"
    COAT_SYSTEM_7_POLYURETHANE_DIRECT_TO_METAL = "COAT_SYS_7_PU_DTM_DIRECT_TO_METAL_10YR_SPEED"
    COAT_SYSTEM_8_EPOXY_SPLASH_ZONE = "COAT_SYS_8_EPOXY_SPLASH_ZONE_ABRASION_RESIST_15YR"
    COAT_SYSTEM_9_POLYSILOXANE_HIGH_BUILD = "COAT_SYS_9_POLYSILOXANE_HIGH_BUILD_30YR_LONG_LIFE"
    COAT_SYSTEM_10_PVDF_FLUOROPOLYMER_CURTAIN = (
        "COAT_SYS_10_PVDF_FLUOROPOLYMER_CURTAIN_WALL_25YR_FADE"
    )
    COAT_SYSTEM_11_EPOXY_FLOORING_SELF_LEVEL = "COAT_SYS_11_EPOXY_FLOORING_SELF_LEVEL_3mm"
    COAT_SYSTEM_12_EPOXY_POLYURETHANE_DECK = "COAT_SYS_12_EPOXY_POLYURETHANE_PARKING_DECK"
    COAT_SYSTEM_13_ANTI_FOULING_COPPER_ACRYLIC = (
        "COAT_SYS_13_ANTI_FOULING_COPPER_ACRYLIC_5YR_MARINE_BELT"
    )
    COAT_SYSTEM_14_INTUMESCENT_FIRE_RATED = "COAT_SYS_14_INTUMESCENT_FIRE_RATED_2HR_FIRE_RESIST"
    COAT_SYSTEM_15_ZINC_PHOSPHATE_PRIMER_2PACK = (
        "COAT_SYS_15_ZINC_PHOSPHATE_PRIMER_2PACK_GENERAL_8YR"
    )
    COAT_SYSTEM_16_POWDER_COAT_POLYESTER_TGIC = (
        "COAT_SYS_16_POWDER_COAT_POLYESTER_TGIC_ALUMINIUM_10YR"
    )
    COAT_SYSTEM_17_EPOXY_FUSION_BONDED_PIPE = "COAT_SYS_17_EPOXY_FUSION_BONDED_FBE_PIPE_50YR"
    COAT_SYSTEM_18_3LPE_3LAYER_POLYETHYLENE = "COAT_SYS_18_3LPE_3LAYER_POLYETHYLENE_PIPELINE_CROSS"
    COAT_SYSTEM_19_HEAT_SHRINKABLE_SLEEVE = "COAT_SYS_19_HEAT_SHRINKABLE_SLEEVE_PIPE_WELD_FIELD"
    COAT_SYSTEM_20_TEMPORARY_SHOP_PRIMER = "COAT_SYS_20_TEMPORARY_SHOP_PRIMER_REMOVABLE_THREE_MONTH"


# ===========================================================================
# SECTION 9 — DRAWING / CAD / LAYOUT STANDARDS (IRC:SP:55-2019)
# ===========================================================================


class LayerGroup(LabeledEnum):
    LAYER_CENTRELINES_CL = "LAYER_CL_CENTRELINES_CHAINAGE_DASHED"
    LAYER_ROADWAY_OUTLINE = "LAYER_ROADWAY_OUTLINE_CARRIAGEWAY_LIMITS"
    LAYER_DECK_STRUCTURE = "LAYER_DECK_STRUCTURE_SUPERSTRUCTURE_TOP_SURFACE"
    LAYER_DECK_REINFORCEMENT = "LAYER_DECK_REINFORCEMENT_STEEL_BARS_DETAIL"
    LAYER_SUBSTRUCTURE_PIER = "LAYER_SUBSTRUCTURE_PIER_CAP_SHAFT_COLUMN"
    LAYER_SUBSTRUCTURE_ABUTMENT = "LAYER_SUBSTRUCTURE_ABUTMENT_WALL_WING_BACK_WALL"
    LAYER_FOUNDATION_PILE_GROUP = "LAYER_FOUNDATION_PILE_GROUP_CAPS_PILES"
    LAYER_FOUNDATION_WELL_CAISSON = "LAYER_FOUNDATION_WELL_CAISSON_STEINING_CUTTING_EDGE"
    LAYER_FOUNDATION_OPEN_CUT = "LAYER_FOUNDATION_OPEN_CUT_FOOTING_STEPPED"
    LAYER_FOUNDATION_RAFT_MAT = "LAYER_FOUNDATION_RAFT_MAT_SLAB_PLATE"
    LAYER_BEARING_PADS_SCHEDULE = "LAYER_BEARING_PADS_SCHEDULE_ELASTOMERIC_POT_SPHERICAL"
    LAYER_EXPANSION_JOINT_DETAIL = "LAYER_EXPANSION_JOINT_DETAIL_MODULAR_FINGER_STRIP_SEAL"
    LAYER_DIMENSIONS_CHAINAGE = "LAYER_DIMENSIONS_CHAINAGE_RADIAL_SPACING_LEVEL_DIM"
    LAYER_LEVELS_CONTOUR_RL = "LAYER_LEVELS_CONTOUR_RL_GROUND_ROAD_FSL_HFL_LWL"
    LAYER_HATCHING_MATERIAL = "LAYER_HATCHING_MATERIAL_CONCRETE_EARTH_SAND_STONE"
    LAYER_HATCHING_REINFORCED_CONCRETE = "LAYER_HATCHING_RC_CONCRETE_STIPPLING_PLUS_BARS"
    LAYER_HATCHING_EARTH_FILL = "LAYER_HATCHING_EARTH_FILL_EMBANKMENT_SLOPE_FILL_HATCHES"
    LAYER_ANNOTATION_TEXT_NOTES = "LAYER_ANNOTATION_TEXT_NOTES_GENERAL_DESCRIPTIVE"
    LAYER_ANNOTATION_KEY_LEGEND = "LAYER_ANNOTATION_KEY_LEGEND_BAR_MARK_SCHEDULE"
    LAYER_ANNOTATION_DRAWING_NO = "LAYER_ANNOTATION_DRAWING_NO_TITLE_REV_TAG_SCALE"
    LAYER_HYDRAULICS_FLOW = "LAYER_HYDRAULICS_FLOW_VECTORS_WATER_LEVEL_SCOUR"
    LAYER_HYDRAULICS_BOUNDARY = "LAYER_HYDRAULICS_BOUNDARY_GUIDE_BANK_GROYNE_SPUR"
    LAYER_TOPOGRAPHY_SURVEY = "LAYER_TOPOGRAPHY_SURVEY_GROUND_CONTOUR_TRIANGULATED"
    LAYER_TREE_VEGETATION_SIGNS = "LAYER_TREE_VEGETATION_SIGNS_APPROACH_ROAD_FURNITURE"
    LAYER_TABLE_BILL_OF_QUANTITIES = (
        "LAYER_TABLE_BILL_OF_QUANTITIES_ITEM_DESCRIPTION_UNIT_RATE_AMOUNT"
    )
    LAYER_TABLE_BAR_BENDING_BBS = (
        "LAYER_TABLE_BAR_BENDING_SCHEDULE_BAR_MARK_SIZE_LENGTH_COUNT_WEIGHT"
    )
    LAYER_TABLE_BEARING_SCHEDULE = "LAYER_TABLE_BEARING_SCHEDULE_LOC_PAD_SIZE_LOAD_RATING"
    LAYER_TABLE_JOINT_SCHEDULE = "LAYER_TABLE_JOINT_SCHEDULE_EXPANSION_JOINT_TYPE_LOCATION"
    LAYER_TABLE_MATERIAL_TAKEOFF = "LAYER_TABLE_MATERIAL_TAKEOFF_CONCRETE_STEEL_MASONS_WORK_VOLUMES"
    LAYER_TITLE_BLOCK_BORDER = "LAYER_TITLE_BLOCK_BORDER_FRAME_REVISION_LOGO"
    LAYER_TITLE_BLOCK_REVISIONS = "LAYER_TITLE_BLOCK_REVISIONS_HISTORY_LIST_APPROVAL"
    LAYER_NORTH_ARROW_SCALE_BAR = "LAYER_NORTH_ARROW_SCALE_BAR_GRAPHIC_SCALE_REFERENCE"
    LAYER_REFERENCE_XREF_UNDERLAY = "LAYER_REFERENCE_XREF_UNDERLAY_EXISTING_SURVEY_GOOGLE_BASEMAP"
    LAYER_CONSTRUCTION_STAGING = "LAYER_CONSTRUCTION_STAGING_SEQUENCE_PHASES_ERECTION"
    LAYER_FORM_WORK_SHORING = "LAYER_FORM_WORK_SHORING_SCAFFOLD_PROPPING_TEMPORARY"
    LAYER_TEMPORARY_WORKS_COFFERDAM = "LAYER_TEMPORARY_WORKS_COFFERDAM_SHEET_PILE_BRACING"
    LAYER_HIDDEN_DASHED_LINES = "LAYER_HIDDEN_DASHED_LINES_OBSCURED_DETAILS_BEHIND"
    LAYER_CENTRE_LINE_MARKER_NON_PRINT = "LAYER_CENTRE_LINE_MARKER_NON_PRINT_CONSTRUCTION_HELPER"
    LAYER_GRID_LINES_NON_PRINT = "LAYER_GRID_LINES_NON_PRINT_MODULAR_COORDINATES"
    LAYER_DEFPOINTS = "LAYER_DEFPOINTS_AUTOCAD_DIMENSION_DEFINITION_POINTS"


class LineWeightCode(LabeledEnum):
    LW_0_POINT_09mm_EXTREMELY_FINE = "LW_0_09mm_EXTRA_FINE_HIDDEN_DETAIL_MINOR"
    LW_0_POINT_13mm_VERY_FINE = "LW_0_13mm_VERY_FINE_HATCHING_TEXT_MINOR_DIM"
    LW_0_POINT_18mm_FINE = "LW_0_18mm_FINE_DIMENSION_LINES_EXTENSION"
    LW_0_POINT_25mm_NORMAL = "LW_0_25mm_NORMAL_HIDDEN_LINES_SECONDARY_OBJECTS"
    LW_0_POINT_35mm_MEDIUM = "LW_0_35mm_MEDIUM_VISIBLE_OBJECT_LINES_GENERAL"
    LW_0_POINT_50mm_THICK = "LW_0_50mm_THICK_MAIN_STRUCTURAL_OUTLINE"
    LW_0_POINT_70mm_VERY_THICK = "LW_0_70mm_VERY_THICK_MAJOR_SECTION_CUT"
    LW_1_POINT_00mm_EXTRA_THICK = "LW_1_00mm_EXTRA_THICK_BORDER_TITLE_BLOCK_FRAME"
    LW_1_POINT_40mm_ULTRA_THICK = "LW_1_40mm_ULTRA_THICK_PRIMARY_STRUCTURAL_CUT"
    LW_2_POINT_00mm_MAXIMUM = "LW_2_00mm_MAXIMUM_MASTER_PLOT_BORDER_SHEET"
    LW_DEFAULT_BY_LAYER = "LW_DEFAULT_BY_LAYER_INHERIT_LAYER_STANDARD"
    LW_DEFAULT_BY_BLOCK = "LW_DEFAULT_BY_BLOCK_INHERIT_BLOCK_REFERENCE"


class HatchPatternCode(LabeledEnum):
    HATCH_SOLID_FILLED = "HATCH_SOLID_FILLED_BLACK_OCCUPIED_CLOSED_AREA"
    HATCH_ANSI31_IRON_STEEL_METAL = "HATCH_ANSI31_IRON_STEEL_METAL_45DEG_LINES"
    HATCH_ANSI32_BRASS_COPPER = "HATCH_ANSI32_BRASS_COPPER_DUAL_45_PLUS_90"
    HATCH_ANSI33_PLASTIC_RUBBER = "HATCH_ANSI33_PLASTIC_RUBBER_TRIPLE_LINES"
    HATCH_ANSI34_FIRE_BRICK_REFACTORY = "HATCH_ANSI34_FIRE_BRICK_REFACTORY_ZIG_ZAG"
    HATCH_ANSI35_STONE_MASONRY = "HATCH_ANSI35_STONE_MASONRY_RANDOM_BLOCK"
    HATCH_CONCRETE_GENERAL = "HATCH_CONCRETE_GENERAL_DOTS_ANSI31_SAND_GRAVEL"
    HATCH_CONCRETE_REINFORCED = "HATCH_CONCRETE_REINFORCED_RC_DOTS_BARS_STIRRUPS"
    HATCH_PLAIN_CEMENT_CONCRETE_PCC = "HATCH_PCC_PLAIN_CEMENT_SMALL_DOTS_EVENLY"
    HATCH_EARTH_EMBANKMENT_FILL = "HATCH_EARTH_EMBANKMENT_FILL_SYMBOL_SLOPE_UPSIDE_DOWN_V"
    HATCH_SAND_LOOSE = "HATCH_SAND_LOOSE_DOTS_SMALL_VARYING_SIZE"
    HATCH_GRAVEL_COARSE = "HATCH_GRAVEL_COARSE_CIRCLES_DOTS_GRANULAR"
    HATCH_SILT_SMOOTH_FINE = "HATCH_SILT_SMOOTH_FINE_TIGHT_DASH_PATTERN"
    HATCH_CLAY_PLASTIC = "HATCH_CLAY_PLASTIC_HORIZONTAL_SHORT_LINES"
    HATCH_ROCK_BEDROCK = "HATCH_ROCK_BEDROCK_IRREGULAR_POLYGONAL_SHAPES"
    HATCH_WATER_LIQUID = "HATCH_WATER_LIQUID_HORIZONTAL_WAVY_LINES_3"
    HATCH_GRASS_TURF_SURFACE = "HATCH_GRASS_TURF_SURFACE_Tufted_BLADES_UPSIDE"
    HATCH_BRICKWORK_STRETCHER = "HATCH_BRICKWORK_STRETCHER_BOND_STANDARD_MORTH_CL_1201"
    HATCH_BRICKWORK_ENGLISH_BOND = "HATCH_BRICKWORK_ENGLISH_BOND_ALTERNATE_COURSES"
    HATCH_BLOCKWORK_CEMENT_CONCRETE = "HATCH_BLOCKWORK_CEMENT_CONCRETE_BLOCKS_400x200"
    HATCH_STONE_RUBBLE_MASONRY = "HATCH_STONE_RUBBLE_MASONRY_UNCOURSED_RANDOM"
    HATCH_STONE_ASHLAR_MASONRY = "HATCH_STONE_ASHLAR_MASONRY_COURSED_DRESSED_JOINTS"
    HATCH_WOOD_GRAIN_PARALLEL = "HATCH_WOOD_GRAIN_PARALLEL_LINES_CLOSE_SPACING"
    HATCH_WOOD_CROSS_GRAIN = "HATCH_WOOD_CROSS_GRAIN_END_VIEW_CONCENTRIC_RING"
    HATCH_ALUMINIUM_LIGHT_METAL = "HATCH_ALUMINIUM_LIGHT_METAL_DIAGONAL_LIGHT_TONE"
    HATCH_GLASS_TRANSPARENT = "HATCH_GLASS_TRANSPARENT_THIN_DIAGONAL_BROKEN_LINES"
    HATCH_INSULATION_MATERIAL = "HATCH_INSULATION_MATERIAL_BATTEN_ZIG_ZAG_DOUBLE"
    HATCH_BITUMEN_ASPHALT_WATERPROOF = "HATCH_BITUMEN_ASPHALT_WATERPROOF_BLACK_SOLID_STRIPE"
    HATCH_PITCHED_ROOF_TILES = "HATCH_PITCHED_ROOF_TILES_INTERLOCKING_WAVY"
    HATCH_SHEET_PILE_INTERLOCK = "HATCH_SHEET_PILE_INTERLOCK_LARSSEN_U_PROFILE_CROSS_SECTION"
    HATCH_STEEL_SECTION_I_BEAM = "HATCH_STEEL_SECTION_I_BEAM_WIDE_FLANGE_PARALLEL_SOLID_FILLED"
    HATCH_GABION_BASKET_WIRE_MESH = "HATCH_GABION_BASKET_WIRE_MESH_GRID_PATTERN_STONES"
    HATCH_GEOTEXTILE_REINFORCING = "HATCH_GEOTEXTILE_REINFORCING_DASH_DOT_PATTERN_SYNTHETIC"
    HATCH_DOTS_ANSI34_CLAY_SOIL = "HATCH_DOTS_ANSI34_CLAY_SOIL_FILL_DENSE_DOT_DENSE"
    HATCH_CROSS_HATCH_90_DEG = "HATCH_CROSS_HATCH_90_DEG_MASONRY_SQUARE_GRID"
    HATCH_ARROWS_FLOW_DIRECTION = "HATCH_ARROWS_FLOW_DIRECTION_HYDRAULICS_CURRENT"
    HATCH_USER_DEFINED_CUSTOM = "HATCH_USER_DEFINED_CUSTOM_SCALE_LINETYPE_ANGLE"


class FontStyle(LabeledEnum):
    FONT_ISOCPEUR_TECHNICAL = "FONT_ISOCPEUR_TECHNICAL_STROKE_ROMAN_SIMPLEX_ISO"
    FONT_ROMANS_SIMPLEX_ROMAN = "FONT_ROMANS_SIMPLEX_ROMAN_STANDARD_AUTOCAD_LEGACY"
    FONT_ROMAND_DUPLEX_ROMAN = "FONT_ROMAND_DUPLEX_ROMAN_BOLD_STROKE"
    FONT_ROMANC_COMPLEX_ROMAN = "FONT_ROMANC_COMPLEX_ROMAN_SERIF_MULTIPLE_STROKE"
    FONT_ROMANT_TRIPLEX_ROMAN = "FONT_ROMANT_TRIPLEX_ROMAN_THICK_BODY"
    FONT_SCRIPTC_COMPLEX_SCRIPT = "FONT_SCRIPTC_COMPLEX_SCRIPT_HANDWRITING_CURSIVE"
    FONT_SCRIPTS_SIMPLEX_SCRIPT = "FONT_SCRIPTS_SIMPLEX_SCRIPT_LIGHT_CURSIVE"
    FONT_GREEKC_COMPLEX_GREEK = "FONT_GREEKC_COMPLEX_GREEK_MATHEMATICAL_SYMBOLS"
    FONT_ITALICC_COMPLEX_ITALIC = "FONT_ITALICC_COMPLEX_ITALIC_OBLIQUE_ROMAN"
    FONT_ITALICS_SIMPLEX_ITALIC = "FONT_ITALICS_SIMPLEX_ITALIC_LIGHT_OBLIQUE"
    FONT_STANDARD_AUTOCAD_SHX = "FONT_STANDARD_AUTOCAD_SHX_SB_STANDARD_DEFAULT"
    FONT_TXT_GENERAL_PURPOSE = "FONT_TXT_GENERAL_PURPOSE_SHX_FAST_PLOTTING_MONOSPACE"
    FONT_MONOTXT_MONOSPACE_TXT = "FONT_MONOTXT_MONOSPACE_TXT_EQUAL_WIDTH_COLUMNS"
    FONT_ARIAL_TRUE_TYPE = "FONT_ARIAL_TRUE_TYPE_PROPORTIONAL_SANS_SERIF_TTF"
    FONT_TIMES_NEW_ROMAN_TTF = "FONT_TIMES_NEW_ROMAN_TTF_PROPORTIONAL_SERIF_PRINT"
    FONT_CALIBRI_MODERN_SANS = "FONT_CALIBRI_MODERN_SANS_SERIF_MICROSOFT_OFFICE"
    FONT_VERDANA_WIDE_READABLE = "FONT_VERDANA_WIDE_READABLE_SANS_SERIF_SCREEN_DISPLAY"
    FONT_COURIER_NEW_MONO_TTF = "FONT_COURIER_NEW_MONO_TTF_FIXED_WIDTH_CODE_BLOCKS"
    FONT_GEORGIA_SERIF_READABLE = "FONT_GEORGIA_SERIF_READABLE_SCREEN_SMALL_POINT"
    FONT_TAHOMA_VERY_WIDE = "FONT_TAHOMA_VERY_WIDE_SANS_SERIF_UI_COMPACT"
    FONT_HELVETICA_CLASSIC_SWISS = "FONT_HELVETICA_CLASSIC_SWISS_SANS_SERIF_MAC"
    FONT_DEVANAGARI_MANGAL_HINDI = "FONT_DEVANAGARI_MANGAL_HINDI_MARATHI_SANSKRIT"
    FONT_DEVANAGARI_KRUTI_DEV = "FONT_DEVANAGARI_KRUTI_DEV_10_16_HINDI_CLASSIC"
    FONT_TAMIL_BAMINI_TAM_TYPE1 = "FONT_TAMIL_BAMINI_TAM_TYPE1_NON_UNICODE"
    FONT_TAMIL_LATHA_TTF = "FONT_TAMIL_LATHA_TTF_UNICODE_WINDOWS_SYSTEM"
    FONT_TELUGU_GAUTAMI_TTF = "FONT_TELUGU_GAUTAMI_TTF_UNICODE_SYSTEM"
    FONT_KANNADA_TERAFONT = "FONT_KANNADA_TERAFONT_KN_NUDGE_NUDI"
    FONT_MALAYALAM_KARTIKA_TTF = "FONT_MALAYALAM_KARTIKA_TTF_UNICODE"
    FONT_BENGALI_VRIJNDA_TTF = "FONT_BENGALI_VRIJNDA_TTF_UNICODE"
    FONT_GUJARATI_SHRUTI_TTF = "FONT_GUJARATI_SHRUTI_TTF_UNICODE"
    FONT_PUNJABI_GURMUKHI_RAAVI = "FONT_PUNJABI_GURMUKHI_RAAVI_TTF_UNICODE"
    FONT_ORIYA_KALINGA_TTF = "FONT_ORIYA_KALINGA_TTF_UNICODE"
    FONT_URDU_PERSIAN_NASTALEEQ = "FONT_URDU_PERSIAN_NASTALEEQ_CALLIGRAPHIC"


class ArrowStyle(LabeledEnum):
    ARROW_CLOSED_SOLID_FILLED = "ARROW_CLOSED_SOLID_FILLED_TRIANGLE_STANDARD_DIMENSION"
    ARROW_OPEN_UNFILLED_OUTLINE = "ARROW_OPEN_UNFILLED_OUTLINE_HOLLOW_TRIANGLE"
    ARROW_DOT_CIRCLE_FILLED = "ARROW_DOT_CIRCLE_FILLED_SMALL_CIRCLE_DOT"
    ARROW_TICK_ARCHITECTURAL = "ARROW_TICK_ARCHITECTURAL_DASHLASH_45DEGREE_MARK"
    ARROW_NONE_PLAIN_EXTENSION = "ARROW_NONE_PLAIN_EXTENSION_END_NO_MARKER"
    ARROW_OBLIQUE_STROKE = "ARROW_OBLIQUE_STROKE_SHORT_LINE_OBLIQUE_DIM_END"
    ARROW_CLOSED_EMPTY_UNFILLED = "ARROW_CLOSED_EMPTY_UNFILLED_TRIANGLE_BORDER"
    ARROW_DOT_SMALL_MINI = "ARROW_DOT_SMALL_MINI_TINY_CIRCLE_SUBDIVISION"
    ARROW_BOX_SQUARE_FILLED = "ARROW_BOX_SQUARE_FILLED_RECTANGULAR_BLOCK_END"
    ARROW_BOX_OPEN_SQUARE = "ARROW_BOX_OPEN_SQUARE_HOLLOW_RECT_OUTLINE"
    ARROW_DIAMOND_FILLED = "ARROW_DIAMOND_FILLED_RHOMBUS_SOLID_END"
    ARROW_DIAMOND_OPEN = "ARROW_DIAMOND_OPEN_HOLLOW_RHOMBUS_OUTLINE"
    ARROW_INTEGRAL_SUM_BIG = "ARROW_INTEGRAL_SUM_BIG_CLOSED_FILLED_LARGE"
    ARROW_ORIGIN_INDICATOR = "ARROW_ORIGIN_INDICATOR_CIRCLE_CROSS_DATUM_MARK"
    ARROW_DATUM_IDENTIFIER_BOX = "ARROW_DATUM_IDENTIFIER_BOX_TRIANGLE_ON_A_BOX_GD_T"
    ARROW_FEATURE_CONTROL_FRAME = "ARROW_FEATURE_CONTROL_FRAME_GD_T_TOLERANCE_SYMBOL"
    ARROW_LEADER_LINE_ARROW = "ARROW_LEADER_LINE_ARROW_CLOSED_SOLID_ANNOTATION"
    ARROW_BALLOON_TAG_ARROW = "ARROW_BALLOON_TAG_ARROW_CLOSED_SMALL_BUBBLE_NOTE"
    ARROW_BLOOD_LINE_SLASH_MARK = "ARROW_BLOOD_LINE_SLASH_MARK_WELDING_JOINT_END"
    ARROW_ERECTION_PIN_MARK = "ARROW_ERECTION_PIN_MARK_FIELD_WELD_FLAG"


class ScaleDenominatorSet(LabeledEnum):
    SCALE_1_TO_1_FULL_SIZE = "SCALE_1_1_FULL_SIZE_ACTUAL_DETAIL_SHOP_DRAWING"
    SCALE_1_TO_2_HALF_SIZE = "SCALE_1_2_HALF_SIZE_ENLARGED_DETAIL"
    SCALE_1_TO_5_LARGE_DETAIL = "SCALE_1_5_LARGE_DETAIL_REINFORCEMENT_JOINT"
    SCALE_1_TO_10_DETAIL_LAYOUT = "SCALE_1_10_DETAIL_LAYOUT_BEARING_JOINT_DETAIL"
    SCALE_1_TO_20_DETAIL_SECTION = "SCALE_1_20_DETAIL_SECTION_PIER_CROSS_SECTION"
    SCALE_1_TO_25_GENERAL_DETAIL = "SCALE_1_25_GENERAL_DETAIL_TYPICAL_PIER_ABUTMENT"
    SCALE_1_TO_50_HALF_GENERAL = "SCALE_1_50_HALF_GENERAL_CROSS_SECTION_ROAD_DETAIL"
    SCALE_1_TO_100_GENERAL_ARRANGEMENT = "SCALE_1_100_GENERAL_ARRANGEMENT_GA_SINGLE_SPAN"
    SCALE_1_TO_125_GA_MINOR_BRIDGE = "SCALE_1_125_GA_MINOR_BRIDGE_12M_SPAN"
    SCALE_1_TO_150_GA_MAJOR_3SPAN = "SCALE_1_150_GA_MAJOR_3SPAN_3x12M"
    SCALE_1_TO_200_GA_MAJOR_BRIDGE = "SCALE_1_200_GA_MAJOR_BRIDGE_5x20M_LONG_SECTION"
    SCALE_1_TO_250_LONG_SECTION = "SCALE_1_250_LONG_SECTION_MULTI_SPAN_PROFILE"
    SCALE_1_TO_300_LONG_PROFILE_GA = "SCALE_1_300_LONG_PROFILE_GA_VIADUCT_10SPAN"
    SCALE_1_TO_400_VIADUCT_LONG_SECTION = "SCALE_1_400_VIADUCT_LONG_SECTION_20SPAN"
    SCALE_1_TO_500_SITE_PLAN_LOCATION = "SCALE_1_500_SITE_PLAN_LOCATION_BRIDGE_APPROACH"
    SCALE_1_TO_1000_AREA_SITE_MAP = "SCALE_1_1000_AREA_SITE_MAP_ROAD_ALIGNMENT"
    SCALE_1_TO_1250_TOWN_PLANNING = "SCALE_1_1250_TOWN_PLANNING_SECTOR_WIDE"
    SCALE_1_TO_2000_REVENUE_SURVEY = "SCALE_1_2000_REVENUE_SURVEY_GAT_WADA_NUMBER"
    SCALE_1_TO_2500_TOPO_SHEET_1INCH = "SCALE_1_2500_TOPO_SHEET_1INCH_MILE_CADASTRAL"
    SCALE_1_TO_5000_SOI_TOPO_1_50K = "SCALE_1_5000_SOI_TOPO_1_50K_COMPRESSED"
    SCALE_1_TO_10000_REGIONAL_PLAN = "SCALE_1_10000_REGIONAL_PLAN_DISTRICT_LEVEL"
    SCALE_A1_DRAWING_SHEET_DEFAULT_100 = "SCALE_A1_DEFAULT_1_100_GA_SHEET1_PLAN_SHEET2_LS"
    SCALE_A1_DRAWING_DEFAULT_150 = "SCALE_A1_DEFAULT_1_150_SHEET2_LONG_SECTION"
    SCALE_A1_DEFAULT_200_CROSS_SHEET3 = "SCALE_A1_DEFAULT_1_200_CROSS_SHEET3_FOUNDATION_SHEET4"
    SCALE_ARCH_D_24x36_48 = "SCALE_ARCH_D_24x36_1_48_IMPERIAL_FT"
    SCALE_ARCH_E_36x48_96 = "SCALE_ARCH_E_36x48_1_96_IMPERIAL_BIG"
    SCALE_CIVIL_ENGINEER_SCALE = "SCALE_CIVIL_ENGINEER_SCALE_CHAIN_10_20_30_40_50_60"
    SCALE_DETAILER_SCALE_CUSTOM = "SCALE_DETAILER_SCALE_CUSTOM_SITE_CALIBRATED_REFERENCE_BAR"


class LineStyleCode(LabeledEnum):
    LS_CONTINUOUS_SOLID = "LS_CONTINUOUS_SOLID_VISIBLE_OUTLINE_IRC_SP55"
    LS_DASHED_HIDDEN_MEDIUM = "LS_DASHED_HIDDEN_MEDIUM_DASH_6mm_GAP_2mm"
    LS_DASHED_LONG_HIDDEN_COARSE = "LS_DASHED_LONG_HIDDEN_COARSE_DASH_12mm_GAP_3mm"
    LS_DOTTED_HIDDEN_FINE = "LS_DOTTED_HIDDEN_FINE_DOT_1mm_GAP_1mm"
    LS_DASH_DOT_CENTERLINE = "LS_DASH_DOT_CENTERLINE_DASH_10_GAP_2_DOT_1_GAP_2"
    LS_DASH_DOUBLE_DOT_CUTTING_PLANE = "LS_DASH_DOUBLE_DOT_CUTTING_PLANE_LONG_DASH_15mm"
    LS_PHANTOM_ALTERNATE_POSITION = "LS_PHANTOM_ALTERNATE_POSITION_DASH_DOT_DOT"
    LS_DIMENSION_CONTINUOUS_FINE = "LS_DIMENSION_CONTINUOUS_FINE_THIN_DIM_LINE"
    LS_EXTENSION_FINE_CONTINUOUS = "LS_EXTENSION_FINE_CONTINUOUS_THIN_EXTENSION_GAP_1mm"
    LS_LEADER_CONTINUOUS_FINE_ARROW = "LS_LEADER_CONTINUOUS_FINE_ARROW_HEAD_END"
    LS_SECTION_CUT_LINE_BOLD_DASH = "LS_SECTION_CUT_LINE_BOLD_DASH_CROSS_SECTION_PLANE"
    LS_BREAK_LINE_FREE_HAND_WAVY = "LS_BREAK_LINE_FREE_HAND_WAVY_SHORT_BREAK_LIMIT"
    LS_BREAK_LINE_ZIG_ZAG_LONG = "LS_BREAK_LINE_ZIG_ZAG_LONG_BREAK_LINE_SYMBOL"
    LS_PROJECTION_ORDINATE_MULTI_DOT = "LS_PROJECTION_ORDINATE_MULTI_DOT_CHAIN_OFFSET"
    LS_GRID_CONSTRUCTION_DASH_FINE = "LS_GRID_CONSTRUCTION_DASH_FINE_LAYOUT_GUIDELINE"
    LS_PROPERTY_BOUNDARY_DASH_DOT_ALTERNATE = "LS_PROPERTY_BOUNDARY_DASH_DOT_ALTERNATE_SURVEY"
    LS_CONTOUR_LINE_FINE_CONTINUOUS_INDEX = (
        "LS_CONTOUR_LINE_FINE_CONTINUOUS_INDEX_LABELLED_EVERY_5TH"
    )
    LS_HATCH_LINE_THIN_45DEG = "LS_HATCH_LINE_THIN_45DEG_OBLIQUE_MATERIAL_HATCH"
    LS_HYDRO_FLOW_ARROW_DASH = "LS_HYDRO_FLOW_ARROW_DASH_DIRECTIONAL_HYDROLOGY"
    LS_REVISION_CLOUD_WAVY_THICK = "LS_REVISION_CLOUD_WAVY_THICK_REV_MARKER_CHANGE"


class DimensionStyleClass(LabeledEnum):
    DS_CLASS_A_ARCHITECTURAL_1mm = "DS_CLASS_A_ARCHITECTURAL_1mm_ARROWHEAD_CLOSED"
    DS_CLASS_B_STRUCTURAL_2mm = "DS_CLASS_B_STRUCTURAL_2mm_BIG_ARROW_STRUCT_DIM"
    DS_CLASS_C_CIVIL_CHAINAGE_METRES = "DS_CLASS_C_CIVIL_CHAINAGE_METRES_KM_PLUS_CHAIN_FORMAT"
    DS_CLASS_D_LEVELS_BENCHMARK_RL = "DS_CLASS_D_LEVELS_BENCHMARK_RL_ELEVATION_ON_DATUM"
    DS_CLASS_E_ANGULAR_DEGREE_MIN_SEC = "DS_CLASS_E_ANGULAR_DEGREE_MIN_SEC_SKEW_ANGLE"
    DS_CLASS_F_COORDINATE_GRID_EAST_NORTH = "DS_CLASS_F_COORDINATE_GRID_EASTING_NORTHING_SURVEY"
    DS_CLASS_G_RADIAL_DIAMETER_R_DIA = "DS_CLASS_G_RADIAL_DIAMETER_R_DIA_CIRCULAR_PILE_CAP"
    DS_CLASS_H_SECTION_CUT_LABEL_STATION = "DS_CLASS_H_SECTION_CUT_LABEL_STATION_SECTIONAL_DRAWING"
    DS_CLASS_I_REBAR_BAR_MARK_DIM = "DS_CLASS_I_REBAR_BAR_MARK_DIM_BBS_SIZE_SPACING"
    DS_CLASS_J_OFFSET_ORDINATE_MULTI = "DS_CLASS_J_OFFSET_ORDINATE_MULTI_BASELINE_DIMENSIONS"
    DS_CLASS_K_CHAMFER_FILLET_RADIUS = "DS_CLASS_K_CHAMFER_FILLET_RADIUS_R3_C3"
    DS_CLASS_L_THICKNESS_T_PLATE = "DS_CLASS_L_THICKNESS_T_PLATE_T12mm_STIFFENER"
    DS_CLASS_M_SLOPE_GRADIENT_1IN_60 = "DS_CLASS_M_SLOPE_GRADIENT_1in_60_VER_HOR_FORMAT"
    DS_CLASS_N_BEARING_DIRECTION_N_120DEG_E = (
        "DS_CLASS_N_BEARING_DIRECTION_N_120deg_E_QUADRANT_SURVEY"
    )
    DS_CLASS_O_AREA_SYMBOL_SQ_M = "DS_CLASS_O_AREA_SYMBOL_SQ_M_HATCH_LABEL"
    DS_CLASS_P_LINEAR_DIM_ROUTE_SURVEY = "DS_CLASS_P_LINEAR_DIM_ROUTE_SURVEY_STATION_INTERVAL"


class ViewTypeClassification(LabeledEnum):
    VT_PLAN_VIEW_TOP_DOWN = "VT_PLAN_VIEW_TOP_DOWN_GENERAL_ARRANGEMENT_SITE"
    VT_ROAD_PLAN_ALIGNMENT = "VT_ROAD_PLAN_ALIGNMENT_CARRIAGEWAY_CENTRELINE_KM"
    VT_FOUNDATION_PLAN = "VT_FOUNDATION_PLAN_PILE_CAP_PILE_GRID_LAYOUT"
    VT_PIER_PLAN_CAP_LAYOUT = "VT_PIER_PLAN_CAP_LAYOUT_PIER_CAP_BEARING_PAD"
    VT_DECK_PLAN_SUPERSTRUCTURE = "VT_DECK_PLAN_SUPERSTRUCTURE_DECK_SLAB_GIRDER_PLAN"
    VT_LONGITUDINAL_SECTION_LS = "VT_LONGITUDINAL_SECTION_LS_ALIGN_THE_CENTRELINE"
    VT_CROSS_SECTION_CS_ROAD = "VT_CROSS_SECTION_CS_ROAD_FORMATION_CARRIAGEWAY"
    VT_CROSS_SECTION_CS_PIER = "VT_CROSS_SECTION_CS_PIER_AT_PILE_CAP_SHAFT_LEVEL"
    VT_CROSS_SECTION_CS_DECK = "VT_CROSS_SECTION_CS_DECK_GIRDER_STIRRUP_RAILING"
    VT_ELEVATION_FRONT_VIEW = "VT_ELEVATION_FRONT_VIEW_SUPERSTRUCTURE_SUB_FACING_TRAFFIC"
    VT_ELEVATION_SIDE_VIEW = "VT_ELEVATION_SIDE_VIEW_PIER_COLUMN_PROFILE"
    VT_SECTIONAL_DETAIL_THROUGH_ABUTMENT = "VT_SECTIONAL_DETAIL_THROUGH_ABUTMENT_WING_RETURN_WALL"
    VT_DETAIL_A_ENLARGED_JOINT = "VT_DETAIL_A_ENLARGED_JOINT_BEARING_PAD_CORNER"
    VT_DETAIL_B_REINFORCEMENT_BAR_SCHEDULE = "VT_DETAIL_B_REINFORCEMENT_BAR_SCHEDULE_BENDING_DETAIL"
    VT_ISOMETRIC_3D_VIEW = "VT_ISOMETRIC_3D_VIEW_PICTORIAL_PRESENTATION"
    VT_EXPLODED_ASSEMBLY_VIEW = "VT_EXPLODED_ASSEMBLY_VIEW_COMPONENT_SEQUENCE_PRESTRESS"
    VT_HYDRAULIC_CROSS_SECTION = "VT_HYDRAULIC_CROSS_SECTION_L_SECTION_SCOUR_BED_LEVEL"
    VT_SEISMIC_DETAIL_ELEVATION = "VT_SEISMIC_DETAIL_ELEVATION_DUCTILE_ZONE_CONFINEMENT"
    VT_CONSTRUCTION_STAGING_VIEW = "VT_CONSTRUCTION_STAGING_VIEW_PHASE_1_2_3_TEMPORARY"
    VT_AS_BUILT_SURVEY_VIEW = "VT_AS_BUILT_SURVEY_VIEW_RED_LINE_MARKUP"


class CrossSectionViewTypeCode(LabeledEnum):
    CS_CODE_A_A_MAJOR_PIER = "CS_A_A_MAJOR_PIER_AT_ABUTMENT_PILE_GROUP"
    CS_CODE_B_B_DECK_SPAN_MID = "CS_B_B_DECK_SPAN_MID_TYPICAL_GIRDER_DRAINAGE"
    CS_CODE_C_C_ABUTMENT_WALL = "CS_C_C_ABUTMENT_WALL_THROUGH_WING_WALL_BACK_WALL"
    CS_CODE_D_CARRIAGEWAY_ROAD = "CS_D_CARRIAGEWAY_ROAD_CROSS_SLOPE_MEDIAN_KERB_FOOTPATH"
    CS_CODE_E_PILE_FOUNDATION = "CS_E_PILE_FOUNDATION_BELOW_PILE_CAP_UNDER_REAM"
    CS_CODE_F_WELL_CAISSON_STEINING = "CS_F_WELL_CAISSON_STEINING_THROUGH_STEINING_WELL_CURB"
    CS_CODE_G_RAFT_FOUNDATION = "CS_G_RAFT_FOUNDATION_PILE_CUM_RAFT_SLAP"
    CS_CODE_H_OPEN_FOUNDATION_STEPPED = "CS_H_OPEN_FOUNDATION_STEPPED_FOOTING_SOIL_STRATUM"
    CS_CODE_I_BOX_CULVERT_SINGLE_CELL = "CS_I_BOX_CULVERT_SINGLE_CELL_RCC_BOX_3x2M"
    CS_CODE_J_BOX_CULVERT_MULTI_CELL = "CS_J_BOX_CULVERT_MULTI_CELL_2_CELL_4_CELL_RUB_RAIL"
    CS_CODE_K_PIPE_CULVERT_CIRCULAR = "CS_K_PIPE_CULVERT_CIRCULAR_HUME_PIPE_1500_NP2"
    CS_CODE_L_SLABCULVERT_ONE_WAY = "CS_L_SLABCULVERT_ONE_WAY_SLAB_WALL_FOOTING"
    CS_CODE_M_SUPER_T_GIRDER_PRESTRESS = "CS_M_SUPER_T_GIRDER_PRESTRESS_C_S_A_GIRDER"
    CS_CODE_N_PSC_I_GIRDER_COMPOSITE = "CS_N_PSC_I_GIRDER_COMPOSITE_DECK_SLAB"
    CS_CODE_O_BOX_GIRDER_SINGLE_CELL = "CS_O_BOX_GIRDER_SINGLE_CELL_CONTINUOUS_FLYOVER"
    CS_CODE_P_TRUSS_BRIDGE_BAILEY = "CS_P_TRUSS_BRIDGE_BAILEY_PANEL_SECTION"
    CS_CODE_Q_ARCH_BRIDGE_SEMI = "CS_Q_ARCH_BRIDGE_SEMI_CIRCULAR_RUBBLED_MASONRY"
    CS_CODE_R_CABLE_STAY_PYLON_DECK = "CS_R_CABLE_STAY_PYLON_DECK_CROSS_SECTION"
    CS_CODE_S_SUSPENSION_HANGER_CABLE = "CS_S_SUSPENSION_HANGER_CABLE_CROSS_SUSPENDER_CLAMP"
    CS_CODE_T_GABION_RETAINING_WALL = "CS_T_GABION_RETAINING_WALL_CAGE_BASKET_LAYER"


class TitleBlockRevisionClass(LabeledEnum):
    TBR_A_DRAWING_NUMBER_GENERAL = "TBR_A_DRAWING_NUMBER_GENERAL_SHEET_NO_TOTAL_SHEET"
    TBR_B_TITLE_NAME_OF_DRAWING = "TBR_B_TITLE_NAME_OF_DRAWING_BRIDGE_AT_KM_12_500"
    TBR_C_PROJECT_NAME_SCHEME = "TBR_C_PROJECT_NAME_SCHEME_NH_44_6LANE_WIDENING"
    TBR_D_CLIENT_EMPLOYER = "TBR_D_CLIENT_EMPLOYER_MORTH_NHAI_PWD_GOVERNMENT"
    TBR_E_CONSULTANT_DESIGNER = "TBR_E_CONSULTANT_DESIGNER_FIRM_NAME_PC_NO"
    TBR_F_CONTRACTOR_BUILDER = "TBR_F_CONTRACTOR_BUILDER_NAME_OF_CONSTRUCTION_FIRM"
    TBR_G_LOCATION_KM_CHAINAGE = "TBR_G_LOCATION_KM_CHAINAGE_STATE_DISTRICT_TALUKA"
    TBR_H_SCALE_DENOMINATOR = "TBR_H_SCALE_DENOMINATOR_NOTED_AS_DRAWN_AS_BUILT"
    TBR_I_PROJECTION_FIRST_THIRD_ANGLE = "TBR_I_PROJECTION_FIRST_THIRD_ANGLE_SYMBOL_METHOD"
    TBR_J_DRAWING_STANDARD_CODE = "TBR_J_DRAWING_STANDARD_CODE_IRC_SP55_IS_14437_SP46"
    TBR_K_UNITS_MM_M_KG_TONNES = "TBR_K_UNITS_MM_M_KG_TONNES_ALL_DIM_IN_MM_UNLESS"
    TBR_L_SHEET_SIZES_A0_A1_A2 = "TBR_L_SHEET_SIZES_A0_A1_A2_DIMENSION_STANDARD"
    TBR_M_REVISION_HISTORY_TABLE = "TBR_M_REVISION_HISTORY_TABLE_REV_NO_DATE_DESCRIPTION_APPROVED"
    TBR_N_APPROVAL_SIGNATURE_DRAWING_CHECKED = (
        "TBR_N_APPROVAL_SIGNATURE_DRAWING_CHECKED_VERIFIED_APPROVED"
    )
    TBR_O_DATE_OF_ISSUE_RELEASE = "TBR_O_DATE_OF_ISSUE_RELEASE_FOR_CONSTRUCTION_IFC"
    TBR_P_PLANNING_COORDINATES_SURVEY = "TBR_P_PLANNING_COORDINATES_SURVEY_WGS84_NEFT_DATUM"
    TBR_Q_DRAWING_CAD_FILE_NAME_DWG = "TBR_Q_DRAWING_CAD_FILE_NAME_DWG_DXF_PDF_BIM_IFC"
    TBR_R_BILL_OF_MATERIALS_BOM = "TBR_R_BILL_OF_MATERIALS_BOM_WEIGHT_QR_CODE_RFID"
    TBR_S_COPYRIGHT_INTELLECTUAL_PROPERTY = (
        "TBR_S_COPYRIGHT_INTELLECTUAL_PROPERTY_CONFIDENTIAL_RESTRICTED"
    )
    TBR_T_KEY_NOTES_REFERENCE_LIST = "TBR_T_KEY_NOTES_REFERENCE_LIST_OF_DRAWINGS_IRC_SP_MORTH_CL"


class PlotterPaperClass(LabeledEnum):
    PLOT_PAPER_A0_SHEET_841x1189 = "PLOT_A0_841x1189_ISO_216_LARGE_FORMAT"
    PLOT_PAPER_A1_SHEET_594x841 = "PLOT_A1_594x841_ISO_216_STANDARD_GA"
    PLOT_PAPER_A2_SHEET_420x594 = "PLOT_A2_420x594_ISO_216_DETAIL_SHEET"
    PLOT_PAPER_A3_SHEET_297x420 = "PLOT_A3_297x420_ISO_216_SHOP_DETAIL"
    PLOT_PAPER_A4_SHEET_210x297 = "PLOT_A4_210x297_ISO_216_DOCUMENT_REPORT"
    PLOT_PAPER_ARCH_C_18x24_INCH = "PLOT_ARCH_C_18x24IN_IMPERIAL_457x610"
    PLOT_PAPER_ARCH_D_24x36_INCH = "PLOT_ARCH_D_24x36IN_IMPERIAL_610x914_COMMON_US"
    PLOT_PAPER_ARCH_E_36x48_INCH = "PLOT_ARCH_E_36x48IN_IMPERIAL_914x1219_LARGE"
    PLOT_PAPER_ARCH_E1_30x42_INCH = "PLOT_ARCH_E1_30x42IN_IMPERIAL_HALF_SIZE_E"
    PLOT_PAPER_ROLL_WIDTH_841mm_A0 = "PLOT_ROLL_WIDTH_841mm_A0_PLOTTER_ROLL"
    PLOT_PAPER_ROLL_WIDTH_914mm_36IN = "PLOT_ROLL_WIDTH_914mm_36IN_PLOTTER_ROLL"
    PLOT_PAPER_BOND_80GSM_UNCOATED = "PLOT_PAPER_BOND_80GSM_UNCOATED_GENERAL_PURPOSE"
    PLOT_PAPER_BOND_90GSM_BRIGHT = "PLOT_PAPER_BOND_90GSM_BRIGHT_WHITE_PLOTTING"
    PLOT_PAPER_COATED_MATTE_120GSM = "PLOT_PAPER_COATED_MATTE_120GSM_PRESENTATION_COLOUR"
    PLOT_PAPER_COATED_GLOSSY_160GSM = "PLOT_PAPER_COATED_GLOSSY_160GSM_REPORT_PRINT"
    PLOT_PAPER_ARCHIVAL_ACID_FREE_MYLAR = "PLOT_PAPER_ARCHIVAL_ACID_FREE_MYLAR_DURABLE"
    PLOT_PAPER_VELLUM_TRANSLUCENT = "PLOT_PAPER_VELLUM_TRANSLUCENT_DIAZO_BLUEPRINT"
    PLOT_PAPER_PHOTO_QUALITY_240GSM = "PLOT_PAPER_PHOTO_QUALITY_240GSM_INKJET_COLOUR"
    PLOT_PAPER_RECYCLED_ECO = "PLOT_PAPER_RECYCLED_ECO_FRIENDLY_70GSM"
    PLOT_PAPER_MYLAR_FILM_4MIL_POLYESTER = "PLOT_PAPER_MYLAR_FILM_4MIL_POLYESTER_ARCHIVE_PERMANENT"


# ===========================================================================
# SECTION 10 — LOAD / SEISMIC / WIND / TEMPERATURE / COMBINATIONS
# ===========================================================================


class SeismicImportanceFactor(LabeledEnum):
    ZONE_II_ORDINARY_IMPORTANCE_I_0_POINT_75 = "ZONE_II_ORDINARY_I_0_75_MINOR_BRIDGE_CULVERT"
    ZONE_III_ORDINARY_IMPORTANCE_I_1_POINT_00 = "ZONE_III_ORDINARY_I_1_00_GENERAL_PURPOSE_BRIDGE"
    ZONE_IV_ORDINARY_IMPORTANCE_I_1_POINT_00 = "ZONE_IV_ORDINARY_I_1_00_GENERAL_PURPOSE"
    ZONE_V_ORDINARY_IMPORTANCE_I_1_POINT_00 = "ZONE_V_ORDINARY_I_1_00_GENERAL_PURPOSE_SEISMIC"
    IMPORTANT_CORRIDOR_I_1_POINT_20 = "IMPORTANT_CORRIDOR_I_1_20_NH_SH_NHDP_CORRIDOR"
    CRITICAL_LIFELINE_I_1_POINT_50 = "CRITICAL_LIFELINE_I_1_50_HOSPITAL_ROUTE_POWER_CROSSING"
    STRATEGIC_DEFENCE_BORDER_I_2_POINT_00 = "STRATEGIC_DEFENCE_I_2_00_BORDER_ROAD_BRO_STRATEGIC"
    URBAN_METRO_FLYOVER_I_1_POINT_30 = "URBAN_METRO_FLYOVER_I_1_30_HIGH_TRAFFIC_DENSITY"
    EXPRESSWAY_ACCESS_CONTROL_I_1_POINT_25 = "EXPRESSWAY_ACCESS_CONTROL_I_1_25_NHAI_EXPRESSWAY"
    PEDESTRIAN_FOOT_OVER_I_0_POINT_50 = "PEDESTRIAN_FOOT_OVER_I_0_50_LIGHT_LOADS_FOB"
    CULVERT_MINOR_12M_I_0_POINT_60 = "CULVERT_MINOR_12M_I_0_60_SPAN_LESS_15M"
    ROB_RAILWAY_OVER_I_1_POINT_50 = "ROB_RAILWAY_OVER_I_1_50_RAIL_CORRIDOR_IR"
    RUB_RAILWAY_UNDER_I_1_POINT_50 = "RUB_RAILWAY_UNDER_I_1_50_RAIL_CROSSING_BOX_CULVERT"
    EARTHEN_EMBANKMENT_RETAINING_I_1_POINT_00 = "EARTHEN_EMBANKMENT_RETAINING_I_1_00_WALL_ABUTMENT"
    ISOLATOR_LRB_HDRB_SPECIAL_I_0_POINT_80 = "ISOLATOR_SPECIAL_I_0_80_SEISMIC_BASE_ISOLATED_BRIDGE"


class WindImportanceFactor(LabeledEnum):
    ORDINARY_MINOR_BRIDGE_k1_0_POINT_90 = "ORDINARY_MINOR_BRIDGE_k1_0_90_SPAN_LT_15M_MINOR_CULVERT"
    ORDINARY_GENERAL_BRIDGE_k1_1_POINT_00 = "ORDINARY_GENERAL_BRIDGE_k1_1_00_IS_875_PART3_DEFAULT"
    MAJOR_BRIDGE_k1_1_POINT_05 = "MAJOR_BRIDGE_k1_1_05_TOTAL_LEN_GT_60M"
    VIADUCT_HIGH_LEVEL_k1_1_POINT_10 = (
        "VIADUCT_HIGH_LEVEL_k1_1_10_PIER_HEIGHT_GT_30M_GROUND_CLEARANCE"
    )
    EXPRESSWAY_NATIONAL_CORRIDOR_k1_1_POINT_15 = (
        "EXPRESSWAY_NATIONAL_k1_1_15_ACCESS_CONTROLLED_NHDP"
    )
    ROB_RAILWAY_OVER_k1_1_POINT_20 = "ROB_RAILWAY_OVER_k1_1_20_RAIL_ROUTE_CROSSING"
    URBAN_FLYOVER_INTERCHANGE_k1_1_POINT_15 = (
        "URBAN_FLYOVER_INTERCHANGE_k1_1_15_HIGH_DECK_AERODYNAMIC"
    )
    PEDESTRIAN_FOOT_OVER_k1_0_POINT_85 = "PEDESTRIAN_FOOT_OVER_k1_0_85_LIGHTWEIGHT_DECK"
    ARCH_DECK_AERODYNAMIC_STABLE_k1_1_POINT_00 = "ARCH_DECK_AERO_STABLE_k1_1_00"
    CABLE_STAYED_LONG_SPAN_k1_1_POINT_30 = "CABLE_STAYED_LONG_SPAN_k1_1_30_DYNAMIC_GUST_FLICKER"
    SUSPENSION_BRIDGE_FOIL_DECK_k1_1_POINT_40 = (
        "SUSPENSION_BRIDGE_FOIL_DECK_k1_1_40_AEROELASTIC_FLUTTER_CHECK"
    )
    COASTAL_TIDAL_ZONE_k1_1_POINT_20 = "COASTAL_TIDAL_ZONE_k1_1_20_CYCLONE_PRONE_50KM_COASTLINE"
    CYCLONE_PRONE_SUNDERBAN_k1_1_POINT_35 = "CYCLONE_PRONE_SUNDERBAN_k1_1_35_EAST_COAST_TROPICAL"
    HIMALAYAN_WINDY_PASS_k1_1_POINT_25 = "HIMALAYAN_WINDY_PASS_k1_1_25_LEH_NATHULA_LAHAUL"
    WIND_TUNNEL_TESTED_VERIFIED_k1_0_POINT_95 = "WIND_TUNNEL_TESTED_k1_0_95_REDUCED_VERIFIED_AERO"


class WindSpeedBasic_ms(UnitHaverEnum):
    VB_33_ms_ZONE_1 = ("VB_33_ms_ZONE_1", "m/s")
    VB_39_ms_ZONE_2 = ("VB_39_ms_ZONE_2", "m/s")
    VB_44_ms_ZONE_3 = ("VB_44_ms_ZONE_3", "m/s")
    VB_47_ms_ZONE_4 = ("VB_47_ms_ZONE_4", "m/s")
    VB_50_ms_ZONE_5 = ("VB_50_ms_ZONE_5", "m/s")
    VB_55_ms_ZONE_6_COASTAL = ("VB_55_ms_ZONE_6_COASTAL", "m/s")
    VB_42_ms_RISK_CATEGORY_III_50YR = ("VB_42_ms_RISK_CAT_III_50YR_RETURN", "m/s")
    VB_48_ms_RISK_CATEGORY_IV_100YR = ("VB_48_ms_RISK_CAT_IV_100YR_RETURN", "m/s")
    VB_52_ms_RISK_CATEGORY_V_500YR = ("VB_52_ms_RISK_CAT_V_500YR_CRITICAL", "m/s")
    VB_36_ms_SPECIAL_ZONE_DELHI = ("VB_36_ms_ZONE_DELHI_NCR_IS875", "m/s")
    VB_35_ms_MODERATE_INLAND = ("VB_35_ms_MODERATE_INLAND_MP_CG_UP", "m/s")
    VB_57_ms_CYCLONE_ODISHA_WB = ("VB_57_ms_CYCLONE_ODISHA_WB_EAST", "m/s")
    VB_58_ms_CYCLONE_TN_GULF = ("VB_58_ms_CYCLONE_TN_GULF_MANNAR", "m/s")
    VB_50_ms_KUTCHH_RANN = ("VB_50_ms_KUTCHH_RANN_GREAT_RANN", "m/s")
    VB_45_ms_MAHARASHTRA_COAST = ("VB_45_ms_MAHARASHTRA_COAST_MUMBAI", "m/s")
    VB_46_ms_KARNATAKA_COAST = ("VB_46_ms_KARNATAKA_COAST_MANGALURU", "m/s")
    VB_48_ms_KERALA_COAST = ("VB_48_ms_KERALA_COAST_TRIVANDRUM", "m/s")
    VB_33_ms_DECCAN_PLATEAU = ("VB_33_ms_DECCAN_PLATEAU_TELANGANA_AP", "m/s")


class LoadCombination(LabeledEnum):
    LC01_DL_DEAD_LOAD_ONLY = "LC01_DL_DEAD_LOAD_ONLY_SELF_WEIGHT_SUPERIMPOSED"
    LC02_DL_PLUS_LL_CLASS_A = "LC02_DL_LL_CLASS_A_TRUCK_LIVE_LOAD"
    LC03_DL_PLUS_LL_CLASS_70R = "LC03_DL_LL_CLASS_70R_TRACKED_TRUCK"
    LC04_DL_PLUS_LL_CLASS_AA_TRACKED = "LC04_DL_LL_CLASS_AA_TRACKED_HEAVY_VEHICLE"
    LC05_DL_PLUS_LL_CLASS_AA_WHEELED = "LC05_DL_LL_CLASS_AA_WHEELED_WAGON"
    LC06_DL_PLUS_LL_PLUS_EQ_EARTHQUAKE = "LC06_DL_LL_EQ_SEISMIC_DUCTILITY_IRC_112"
    LC07_DL_PLUS_LL_PLUS_EQ_MINOR = "LC07_DL_LL_EQ_MINOR_REDUCED_PARTIAL_FACTOR"
    LC08_DL_PLUS_WIND_LOAD_W = "LC08_DL_W_WIND_IS_875_PART3_NORMAL_SPEED"
    LC09_DL_PLUS_LL_PLUS_WIND_W = "LC09_DL_LL_W_COMBINED_HIGHWAY"
    LC10_DL_PLUS_TEMP_TEMPERATURE = "LC10_DL_TEMP_TEMPERATURE_UNIFORM_PLUS_GRADIENT"
    LC11_DL_PLUS_LL_PLUS_TEMP_TEMPERATURE = "LC11_DL_LL_TEMP_T_THERMAL_EXPANSION_MOVEMENT"
    LC12_DL_PLUS_SHRINKAGE_CREEP_CONCRETE = "LC12_DL_SHRINKAGE_CREEP_LONG_TERM_EFFECT_PSC"
    LC13_DL_PLUS_LL_PLUS_EQ_PLUS_TEMP = "LC13_DL_LL_EQ_TEMP_COMBINED_SEVERE"
    LC14_DL_PLUS_LL_PLUS_WIND_PLUS_TEMP = "LC14_DL_LL_W_TEMP_ALL_CLIMATIC_LIVE"
    LC15_DL_PLUS_EROSION_SCOUR_FLOOD = "LC15_DL_EROSION_SCOUR_FLOOD_PIER_STABILITY_AGAINST_SCOUR"
    LC16_DL_PLUS_BRAKE_FORCE_TRACTION = "LC16_DL_BRAKE_FORCE_TRACTION_LONGITUDINAL_LL_FACTOR"
    LC17_DL_PLUS_CENTRIFUGAL_FORCE = "LC17_DL_CENTRIFUGAL_FORCE_HORIZONTAL_CURVE_RADIUS_R"
    LC18_DL_PLUS_EARTH_PRESSURE = "LC18_DL_EARTH_PRESSURE_KA_KP_AT_REST_ABUTMENT_WALL"
    LC19_DL_PLUS_WATER_PRESSURE_BUOYANCY = (
        "LC19_DL_WATER_PRESSURE_BUOYANCY_FOUNDATION_FREEBOARD_HFL"
    )
    LC20_DL_PLUS_LL_PLUS_ICE_LOAD = "LC20_DL_LL_ICE_LOAD_HIMALAYAN_RIVER_ZANSKAR_SIND"
    LC21_DL_PLUS_LL_PLUS_RAILWAY_LOAD = "LC21_DL_LL_RAILWAY_LOAD_RDSO_BRIDGE_70R"
    LC22_DL_PLUS_CONSTRUCTION_STAGING_LOAD = (
        "LC22_DL_CONSTRUCTION_STAGING_TEMPORARY_ERECTION_SEQUENCE"
    )
    LC23_DL_PLUS_LL_PLUS_IMPACT_FACTOR = "LC23_DL_LL_IMPACT_FACTOR_DYNAMIC_IRC_6"
    LC24_DL_PLUS_FOOTPATH_PEDESTRIAN_LOAD = "LC24_DL_FOOTPATH_PEDESTRIAN_LOAD_400kg_PER_SQ_M"
    LC25_DL_PLUS_LL_PLUS_WEARING_COAT_SURFACE = (
        "LC25_DL_LL_WEARING_COAT_BC_SMA_SURFACE_LOAD_UNIFORM"
    )
    LC26_DL_PLUS_SEISMIC_IC_DUCTILITY = (
        "LC26_DL_SEISMIC_DUCTILITY_IMPROVEMENT_FACTOR_IR_112_ZONE_FACTOR"
    )
    LC27_DL_PLUS_BLAST_LOAD_DEFENCE = "LC27_DL_BLAST_LOAD_DEFENCE_STRATEGIC_BRIDGE_BORDER"
    LC28_DL_PLUS_AVALANCHE_LOAD_HIMALAYA = "LC28_DL_AVALANCHE_LOAD_HIMALAYA_SNOW_DYNAMIC_IMPACT"
    LC29_DL_PLUS_SHIP_BARGE_COLLISION = "LC29_DL_SHIP_BARGE_COLLISION_NAVIGABLE_RIVER_BRIDGE"
    LC30_DL_PLUS_DEBRIS_FLOW_FLASH_FLOOD = "LC30_DL_DEBRIS_FLOW_FLASH_FLOOD_HILLY_TORRENT"
    LC31_SERVICEABILITY_LIMIT_STATE_LL_ONLY = (
        "LC31_SLS_LL_SERVICEABILITY_DEFLECTION_CRACK_WIDTH_CHECK"
    )
    LC32_FATIGUE_LOAD_CYCLE_200_MILLION = "LC32_FATIGUE_200M_CYCLE_DETAIL_CATEGORY_STEEL_WELD"


class ImpactFactorCoeff(LabeledEnum):
    IF_CLASS_A_0_POINT_08_MINOR = "IF_CLASS_A_0_08_MINOR_SPAN_LT_10M_STD_SIMPLE"
    IF_CLASS_A_0_POINT_10_NORMAL = "IF_CLASS_A_0_10_NORMAL_SPAN_10_30M_DEFAULT_IRC_6"
    IF_CLASS_A_0_POINT_15_LONG_SPAN = "IF_CLASS_A_0_15_LONG_SPAN_GT_60M_FLEXIBLE"
    IF_CLASS_70R_0_POINT_10_STEEL_TRUSS = "IF_CLASS_70R_0_10_STEEL_TRUSS_PSCTRU_BOX"
    IF_CLASS_70RT_TRACKED_0_POINT_25 = "IF_CLASS_70RT_TRACKED_0_25_HEAVY_IMPACT_LOAD"
    IF_CLASS_70RW_WHEELED_0_POINT_20 = "IF_CLASS_70RW_WHEELED_0_20_VEHICLE_WHEELED"
    IF_CLASS_AA_TRACKED_0_POINT_25_CRITICAL = "IF_CLASS_AA_TRACKED_0_25_CRITICAL_MILITARY_LOAD"
    IF_CLASS_AA_WHEELED_0_POINT_15 = "IF_CLASS_AA_WHEELED_0_15_WAGON_8_WHEEL"
    IF_PSC_BOX_GIRDER_0_POINT_05 = "IF_PSC_BOX_GIRDER_0_05_RIGID_DECK_SMOOTH_RIDE"
    IF_SOLID_SLAB_BRIDGE_0_POINT_05 = "IF_SOLID_SLAB_BRIDGE_0_05_MINOR_12M_STIFF_DECK"
    IF_CULVERT_BC_SLABCULVERT_0_POINT_03 = "IF_CULVERT_BC_SLABCULVERT_0_03_RIGID_EARTH_COVERED"
    IF_PIPE_CULVERT_1500_0_POINT_02 = "IF_PIPE_CULVERT_1500_0_02_FLEXIBLE_PIPE_LOW_IMPACT"
    IF_HIGHWAY_FLYOVER_0_POINT_12 = "IF_HIGHWAY_FLYOVER_0_12_RAMP_TERMINAL_JUNCTION"
    IF_ROB_RAILWAY_OVER_0_POINT_30 = "IF_ROB_RAILWAY_OVER_0_30_IR_RDSO_STATIC_PLUS_DYNAMIC_30PCT"
    IF_FOOT_OVER_BRIDGE_0_POINT_05_PED = "IF_FOB_0_05_PEDESTRIAN_JOGGING_IMPACT"
    IF_BAILEY_BRIDGE_0_POINT_20_MILITARY = "IF_BAILEY_BRIDGE_0_20_PANEL_MODULAR_MILITARY"
    IF_METRO_GUIDEWAY_RT0_POINT_15 = "IF_METRO_GUIDEWAY_RT0_15_DYNAMIC_RAIL_CAR"
    IF_PEDESTRIAN_CROWD_0_POINT_10_FOOTPATH = "IF_PEDESTRIAN_CROWD_0_10_FOOTPATH_DYNAMIC"
    IF_DYNAMIC_TESTED_0_POINT_9x_CALC = "IF_DYNAMIC_TESTED_0_9_CALCULATED_VERIFIED_SITE_TEST"
    IF_SEISMIC_DUCTILITY_0_POINT_00_NO_IMPACT = "IF_SEISMIC_0_00_NO_IMPACT_CONCURRENT_EQ"


class TemperatureLoadDeltaT(LabeledEnum):
    DT_UNIFORM_PLUS_15C_HOT_SUMMER = "DT_UNIFORM_PLUS_15C_HOT_SUMMER_MAX_RISE_ABOVE_ERECTION"
    DT_UNIFORM_MINUS_10C_WINTER = "DT_UNIFORM_MINUS_10C_WINTER_FALL_BELOW_ERECTION_TEMP"
    DT_UNIFORM_PLUS_20C_THAR_DESERT = "DT_UNIFORM_PLUS_20C_THAR_DESERT_RJ_55C_DAILY_SWING"
    DT_UNIFORM_MINUS_15C_HIMALAYA = "DT_UNIFORM_MINUS_15C_HIMALAYA_NEGATIVE_MINUS_20C_NIGHT"
    DT_UNIFORM_PLUS_12C_MODERATE_CLIMATE = "DT_UNIFORM_PLUS_12C_MODERATE_CLIMATE_CENTRAL_INDIA"
    DT_UNIFORM_MINUS_8C_COASTAL_MILD = "DT_UNIFORM_MINUS_8C_COASTAL_MILD_KARNATAKA_KERALA"
    DT_GRADIENT_VERTICAL_5C_TOP_BOTTOM_200mm = "DT_GRADIENT_VERTICAL_5C_TOP_BOTTOM_200mm_DECK_THICK"
    DT_GRADIENT_VERTICAL_8C_TOP_BOTTOM_400mm = (
        "DT_GRADIENT_VERTICAL_8C_TOP_BOTTOM_400mm_DEEP_BOX_GIRDER"
    )
    DT_GRADIENT_VERTICAL_10C_HEAVY_SOLAR = "DT_GRADIENT_VERTICAL_10C_HEAVY_SOLAR_NO_OVERCAST_AZURE"
    DT_GRADIENT_HORIZONTAL_4C_SKEW_BRIDGE = "DT_GRADIENT_HORIZONTAL_4C_SKEW_BRIDGE_N_S_SIDE_FACING"
    DT_GRADIENT_TRANSVERSE_3C_WIDE_CARRIAGEWAY = (
        "DT_GRADIENT_TRANSVERSE_3C_WIDE_CARRIAGEWAY_14m_4_LANE"
    )
    DT_DAILY_CYCLIC_PLUS_MINUS_7C = "DT_DAILY_CYCLIC_PLUS_MINUS_7C_SOLAR_NOCTURNAL_RADIATION"
    DT_MONSOON_COOLING_DOWN_6C = "DT_MONSOON_COOLING_DOWN_6C_SUDDEN_RAIN_TEMPERATURE_DROP"
    DT_NIGHT_RADIATION_COOLING_5C = "DT_NIGHT_RADIATION_COOLING_5C_CLEAR_SKY_HEAT_LOSS"
    DT_CONCRETE_HYDRATION_PLUS_25C_POUR = (
        "DT_CONCRETE_HYDRATION_PLUS_25C_POUR_MASS_CONCRETE_DAM_CURE"
    )
    DT_CONSTRUCTION_ERECTION_TOLERANCE_5C = (
        "DT_CONSTRUCTION_ERECTION_TOLERANCE_5C_ASSEMBLY_TEMP_OFFSET"
    )
    DT_FIRE_HEATING_ABNORMAL_500C = "DT_FIRE_HEATING_ABNORMAL_500C_TEMPERATURE_ABNORMAL"
    DT_JOINT_MOVEMENT_RANGE_DT_25C = "DT_JOINT_MOVEMENT_RANGE_DT_25C_EXPANSION_JOINT_MOVEMENT_CALC"
    DT_PRESTRESS_LOSS_TEMP_CHANGE_20C = "DT_PRESTRESS_LOSS_TEMP_CHANGE_20C_CREEP_LOSS_TEMPERATURE"
    DT_BEARING_PAD_ROTATION_DT_15C = "DT_BEARING_PAD_ROTATION_DT_15C_UNEVEN_EXPANSION"


class PrestressLossTypeEnum(LabeledEnum):
    PL_IMMEDIATE_ELASTIC_SHORTENING = "PL_IMMEDIATE_ELASTIC_SHORTENING_PRE_TENSION_TRANSFER"
    PL_FRICTION_WOBBLE_CURVATURE = "PL_FRICTION_WOBBLE_K_CURVATURE_MU_PTENDON_POST_TENSION"
    PL_ANCHORAGE_SEATING_SLIP = "PL_ANCHORAGE_SEATING_SLIP_WEDGE_GRIP_DRAW_IN_6mm"
    PL_RELAXATION_STEEL_STRESS = "PL_RELAXATION_STEEL_STRESS_CLASS_1_NORMAL_CLASS_2_LOW"
    PL_CREEP_OF_CONCRETE_PHI = "PL_CREEP_OF_CONCRETE_PHI_COEFFICIENT_LONG_TERM_DRY"
    PL_SHRINKAGE_OF_CONCRETE_DRYING = "PL_SHRINKAGE_OF_CONCRETE_DRYING_AUTO_GENOUS_EPS_CSH"
    PL_SWELING_OF_CONCRETE_MOIST = "PL_SWELING_OF_CONCRETE_MOIST_AFTER_CURE_EXPANSION"
    PL_BENDING_OF_TENDON_DEV = "PL_BENDING_OF_TENDON_DEV_PRE_STRESS_BEND_LOSS_OVER_SADDLE"
    PL_ELONGATION_MEASURED_CHECK = "PL_ELONGATION_MEASURED_CHECK_JACK_EXTENSION_CALIBRATION"
    PL_STRESSING_SEQUENCE_INDUCED = "PL_STRESSING_SEQUENCE_INDUCED_STAGE_LOSS_INCREMENTAL"
    PL_TEMPERATURE_DIFFERENTIAL_LOSS = "PL_TEMPERATURE_DIFFERENTIAL_LOSS_HOT_WEATHER_STRESS"
    PL_TIME_DEPENDENT_RELAXATION_RHO_1000 = "PL_TIME_DEPENDENT_RELAXATION_RHO_1000H_ISO_15630"
    PL_CONCRETE_MODULAR_RATIO_ALPHA_E = "PL_CONCRETE_MODULAR_RATIO_ALPHA_E_ES_BY_EC"
    PL_DEFLECTION_DUCT_PROFILE_VARIATION = (
        "PL_DEFLECTION_DUCT_PROFILE_VARIATION_AS_BUILT_DUCT_ERROR"
    )
    PL_PRESTRESS_FORCE_LIMIT_TENDON_CAPACITY = (
        "PL_PRESTRESS_FORCE_LIMIT_TENDON_CAPACITY_CHAR_STRENGTH"
    )


class CreepShrinkageFactorClass(LabeledEnum):
    CREEP_PHI_NOTIONAL_1_POINT_5 = "CREEP_PHI_NOTIONAL_1_POINT_5_DRY_INLAND_NORMAL"
    CREEP_PHI_NOTIONAL_2_POINT_0 = "CREEP_PHI_NOTIONAL_2_POINT_0_HUMID_TROPICAL_WET"
    CREEP_PHI_NOTIONAL_3_POINT_0 = "CREEP_PHI_NOTIONAL_3_POINT_0_THIN_MEMBER_DRY_HOT"
    CREEP_PHI_NOTIONAL_4_POINT_0 = "CREEP_PHI_NOTIONAL_4_POINT_0_MASSIVE_SLOW_HARDENING"
    CREEP_COEFFICIENT_FINAL_25YR = "CREEP_COEFFICIENT_FINAL_25YR_LONG_TERM_PREDICTED"
    SHRINKAGE_EPS_CSD_300_MICROSTRAIN = "SHRINKAGE_EPS_CSD_300_MICROSTRAIN_DRYING_20C_50RH"
    SHRINKAGE_EPS_CSD_450_MICROSTRAIN = "SHRINKAGE_EPS_CSD_450_MICROSTRAIN_ARID_DRY_20RH"
    SHRINKAGE_EPS_CSD_600_MICROSTRAIN = "SHRINKAGE_EPS_CSD_600_MICROSTRAIN_THIN_SECTION_EARLY_DRY"
    SHRINKAGE_EPS_CA_100_MICROSTRAIN_AUTO = "SHRINKAGE_EPS_CA_100_MICROSTRAIN_AUTOGENOUS_HIGH_PERF"
    SHRINKAGE_EPS_CA_50_MICROSTRAIN_LOW_HEAT = "SHRINKAGE_EPS_CA_50_MICROSTRAIN_LOW_HEAT_CEMENT"
    CREEP_CORRECTION_HUMIDITY_80PCT = "CREEP_CORRECTION_HUMIDITY_80PCT_REDUCTION_0_POINT_7"
    CREEP_CORRECTION_HUMIDITY_40PCT = "CREEP_CORRECTION_HUMIDITY_40PCT_INCREASE_1_POINT_2"
    CREEP_SIZE_FACTOR_THICK_GT_500MM = "CREEP_SIZE_FACTOR_THICK_GT_500MM_MEMBER_REDUCTION"
    CREEP_SIZE_FACTOR_THIN_LT_100MM = "CREEP_SIZE_FACTOR_THIN_LT_100MM_INCREASE_1_POINT_5"
    AGE_AT_LOADING_3DAY_ADJUSTMENT = "AGE_AT_LOADING_3DAY_ADJUSTMENT_PHI_MULTIPLIER_HIGH"


class FrictionCoeffBearingPadType(LabeledEnum):
    MU_ELASTOMERIC_RUBBER_CONCRETE_0_POINT_30 = (
        "MU_ELASTOMERIC_RUBBER_CONCRETE_0_POINT_30_GRAVITY_SIMPLE"
    )
    MU_ELASTOMERIC_RUBBER_STEEL_0_POINT_25 = "MU_ELASTOMERIC_RUBBER_STEEL_0_POINT_25_STEEL_SURFACE"
    MU_PTFE_TEF_FILLED_ON_SS_304_0_POINT_04 = (
        "MU_PTFE_TEF_FILLED_ON_SS_304_0_POINT_04_LUBRICATED_SLIDING"
    )
    MU_PTFE_ON_SS_DRY_UNLUBRICATED_0_POINT_08 = "MU_PTFE_ON_SS_DRY_UNLUBRICATED_0_POINT_08_UNLUB"
    MU_POT_BEARING_TEF_PTFE_0_POINT_03 = "MU_POT_BEARING_TEF_PTFE_0_POINT_03_ENGINEERED_LUB"
    MU_SPHERICAL_BEARING_STEEL_BRONZE_0_POINT_05 = (
        "MU_SPHERICAL_BEARING_STEEL_BRONZE_0_POINT_05_LINED"
    )
    MU_ROCKER_BEARING_PIN_HINGE_0_POINT_10 = "MU_ROCKER_BEARING_PIN_HINGE_0_POINT_10_PIN_ROTATION"
    MU_KNIFE_EDGE_BEARING_0_POINT_15 = "MU_KNIFE_EDGE_BEARING_0_POINT_15_OLD_GENERATION"
    MU_GUNMETAL_BRONZE_ON_STEEL_0_POINT_12 = "MU_GUNMETAL_BRONZE_ON_STEEL_0_POINT_12_MEDIUM_LOAD"
    MU_STAINLESS_SS304_ON_PTFE_0_POINT_05 = (
        "MU_STAINLESS_SS304_ON_PTFE_0_POINT_05_PTFE_BEARING_SHEET"
    )
    MU_RCC_ON_MASONRY_0_POINT_40 = "MU_RCC_ON_MASONRY_0_POINT_40_ABUTMENT_PLF_STONE"
    MU_PILE_SOIL_INTERFACE_CLAY_0_POINT_35 = "MU_PILE_SOIL_INTERFACE_CLAY_0_POINT_35_SKIN_FRICTION"
    MU_PILE_SOIL_INTERFACE_SAND_0_POINT_45 = (
        "MU_PILE_SOIL_INTERFACE_SAND_0_POINT_45_GRANULAR_LATERAL"
    )
    MU_ABUTMENT_BACK_FILL_SAND_KA_0_POINT_33 = "MU_ABUTMENT_BACK_FILL_SAND_KA_0_POINT_33_COULOMB"
    MU_WHEEL_ON_PAVEMENT_0_POINT_40 = "MU_WHEEL_ON_PAVEMENT_0_POINT_40_TRUCK_BRAKING"


class DampingRatioTypeEnum(LabeledEnum):
    XI_2_PCT_STEEL_BOX_TRUSS = "XI_2_PCT_STEEL_BOX_TRUSS_UNREPAIRED_FRICTION"
    XI_3_PCT_PRESTRESSED_CONCRETE = "XI_3_PCT_PRESTRESSED_CONCRETE_CRACKED_NO_MINIMAL"
    XI_5_PCT_RC_REINFORCED_CONCRETE = "XI_5_PCT_RC_REINFORCED_CONCRETE_CRACKED_DEFAULT_IRC_112"
    XI_7_PCT_RC_DUCTILE_SEISMIC_DETAIL = "XI_7_PCT_RC_DUCTILE_SEISMIC_DETAIL_CONFINED_PLUS_DAMP"
    XI_10_PCT_COMPOSITE_STEEL_RCC_DECK = "XI_10_PCT_COMPOSITE_STEEL_RCC_DECK_INTERFACE_SLIP"
    XI_15_PCT_MASONRY_RUBBLE_STONE = "XI_15_PCT_MASONRY_RUBBLE_STONE_MORTAR_DISIPATION"
    XI_20_PCT_ISOLATED_BEARING_HDR_LRB = "XI_20_PCT_ISOLATED_BEARING_HDR_LRB_HIGH_DAMPING_RUBBER"
    XI_30_PCT_FRICTION_PENDULUM_FP = "XI_30_PCT_FRICTION_PENDULUM_FP_SLIDING_FRICTION"
    XI_25_PCT_LEAD_RUBBER_BEARING_PLUG = "XI_25_PCT_LEAD_RUBBER_BEARING_PLUG_LEAD_YIELD"
    XI_12_PCT_STEEL_DAMPING_WALL_VD = "XI_12_PCT_STEEL_DAMPING_WALL_VD_YIELD_PLATE"
    XI_18_PCT_VISCOUS_FLUID_DAMPER = "XI_18_PCT_VISCOUS_FLUID_DAMPER_VFD_SUPPLEMENT"
    XI_05_PCT_METRO_GUIDEWAY_LIGHT = "XI_05_PCT_METRO_GUIDEWAY_LIGHT_STIFF_WELDED"
    XI_4_PCT_PRECAST_SEGMENTAL = "XI_4_PCT_PRECAST_SEGMENTAL_MINOR_JOINT_FRICTION"
    XI_8_PCT_MASSIVE_FOUNDATION_SOIL = "XI_8_PCT_MASSIVE_FOUNDATION_SOIL_RADIATION_DAMPING"
    XI_22_PCT_TUNED_MASS_DAMPER_TMD = "XI_22_PCT_TMD_TUNED_MASS_DAMPER_AUXILIARY"


class ResponseSpectrumCategory(LabeledEnum):
    RSC_ZONE_II_LOW_SEISMIC_MH_50 = "RSC_ZONE_II_LOW_SEISMIC_MH_50_Z_FACTOR_0_POINT_10"
    RSC_ZONE_III_MODERATE_MH_50 = "RSC_ZONE_III_MODERATE_MH_50_Z_FACTOR_0_POINT_16"
    RSC_ZONE_IV_HIGH_SEISMIC_MH_50 = "RSC_ZONE_IV_HIGH_SEISMIC_MH_50_Z_FACTOR_0_POINT_24"
    RSC_ZONE_V_VERY_HIGH_MH_50 = "RSC_ZONE_V_VERY_HIGH_MH_50_Z_FACTOR_0_POINT_36"
    RSC_ZONE_II_MH_100_DESIGN_EXTENDED = "RSC_ZONE_II_MH_100_EXTENDED_RETURN_PERIOD"
    RSC_ZONE_III_MH_100_DESIGN_EXTENDED = "RSC_ZONE_III_MH_100_EXTENDED_RETURN"
    RSC_ZONE_IV_MH_100_DESIGN_EXTENDED = "RSC_ZONE_IV_MH_100_EXTENDED_RETURN"
    RSC_ZONE_V_MH_100_DESIGN_EXTENDED = "RSC_ZONE_V_MH_100_EXTENDED_RETURN"
    RSC_MCE_MAXIMUM_CONSIDERED_EARTHQUAKE = "RSC_MCE_MAXIMUM_CONSIDERED_EARTHQUAKE_2_POINT_5x_MH_50"
    RSC_SITE_CLASS_A_ROCK_HARD = "RSC_SITE_CLASS_A_ROCK_HARD_SA_BY_G_2_POINT_5"
    RSC_SITE_CLASS_B_MEDIUM_ROCK = "RSC_SITE_CLASS_B_MEDIUM_ROCK_STIFF"
    RSC_SITE_CLASS_C_SOFT_ROCK_DENSE_SOIL = "RSC_SITE_CLASS_C_SOFT_ROCK_DENSE_SAND_GRAVEL"
    RSC_SITE_CLASS_D_STIFF_SOIL = "RSC_SITE_CLASS_D_STIFF_SOIL_MEDIUM_DENSE"
    RSC_SITE_CLASS_E_SOFT_SOIL_HIGH = "RSC_SITE_CLASS_E_SOFT_SOIL_HIGH_COMPRESSIBILITY"
    RSC_SITE_CLASS_F_SPECIAL_LIQ = "RSC_SITE_CLASS_F_SPECIAL_LIQUIFIABLE_PEAT_MUCK"
    RSC_TIME_PERIOD_FIRST_MODE_FUNDAMENTAL = (
        "RSC_TIME_PERIOD_FIRST_MODE_FUNDAMENTAL_T1_0_POINT_09d_BY_SQRT_H"
    )
    RSC_TIME_PERIOD_SECOND_MODE_T2 = "RSC_TIME_PERIOD_SECOND_MODE_T2_TRANSVERSE_1_POINT_25_T1"
    RSC_TIME_PERIOD_THIRD_MODE_T3 = "RSC_TIME_PERIOD_THIRD_MODE_T3_TORSIONAL_0_POINT_7_T1"


class FatigueDetailCategorySteel(LabeledEnum):
    FC_CAT_100_JOINT_FULL_PEN_GROOVE = "FC_CAT_100_JOINT_FULL_PEN_GROOVE_BACKING_BAR_REMOVED"
    FC_CAT_90_TRANSVERSE_FILLET_WELD = "FC_CAT_90_TRANSVERSE_FILLET_WELD_NO_LACK_OF_FUSION"
    FC_CAT_80_CONTINUOUS_INTERMITTENT_WELD = "FC_CAT_80_CONTINUOUS_INTERMITTENT_WELD_CRACK_STARTER"
    FC_CAT_70_LOAD_INDUCED_WELD_TOE = "FC_CAT_70_LOAD_INDUCED_WELD_TOE_AS_WELDED_GROUND"
    FC_CAT_63_STIFFENER_WELD_END_WRAPPED = "FC_CAT_63_STIFFENER_WELD_END_WRAPPED_2X_THICK"
    FC_CAT_50_COPE_HOLE_CORNER_RADIUS = "FC_CAT_50_COPE_HOLE_CORNER_RADIUS_GT_50mm_R"
    FC_CAT_45_WEB_FLANGE_FILLET_ROOT = "FC_CAT_45_WEB_FLANGE_FILLET_ROOT_CRACK_GROWTH"
    FC_CAT_40_MACHINED_HOLD_DOWN_BOLT = "FC_CAT_40_MACHINED_HOLD_DOWN_BOLT_THREAD_STRESS"
    FC_CAT_36_HIGH_Strength_BOLT_SHEAR = "FC_CAT_36_HIGH_STR_BOLT_SHEAR_FRICTION_GRIP_S8T"
    FC_CAT_32_HOLE_PUNCHED_REAMED_STRESS = "FC_CAT_32_HOLE_PUNCHED_REAMED_STRESS_CONC_3_POINT_0"
    FC_CAT_28_PRESTRESS_STRAND_ANCHORAGE = "FC_CAT_28_PRESTRESS_STRAND_ANCHORAGE_WEDGE_ZONE"
    FC_CAT_125_PLATE_BASE_MATERIAL_AS_ROLLED = "FC_CAT_125_PLATE_BASE_MATERIAL_AS_ROLLED_NO_WELD"
    FC_CAT_112_FLAME_CUT_EDGE_PLANNED = "FC_CAT_112_FLAME_CUT_EDGE_PLANNED_SQUARE"
    FC_CAT_140_HOT_ROLLED_I_SECTION_WEB = "FC_CAT_140_HOT_ROLLED_I_SECTION_WEB_FATIGUE_SMOOTH"
    FC_CAT_100_REINFORCED_DETAIL_SR = "FC_CAT_100_REINFORCED_DETAIL_SR_CRACK_ARRESTER"
    FC_CAT_80_DYNAMIC_LOAD_FATIGUE_200M_CYCLE = "FC_CAT_80_DYNAMIC_LOAD_FATIGUE_200M_CYCLE_FLYOVER"


class DuctilityClassLink(LabeledEnum):
    DC_DUCTILITY_CLASS_LOW_LIMIT_STATE = (
        "DC_DUCTILITY_CLASS_LOW_LIMIT_STATE_NON_SEISMIC_IR_112_3POINTDC"
    )
    DC_DUCTILITY_CLASS_MEDIUM_DCM = "DC_DUCTILITY_CLASS_MEDIUM_DCM_IR_112_MU_2_TO_4"
    DC_DUCTILITY_CLASS_HIGH_DCH = "DC_DUCTILITY_CLASS_HIGH_DCH_IR_112_MU_4_TO_6_ZONE_IV_V"
    DC_DUCTILITY_CLASS_VERY_HIGH_DCV = "DC_DUCTILITY_CLASS_VERY_HIGH_DCV_MU_6_TO_8_CRITICAL_BRIDGE"
    DC_CAPACITY_DESIGN_HIERARCHY = "DC_CAPACITY_DESIGN_HIERARCHY_FLEX_BEFORE_SHEAR_GRAVITY"
    DC_PLASTIC_HINGE_ZONE = "DC_PLASTIC_HINGE_ZONE_COLUMN_BEAM_END_ENERGY"
    DC_CONFINEMENT_SPIRAL_TIES_PITCH = "DC_CONFINEMENT_SPIRAL_TIES_PITCH_75MM_MIN_HIGH"
    DC_HOOP_REINFORCEMENT_TRANSVERSE = "DC_HOOP_REINFORCEMENT_TRANSVERSE_135DEG_HOOK_10d_LEG"
    DC_LONGITUDINAL_REBAR_SPLICING_ZONE = "DC_LG_REBAR_SPLICING_ZONE_NOT_IN_PLSTC_HINGE"
    DC_STRONG_COLUMN_WEAK_BEAM_RATIO_1_POINT_2 = "DC_SC_WB_RATIO_1_POINT_2_MIN_IR_112_CAPACITY"
    DC_SLAB_COLUMN_PUNCHING_SHEAR = "DC_SLAB_COLUMN_PUNCHING_SHEAR_REINFORCED_SHEAR_STUDS"
    DC_LATERAL_TORSIONAL_BUCKLING_BRACING = "DC_LATERAL_TORSIONAL_BUCKLING_BRACING_STEEL_I_BEAM"
    DC_SECTION_CLASS_1_PLASTIC_COMPACT = "DC_SECTION_CLASS_1_PLASTIC_COMPACT_EN_1993_DUCTILE"
    DC_SECTION_CLASS_2_COMPACT = "DC_SECTION_CLASS_2_COMPACT_LIMITED_ROTATION"
    DC_SECTION_CLASS_3_SEMICOMPACT_SLENDER = "DC_SECTION_CLASS_3_SEMICOMPACT_NON_PLASTIC"
    DC_SECTION_CLASS_4_SLENDER_LOCAL_BUCKLE = (
        "DC_SECTION_CLASS_4_SLENDER_LOCAL_BUCKLE_EARLY_NON_DUCTILE"
    )


class RetainingWallModeType(LabeledEnum):
    RWM_GRAVITY_PLAIN_CONCRETE_MASONRY = "RWM_GRAVITY_PLAIN_CONCRETE_MASONRY_SELF_WEIGHT_STABLE"
    RWM_CANTILEVER_RCC_T_L_SHAPE = "RWM_CANTILEVER_RCC_T_L_SHAPE_BASE_SLENDER"
    RWM_COUNTERFORT_RETAINING_VERTICAL_STIFFENERS = (
        "RWM_COUNTERFORT_RETAINING_VERTICAL_STIFFENERS_HIGH_GT_6M"
    )
    RWM_BUTTRESS_COUNTERFORT_FRONT = "RWM_BUTTRESS_COUNTERFORT_FRONT_SIDE_HIGH_GT_8M"
    RWM_ANCHORED_BULKHEAD_SHEET_PILE = "RWM_ANCHORED_BULKHEAD_SHEET_PILE_TIE_ROD_ANCHOR"
    RWM_CANTILEVER_SHEET_PILE_COFFERDAM = "RWM_CANTILEVER_SHEET_PILE_COFFERDAM_EMBEDMENT_DEPTH"
    RWM_DIA_PHRAGM_WALL_PANEL = "RWM_DIA_PHRAGM_WALL_PANEL_GROUND_ANCHOR_DEEP_EXCAVATION"
    RWM_SOLDIER_PILE_LAGGING_WOOD = "RWM_SOLDIER_PILE_LAGGING_WOOD_BRACED_EXCAVATION_TEMP"
    RWM_REINFORCED_EARTH_SANDWICH_METAL_STRIP = "RWM_REINFORCED_EARTH_SANDWICH_METAL_STRIP_GEOGRID"
    RWM_MECHANICALLY_STABILISED_EARTH_MSE = "RWM_MSE_MECH_STABILISED_EARTH_METAL_GEOGRID_BACK_FILL"
    RWM_WRAP_FACED_GEOSOFT_FABRIC = "RWM_WRAP_FACED_GEOSOFT_FABRIC_TEMP_ROADSIDE_EMBANKMENT"
    RWM_GABION_BASKET_CAGE_WALL = "RWM_GABION_BASKET_CAGE_WALL_SLOPE_PROTECTION_DRAINAGE"
    RWM_Crib_WOOD_CONCRETE_BIN = "RWM_Crib_WOOD_CONCRETE_BIN_TIMBER_PRECAST"
    RWM_ABUTMENT_WALL_BACK_SPAN_ABUTMENT = "RWM_ABUTMENT_WALL_BACK_SPAN_ABUTMENT_BRIDGE_FOUNDATION"
    RWM_WING_WALL_FLARED_APPROACH = "RWM_WING_WALL_FLARED_APPROACH_EMBANKMENT_TRANSITION_45DEG"
    RWM_RETURN_WALL_PARALLEL_TRAFFIC = "RWM_RETURN_WALL_PARALLEL_TRAFFIC_END_ABUTMENT_90DEG"
    RWM_TOE_WALL_SLOPE_STABILISATION = "RWM_TOE_WALL_SLOPE_STABILISATION_LOW_HILL_SIDE_FILL"
    RWM_CHECK_DAM_HILL_TORRENT_GULLY = "RWM_CHECK_DAM_HILL_TORRENT_GULLY_CONTROL_EROSION_GRADE"


# ===========================================================================
# M0 Legacy enums (ConcreteGrade, SteelGrade, etc. — preserved, sorted after sections 1-10)
# ===========================================================================


class ConcreteGrade(LabeledEnum):
    M15 = "M15"
    M20 = "M20"
    M25 = "M25"
    M30 = "M30"
    M35 = "M35"
    M40 = "M40"
    M45 = "M45"
    M50 = "M50"
    M55 = "M55"
    M60 = "M60"
    M65 = "M65"
    M70 = "M70"
    M80 = "M80"
    M100 = "M100"


class SteelGrade(LabeledEnum):
    Fe250 = "Fe250"
    Fe415 = "Fe415"
    Fe415D = "Fe415D"
    Fe500 = "Fe500"
    Fe500D = "Fe500D"
    Fe500S = "Fe500S"
    Fe550 = "Fe550"
    Fe550D = "Fe550D"
    Fe600 = "Fe600"
    SD400 = "SD400"
    SD500 = "SD500"


class PrestressGrade(LabeledEnum):
    G1570 = "1570_MPa"
    G1720 = "1720_MPa"
    G1770 = "1770_MPa"
    G1860 = "1860_MPa"
    G1960 = "1960_MPa"
    G2060 = "2060_MPa"
    G2100 = "2100_MPa"
    G2350 = "2350_MPa"


class BearingType(LabeledEnum):
    ELASTOMERIC_NEOPRENE = "ELASTOMERIC_NEOPRENE"
    ELASTOMERIC_NATURAL_RUBBER = "ELASTOMERIC_NATURAL_RUBBER"
    ELASTOMERIC_NITRILE = "ELASTOMERIC_NITRILE"
    ELASTOMERIC_POLYURETHANE = "ELASTOMERIC_POLYURETHANE"
    POT_PTFE = "POT_PTFE"
    POT_ELASTOMERIC = "POT_ELASTOMERIC"
    SPHERICAL_PTFE = "SPHERICAL_PTFE"
    SPHERICAL_ROLLER = "SPHERICAL_ROLLER"
    DISC_SPRING = "DISC_SPRING"
    ROCKER_STEEL = "ROCKER_STEEL"
    ROLLER_KNIFE_EDGE = "ROLLER_KNIFE_EDGE"
    ROLLER_BASCOPE = "ROLLER_BASCOPE"
    KNIFE_EDGE = "KNIFE_EDGE"
    GUIDE_BEARING = "GUIDE_BEARING"
    FIXED_BEARING = "FIXED_BEARING"
    FREE_BEARING = "FREE_BEARING"
    COMPOSITE_LAMINATED = "COMPOSITE_LAMINATED"
    HINGE_BEARING = "HINGE_BEARING"
    TENSION_BEARING = "TENSION_BEARING"
    ISOLATOR_LRB = "ISOLATOR_LRB_LEAD_RUBBER"
    ISOLATOR_HDRB = "ISOLATOR_HDRB_HIGH_DAMPING_RUBBER"
    ISOLATOR_FRICTION_PENDULUM = "ISOLATOR_FRICTION_PENDULUM"


class ExpansionJointType(LabeledEnum):
    STRIP_SEAL = "STRIP_SEAL"
    SINGLE_MODULAR = "SINGLE_MODULAR"
    MULTI_MODULAR = "MULTI_MODULAR"
    FINGER_CANTILEVER = "FINGER_CANTILEVER"
    FINGER_SIMPLE_SUPPORTED = "FINGER_SIMPLE_SUPPORTED"
    FINGER_OVERLAPPING = "FINGER_OVERLAPPING"
    ASPHALTIC_PLUG = "ASPHALTIC_PLUG"
    BURIED_CONTINUOUS_DECK = "BURIED_CONTINUOUS_DECK"
    BURIED_SLIDING_PLATE = "BURIED_SLIDING_PLATE"
    SEALANT_JOINT = "SEALANT_JOINT"
    COMPRESSION_SEAL = "COMPRESSION_SEAL"
    PREFORMED_ELASTOMERIC = "PREFORMED_ELASTOMERIC"
    MATSLIP_SLIDING_SURFACE = "MATSLIP_SLIDING_SURFACE"
    SWEDGE_TEE = "SWEDGE_TEE"
    NEOPRENE_WABO = "NEOPRENE_WABO"
    MAURER_SA_AC = "MAURER_SA_AC"
    TENSA_MAURER_MODULAR = "TENSA_MAURER_MODULAR"
    BRITSPAN = "BRITSPAN"
    INTEGRAL_ABUTMENT_NO_JOINT = "INTEGRAL_NO_JOINT"


class DesignCode(LabeledEnum):
    IRC_5_2015 = "IRC:5-2015"
    IRC_6_2017 = "IRC:6-2017"
    IRC_21_2000 = "IRC:21-2000"
    IRC_24_2010 = "IRC:24-2010"
    IRC_SP_55_2019 = "IRC:SP:55-2019"
    IRC_78_2014 = "IRC:78-2014"
    IRC_83_2014 = "IRC:83(Part-II)-2014"
    IRC_87_2018 = "IRC:87-2018"
    IRC_98_2005 = "IRC:98-2005"
    IRC_103_2012 = "IRC:103-2012"
    IRC_112_2020 = "IRC:112-2020"
    IRC_114_2020 = "IRC:114-2020"
    MORTH_5_REV = "MORTH_5_REV"
    MORTH_SPEC = "MORTH_STANDARD_SPEC"
    AASHTO_LRFD_8 = "AASHTO_LRFD_8TH"
    BS_5400 = "BS_5400"
    EN_1991_2 = "EN_1991-2_EUROCODE"
    IS_456_2000 = "IS_456-2000"
    IS_1343_2012 = "IS_1343-2012"
    IS_800_2007 = "IS_800-2007"
    IS_1786_2008 = "IS_1786-2008"
    IS_875_1987 = "IS_875-1987"
    IS_1893_2016 = "IS_1893-2016"
    IS_2062_2011 = "IS_2062-2011"
    IS_10300_2015 = "IS_10300-2015"
    STATE_PWD = "STATE_PWD"
    RDSO = "RDSO_RAILWAY"
    INDIAN_RAILWAYS = "INDIAN_RAILWAYS"


class LoadClass(LabeledEnum):
    CLASS_A = "IRC_CLASS_A"
    CLASS_70R = "IRC_CLASS_70R"
    CLASS_70RT = "IRC_CLASS_70RT_TRACKED"
    CLASS_70RW = "IRC_CLASS_70RW_WHEELED"
    CLASS_AA = "IRC_CLASS_AA"
    CLASS_AAT = "IRC_CLASS_AA_TRACKED"
    CLASS_AAW = "IRC_CLASS_AA_WHEELED"
    CLASS_SPECIAL_VEHICLE = "SPECIAL_VEHICLE"
    CLASS_30R = "CLASS_30R"
    HR_TRAFFIC = "HIGHLY_RESTRICTED_TRAFFIC"
    AASHTO_HL93 = "AASHTO_HL93"
    EN_91_KN = "EN_LOAD_MODEL_91KN"
    ARAI_TRUCK = "ARAI_STANDARD_TRUCK"
    PEDESTRIAN_ONLY = "PEDESTRIAN_ONLY"
    LIGHT_VEHICLE_ONLY = "LIGHT_VEHICLE_ONLY"
    CYCLE_TRACK_ONLY = "CYCLE_TRACK_ONLY"
    SPECIAL_OVERDIMENSION_CONVOY = "ODC_SPECIAL_CONVOY"


class SeismicZone(LabeledEnum):
    ZONE_II = "ZONE_II"
    ZONE_III = "ZONE_III"
    ZONE_IV = "ZONE_IV"
    ZONE_V = "ZONE_V"
    ZONE_0 = "ZONE_0_NON_SEISMIC"


class OutputFormat(LabeledEnum):
    DXF = "DXF"
    DXF_R2000 = "DXF_R2000"
    DXF_R2006 = "DXF_R2006"
    DXF_R2010 = "DXF_R2010"
    DXF_R2013 = "DXF_R2013"
    DXF_R2018 = "DXF_R2018"
    DWG = "DWG"
    PDF = "PDF"
    PDF_A1 = "PDF_A1"
    PDF_A2 = "PDF_A2"
    PDF_A3 = "PDF_A3"
    PDF_A = "PDFA_ARCHIVE"
    PNG = "PNG"
    JPEG = "JPEG"
    TIFF = "TIFF"
    BMP = "BMP"
    SVG = "SVG"
    SVGZ = "SVGZ_COMPRESSED"
    WEBP = "WEBP"
    EPS = "EPS_ENCAPSULATED"
    THREE_JSON = "THREE_JSON"
    GLTF = "GLTF"
    GLB = "GLB"
    STEP_STP = "STEP_STP"
    IFC = "IFC_BUILDINGSMART"
    OBJ = "WAVEFRONT_OBJ"
    STL = "STL"
    XLSX = "XLSX"
    XLSM = "XLSM_MACRO_ENABLED"
    XLS = "XLS_LEGACY"
    ODS = "ODS_OPEN_DOC"
    CSV = "CSV"
    TSV = "TSV"
    JSON = "JSON"
    YAML = "YAML"
    XML = "XML"
    HTML = "HTML"
    DOCX = "DOCX_REPORT"
    RTF = "RTF"
    PARQUET = "PARQUET"
    ZIP = "ZIP"
    TAR_GZ = "TAR_GZ"
    SEVEN_ZIP = "7Z"
    EMAIL_BUNDLE = "EMAIL_READY_BUNDLE"


class AcadVersion(LabeledEnum):
    R12 = "R12_DXF_R12"
    R14 = "R14_DXF_R14"
    R2000 = "R2000_ACAD_2000"
    R2004 = "R2004_ACAD_2004"
    R2006 = "R2006_ACAD_2006"
    R2007 = "R2007_ACAD_2007"
    R2010 = "R2010_ACAD_2010"
    R2013 = "R2013_ACAD_2013"
    R2018 = "R2018_ACAD_2018"
    R2022 = "R2022_ACAD_2022"
    R2024 = "R2024_ACAD_2024"


class SheetSize(LabeledEnum):
    A0 = "ISO_A0_841x1189"
    A1 = "ISO_A1_594x841"
    A2 = "ISO_A2_420x594"
    A3 = "ISO_A3_297x420"
    A4 = "ISO_A4_210x297"
    A0_EXTENDED = "ISO_A0_EXTENDED"
    A1_EXTENDED = "ISO_A1_EXTENDED"
    A2_EXTENDED = "ISO_A2_EXTENDED"
    ARCH_A = "ARCH_A_9x12_IN"
    ARCH_B = "ARCH_B_12x18_IN"
    ARCH_C = "ARCH_C_18x24_IN"
    ARCH_D = "ARCH_D_24x36_IN"
    ARCH_E = "ARCH_E_36x48_IN"
    ANSI_A = "ANSI_A_8p5x11_IN"
    ANSI_B = "ANSI_B_11x17_IN"
    ANSI_C = "ANSI_C_17x22_IN"
    ANSI_D = "ANSI_D_22x34_IN"
    ANSI_E = "ANSI_E_34x44_IN"
    CUSTOM = "CUSTOM_USER"


class DrawingScale(IntEnumStrict):
    S10 = 10
    S20 = 20
    S25 = 25
    S30 = 30
    S40 = 40
    S50 = 50
    S60 = 60
    S75 = 75
    S100 = 100
    S125 = 125
    S150 = 150
    S200 = 200
    S250 = 250
    S300 = 300
    S400 = 400
    S500 = 500
    S600 = 600
    S750 = 750
    S1000 = 1000
    S1250 = 1250
    S1500 = 1500
    S2000 = 2000
    S2500 = 2500
    S3000 = 3000
    S5000 = 5000


class LayerStandard(LabeledEnum):
    IRC = "IRC_SP55"
    IRC_SP55_2019 = "IRC_SP55_2019"
    CPWD = "CPWD_SPEC"
    NHAI = "NHAI"
    MORTH = "MORTH"
    RDSO = "RDSO_RAILWAY"
    AASHTO = "AASHTO_NTPELDP"
    BS1192 = "BS_1192"
    ISO_13567 = "ISO_13567"
    CUSTOM = "CUSTOM"


class TitleBlockStyle(LabeledEnum):
    STANDARD = "STANDARD"
    COMPACT = "COMPACT"
    DETAILED = "DETAILED"
    NHAI = "NHAI_OFFICIAL"
    CPWD = "CPWD_OFFICIAL"
    PWD_STATE = "STATE_PWD"
    MORTH = "MORTH_OFFICIAL"
    RAILWAY_RDSO = "RAILWAY_RDSO"
    PORT = "PORT_AUTHORITY"
    CLIENT_CUSTOM = "CLIENT_CUSTOM_BRAND"
    ISO_7200 = "ISO_7200_TECHNICAL_DRAWING"
    ARCHITECTURAL = "ARCHITECTURAL_TB"
    MINIMAL = "MINIMAL"
    ACADEMIC = "ACADEMIC_EDUCATION"
    OLD_STYLE = "OLD_CLASSIC_STYLE"


class ValidationSeverity(LabeledEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    WARNING = "WARNING"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
    SUGGESTION = "SUGGESTION"
    HINT = "HINT"
    OK = "OK_PASS"
    OK_PASS = "OK_PASS"
    PASS = "PASS"
    BLOCKER = "BLOCKER"


# ===========================================================================
# M1W2 — Additional referenced enums (180+ registry target)
# Section 11 — Project / QA / Metadata / Survey
# ===========================================================================


class ProjectStage(LabeledEnum):
    CONCEPT = "CONCEPT"
    PRELIMINARY = "PRELIMINARY_GAD"
    DETAILED_GAD = "DETAILED_GAD"
    DESIGN_DEVELOPED = "DESIGN_DEVELOPED_60PCT"
    TENDER_ISSUE = "ISSUE_FOR_TENDER"
    CONSTRUCTION = "CONSTRUCTION_ISSUE"
    AS_BUILT = "AS_BUILT"


class ProjectOwnerType(LabeledEnum):
    STATE_PWD = "STATE_PWD"
    NHAI = "NHAI"
    MORTH = "MORTH"
    RAILWAY = "INDIAN_RAILWAYS"
    MUNICIPAL = "MUNICIPAL_CORPORATION"
    BRO = "BORDER_ROADS"
    PVT_DEVELOPER = "PRIVATE_DEVELOPER"
    CPWD = "CPWD"


class BridgeSelectionCriterion(LabeledEnum):
    MIN_SPAN_MINOR = "MINOR_BRIDGE_MIN_SPAN"
    HYDRAULIC_CLEARANCE = "HYDRAULIC_CLEARANCE_GOVERNS"
    ROAD_GEOMETRY = "ROAD_GEOMETRY_DRIVEN"
    SOIL_FOUNDATION = "SOIL_FOUNDATION_GOVERNS"
    AESTHETIC = "AESTHETIC_PEER_REVIEW"
    COST_OPTIMUM = "LCC_COST_OPTIMUM"


class BridgeLengthCode(LabeledEnum):
    CULVERT_LT6M = "CULVERT_LT_6M"
    MINOR_6TO30M = "MINOR_BRIDGE_6_TO_30M"
    MAJOR_30TO100M = "MAJOR_BRIDGE_30_TO_100M"
    LONG_GT100M = "LONG_SPAN_GT_100M"
    VIADUCT = "VIADUCT_MULTI_SPAN"


class SpanArrangementClass(LabeledEnum):
    SIMPLE_EQUAL = "SIMPLY_SUPPORTED_EQUAL_SPANS"
    SIMPLE_VARIABLE = "SIMPLY_SUPPORTED_VARIABLE"
    CONTINUOUS_2SPAN = "CONTINUOUS_2_SPAN"
    CONTINUOUS_3SPAN = "CONTINUOUS_3_SPAN"
    CONTINUOUS_MULTI = "CONTINUOUS_MULTI_SPAN"
    CANTILEVER_SPAN = "CANTILEVER_SUSPENDED_SPANS"


# ===========================================================================
# Section 12 — Geometry / Cross-section width classes
# ===========================================================================


class CarriagewayWidthClass(LabeledEnum):
    SINGLE_LANE_3_5M = "SINGLE_LANE_3_5M"
    INTERMEDIATE_5_5M = "INTERMEDIATE_5_5M"
    TWO_LANE_7_0M = "TWO_LANE_7_0M"
    TWO_LANE_7_5M = "TWO_LANE_7_5M"
    FOUR_LANE_14_0M = "FOUR_LANE_14_0M"
    FOUR_LANE_15_0M = "FOUR_LANE_15_0M"
    SIX_LANE_21_0M = "SIX_LANE_21_0M"
    MULTI_LANE_GT22M = "MULTI_LANE_GT_22M"


class FootpathWidthClass(LabeledEnum):
    NONE = "NO_FOOTPATH"
    NARROW_1_0M = "NARROW_1_0M"
    STANDARD_1_5M = "STANDARD_1_5M"
    WIDE_2_0M = "WIDE_2_0M"
    PEDESTRIAN_3_0M = "PEDESTRIAN_MALL_3_0M"
    CYCLE_TRACK = "COMBINED_CYCLE_AND_FOOTPATH"


class DeckWidthOverallClass(LabeledEnum):
    NARROW_LT10M = "NARROW_LT_10M"
    STANDARD_10TO15M = "STANDARD_10_TO_15M"
    WIDE_15TO25M = "WIDE_15_TO_25M"
    ULTRA_WIDE_GT25M = "ULTRA_WIDE_GT_25M"


class PierHeightClass(LabeledEnum):
    LOW_LT5M = "LOW_PIER_LT_5M"
    MEDIUM_5TO12M = "MEDIUM_5_TO_12M"
    HIGH_12TO20M = "HIGH_12_TO_20M"
    VERY_HIGH_20TO35M = "VERY_HIGH_20_TO_35M"
    TALL_PIER_GT35M = "TALL_PIER_GT_35M"


class SpanLengthCode(LabeledEnum):
    SHORT_LT10M = "SHORT_SPAN_LT_10M"
    MODERATE_10TO25M = "MODERATE_10_TO_25M"
    STANDARD_25TO50M = "STANDARD_25_TO_50M"
    LONG_50TO100M = "LONG_50_TO_100M"
    VERY_LONG_GT100M = "VERY_LONG_GT_100M"


# ===========================================================================
# Section 13 — Materials / Detailing helper enums
# ===========================================================================


class ExposureZoneClass(LabeledEnum):
    MILD = "MILD_EXPOSURE"
    MODERATE = "MODERATE_EXPOSURE"
    SEVERE = "SEVERE_EXPOSURE"
    VERY_SEVERE = "VERY_SEVERE_EXPOSURE"
    EXTREME = "EXTREME_EXPOSURE"


class SuperstructureMaterial(LabeledEnum):
    RCC_CAST_IN_SITU = "RCC_CAST_IN_SITU"
    RCC_PRECAST = "RCC_PRECAST"
    PSC_POST_TENSIONED = "PSC_POST_TENSIONED"
    PSC_PRE_TENSIONED = "PSC_PRE_TENSIONED"
    STEEL_COMPOSITE = "STEEL_CONCRETE_COMPOSITE"
    STEEL_PLATE_GIRDER = "STEEL_PLATE_GIRDER"
    STEEL_TRUSS = "STEEL_TRUSS"
    MASONRY = "STONE_MASONRY_ARCH"


class ReinforcementGradeType(LabeledEnum):
    FE250 = "Fe250_MILD_STEEL"
    FE415 = "Fe415_THERMEX"
    FE500 = "Fe500_HYSD"
    FE500D = "Fe500D_DUCTILE"
    FE550D = "Fe550D_HIGH_DUCTILE"
    FE600 = "Fe600_ULTRA_HIGH"
    HDPE_TMT = "HDPE_COATED_TMT"


class BearingPadMaterial(LabeledEnum):
    NRB_NATURAL = "NRB_NATURAL_RUBBER_50ShA"
    NEOPRENE = "NEOPRENE_CHLOROPRENE"
    NITRILE = "NITRILE_NBR_OIL_RESISTANT"
    URETHANE = "POLYURETHANE_THERMOPLASTIC"
    EPDM = "EPDM_ETHYLENE_PROPYLENE"
    PTFE_GLASS_FILLED = "PTFE_GLASS_FILLED_SLIDING"


# ===========================================================================
# Section 14 — Survey / Grid / Drawing metadata
# ===========================================================================


class ChainageReferenceSystem(LabeledEnum):
    CUMULATIVE_PROJECT = "CUMULATIVE_PROJECT_CHAINAGE"
    KMPLUS = "KM_PLUS_STYLE"
    STATION_FEET = "STATION_STYLE_100FT"
    LOCAL_RESET = "LOCAL_RESET_AT_STRUCTURE"
    INDEPENDENT_BASELINE = "INDEPENDENT_BASELINE"


class SurveyGridZone(LabeledEnum):
    WGS84_UTM = "WGS84_UTM"
    INDIAN_DATUM_1971 = "INDIAN_DATUM_1971_EVEREST"
    INDIAN_DATUM_2003 = "INDIAN_DATUM_WGS84_2003"
    KALIANPUR = "KALIANPUR_DATUM"
    GCS_LOCAL_GRID = "LOCAL_CUSTOM_CARTESIAN_GRID"
    ASSUMED_LOCAL = "ASSUMED_LOCAL_SITE_GRID"


# ===========================================================================
# ENUM_REGISTRY (used by Excel template generator for dropdowns)
# ===========================================================================


_ENUM_ORDER = [
    # Section 1 — Project / Client
    ClientType,
    ConsultantType,
    ContractorType,
    ProjectPhase,
    Currency,
    RevisionTag,
    Language,
    IndianStateCode,
    SurveyAgency,
    TenderType,
    FundingSourceType,
    WorkStatusType,
    ContractPackageType,
    DesignFirmCategoryClass,
    ProjectStage,
    ProjectOwnerType,
    # Section 2 — Bridge Category / Selection
    BridgeCategory,
    SuperstructureType,
    SpanConfiguration,
    CarriagewayLaneConfig,
    BridgeSubcategory,
    CarriagewaySkewConfig,
    UsageIntensityType,
    WaterwayCrossingType,
    InterchangeGradeSeparationType,
    BridgeSelectionCriterion,
    BridgeLengthCode,
    SpanArrangementClass,
    # Section 3 — Geometry
    SkewDirection,
    AlignmentType,
    KerbType,
    FootpathType,
    MedianType,
    CrashBarrierType,
    ChainageUnit,
    RotationDirection,
    PavementCrustComposition,
    TransitionCurveType,
    VerticalAlignmentType,
    DrainageCrossfallType,
    SuperelevationRotationAxis,
    WideningTypeOnCurve,
    HorizontalCurveTransitionType,
    SightDistanceCategory,
    CarriagewayWidthClass,
    FootpathWidthClass,
    DeckWidthOverallClass,
    PierHeightClass,
    SpanLengthCode,
    # Section 4 — Superstructure
    WearingCoatType,
    ParapetType,
    RailingType,
    DrainageType,
    GirderType,
    SlabType,
    CamberMethod,
    CantileverOverhangType,
    SuperstructureSegmentation,
    DeckJointSpacing,
    WebOpenCutoutType,
    PrecastSegmentJointType,
    DeckPourSequenceMethod,
    ArchShapeType,
    CableStayingSystemClass,
    TrussConfigurationClass,
    # Section 5 — Substructure
    PierType,
    PierCapType,
    PierShaftShape,
    AbutmentType,
    ReturnWallType,
    WingWallType,
    AbutmentPedestalType,
    WellSteiningType,
    PierTieBeamLocationType,
    AbutmentBackfillSpecificationType,
    # Section 6 — Foundation
    FoundationType,
    PileType,
    PileShape,
    PileBaseType,
    WellCurbType,
    WellCuttingEdgeShape,
    UnderReamCount,
    RaftMatType,
    OpenFoundationDepth,
    SheetPileType,
    BearingCapacitySoilType,
    GroundImprovementType,
    PileInstallationMethodType,
    SettlementCriterionCategoryType,
    # Section 7 — Hydraulic / Scour / Flood
    WaterSourceType,
    ScourRegimeType,
    ScourMeasurementMethod,
    HydrographShapeType,
    BankProtectionMethodType,
    RiverTrainingWorkType,
    AffluxEstimationFormulaType,
    FreeboardAdditionFactorType,
    FloodFrequencyAnalysisMethodType,
    FloodReturnPeriodDesign,
    RainfallIntensityStormType,
    RiverBedMaterialSizeType,
    HydraulicDesignMethod,
    DischargeMeasurementMethod,
    FlowVelocityCategory,
    BridgeHydraulicOpeningType,
    SedimentLoadTransportType,
    GradeControlStructureType,
    BankErosionCategoryClass,
    LaceyRegimeFactorType,
    IceLoadType,
    WaterQualityAggressiveType,
    RiverBankType,
    SoilClass,
    RegimeConstantKValue,
    RiverGeomorphologyType,
    WaterSurfaceProfileType,
    ScourProtectionSubtype,
    SedimentYieldClassification,
    RiverCrossingClass,
    # Section 8 — Materials / Construction / Components
    ConcreteAggregateType,
    CementType,
    AdmixtureType,
    WeldType,
    BearingMaterial,
    JointSealantType,
    WearingCoatGrade,
    ConcreteCoverNominalClass,
    ConcreteSlumpClass,
    ConcreteCuringMethodType,
    ReinforcementBarType,
    RebarCouplerType,
    ConcreteSurfaceFinishClass,
    FormworkPanelType,
    FormworkReleaseAgentType,
    WaterproofingMembraneType,
    AntiCorrosionProtectionType,
    PaintCoatSystemType,
    ExposureZoneClass,
    SuperstructureMaterial,
    ReinforcementGradeType,
    BearingPadMaterial,
    # Section 9 — Drawing / CAD / Layout Standards (IRC:SP:55-2019)
    LayerGroup,
    LineWeightCode,
    HatchPatternCode,
    FontStyle,
    ArrowStyle,
    ScaleDenominatorSet,
    LineStyleCode,
    DimensionStyleClass,
    ViewTypeClassification,
    CrossSectionViewTypeCode,
    TitleBlockRevisionClass,
    PlotterPaperClass,
    ChainageReferenceSystem,
    SurveyGridZone,
    # Section 10 — Load / Seismic / Wind / Temperature / Combinations
    SeismicImportanceFactor,
    WindImportanceFactor,
    WindSpeedBasic_ms,
    LoadCombination,
    ImpactFactorCoeff,
    TemperatureLoadDeltaT,
    PrestressLossTypeEnum,
    CreepShrinkageFactorClass,
    FrictionCoeffBearingPadType,
    DampingRatioTypeEnum,
    ResponseSpectrumCategory,
    FatigueDetailCategorySteel,
    DuctilityClassLink,
    RetainingWallModeType,
]

# Include the M0 legacy enums still defined today where no replacement created yet:
_M0_LEGACY = [
    ConcreteGrade,
    SteelGrade,
    PrestressGrade,
    BearingType,
    ExpansionJointType,
    DesignCode,
    LoadClass,
    SeismicZone,
    OutputFormat,
    AcadVersion,
    SheetSize,
    DrawingScale,
    LayerStandard,
    TitleBlockStyle,
    ValidationSeverity,
]

ENUM_REGISTRY: dict[str, type[Enum]] = {
    e.__name__: e
    for e in (_ENUM_ORDER + _M0_LEGACY)  # type: ignore[arg-type]
}

__all_extras: list[str] = []
for _cls in list(ENUM_REGISTRY.values()):
    if _cls.__name__ not in __all_extras:
        __all_extras.append(_cls.__name__)


# ===========================================================================
# Public API
# ===========================================================================


__all__ = [
    "StrEnum",
    "IntEnumStrict",
    "LabeledEnum",
    "UnitHaverEnum",
    "RangeBoundedEnum",
    "ENUM_REGISTRY",
    *__all_extras,
]
