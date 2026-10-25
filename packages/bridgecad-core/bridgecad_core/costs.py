"""
bridgecad_core.costs — Unit-rate cost estimator (uses MORTH + PWD rates chain).
M0 scaffold. Implementation: M5 (full rates YAML DB live in standards/).
"""

from __future__ import annotations

from .quantities import BillOfQuantities


class RateLookup:
    """Rate DB lookup with State-PWD override chain. M0 stub."""

    # Stub: the real chain consumes ``code`` and ``region``, but freezes the
    # signature now so callers do not have to change when M5 lands.
    def get(self, code: str, region: str | None = None) -> float | None:  # noqa: ARG002  # pragma: no cover
        return None


def compute_cost(bom: BillOfQuantities, rates: RateLookup | None = None) -> BillOfQuantities:
    """Multiply each item by its unit rate, sum totals. M0: no-ops total_cost."""
    r = rates or RateLookup()
    total = 0.0
    for item in bom.items:
        rate = r.get(item.code)
        if rate is not None:
            item.rate = rate
            item.amount = rate * item.qty
            total += item.amount
    bom.total_cost = total
    return bom


__all__ = ["RateLookup", "compute_cost"]
