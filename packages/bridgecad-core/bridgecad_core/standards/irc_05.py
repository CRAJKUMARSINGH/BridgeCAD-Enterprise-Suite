"""
bridgecad_core.standards.irc_05 — IRC:5-2015 Hydraulic Design Formulas.

Implements:
  - Lacey's Regime equations (IRC:5 Clause 24)
  - Design scour depth (IRC:78 Clause 7)
  - Afflux estimation
  - Waterway adequacy check
  - Freeboard requirements (IRC:5 / NHAI / MORTH)
  - Linear waterway formula (IRC:5 Clause 17)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Lacey's Regime Method (IRC:5-2015 Clause 24)
# ---------------------------------------------------------------------------


def lacey_silt_factor(d50_mm: float) -> float:
    """Lacey's silt factor f = 1.76 × √(d50_mm).

    Parameters
    ----------
    d50_mm : float  Median grain diameter in mm.

    Returns
    -------
    float  Silt factor f (dimensionless, typically 0.5–4.0)

    Reference
    ---------
    IRC:5-2015 Clause 24.1
    """
    if d50_mm <= 0:
        return 1.0
    return 1.76 * math.sqrt(d50_mm)


def lacey_regime_velocity(f: float, R: float) -> float:
    """Mean velocity V = 10.8 × R^(2/3) × S^(1/3)  — simplified form.

    Using V = K × f^(1/3) × R^(2/3) where K ≈ 0.44 (Lacey 1929):
    V = 0.44 × f^(1/3) × R^(2/3)

    Parameters
    ----------
    f : float  Lacey silt factor.
    R : float  Hydraulic radius (depth for wide channel), metres.

    Returns
    -------
    float  Mean velocity m/s.

    Reference : IRC:5-2015 Cl.24.1
    """
    if f <= 0 or R <= 0:
        return 0.0
    return float(0.44 * (f ** (1.0 / 3.0)) * (R ** (2.0 / 3.0)))


def lacey_regime_depth(Q: float, f: float) -> float:
    """Hydraulic mean depth D = 0.477 × (Q/f²)^(1/3).

    Parameters
    ----------
    Q : float  Design discharge m³/s.
    f : float  Lacey silt factor.

    Returns
    -------
    float  Regime hydraulic mean depth (m).

    Reference : IRC:5-2015 Cl.24.2  R = 0.477 × (Q/f²)^(1/3)
    """
    if Q <= 0 or f <= 0:
        return 0.0
    return float(0.477 * ((Q / (f**2)) ** (1.0 / 3.0)))


def lacey_regime_slope(f: float, Q: float) -> float:
    """Regime slope S = f^(5/3) / (3340 × Q^(1/6)).

    Parameters
    ----------
    f : float  Lacey silt factor.
    Q : float  Design discharge m³/s.

    Returns
    -------
    float  Regime longitudinal slope (dimensionless).

    Reference : IRC:5-2015 Cl.24.3
    """
    if f <= 0 or Q <= 0:
        return 0.0
    return float((f ** (5.0 / 3.0)) / (3340.0 * (Q ** (1.0 / 6.0))))


def lacey_regime_perimeter(Q: float) -> float:
    """Wetted perimeter P = 4.75 × √Q.

    Parameters
    ----------
    Q : float  Design discharge m³/s.

    Returns
    -------
    float  Regime wetted perimeter (m).

    Reference : IRC:5-2015 Cl.24.4
    """
    if Q <= 0:
        return 0.0
    return 4.75 * math.sqrt(Q)


def lacey_scour_depth(Q: float, f: float) -> float:
    """Normal scour depth (Lacey's) D_s = 1.34 × (q²/f)^(1/3).

    q = Q / L_w (discharge intensity per metre of waterway).
    Simplified to use regime depth:  D_s = 1.34 × R.

    Parameters
    ----------
    Q : float  Design discharge m³/s.
    f : float  Lacey silt factor.

    Returns
    -------
    float  Normal scour depth D_s below HFL (m).

    Reference : IRC:78-2014 Clause 7.2 / IRC:5-2015 Cl.24.6
    """
    R = lacey_regime_depth(Q, f)
    return 1.34 * R


def design_scour_depth(
    Q: float,
    f: float,
    structure_type: str = "PIER",
    regime_method: bool = True,
    q_per_m: float | None = None,
) -> float:
    """IRC design scour depth with multiplier for structure type.

    IRC:78-2014 Table 3 multipliers:
      Pier (general)   → 2.0 × D_s
      Abutment         → 1.27 × D_s
      Guide bund nose  → 2.75 × D_s
      Guide bund body  → 1.5  × D_s

    Parameters
    ----------
    Q : float    Design discharge m³/s.
    f : float    Lacey silt factor.
    structure_type : str   "PIER" | "ABUTMENT" | "GUIDE_BUND_NOSE" | "GUIDE_BUND_BODY"
    regime_method : bool   Use Lacey regime method (True) vs rational formula.
    q_per_m : float | None  Discharge per metre width (for rational method).

    Returns
    -------
    float  Design scour depth below HFL (m).

    Reference : IRC:78-2014 Clause 7.3
    """
    MULT = {
        "PIER": 2.00,
        "ABUTMENT": 1.27,
        "GUIDE_BUND_NOSE": 2.75,
        "GUIDE_BUND_BODY": 1.50,
    }
    mult = MULT.get(structure_type.upper(), 2.00)

    if regime_method or q_per_m is None:
        D_s = lacey_scour_depth(Q, f)
    else:
        # Rational: D_s = 1.34 × (q²/f)^(1/3)
        D_s = 1.34 * ((q_per_m**2 / max(f, 0.01)) ** (1.0 / 3.0)) if q_per_m > 0 else 0.0

    return mult * D_s


def linear_waterway(Q: float) -> float:
    """Linear waterway L_w = C × √Q   where C = 4.8 for natural channels.

    Parameters
    ----------
    Q : float  Design discharge m³/s.

    Returns
    -------
    float  Linear waterway (m).

    Reference : IRC:5-2015 Clause 17  (C=4.8 natural, C=6.3 artificial canal)
    """
    if Q <= 0:
        return 0.0
    return 4.8 * math.sqrt(Q)


def afflux(
    Q: float,
    A_nat: float,
    A_bridge: float,
    V_nat: float,
) -> float:
    """Approximate afflux using Yarnell / energy balance approach.

    Δh ≈ V_approach² / (2g) × [(A_nat/A_bridge)² − 1]

    Parameters
    ----------
    Q : float         Design discharge m³/s.
    A_nat : float     Natural channel area (m²) at HFL.
    A_bridge : float  Bridge waterway opening area (m²).
    V_nat : float     Natural flood velocity (m/s) — Q / A_nat.

    Returns
    -------
    float  Afflux Δh (m).

    Reference : IRC:5-2015 Clause 21 (simplified energy balance)
    """
    g = 9.81
    if A_bridge <= 0 or A_nat <= 0 or V_nat <= 0:
        return 0.0
    ratio = A_nat / A_bridge
    return (V_nat**2 / (2.0 * g)) * (ratio**2 - 1.0)


def freeboard_min(
    structure_class: str = "MAJOR",
    hfl_m: float = 0.0,
    soffit_m: float = 0.0,
) -> float:
    """Minimum freeboard requirements per IRC:5-2015 / NHAI/MORTH norms.

    Parameters
    ----------
    structure_class : str  "MAJOR" | "MINOR" | "CULVERT" | "NHAI" | "EXPRESSWAY"
    hfl_m : float          HFL reduced level (m) — for verification.
    soffit_m : float       Deck soffit RL (m) — for verification.

    Returns
    -------
    float  Minimum freeboard (m).

    Reference
    ---------
    IRC:5-2015 Cl.22  |  MORTH 5th Rev Cl.704  |  NHAI Guidelines 2019
    """
    FB_MIN = {
        "MAJOR": 1.00,  # IRC:5-2015 Cl.22.1 major bridge
        "MINOR": 0.60,  # IRC:5-2015 Cl.22.2 minor bridge
        "CULVERT": 0.30,  # IRC SP:13
        "NHAI": 2.00,  # NHAI National corridor standard
        "EXPRESSWAY": 2.00,  # Access-controlled expressway
        "STATE_HWY": 1.50,  # State highway typical
        "PMGSY": 0.60,  # PMGSY rural connectivity
    }
    return FB_MIN.get(structure_class.upper(), 1.00)


# ---------------------------------------------------------------------------
# Composite result dataclass
# ---------------------------------------------------------------------------


@dataclass
class HydraulicDesignResult:
    """Summary of IRC:5 hydraulic calculations for a bridge site."""

    Q_design_cumecs: float
    lacey_f: float
    regime_depth_m: float
    regime_velocity_mps: float
    regime_perimeter_m: float
    regime_slope: float
    linear_waterway_m: float
    normal_scour_m: float
    design_scour_pier_m: float
    design_scour_abut_m: float
    afflux_m: float
    freeboard_required_m: float


def compute_hydraulics(
    Q: float,
    f: float,
    A_nat: float = 0.0,
    A_bridge: float = 0.0,
    structure_class: str = "MAJOR",
) -> HydraulicDesignResult:
    """Run all IRC:5 hydraulic calculations for a given discharge and site.

    Parameters
    ----------
    Q : float          Design discharge (m³/s).
    f : float          Lacey silt factor.
    A_nat : float      Natural channel area at HFL (m²) — for afflux.
    A_bridge : float   Bridge waterway opening (m²) — for afflux.
    structure_class : str  For freeboard selection.

    Returns
    -------
    HydraulicDesignResult
    """
    R = lacey_regime_depth(Q, f)
    V = lacey_regime_velocity(f, R)
    P = lacey_regime_perimeter(Q)
    S = lacey_regime_slope(f, Q)
    Lw = linear_waterway(Q)
    Ds = lacey_scour_depth(Q, f)
    Dp = design_scour_depth(Q, f, "PIER")
    Da = design_scour_depth(Q, f, "ABUTMENT")
    V_nat = (Q / A_nat) if A_nat > 0 else V
    Ah = afflux(Q, A_nat if A_nat > 0 else P * R, A_bridge if A_bridge > 0 else Lw * R, V_nat)
    fb = freeboard_min(structure_class)
    return HydraulicDesignResult(
        Q_design_cumecs=Q,
        lacey_f=round(f, 3),
        regime_depth_m=round(R, 3),
        regime_velocity_mps=round(V, 3),
        regime_perimeter_m=round(P, 2),
        regime_slope=round(S, 8),
        linear_waterway_m=round(Lw, 1),
        normal_scour_m=round(Ds, 3),
        design_scour_pier_m=round(Dp, 3),
        design_scour_abut_m=round(Da, 3),
        afflux_m=round(Ah, 3),
        freeboard_required_m=fb,
    )


__all__ = [
    "lacey_silt_factor",
    "lacey_regime_velocity",
    "lacey_regime_depth",
    "lacey_regime_slope",
    "lacey_regime_perimeter",
    "lacey_scour_depth",
    "design_scour_depth",
    "linear_waterway",
    "afflux",
    "freeboard_min",
    "HydraulicDesignResult",
    "compute_hydraulics",
]
