"""bridgecad_ai — AI optimization and estimation (M8)."""
from .optimizer      import BridgeOptimizer, OptimizationResult
from .estimator      import QuantityEstimate, CostEstimate, estimate_quantities, estimate_cost
from .comparator     import ComparisonResult, compare, radar_data
from .param_suggester import SuggestedParams, suggest

__version__ = "0.1.0-rc1"
__all__ = [
    "BridgeOptimizer", "OptimizationResult",
    "QuantityEstimate", "CostEstimate", "estimate_quantities", "estimate_cost",
    "ComparisonResult", "compare", "radar_data",
    "SuggestedParams", "suggest",
]
