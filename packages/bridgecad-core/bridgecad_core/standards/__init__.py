"""bridgecad_core.standards — IRC/MORTH engineering standards (M1)."""
from .irc_05    import compute_hydraulics, HydraulicDesignResult, lacey_scour_depth, design_scour_depth, freeboard_min
from .irc_21    import check_structural_adequacy, StructuralCheckResult, span_depth_limits, impact_factor
from .irc_sp55  import preferred_scale, text_height, lineweight_for_layer, sheet_spec, hatch_for_material, dimension_style
from .morth_specs import concrete_spec, rebar_spec, contract_clause, TEST_FREQUENCIES

__all__ = [
    # IRC:5
    "compute_hydraulics", "HydraulicDesignResult",
    "lacey_scour_depth", "design_scour_depth", "freeboard_min",
    # IRC:21
    "check_structural_adequacy", "StructuralCheckResult",
    "span_depth_limits", "impact_factor",
    # IRC SP:55
    "preferred_scale", "text_height", "lineweight_for_layer",
    "sheet_spec", "hatch_for_material", "dimension_style",
    # MORTH
    "concrete_spec", "rebar_spec", "contract_clause", "TEST_FREQUENCIES",
]
