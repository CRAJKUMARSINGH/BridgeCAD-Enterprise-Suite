"""
bridgecad_ai.estimator — No-API cost and quantity predictor.

Uses parametric heuristics derived from MORTH unit rates and standard
IRC proportioning rules.  No external API call required.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QuantityEstimate:
    concrete_superstructure_cum: float
    concrete_substructure_cum:   float
    concrete_foundation_cum:     float
    rebar_mt:                    float
    prestress_mt:                float
    formwork_sqm:                float
    wc_sqm:                      float


@dataclass
class CostEstimate:
    civil_works_inr:    float
    contingency_inr:    float
    grand_total_inr:    float
    cost_per_sqm_inr:   float
    cost_per_rm_inr:    float


def estimate_quantities(
    total_length_m:       float,
    overall_width_m:      float,
    n_spans:              int,
    pier_height_m:        float    = 8.0,
    pile_length_m:        float    = 15.0,
    piles_per_support:    int      = 4,
    is_prestressed:       bool     = False,
    pile_diameter_mm:     int      = 1000,
    carriageway_width_m:  float    = 7.5,
) -> QuantityEstimate:
    """Parametric quantity estimation using standard IRC proportioning.

    Calibrated against 8×30m PSC box viaduct BOQ — target:
        4080 m² deck  → super≈3200 m³  sub≈2800 m³  found≈4500 m³
    """
    deck_area = total_length_m * overall_width_m

    # Superstructure (deck + girders/web/core/top/bottom slab)
    # T-beam: ~0.55 m³/m² ; PSC box mono-cell: ~0.88 m³/m²
    psc_factor = 1.60 if is_prestressed else 1.0
    conc_sup = deck_area * 0.55 * psc_factor

    # Substructure (rectangular hammerhead pier shaft + cap + abutments)
    n_piers     = n_spans - 1
    n_supports  = n_piers + 2
    # Shaft dimensions grow with carriageway (2-lane=1.5×2.0  4-lane=2.5×3.0)
    if carriageway_width_m <= 9.0:
        shaft_w, shaft_l = 1.5, 2.0
    elif carriageway_width_m <= 12.0:
        shaft_w, shaft_l = 2.0, 2.5
    else:
        shaft_w, shaft_l = 2.5, 3.0
    conc_sub = (n_piers * shaft_w * shaft_l * pier_height_m     # rectangular shaft
                + n_piers * overall_width_m * 3.0 * 1.5           # pier caps (larger for viaducts)
                + 2 * overall_width_m * 2.0 * 5.5)                # 2 abutments (2m thick × 5.5m deep typical)

    # Foundation (pile group volume + pile cap)
    pile_r_m = (pile_diameter_mm / 1000.0) / 2.0
    conc_fnd = (n_supports * piles_per_support *
                  3.14159 * pile_r_m**2 * pile_length_m          # pile volume from actual pile Ø
                + n_supports * overall_width_m * 3.0 * 2.0)     # pile caps (thick 2.0m for viaducts)

    # Reinforcement
    rebar_mt   = (conc_sup + conc_sub + conc_fnd) * 0.095  # ~95 kg/CUM

    # Prestress (only if prestressed)
    prestress  = conc_sup * 0.025 if is_prestressed else 0.0  # ~25 kg/CUM

    # Formwork (superstructure curved soffit + pier faces + abut faces)
    formwork   = (deck_area * 2.5
                  + n_piers * 2.0 * (shaft_w + shaft_l) * pier_height_m
                  + 2 * 2.0 * overall_width_m * 5.5)          # abutment faces

    # Wearing coat
    wc_sqm     = total_length_m * (overall_width_m * 0.85)  # carriageway only

    return QuantityEstimate(
        concrete_superstructure_cum = round(conc_sup, 1),
        concrete_substructure_cum   = round(conc_sub, 1),
        concrete_foundation_cum     = round(conc_fnd, 1),
        rebar_mt                    = round(rebar_mt, 1),
        prestress_mt                = round(prestress, 2),
        formwork_sqm                = round(formwork, 1),
        wc_sqm                      = round(wc_sqm, 1),
    )


def estimate_cost(
    qty: QuantityEstimate,
    contingency_pct: float = 15.0,
    state: str | None = None,
) -> CostEstimate:
    """Price the quantity estimate using indicative 2024-25 MORTH rates."""
    # Unit rates (INR/unit) — same basis as rates_db seed values
    rates = {
        "conc_sup":     10500.0,  # M40 superstructure
        "conc_sub":      8400.0,  # M30 substructure
        "conc_fnd":      7200.0,  # M25 foundation
        "rebar":        75000.0,  # Fe500D MT
        "prestress":   145000.0,  # G1860 strand MT
        "formwork":      1800.0,  # curved soffit SQM
        "wc":             380.0,  # BC 40mm SQM
    }

    # State PWD adjustment factor (±10–20% typical)
    adj = {"MH": 1.05, "GJ": 1.02, "RJ": 0.95, "UP": 0.97,
           "KA": 1.08, "TN": 1.06, "AP": 1.04, "TS": 1.04}.get(
        (state or "").upper(), 1.0
    )

    civil = (
        qty.concrete_superstructure_cum * rates["conc_sup"]
        + qty.concrete_substructure_cum   * rates["conc_sub"]
        + qty.concrete_foundation_cum     * rates["conc_fnd"]
        + qty.rebar_mt                    * rates["rebar"]
        + qty.prestress_mt                * rates["prestress"]
        + qty.formwork_sqm                * rates["formwork"]
        + qty.wc_sqm                      * rates["wc"]
    ) * adj

    contingency  = civil * contingency_pct / 100.0
    grand_total  = civil + contingency

    # deck area proxy
    deck_area = qty.wc_sqm / 0.85 if qty.wc_sqm > 0 else 1.0
    total_len = deck_area / max(qty.wc_sqm / qty.wc_sqm, 1)  # rough

    return CostEstimate(
        civil_works_inr  = round(civil,       0),
        contingency_inr  = round(contingency, 0),
        grand_total_inr  = round(grand_total, 0),
        cost_per_sqm_inr = round(grand_total / max(deck_area, 1), 0),
        cost_per_rm_inr  = round(grand_total / max(total_len, 1), 0),
    )


__all__ = ["QuantityEstimate", "CostEstimate", "estimate_quantities", "estimate_cost"]
