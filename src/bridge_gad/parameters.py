#!/usr/bin/env python3
"""
Bridge Parameters and Configuration Classes

Defines the parameter structures and validation for bridge design
with support for various input sources (Excel, JSON, manual input).
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from .bridge_types import BridgeType, MaterialType, OutputFormat, validate_span_for_bridge_type

logger = logging.getLogger(__name__)


@dataclass
class BridgeParameters:
    """Main bridge configuration parameters with validation"""

    # Basic geometry (required)
    bridge_type: BridgeType = BridgeType.SLAB
    span_length: float = 30.0  # Total bridge length in meters
    deck_width: float = 8.0    # Deck width in meters

    # Scale and coordinate system
    scale1: float = 100.0      # Plan/elevation scale
    scale2: float = 50.0       # Section scale
    datum: float = 100000.0    # Datum level in mm
    left: float = 0.0          # Left chainage
    right: Optional[float] = None  # Right chainage (calculated if None) — FIX CURSOR-003

    # Structure configuration
    num_spans: int = 1         # Number of spans
    supports: int = 0          # Number of intermediate supports
    skew_angle: float = 0.0    # Skew angle in degrees

    # Material and loading
    material: MaterialType = MaterialType.CONCRETE
    load_capacity: float = 50.0  # Design load in kN/m

    # Structural dimensions (in mm)
    deck_thickness: float = 200.0    # Deck thickness
    girder_depth: float = 800.0      # Girder depth
    foundation_depth: float = 2000.0  # Foundation depth

    # Abutment parameters (in mm)
    abutment_length: float = 1000.0  # Abutment length
    abutment_height: float = 3000.0  # Abutment height

    # Optional advanced parameters
    approach_length: float = 50000.0  # Approach slab length
    rail_height: float = 1200.0       # Rail height
    kerb_width: float = 300.0         # Kerb width

    # Output configuration
    output_formats: List[OutputFormat] = field(default_factory=lambda: [OutputFormat.DXF])
    project_name: str = "Bridge Project"
    drawing_title: str = "General Arrangement Drawing"

    def __post_init__(self):
        """Validate parameters after initialization"""
        self._validate_parameters()
        self._calculate_derived_values()

    def _validate_parameters(self):
        """Comprehensive parameter validation"""
        errors = []

        # Basic geometry validation
        if self.span_length <= 0:
            errors.append("Span length must be positive")

        if self.deck_width <= 0:
            errors.append("Deck width must be positive")

        # Bridge type specific validation
        if not validate_span_for_bridge_type(self.bridge_type, self.span_length):
            from .bridge_types import get_bridge_characteristics
            chars = get_bridge_characteristics(self.bridge_type)
            errors.append(f"Span length {self.span_length}m is not suitable for {self.bridge_type.value} "
                          f"(recommended range: {chars.min_span}-{chars.max_span}m)")

        # Scale validation
        if self.scale1 <= 0 or self.scale2 <= 0:
            errors.append("Scales must be positive")

        # Support validation
        if self.supports < 0:
            errors.append("Number of supports cannot be negative")

        # Angle validation
        if not -45 <= self.skew_angle <= 45:
            errors.append("Skew angle should be between -45 and 45 degrees")

        # Thickness validation
        if self.deck_thickness <= 0:
            errors.append("Deck thickness must be positive")

        # Load validation
        if self.load_capacity <= 0:
            errors.append("Load capacity must be positive")

        if errors:
            error_message = "Parameter validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_message)
            raise ValueError(error_message)

        logger.info("Bridge parameters validated successfully")

    def _calculate_derived_values(self):
        """Calculate derived values from input parameters"""
        # Calculate right chainage if not provided
        if self.right is None:
            self.right = self.left + self.span_length

        # Ensure num_spans is consistent with supports
        if self.supports > 0 and self.num_spans == 1:
            self.num_spans = self.supports + 1

        logger.info(f"Calculated derived values: right={self.right}, num_spans={self.num_spans}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary for serialization"""
        return {
            'bridge_type': self.bridge_type.value,
            'span_length': self.span_length,
            'deck_width': self.deck_width,
            'scale1': self.scale1,
            'scale2': self.scale2,
            'datum': self.datum,
            'left': self.left,
            'right': self.right,
            'num_spans': self.num_spans,
            'supports': self.supports,
            'skew_angle': self.skew_angle,
            'material': self.material.value,
            'load_capacity': self.load_capacity,
            'deck_thickness': self.deck_thickness,
            'girder_depth': self.girder_depth,
            'foundation_depth': self.foundation_depth,
            'abutment_length': self.abutment_length,
            'abutment_height': self.abutment_height,
            'approach_length': self.approach_length,
            'rail_height': self.rail_height,
            'kerb_width': self.kerb_width,
            'output_formats': [fmt.value for fmt in self.output_formats],
            'project_name': self.project_name,
            'drawing_title': self.drawing_title
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BridgeParameters':
        """Create parameters from dictionary"""
        # Convert enum strings back to enums
        if 'bridge_type' in data:
            data['bridge_type'] = BridgeType(data['bridge_type'])
        if 'material' in data:
            data['material'] = MaterialType(data['material'])
        if 'output_formats' in data:
            data['output_formats'] = [OutputFormat(fmt) for fmt in data['output_formats']]

        return cls(**data)

    def get_coordinate_transformations(self):
        """Get coordinate transformation functions matching original LISP functions"""
        import math

        # Calculate scaling factors
        sc = self.scale1 / self.scale2 if self.scale2 != 0 else 1
        vvs = 1000.0  # Vertical visual scale
        hhs = 1000.0  # Horizontal visual scale

        # Skew calculations
        skew_rad = math.radians(self.skew_angle)
        s = math.sin(skew_rad)
        c = math.cos(skew_rad)
        tn = s / c if c != 0 else 0

        def vpos(a):
            """Vertical position transformation (matches LISP vpos)"""
            return self.datum + vvs * (a - self.datum)

        def hpos(a):
            """Horizontal position transformation (matches LISP hpos)"""
            return self.left + hhs * (a - self.left)

        def v2pos(a):
            """Scaled vertical position (matches LISP v2pos)"""
            return self.datum + sc * vvs * (a - self.datum)

        def h2pos(a):
            """Scaled horizontal position (matches LISP h2pos)"""
            return self.left + sc * hhs * (a - self.left)

        return {
            'vpos': vpos,
            'hpos': hpos,
            'v2pos': v2pos,
            'h2pos': h2pos,
            'sc': sc,
            'skew_rad': skew_rad,
            's': s,
            'c': c,
            'tn': tn
        }


@dataclass
class DrawingConfiguration:
    """Configuration for drawing appearance and output"""

    # Drawing appearance
    line_width: float = 2.0
    annotation_fontsize: float = 10.0
    title_fontsize: float = 14.0
    dimension_fontsize: float = 8.0

    # Colors (as hex strings)
    structure_color: str = "#000000"  # Black
    deck_color: str = "#808080"       # Gray
    supports_color: str = "#000080"   # Dark blue
    foundations_color: str = "#8B4513"  # Brown
    dimensions_color: str = "#FF0000"  # Red
    annotations_color: str = "#0000FF"  # Blue

    # Page settings
    page_size: str = "A3"  # A3, A4, etc.
    orientation: str = "landscape"  # landscape, portrait

    # Grid settings
    show_grid: bool = True
    grid_spacing: float = 1000.0  # Grid spacing in mm

    def get_color_scheme(self) -> Dict[str, str]:
        """Get complete color scheme as dictionary"""
        return {
            'structure': self.structure_color,
            'deck': self.deck_color,
            'supports': self.supports_color,
            'foundations': self.foundations_color,
            'dimensions': self.dimensions_color,
            'annotations': self.annotations_color
        }


def create_default_parameters() -> BridgeParameters:
    """Create default bridge parameters for fallback scenarios"""
    return BridgeParameters(
        bridge_type=BridgeType.SLAB,
        span_length=30.0,
        deck_width=8.0,
        scale1=100.0,
        scale2=50.0,
        datum=100000.0,
        left=0.0,
        num_spans=1,
        supports=0,
        material=MaterialType.CONCRETE,
        project_name="Default Bridge Project",
        drawing_title="Slab Bridge - General Arrangement"
    )


def validate_parameter_ranges(params: BridgeParameters) -> List[str]:
    """Validate parameter ranges and return warnings (non-critical issues)"""
    warnings = []

    # Engineering practice warnings
    if params.span_length > 50 and params.bridge_type == BridgeType.SLAB:
        warnings.append("Slab bridges over 50m span may need special consideration")

    if params.deck_width < 3.0:
        warnings.append("Deck width less than 3m may be too narrow for traffic")

    if params.skew_angle > 20:
        warnings.append("Large skew angles may complicate construction")

    if params.load_capacity > 100:
        warnings.append("Very high load capacity may require special analysis")

    return warnings
