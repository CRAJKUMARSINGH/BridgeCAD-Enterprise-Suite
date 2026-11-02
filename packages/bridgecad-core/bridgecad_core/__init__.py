"""
BridgeCAD Enterprise — Core Domain Package.

M0 scaffold: module files exist but implementation is scheduled for M1.
Submodules:
  - types: 200+ enums (bridge category, superstructure, pier, foundation, materials, ...)
  - models: Pydantic V2 aggregate BridgeProject (14 sheets mapped)
  - geometry.{plan, long_section, cross_section, foundation}: pure math
  - standards.{irc_sp55, irc_05, irc_21, morth_specs}
  - validation: 150 check_*() functions
  - quantities: concrete/steel BOM extractor
  - costs: unit-rate cost estimator
"""

from . import (
    costs,
    geometry,
    models,
    quantities,
    standards,
    types,
    validation,
    validation_registry,
)
from .geometry import (
    BridgePlanGeometry,
    CrossSectionGeometry,
    LongSectionGeometry,
    PileGroupLayout,
    compute_cross_section_geometry,
    compute_long_section_geometry,
    compute_pile_group_layout,
    compute_plan_geometry,
)
from .models import BridgeProject, ProjectMaster, ValidationModel
from .standards import (  # hydraulic, structural, combination and drawing rules
    Envelope,
    HydraulicDesignResult,
    LoadCombination,
    StructuralCheckResult,
    check_structural_adequacy,
    combinations_for,
    compute_hydraulics,
    design_scour_depth,
    dimension_style,
    envelope,
    freeboard_min,
    hatch_for_material,
    impact_factor,
    irc6_combinations,
    lineweight_for_layer,
    preferred_scale,
    text_height,
)
from .types import (  # re-export frequently used types at top level
    AbutmentType,
    BearingType,
    BridgeCategory,
    BridgeSelectionCriterion,
    ConcreteGrade,
    ExpansionJointType,
    FoundationType,
    PierType,
    SteelGrade,
    SuperstructureType,
)

__version__ = "0.1.0-rc1"
__all__ = [
    "types",
    "models",
    "validation",
    "quantities",
    "costs",
    "geometry",
    "standards",
    "validation_registry",
    # top-level type shortcuts (Day 4 exports)
    "BridgeCategory",
    "BridgeSelectionCriterion",
    "BearingType",
    "ExpansionJointType",
    "SuperstructureType",
    "PierType",
    "AbutmentType",
    "FoundationType",
    "ConcreteGrade",
    "SteelGrade",
    "BridgeProject",
    "ValidationModel",
    "ProjectMaster",
    "BridgePlanGeometry",
    "compute_plan_geometry",
    "LongSectionGeometry",
    "compute_long_section_geometry",
    "CrossSectionGeometry",
    "compute_cross_section_geometry",
    "PileGroupLayout",
    "compute_pile_group_layout",
    "preferred_scale",
    "text_height",
    "lineweight_for_layer",
    "hatch_for_material",
    "dimension_style",
    # IRC:5 hydraulics
    "compute_hydraulics",
    "HydraulicDesignResult",
    "design_scour_depth",
    "freeboard_min",
    # IRC:21 / IRC:112 structural
    "check_structural_adequacy",
    "StructuralCheckResult",
    "impact_factor",
    # IRC:6 / EN 1990 combinations
    "irc6_combinations",
    "combinations_for",
    "Envelope",
    "envelope",
    "LoadCombination",
]
