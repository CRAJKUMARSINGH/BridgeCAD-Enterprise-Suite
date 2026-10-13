"""
bridgecad_ai.optimizer — scipy SLSQP cost-minimization of span/depth/width.

Finds the span length and girder depth that minimise concrete volume (proxy
for cost) subject to IRC structural, hydraulic, and width constraints.

Usage
-----
    from bridgecad_ai.optimizer import BridgeOptimizer, OptimizationResult
    opt = BridgeOptimizer()
    result = opt.optimize(
        total_length_m=36.0,
        carriageway_width_m=7.5,
        hfl_m=562.0,
        soffit_clearance_m=2.0,
    )
    print(result)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

try:
    from scipy.optimize import minimize, OptimizeResult
    _SCIPY_OK = True
except ImportError:
    _SCIPY_OK = False


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class OptimizationResult:
    success:          bool
    message:          str
    optimal_span_m:   float = 0.0
    optimal_depth_m:  float = 0.0
    optimal_n_spans:  int   = 1
    concrete_vol_cum: float = 0.0
    estimated_cost_inr: float = 0.0
    iterations:       int   = 0
    objective_value:  float = 0.0
    constraint_violations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Cost model helpers
# ---------------------------------------------------------------------------

def _concrete_vol_estimate(
    span_m: float,
    depth_m: float,
    width_m: float,
    n_spans: int,
    girders_per_deck: int = 4,
) -> float:
    """Estimate total concrete volume (CUM) — simplified parametric model.

    Deck slab + girders + substructure (piers + pile caps).
    """
    total_len = span_m * n_spans

    # Deck slab (200 mm average thickness)
    deck_vol = total_len * width_m * 0.20

    # Girders: I-section approximate = 0.12 × depth² × length
    girder_vol = n_spans * span_m * girders_per_deck * 0.12 * depth_m ** 2

    # Piers (n_spans-1): cylindrical shaft h≈8m dia≈1.5m + cap
    n_piers = max(0, n_spans - 1)
    pier_vol = n_piers * (3.14159 * 0.75 ** 2 * 8.0 + 2.0 * width_m * 1.0 * 0.8)

    # Foundations: pile cap 4×piles per support, 2 abutments
    n_supports = n_piers + 2
    found_vol  = n_supports * (4 * 3.14159 * 0.5 ** 2 * 15.0 + width_m * 2.5 * 1.5)

    return deck_vol + girder_vol + pier_vol + found_vol


def _unit_rate_per_cum(span_m: float, depth_m: float) -> float:
    """Blended unit rate INR/CUM increasing with span depth."""
    base = 8500.0   # M30 substructure rate
    if span_m > 30:
        base = 11000.0   # M40 superstructure for longer spans
    if depth_m > 2.0:
        base *= 1.15     # prestressed / more complex formwork
    return base


# ---------------------------------------------------------------------------
# Optimizer
# ---------------------------------------------------------------------------

class BridgeOptimizer:
    """Minimise concrete volume subject to IRC structural constraints."""

    # IRC:21 / IRC:112 span/depth limits
    SPAN_DEPTH_MIN = 10.0   # L/d ≥ 10 (IRC minimum)
    SPAN_DEPTH_MAX = 20.0   # L/d ≤ 20 (practical limit for T-beam)
    SPAN_MIN_M     = 6.0
    SPAN_MAX_M     = 45.0
    DEPTH_MIN_M    = 0.6
    DEPTH_MAX_M    = 3.5

    def optimize(
        self,
        total_length_m:       float,
        carriageway_width_m:  float  = 7.5,
        hfl_m:                float  = 0.0,
        soffit_clearance_m:   float  = 2.0,
        girders_per_deck:     int    = 4,
        max_span_m:           float  = 30.0,
    ) -> OptimizationResult:
        """Find optimal (span_length, girder_depth) for a bridge.

        Parameters
        ----------
        total_length_m : float
            Fixed total bridge length.
        carriageway_width_m : float
            Carriageway width — affects cost scaling.
        hfl_m, soffit_clearance_m : float
            Hydraulic constraint: soffit RL ≥ hfl_m + soffit_clearance_m.
        max_span_m : float
            Maximum allowed individual span length.
        """
        if not _SCIPY_OK:
            return self._heuristic_fallback(total_length_m, max_span_m, carriageway_width_m)

        violations: list[str] = []

        def _objective(x: np.ndarray) -> float:
            span, depth = float(x[0]), float(x[1])
            n = max(1, round(total_length_m / span))
            vol  = _concrete_vol_estimate(span, depth, carriageway_width_m,
                                          n, girders_per_deck)
            rate = _unit_rate_per_cum(span, depth)
            return vol * rate   # minimise estimated cost

        # Constraints — all must be ≥ 0
        def c_span_depth_min(x):  return x[0] / x[1] - self.SPAN_DEPTH_MIN
        def c_span_depth_max(x):  return self.SPAN_DEPTH_MAX - x[0] / x[1]
        def c_span_max(x):        return max_span_m - x[0]
        def c_depth_min(x):       return x[1] - self.DEPTH_MIN_M

        constraints = [
            {"type": "ineq", "fun": c_span_depth_min},
            {"type": "ineq", "fun": c_span_depth_max},
            {"type": "ineq", "fun": c_span_max},
            {"type": "ineq", "fun": c_depth_min},
        ]
        bounds = [
            (self.SPAN_MIN_M, min(self.SPAN_MAX_M, max_span_m)),
            (self.DEPTH_MIN_M, self.DEPTH_MAX_M),
        ]

        # Initial guess: span = total_length/3 capped at max, depth = span/15
        x0_span  = min(max(total_length_m / 3.0, self.SPAN_MIN_M), max_span_m)
        x0_depth = max(x0_span / 15.0, self.DEPTH_MIN_M)
        x0       = np.array([x0_span, x0_depth])

        try:
            res: OptimizeResult = minimize(
                _objective, x0, method="SLSQP",
                bounds=bounds, constraints=constraints,
                options={"maxiter": 200, "ftol": 1e-6},
            )
        except Exception as exc:
            return OptimizationResult(False, f"Optimizer error: {exc}")

        if not res.success:
            # Try heuristic fallback
            return self._heuristic_fallback(total_length_m, max_span_m,
                                             carriageway_width_m,
                                             note=res.message)

        span_opt  = float(res.x[0])
        depth_opt = float(res.x[1])
        n_opt     = max(1, round(total_length_m / span_opt))
        vol_opt   = _concrete_vol_estimate(span_opt, depth_opt,
                                            carriageway_width_m, n_opt)
        cost_opt  = vol_opt * _unit_rate_per_cum(span_opt, depth_opt)

        return OptimizationResult(
            success=True,
            message=f"SLSQP converged in {res.nit} iterations",
            optimal_span_m=round(span_opt, 2),
            optimal_depth_m=round(depth_opt, 3),
            optimal_n_spans=n_opt,
            concrete_vol_cum=round(vol_opt, 1),
            estimated_cost_inr=round(cost_opt, 0),
            iterations=res.nit,
            objective_value=round(float(res.fun), 0),
            constraint_violations=violations,
        )

    def _heuristic_fallback(
        self,
        total_length_m: float,
        max_span_m: float,
        width_m: float,
        note: str = "heuristic",
    ) -> OptimizationResult:
        """IRC-based heuristic when scipy fails / not available."""
        # IRC recommended span/depth ≈ 15 for T-beam
        n_spans = max(1, round(total_length_m / min(max_span_m, 20.0)))
        span    = total_length_m / n_spans
        span    = min(max(span, self.SPAN_MIN_M), max_span_m)
        depth   = round(span / 15.0, 2)
        depth   = min(max(depth, self.DEPTH_MIN_M), self.DEPTH_MAX_M)
        vol     = _concrete_vol_estimate(span, depth, width_m, n_spans)
        rate    = _unit_rate_per_cum(span, depth)
        return OptimizationResult(
            success=True,
            message=f"Heuristic fallback ({note})",
            optimal_span_m=round(span, 2),
            optimal_depth_m=depth,
            optimal_n_spans=n_spans,
            concrete_vol_cum=round(vol, 1),
            estimated_cost_inr=round(vol * rate, 0),
            iterations=0,
        )


__all__ = ["BridgeOptimizer", "OptimizationResult"]
