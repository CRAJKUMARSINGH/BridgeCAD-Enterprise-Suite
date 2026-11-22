"""bridgecad_ai — AI optimization, estimation and drawing review (M8)."""

from .comparator import ComparisonResult, compare, radar_data
from .drawing_review import (
    AIReviewError,
    CheckItem,
    DrawingFacts,
    extract_facts,
    review,
    to_markdown,
)
from .estimator import CostEstimate, QuantityEstimate, estimate_cost, estimate_quantities
from .optimizer import BridgeOptimizer, OptimizationResult
from .param_suggester import SuggestedParams, suggest

__version__ = "0.1.0-rc1"
__all__ = [
    "BridgeOptimizer",
    "OptimizationResult",
    "QuantityEstimate",
    "CostEstimate",
    "estimate_quantities",
    "estimate_cost",
    "ComparisonResult",
    "compare",
    "radar_data",
    "SuggestedParams",
    "suggest",
    # Drawing review
    "CheckItem",
    "DrawingFacts",
    "extract_facts",
    "review",
    "to_markdown",
    "AIReviewError",
]
