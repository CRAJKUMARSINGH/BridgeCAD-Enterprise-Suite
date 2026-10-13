"""
bridgecad_ai.comparator — Side-by-side bridge design comparison.

Compares two BridgeProject instances across 6 dimensions and produces:
  - Percentage diff table
  - Radar chart data (for plotting with matplotlib / plotly)
  - Plain-text summary
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ComparisonResult:
    """Side-by-side comparison of two bridge designs."""
    label_a:    str
    label_b:    str
    dimensions: list[str]
    values_a:   list[float]
    values_b:   list[float]
    pct_diff:   list[float]    # (B-A)/A × 100
    summary:    str

    def better(self, dim: str) -> str:
        """Return 'A' or 'B' for the dimension with lower value (cost/vol) or 'equal'."""
        if dim not in self.dimensions:
            return "unknown"
        i  = self.dimensions.index(dim)
        va = self.values_a[i]
        vb = self.values_b[i]
        if abs(va - vb) < 0.01 * max(abs(va), abs(vb), 1):
            return "equal"
        return "A" if va < vb else "B"


# Standard comparison dimensions
_DIMS = [
    "total_length_m",
    "overall_width_m",
    "concrete_vol_approx_cum",
    "rebar_mt",
    "span_depth_ratio",
    "estimated_cost_inr_M",    # in crores/millions for readability
]


def _extract_metrics(project: Any) -> list[float]:
    """Pull comparison metrics from a BridgeProject."""
    gi   = project.geometry_input
    calc = project.calculations
    ss   = project.superstructure

    total_len   = float(gi.total_length_m)
    overall_w   = float(gi.overall_width_m)
    conc_total  = sum([
        float(getattr(calc, "concrete_volume_superstructure_cum", 0) or 0),
        float(getattr(calc, "concrete_volume_substructure_cum",   0) or 0),
        float(getattr(calc, "concrete_volume_foundation_cum",     0) or 0),
    ])
    rebar       = float(getattr(calc, "rebar_weight_tonnes_approx", 0) or 0)
    girder_d_m  = float(getattr(ss, "girder_depth_mm", 900) or 900) / 1000.0
    span_d      = (total_len / girder_d_m) if girder_d_m > 0 else 0.0
    cost_m      = float(getattr(calc, "total_estimated_quantity_cost_inr", 0) or 0) / 1e7

    return [total_len, overall_w, conc_total, rebar, span_d, cost_m]


def compare(
    project_a: Any,
    project_b: Any,
    label_a: str = "Option A",
    label_b: str = "Option B",
) -> ComparisonResult:
    """Compare two BridgeProject instances.

    Returns
    -------
    ComparisonResult
        Includes values, pct_diff, and summary string.
    """
    va = _extract_metrics(project_a)
    vb = _extract_metrics(project_b)

    pct_diff = []
    for a, b in zip(va, vb):
        if abs(a) < 1e-9:
            pct_diff.append(0.0)
        else:
            pct_diff.append(round((b - a) / a * 100.0, 1))

    # Summary narrative
    cost_dim = _DIMS.index("estimated_cost_inr_M")
    conc_dim = _DIMS.index("concrete_vol_approx_cum")
    cheaper  = label_a if va[cost_dim] <= vb[cost_dim] else label_b
    lighter  = label_a if va[conc_dim] <= vb[conc_dim] else label_b

    summary = (
        f"Comparison: {label_a} vs {label_b}\n"
        f"  Lower cost         : {cheaper}  "
        f"(A=₹{va[cost_dim]:.2f}Cr  B=₹{vb[cost_dim]:.2f}Cr"
        f"  Δ={pct_diff[cost_dim]:+.1f}%)\n"
        f"  Less concrete      : {lighter}  "
        f"(A={va[conc_dim]:.0f}m³  B={vb[conc_dim]:.0f}m³"
        f"  Δ={pct_diff[conc_dim]:+.1f}%)\n"
        f"  Rebar Δ            : {pct_diff[_DIMS.index('rebar_mt')]:+.1f}%\n"
        f"  Overall width Δ    : {pct_diff[_DIMS.index('overall_width_m')]:+.1f}%\n"
    )

    return ComparisonResult(
        label_a=label_a, label_b=label_b,
        dimensions=_DIMS,
        values_a=[round(v, 3) for v in va],
        values_b=[round(v, 3) for v in vb],
        pct_diff=pct_diff,
        summary=summary,
    )


def radar_data(result: ComparisonResult) -> dict:
    """Return radar chart data dict compatible with matplotlib / Plotly."""
    # Normalise both datasets to 0–1 scale per dimension
    import math
    normed_a, normed_b = [], []
    for a, b in zip(result.values_a, result.values_b):
        mx = max(abs(a), abs(b), 1e-9)
        normed_a.append(round(a / mx, 3))
        normed_b.append(round(b / mx, 3))
    return {
        "dimensions": result.dimensions,
        "label_a":    result.label_a,
        "label_b":    result.label_b,
        "values_a":   normed_a,
        "values_b":   normed_b,
        "raw_a":      result.values_a,
        "raw_b":      result.values_b,
        "pct_diff":   result.pct_diff,
    }


__all__ = ["ComparisonResult", "compare", "radar_data"]
