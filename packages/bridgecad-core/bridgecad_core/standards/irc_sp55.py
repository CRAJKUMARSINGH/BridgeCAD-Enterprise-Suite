"""
bridgecad_core.standards.irc_sp55 — IRC:SP:55-2019 Drawing Standards.

Implements:
  - Standard drawing scales per view type
  - Text height tables (by view type and annotation type)
  - Lineweight schedule (ISO/IRC)
  - Layer naming convention
  - Sheet size / margin tables
  - Title block cell definitions
  - Dimension style parameters
  - Hatch pattern assignments by material
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Drawing Scales — IRC SP:55-2019 Annex G / Clause 11.1
# ---------------------------------------------------------------------------

STANDARD_SCALES: dict[str, list[int]] = {
    # View type → allowed scale denominators
    "GENERAL_ARRANGEMENT": [100, 200, 500],
    "PLAN_VIEW": [100, 200, 500],
    "LONGITUDINAL_SECTION": [100, 200, 500],
    "CROSS_SECTION": [25, 50, 100],
    "FOUNDATION_DETAILS": [25, 50, 100],
    "PIER_DETAILS": [20, 25, 50],
    "ABUTMENT_DETAILS": [20, 25, 50],
    "BEARING_DETAILS": [5, 10, 20],
    "EXPANSION_JOINT": [5, 10, 20],
    "REINFORCEMENT": [20, 25, 50],
    "BAR_BENDING_SCHEDULE": [1],  # table — no drawing scale
    "SITE_PLAN": [500, 1000, 2000],
    "KEY_PLAN": [2000, 5000],
}

PREFERRED_SCALE: dict[str, int] = {
    "GENERAL_ARRANGEMENT": 100,
    "PLAN_VIEW": 100,
    "LONGITUDINAL_SECTION": 100,
    "CROSS_SECTION": 50,
    "FOUNDATION_DETAILS": 50,
    "PIER_DETAILS": 25,
    "ABUTMENT_DETAILS": 25,
    "BEARING_DETAILS": 10,
    "EXPANSION_JOINT": 10,
    "REINFORCEMENT": 25,
    "SITE_PLAN": 1000,
    "KEY_PLAN": 5000,
}


def preferred_scale(view_type: str) -> int:
    """Return the IRC SP:55 preferred scale denominator for a view type."""
    return PREFERRED_SCALE.get(view_type.upper(), 100)


# ---------------------------------------------------------------------------
# Text Heights — IRC SP:55-2019 Clause 11.2
# ---------------------------------------------------------------------------

# text_height_mm[sheet_size][annotation_type] = height in mm (at plot scale)
TEXT_HEIGHT_MM: dict[str, dict[str, float]] = {
    "A0": {
        "TITLE": 6.0,
        "SUBTITLE": 4.0,
        "HEADING": 3.5,
        "BODY": 2.5,
        "DIMENSION": 2.5,
        "NOTE": 2.0,
        "LABEL": 2.5,
        "LEVEL_TAG": 2.0,
        "CHAINAGE": 2.0,
        "SPEC_NOTE": 1.8,
    },
    "A1": {
        "TITLE": 5.0,
        "SUBTITLE": 3.5,
        "HEADING": 3.0,
        "BODY": 2.5,
        "DIMENSION": 2.5,
        "NOTE": 2.0,
        "LABEL": 2.5,
        "LEVEL_TAG": 2.0,
        "CHAINAGE": 2.0,
        "SPEC_NOTE": 1.8,
    },
    "A2": {
        "TITLE": 4.0,
        "SUBTITLE": 3.0,
        "HEADING": 2.5,
        "BODY": 2.0,
        "DIMENSION": 2.0,
        "NOTE": 1.8,
        "LABEL": 2.0,
        "LEVEL_TAG": 1.8,
        "CHAINAGE": 1.8,
        "SPEC_NOTE": 1.5,
    },
    "A3": {
        "TITLE": 3.5,
        "SUBTITLE": 2.5,
        "HEADING": 2.0,
        "BODY": 1.8,
        "DIMENSION": 1.8,
        "NOTE": 1.5,
        "LABEL": 1.8,
        "LEVEL_TAG": 1.5,
        "CHAINAGE": 1.5,
        "SPEC_NOTE": 1.2,
    },
}


def text_height(sheet_size: str = "A1", annotation_type: str = "BODY") -> float:
    """Return IRC SP:55 text height (mm at plot scale).

    Parameters
    ----------
    sheet_size       : str  A0 | A1 | A2 | A3 | A4
    annotation_type  : str  TITLE | SUBTITLE | HEADING | BODY | DIMENSION |
                             NOTE | LABEL | LEVEL_TAG | CHAINAGE | SPEC_NOTE

    Returns
    -------
    float  Text height in mm.
    """
    size_table = TEXT_HEIGHT_MM.get(sheet_size.upper(), TEXT_HEIGHT_MM["A1"])
    return size_table.get(annotation_type.upper(), 2.5)


# ---------------------------------------------------------------------------
# Lineweight Schedule — IRC SP:55-2019 Annex F / ISO 128
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LineweightSpec:
    name: str
    weight_mm: float  # mm  (e.g. 0.50)
    aci_lw: int  # AutoCAD lineweight code (hundredths of mm, e.g. 50 = 0.50mm)
    description: str


LINEWEIGHTS: dict[str, LineweightSpec] = {
    "EXTRA_HEAVY": LineweightSpec(
        "EXTRA_HEAVY", 0.70, 70, "Primary structural outline (cut sections)"
    ),
    "HEAVY": LineweightSpec("HEAVY", 0.50, 50, "Main outline visible in plan/elevation"),
    "MEDIUM": LineweightSpec("MEDIUM", 0.35, 35, "Secondary outlines, substructure"),
    "STANDARD": LineweightSpec("STANDARD", 0.25, 25, "Hatching boundaries, minor elements"),
    "LIGHT": LineweightSpec("LIGHT", 0.18, 18, "Dimensions, text leaders, section marks"),
    "THIN": LineweightSpec("THIN", 0.13, 13, "Hatch lines, grid lines, reference lines"),
    "HAIR": LineweightSpec("HAIR", 0.09, 9, "Construction lines, overlaid grid"),
}

# Lineweight assignment per layer type
LAYER_LINEWEIGHT: dict[str, str] = {
    "STRUC-OUTLINE": "EXTRA_HEAVY",
    "STRUC-SECTION": "HEAVY",
    "STRUC-HIDDEN": "LIGHT",
    "STRUC-CENTRE": "LIGHT",
    "STRUC-HATCHING": "THIN",
    "CIVIL-GROUND": "MEDIUM",
    "CIVIL-HFL": "STANDARD",
    "CIVIL-LWL": "STANDARD",
    "CIVIL-SCOUR": "STANDARD",
    "SUPER-DECK": "HEAVY",
    "SUPER-GIRDER": "HEAVY",
    "SUPER-PARAPET": "MEDIUM",
    "SUB-PIER": "HEAVY",
    "SUB-ABUT": "HEAVY",
    "SUB-BEARING": "STANDARD",
    "FOUND-PILE": "MEDIUM",
    "FOUND-CAP": "MEDIUM",
    "DIM-LINEAR": "LIGHT",
    "DIM-LEADER": "LIGHT",
    "TEXT-GENERAL": "LIGHT",
    "TEXT-TITLE": "MEDIUM",
    "BORDER-OUTER": "EXTRA_HEAVY",
    "BORDER-INNER": "HEAVY",
    "TITLEBLK-BOX": "MEDIUM",
}


def lineweight_for_layer(layer_name: str) -> LineweightSpec:
    """Return the IRC SP:55 lineweight spec for a given layer name."""
    key = LAYER_LINEWEIGHT.get(layer_name, "LIGHT")
    return LINEWEIGHTS[key]


# ---------------------------------------------------------------------------
# Sheet Sizes & Margins — ISO 5457 / IRC SP:55-2019 Annex G
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SheetSpec:
    name: str
    width_mm: float
    height_mm: float
    margin_left_mm: float  # wider left for binding
    margin_other_mm: float
    title_block_w_mm: float
    title_block_h_mm: float


SHEET_SPECS: dict[str, SheetSpec] = {
    "A0": SheetSpec("A0", 1189, 841, 20, 10, 190, 55),
    "A1": SheetSpec("A1", 841, 594, 20, 10, 185, 55),
    "A2": SheetSpec("A2", 594, 420, 15, 10, 180, 50),
    "A3": SheetSpec("A3", 420, 297, 15, 10, 170, 45),
    "A4": SheetSpec("A4", 297, 210, 15, 10, 160, 40),
    "A0_EXTENDED": SheetSpec("A0_EXTENDED", 1682, 841, 20, 10, 190, 55),
    "A1_EXTENDED": SheetSpec("A1_EXTENDED", 1189, 594, 20, 10, 185, 55),
}


def sheet_spec(size: str = "A1") -> SheetSpec:
    """Return sheet dimensions and margins for a given sheet size."""
    return SHEET_SPECS.get(size.upper(), SHEET_SPECS["A1"])


# ---------------------------------------------------------------------------
# Hatch Pattern Assignment — IRC SP:55-2019 Annex F
# ---------------------------------------------------------------------------

MATERIAL_HATCH: dict[str, tuple[str, float]] = {
    # material → (pattern_name, scale)
    "CONCRETE": ("ANSI31", 1.0),  # 45° diagonal lines
    "RCC": ("ANSI31", 1.0),
    "MASONRY": ("ANSI37", 1.0),  # brick pattern
    "EARTH": ("EARTH", 1.0),  # gravel/earth
    "ROCK": ("AR-RROCK", 0.5),
    "STEEL": ("ANSI31", 0.5),  # fine diagonal
    "SAND": ("AR-SAND", 0.3),
    "GRAVEL": ("GRAVEL", 0.5),
    "BITUMINOUS": ("AR-SAND", 0.5),
    "WATER": ("ANSI31", 3.0),  # coarse diagonal (blue layer)
    "FILL_GRANULAR": ("DOTS", 1.0),
    "FILL_MOORUM": ("EARTH", 1.0),
    "TIMBER": ("ANSI32", 1.0),
    "INSULATION": ("ANSI33", 1.0),
    "SOLID_FILL": ("SOLID", 1.0),
}


def hatch_for_material(material: str) -> tuple[str, float]:
    """Return (hatch_pattern_name, scale) for a material type."""
    return MATERIAL_HATCH.get(material.upper(), ("ANSI31", 1.0))


# ---------------------------------------------------------------------------
# Dimension Style Parameters — IRC SP:55-2019 Clause 11.3
# ---------------------------------------------------------------------------


@dataclass
class DimStyleSpec:
    """IRC SP:55 dimension style parameters for ezdxf / AutoCAD."""

    name: str
    text_height_mm: float = 2.5
    arrow_size_mm: float = 2.5
    extension_mm: float = 1.5  # extension line overhang
    offset_mm: float = 1.0  # gap between object and dim line
    gap_mm: float = 0.8  # text gap from dim line
    decimal_places: int = 3  # default mm precision
    units: str = "mm"  # mm | m


DIMENSION_STYLES: dict[str, DimStyleSpec] = {
    "IRC_DIM_MM_A1": DimStyleSpec("IRC_DIM_MM_A1", 2.5, 2.5, 1.5, 1.0, 0.8, 3, "mm"),
    "IRC_DIM_M_A1": DimStyleSpec("IRC_DIM_M_A1", 2.5, 2.5, 1.5, 1.0, 0.8, 3, "m"),
    "IRC_DIM_MM_A0": DimStyleSpec("IRC_DIM_MM_A0", 3.0, 3.0, 2.0, 1.5, 1.0, 3, "mm"),
    "IRC_DIM_MM_A2": DimStyleSpec("IRC_DIM_MM_A2", 2.0, 2.0, 1.2, 0.8, 0.6, 3, "mm"),
    "IRC_DIM_MM_A3": DimStyleSpec("IRC_DIM_MM_A3", 1.8, 1.8, 1.0, 0.6, 0.5, 3, "mm"),
}


def dimension_style(sheet_size: str = "A1", units: str = "mm") -> DimStyleSpec:
    """Return IRC SP:55 dimension style for a sheet size and unit."""
    key = f"IRC_DIM_{units.upper()}_{sheet_size.upper()}"
    return DIMENSION_STYLES.get(key, DIMENSION_STYLES["IRC_DIM_MM_A1"])


# ---------------------------------------------------------------------------
# Layer Naming Convention Summary — IRC SP:55-2019 Annex F Table F-1
# ---------------------------------------------------------------------------

LAYER_DESCRIPTION: dict[str, str] = {
    "STRUC-OUTLINE": "Structural outline — primary visible lines",
    "STRUC-SECTION": "Section cut — heavy outline at cut plane",
    "STRUC-HIDDEN": "Hidden lines (beyond cut)",
    "STRUC-CENTRE": "Centrelines and axis",
    "STRUC-HATCHING": "Section hatching (concrete, soil, steel)",
    "CIVIL-GROUND": "Existing ground profile (EG)",
    "CIVIL-HFL": "Highest Flood Level line",
    "CIVIL-LWL": "Low Water Level line",
    "CIVIL-SCOUR": "Design scour level",
    "CIVIL-ROAD": "Approach road surface",
    "SUPER-DECK": "Deck slab faces (top + soffit)",
    "SUPER-GIRDER": "Longitudinal girder outlines",
    "SUPER-PARAPET": "Parapet / crash barrier",
    "SUPER-WEARING": "Wearing coat layer",
    "SUB-PIER": "Pier shaft + cap",
    "SUB-ABUT": "Abutment + wing walls",
    "SUB-BEARING": "Bearing pad positions",
    "SUB-EXPJOINT": "Expansion joint locations",
    "FOUND-PILE": "Pile circles + elevation",
    "FOUND-CAP": "Pile cap / raft / footing",
    "FOUND-WELL": "Well steining circles",
    "DIM-LINEAR": "Linear dimensions",
    "DIM-LEADER": "Leader lines",
    "DIM-LEVEL": "RL level tags",
    "DIM-CHAINAGE": "Chainage markers",
    "TEXT-GENERAL": "General annotations",
    "TEXT-TITLE": "Title block text",
    "BORDER-OUTER": "Sheet outer border",
    "BORDER-INNER": "Sheet inner margin",
    "TITLEBLK-BOX": "Title block cells",
    "SYM-NORTHARROW": "North arrow symbol",
    "SYM-SECTIONMARK": "Section A-A cut markers",
}


__all__ = [
    "STANDARD_SCALES",
    "PREFERRED_SCALE",
    "preferred_scale",
    "TEXT_HEIGHT_MM",
    "text_height",
    "LineweightSpec",
    "LINEWEIGHTS",
    "LAYER_LINEWEIGHT",
    "lineweight_for_layer",
    "SheetSpec",
    "SHEET_SPECS",
    "sheet_spec",
    "MATERIAL_HATCH",
    "hatch_for_material",
    "DimStyleSpec",
    "DIMENSION_STYLES",
    "dimension_style",
    "LAYER_DESCRIPTION",
]
