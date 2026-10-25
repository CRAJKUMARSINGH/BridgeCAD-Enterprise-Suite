"""
bridgecad_core.standards.morth_specs — MORTH 5th Revision Specification Lookup.

Provides:
  - MORTH item code → description / unit mapping
  - Contract clause references
  - Material specification minimums (concrete, steel, bituminous)
  - Inspection / testing frequencies
  - Safety / quality class definitions
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# MORTH Chapter Codes and Titles
# ---------------------------------------------------------------------------

MORTH_CHAPTERS: dict[str, str] = {
    "100": "Project Preparation and Documentation",
    "200": "Site Clearance",
    "300": "Earthwork, Erosion Control and Drainage",
    "400": "Sub-Base and Base Courses",
    "500": "Bituminous Courses",
    "600": "Cement Concrete Pavement",
    "700": "Bridges, Culverts and Structures",
    "800": "Traffic Signs, Markings and Appurtenances",
    "900": "Maintenance of Traffic and Miscellaneous",
    "1000": "Quality Control and Acceptance",
    "1600": "Reinforcement and Prestressing Steel",
    "1700": "Concrete Works for Bridges",
    "1800": "Piling and Well Foundation",
    "2400": "Structural Steel Fabrication",
    "2500": "River Training and Bank Protection",
    "2600": "Bridge Deck Waterproofing",
    "2700": "Bearings for Bridges",
    "2800": "Expansion Joints",
    "2900": "Bridge Accessories",
}


# ---------------------------------------------------------------------------
# Concrete Mix Design Minimums — MORTH 5th Rev Clause 1700
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConcreteSpec:
    grade: str  # e.g. "M30"
    min_cement_kg_m3: float  # minimum cement content kg/m³
    max_water_cement: float  # maximum w/c ratio
    min_compressive_Mpa: float  # 28-day characteristic strength MPa
    exposure_class: str  # per IS:456 Table 5
    min_cover_mm: int  # nominal cover for given exposure
    max_chloride_pct: float  # % by weight of cement


CONCRETE_SPECS: dict[str, ConcreteSpec] = {
    "M15": ConcreteSpec("M15", 200, 0.60, 15, "MILD", 20, 0.60),
    "M20": ConcreteSpec("M20", 250, 0.55, 20, "MILD", 20, 0.60),
    "M25": ConcreteSpec("M25", 280, 0.50, 25, "MODERATE", 30, 0.60),
    "M30": ConcreteSpec("M30", 300, 0.45, 30, "MODERATE", 30, 0.30),
    "M35": ConcreteSpec("M35", 320, 0.43, 35, "SEVERE", 45, 0.30),
    "M40": ConcreteSpec("M40", 340, 0.40, 40, "SEVERE", 45, 0.20),
    "M45": ConcreteSpec("M45", 360, 0.38, 45, "VERY_SEVERE", 50, 0.20),
    "M50": ConcreteSpec("M50", 380, 0.36, 50, "VERY_SEVERE", 50, 0.20),
    "M55": ConcreteSpec("M55", 400, 0.34, 55, "EXTREME", 75, 0.10),
    "M60": ConcreteSpec("M60", 420, 0.32, 60, "EXTREME", 75, 0.10),
}


def concrete_spec(grade: str) -> ConcreteSpec | None:
    """Return MORTH concrete specification for a given grade."""
    return CONCRETE_SPECS.get(grade.upper())


# ---------------------------------------------------------------------------
# Reinforcement Steel — MORTH 5th Rev Clause 1601 / IS:1786
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RebarSpec:
    grade: str
    fy_MPa: float  # characteristic yield strength
    fu_MPa: float  # ultimate tensile strength
    elongation_pct: float  # minimum elongation at fracture
    is_standard: str
    notes: str


REBAR_SPECS: dict[str, RebarSpec] = {
    "Fe415": RebarSpec("Fe415", 415, 485, 14.5, "IS:1786", "General purpose"),
    "Fe415D": RebarSpec("Fe415D", 415, 500, 18.0, "IS:1786", "Ductile — seismic zones"),
    "Fe500": RebarSpec("Fe500", 500, 545, 12.0, "IS:1786", "Higher strength"),
    "Fe500D": RebarSpec("Fe500D", 500, 565, 16.0, "IS:1786", "Ductile — preferred for bridges"),
    "Fe550": RebarSpec("Fe550", 550, 585, 10.0, "IS:1786", "High-strength special projects"),
    "Fe550D": RebarSpec("Fe550D", 550, 600, 14.5, "IS:1786", "Ductile high-strength"),
    "Fe600": RebarSpec("Fe600", 600, 660, 8.0, "IS:1786", "Very high strength — rare"),
}


def rebar_spec(grade: str) -> RebarSpec | None:
    """Return reinforcement specification for a given grade."""
    return REBAR_SPECS.get(grade.upper())


# ---------------------------------------------------------------------------
# Prestressing Steel — MORTH / IS:1343 / IS:14268
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PrestressSpec:
    grade: str
    fpk_MPa: float  # characteristic tensile strength
    fp0_1k_MPa: float  # 0.1% proof stress
    fy_MPA: float  # yield strength (0.2% offset)
    elongation_pct: float
    type: str  # STRAND | WIRE | BAR
    diameter_mm: float
    area_mm2: float
    is_standard: str


PRESTRESS_SPECS: dict[str, PrestressSpec] = {
    "G1860_12.7": PrestressSpec(
        "G1860_12.7", 1860, 1580, 1670, 3.5, "STRAND", 12.7, 98.7, "IS:14268"
    ),
    "G1860_15.2": PrestressSpec(
        "G1860_15.2", 1860, 1580, 1670, 3.5, "STRAND", 15.2, 139.0, "IS:14268"
    ),
    "G1960_12.7": PrestressSpec(
        "G1960_12.7", 1960, 1670, 1770, 3.5, "STRAND", 12.7, 98.7, "IS:14268"
    ),
    "HT_WIRE_5": PrestressSpec("HT_WIRE_5", 1715, 1470, 1550, 2.5, "WIRE", 5.0, 19.6, "IS:1785"),
    "HT_WIRE_7": PrestressSpec("HT_WIRE_7", 1570, 1340, 1415, 2.5, "WIRE", 7.0, 38.5, "IS:1785"),
}


# ---------------------------------------------------------------------------
# Bituminous Wearing Coat — MORTH Clause 500–510
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BituminousSpec:
    type: str  # BC / SMA / DBM / SDBC / OGFC
    thickness_mm: tuple  # (min, max)
    voids_pct: tuple  # air voids range
    stability_kN: float  # Marshall stability minimum
    flow_mm: tuple  # Marshall flow range
    bitumen_grade: str  # VG-30 | VG-40 | PMB-40 | PMB-45
    clause: str


BITUMINOUS_SPECS: dict[str, BituminousSpec] = {
    "BC": BituminousSpec("BC", (25, 50), (3, 5), 9.0, (2, 4), "VG-30", "MORTH Cl.510"),
    "SMA": BituminousSpec("SMA", (25, 50), (3, 4), 10.0, (2, 4), "PMB-45", "MORTH Cl.510"),
    "DBM": BituminousSpec("DBM", (50, 100), (3, 5), 9.0, (2, 4), "VG-30", "MORTH Cl.505"),
    "SDBC": BituminousSpec("SDBC", (20, 25), (3, 5), 8.0, (2, 4), "VG-30", "MORTH Cl.510"),
    "OGFC": BituminousSpec("OGFC", (25, 40), (18, 22), 5.0, (2, 4), "PMB-40", "MORTH Cl.510"),
}


# ---------------------------------------------------------------------------
# Testing Frequencies — MORTH 5th Rev Clause 1000 (QA Framework)
# ---------------------------------------------------------------------------

TEST_FREQUENCIES: dict[str, str] = {
    # material / activity → testing frequency
    "CONCRETE_CUBE_COMPRESSIVE": "1 set per 5 CUM (min 3 cubes per set per IS:456)",
    "CONCRETE_SLUMP": "Every batch / every 2 CUM minimum",
    "REBAR_TENSILE": "1 sample per 50 MT or per heat of steel (IS:1786)",
    "REBAR_BEND_REBEND": "1 sample per 50 MT or per heat",
    "PILE_INTEGRITY_TEST": "100% PIT for all piles < 10 m dia; 10% for large dia",
    "PILE_LOAD_TEST": "1 initial + 1 per 100 piles routine (IS:2911)",
    "BITUMINOUS_MARSHALL": "Per mix design + 1 per 500 CUM production",
    "BITUMINOUS_THICKNESS": "Core samples at 250 m intervals",
    "BEARING_INSPECTION": "100% visual + 10% dimensional on delivery",
    "EXPANSION_JOINT_INSPECTION": "100% before sealing / installation",
    "FORMWORK_INSPECTION": "Before every major pour ≥ 20 CUM",
    "PRESTRESS_JACKING_LOG": "Every tendon — elongation vs. jack pressure",
    "WATER_QUALITY": "Before use, monthly for marine exposure",
}


# ---------------------------------------------------------------------------
# Contract clause references for common bridge items
# ---------------------------------------------------------------------------

CONTRACT_CLAUSES: dict[str, str] = {
    "CONCRETE_MIX_DESIGN": "MORTH Cl.1714 / IS:10262",
    "FORMWORK_STRIPPING": "MORTH Cl.1707 / IS:456 Cl.11",
    "CURING_PERIOD": "MORTH Cl.1714.4 — 14 days wet curing for OPC; 28 days for PPC/PSC",
    "PILE_CONCRETING": "MORTH Cl.1812 — tremie method under water",
    "BEARING_INSTALLATION": "MORTH Cl.2702 / IRC:83",
    "EXPANSION_JOINT_INSTALLATION": "MORTH Cl.2802 / IRC SP:55 Cl.7.3",
    "WATERPROOFING": "MORTH Cl.2602 — applied before wearing coat",
    "BACKFILL_COMPACTION": "MORTH Cl.305 — 95% proctor density, 250 mm lifts",
    "RIVER_TRAINING": "MORTH Cl.2501–2504 / IRC:5-2015",
    "WEIGH_BRIDGE_CALIBRATION": "MORTH Cl.1003 — monthly calibration",
    "QAP_APPROVAL": "MORTH Cl.1007 — Quality Assurance Plan before start",
    "SAFETY_OFFICER": "MORTH Cl.1205 — mandatory safety officer for bridges",
    "ENVIRONMENT_CLEARANCE": "MoEF / CRZ notification for coastal bridges",
}


def contract_clause(item: str) -> str:
    """Return the MORTH clause reference for a contract item."""
    return CONTRACT_CLAUSES.get(item.upper().replace(" ", "_"), "Refer MORTH 5th Rev")


__all__ = [
    "MORTH_CHAPTERS",
    "ConcreteSpec",
    "CONCRETE_SPECS",
    "concrete_spec",
    "RebarSpec",
    "REBAR_SPECS",
    "rebar_spec",
    "PrestressSpec",
    "PRESTRESS_SPECS",
    "BituminousSpec",
    "BITUMINOUS_SPECS",
    "TEST_FREQUENCIES",
    "CONTRACT_CLAUSES",
    "contract_clause",
]
