"""bridgecad_core.geometry — pure-Python geometry subpackage (M1 Week 1 Day 4)."""

from .abutment import WingWall, resolve_abtl, wing_wall_geometry
from .cross_section import CrossSectionGeometry, compute_cross_section_geometry
from .foundation import PileGroupLayout, compute_pile_group_layout
from .long_section import (
    LongSectionGeometry,
    compute_long_section_geometry,
    pier_positions,
    span_boundaries,
    span_lengths_m,
)
from .plan import BridgePlanGeometry, compute_plan_geometry

__all__ = [
    "BridgePlanGeometry", "compute_plan_geometry",
    "LongSectionGeometry", "compute_long_section_geometry",
    "span_lengths_m", "span_boundaries", "pier_positions",
    "CrossSectionGeometry", "compute_cross_section_geometry",
    "PileGroupLayout", "compute_pile_group_layout",
    "WingWall", "resolve_abtl", "wing_wall_geometry",
]
