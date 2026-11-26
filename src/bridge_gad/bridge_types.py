#!/usr/bin/env python3
"""
Bridge Type Definitions and Enumerations

Defines the various bridge types supported by the BridgeGAD system
and their associated characteristics.
"""

from enum import Enum
from typing import Dict, List
from dataclasses import dataclass


class BridgeType(Enum):
    """Enumeration of supported bridge types"""
    SLAB = "slab"
    BEAM = "beam"
    TRUSS = "truss"
    ARCH = "arch"
    SUSPENSION = "suspension"
    CABLE_STAYED = "cable_stayed"
    T_BEAM = "t_beam"
    BOX_GIRDER = "box_girder"


class OutputFormat(Enum):
    """Supported output formats for bridge drawings"""
    DXF = "dxf"
    PDF = "pdf"
    SVG = "svg"
    PNG = "png"
    HTML = "html"
    ALL = "all"


class MaterialType(Enum):
    """Bridge construction materials"""
    CONCRETE = "concrete"
    STEEL = "steel"
    TIMBER = "timber"
    STONE = "stone"
    COMPOSITE = "composite"


class LoadType(Enum):
    """Types of loads considered in bridge design"""
    DEAD_LOAD = "dead_load"
    LIVE_LOAD = "live_load"
    WIND_LOAD = "wind_load"
    SEISMIC_LOAD = "seismic_load"
    THERMAL_LOAD = "thermal_load"


@dataclass
class BridgeCharacteristics:
    """Characteristics and constraints for each bridge type"""
    min_span: float  # Minimum practical span in meters
    max_span: float  # Maximum practical span in meters
    typical_span: float  # Typical span range in meters
    min_supports: int  # Minimum number of supports
    max_supports: int  # Maximum number of supports
    materials: List[MaterialType]  # Suitable materials
    complexity_level: int  # 1-5, where 5 is most complex


# Bridge type characteristics database
BRIDGE_CHARACTERISTICS: Dict[BridgeType, BridgeCharacteristics] = {
    BridgeType.SLAB: BridgeCharacteristics(
        min_span=5.0,
        max_span=25.0,
        typical_span=12.0,
        min_supports=0,
        max_supports=5,
        materials=[MaterialType.CONCRETE],
        complexity_level=1
    ),
    BridgeType.BEAM: BridgeCharacteristics(
        min_span=10.0,
        max_span=60.0,
        typical_span=25.0,
        min_supports=0,
        max_supports=8,
        materials=[MaterialType.CONCRETE, MaterialType.STEEL],
        complexity_level=2
    ),
    BridgeType.T_BEAM: BridgeCharacteristics(
        min_span=15.0,
        max_span=45.0,
        typical_span=30.0,
        min_supports=0,
        max_supports=6,
        materials=[MaterialType.CONCRETE],
        complexity_level=2
    ),
    BridgeType.BOX_GIRDER: BridgeCharacteristics(
        min_span=20.0,
        max_span=150.0,
        typical_span=50.0,
        min_supports=0,
        max_supports=10,
        materials=[MaterialType.CONCRETE, MaterialType.STEEL],
        complexity_level=3
    ),
    BridgeType.TRUSS: BridgeCharacteristics(
        min_span=30.0,
        max_span=200.0,
        typical_span=80.0,
        min_supports=0,
        max_supports=15,
        materials=[MaterialType.STEEL],
        complexity_level=4
    ),
    BridgeType.ARCH: BridgeCharacteristics(
        min_span=40.0,
        max_span=300.0,
        typical_span=100.0,
        min_supports=0,
        max_supports=20,
        materials=[MaterialType.CONCRETE, MaterialType.STONE],
        complexity_level=4
    ),
    BridgeType.SUSPENSION: BridgeCharacteristics(
        min_span=200.0,
        max_span=2000.0,
        typical_span=800.0,
        min_supports=2,
        max_supports=4,
        materials=[MaterialType.STEEL],
        complexity_level=5
    ),
    BridgeType.CABLE_STAYED: BridgeCharacteristics(
        min_span=150.0,
        max_span=1000.0,
        typical_span=400.0,
        min_supports=1,
        max_supports=3,
        materials=[MaterialType.STEEL, MaterialType.CONCRETE],
        complexity_level=5
    )
}


def get_bridge_characteristics(bridge_type: BridgeType) -> BridgeCharacteristics:
    """Get characteristics for a specific bridge type"""
    return BRIDGE_CHARACTERISTICS.get(bridge_type, BRIDGE_CHARACTERISTICS[BridgeType.SLAB])


def get_suitable_materials(bridge_type: BridgeType) -> List[MaterialType]:
    """Get list of suitable materials for a bridge type"""
    characteristics = get_bridge_characteristics(bridge_type)
    return characteristics.materials


def validate_span_for_bridge_type(bridge_type: BridgeType, span_length: float) -> bool:
    """Validate if a span length is appropriate for the given bridge type"""
    characteristics = get_bridge_characteristics(bridge_type)
    return characteristics.min_span <= span_length <= characteristics.max_span


def get_recommended_supports(bridge_type: BridgeType, span_length: float) -> int:
    """Get recommended number of supports based on bridge type and span"""
    characteristics = get_bridge_characteristics(bridge_type)

    if span_length <= characteristics.typical_span:
        return characteristics.min_supports
    else:
        # Calculate supports based on span length
        support_spacing = characteristics.typical_span * 0.8
        calculated_supports = max(0, int((span_length - characteristics.typical_span) / support_spacing))
        return min(calculated_supports, characteristics.max_supports)


def get_bridge_type_display_name(bridge_type: BridgeType) -> str:
    """Get user-friendly display name for bridge type"""
    display_names = {
        BridgeType.SLAB: "Slab Bridge",
        BridgeType.BEAM: "Beam Bridge",
        BridgeType.T_BEAM: "T-Beam Bridge",
        BridgeType.BOX_GIRDER: "Box Girder Bridge",
        BridgeType.TRUSS: "Truss Bridge",
        BridgeType.ARCH: "Arch Bridge",
        BridgeType.SUSPENSION: "Suspension Bridge",
        BridgeType.CABLE_STAYED: "Cable-Stayed Bridge"
    }
    return display_names.get(bridge_type, bridge_type.value.title())


def get_output_format_extension(output_format: OutputFormat) -> str:
    """Get file extension for output format"""
    extensions = {
        OutputFormat.DXF: ".dxf",
        OutputFormat.PDF: ".pdf",
        OutputFormat.SVG: ".svg",
        OutputFormat.PNG: ".png",
        OutputFormat.HTML: ".html"
    }
    return extensions.get(output_format, ".dxf")
