"""bridgecad_core.standards — IRC/MORTH engineering standards (M1)."""

from .irc_05 import (
    HydraulicDesignResult,
    compute_hydraulics,
    design_scour_depth,
    freeboard_min,
    lacey_scour_depth,
)
from .irc_21 import (
    StructuralCheckResult,
    check_structural_adequacy,
    classify_span_depth,
    impact_factor,
    span_depth_limits,
)
from .irc_sp55 import (
    dimension_style,
    hatch_for_material,
    lineweight_for_layer,
    preferred_scale,
    sheet_spec,
    text_height,
)
from .morth_specs import TEST_FREQUENCIES, concrete_spec, contract_clause, rebar_spec

__all__ = [
    # IRC:5
    "compute_hydraulics",
    "HydraulicDesignResult",
    "lacey_scour_depth",
    "design_scour_depth",
    "freeboard_min",
    # IRC:21
    "check_structural_adequacy",
    "StructuralCheckResult",
    "span_depth_limits",
    "classify_span_depth",
    "impact_factor",
    # IRC SP:55
    "preferred_scale",
    "text_height",
    "lineweight_for_layer",
    "sheet_spec",
    "hatch_for_material",
    "dimension_style",
    # MORTH
    "concrete_spec",
    "rebar_spec",
    "contract_clause",
    "TEST_FREQUENCIES",
]
