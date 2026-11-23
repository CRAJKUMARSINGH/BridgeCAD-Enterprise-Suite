"""bridgecad_core.geometry.superstructure_profiles — accurate component geometry
for solid slab, RCC T-beam and PSC I-girder decks.

This module gives the drawing generators *real* component shapes and dimension
sets in the way established Indian bridge-drafting practice produces them, instead
of generic rectangles:

  - solid slab   : deck slab with cantilever/haunch definition, thickness derived
                   from span when the workbook leaves it blank
  - RCC T-beam   : stem + monolithic top slab + haunches, girder depth/spacing
                   derived from span, diaphragm (cross-girder) stations
  - PSC I-girder : true I-section (top flange / web / bottom flange) with
                   fillets, girder depth/spacing derived from span, diaphragm
                   stations, per-girder bearing positions

All returned coordinates are in millimetres in a LOCAL girder coordinate system
(origin at top-centre of the section, X transverse, Y positive DOWN), ready for
the sheet renderer to translate onto the deck.  Deck-level placement (spacing,
overhangs, levels) stays with the sheet module — this module owns the section
shapes and the standard dimension derivations.

Every derived default is tagged ``provenance`` so the QA layer can display it,
and values that must be confirmed against the governing standard / approved
standard drawing before contractual use are flagged ``verify_before_use``.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DerivedDefaults:
    """Span-derived standard dimensions proposed when the workbook omits them."""

    bridge_type: str
    span_m: float
    girder_depth_mm: int | None = None
    girder_spacing_m: float | None = None
    girders_per_deck: int | None = None
    deck_slab_thickness_mm: int | None = None
    stem_width_mm: int | None = None
    top_flange_width_mm: int | None = None
    bottom_flange_width_mm: int | None = None
    web_thickness_mm: int | None = None
    diaphragm_max_spacing_m: float = 6.0
    provenance: dict[str, str] = field(default_factory=dict)
    verify_before_use: bool = True


# ---------------------------------------------------------------------------
# Span-derived defaults (Indian practice; confirm against approved standard
# drawings / the governing code before contractual use)
# ---------------------------------------------------------------------------

def derive_defaults(bridge_type: str, span_m: float,
                    carriageway_width_m: float = 7.5) -> DerivedDefaults:
    kind = _classify(bridge_type)
    prov: dict[str, str] = {"span_m": f"{span_m:g}", "carriageway_width_m": f"{carriageway_width_m:g}"}

    if kind == "slab":
        # Solid slab decks: thickness grows roughly with span; Indian PWD
        # practice lands ~ span/25 (12 m -> ~480 mm).  Capped at 1200 mm.
        t = int(min(1200, max(200, round(span_m * 1000.0 / 25.0 / 10.0) * 10)))
        prov["deck_slab_thickness_mm"] = "span/25 rounded to 10 mm (practice; verify_before_use)"
        return DerivedDefaults(bridge_type="slab", span_m=span_m,
                               deck_slab_thickness_mm=t, provenance=prov)

    if kind == "t_beam":
        # RCC T-beam: girder depth ~ span/12 (PWD standard T-beam designs
        # 15 m -> 1250-1500 mm), spacing 1.9-2.2 m so the slab overhangs
        # stay ~0.6-0.9 m; 3 girders for 7.5 m two-lane carriageway.
        depth = int(round(span_m * 1000.0 / 12.0 / 50.0) * 50)
        depth = max(1000, depth)
        n = _girders_for_width(carriageway_width_m, spacing=2.0)
        prov["girder_depth_mm"] = "span/12 rounded to 50 mm (practice; verify_before_use)"
        prov["girders_per_deck"] = "carriageway/spacing (practice; verify_before_use)"
        return DerivedDefaults(bridge_type="t_beam", span_m=span_m,
                               girder_depth_mm=depth, girder_spacing_m=2.0,
                               girders_per_deck=n, deck_slab_thickness_mm=250,
                               stem_width_mm=250, diaphragm_max_spacing_m=6.0,
                               provenance=prov)

    if kind == "i_girder":
        # PSC I-girder: depth ~ span/16 (30 m -> ~1875; approved standard
        # drawings commonly 1600-1900 mm for 30-40 m), spacing 2.0-2.5 m.
        depth = int(round(span_m * 1000.0 / 16.0 / 50.0) * 50)
        depth = max(1200, depth)
        n = _girders_for_width(carriageway_width_m, spacing=2.5)
        prov["girder_depth_mm"] = "span/16 rounded to 50 mm (practice; verify_before_use)"
        return DerivedDefaults(bridge_type="i_girder", span_m=span_m,
                               girder_depth_mm=depth, girder_spacing_m=2.5,
                               girders_per_deck=n, deck_slab_thickness_mm=200,
                               web_thickness_mm=200,
                               top_flange_width_mm=1000,
                               bottom_flange_width_mm=650,
                               diaphragm_max_spacing_m=6.0,
                               provenance=prov)

    return DerivedDefaults(bridge_type=kind, span_m=span_m, provenance=prov)


def _girders_for_width(carriageway_width_m: float, spacing: float) -> int:
    """Girder count so that outer spacing + overhangs cover the carriageway."""
    n = max(2, int(carriageway_width_m / spacing) + 1)
    return n


def _classify(bridge_type: str) -> str:
    t = (bridge_type or "").upper().replace("-", "_")
    if "BOX_CELL" in t:
        return "box_cell"
    if "BOX" in t:
        return "box"
    if "T_BEAM" in t or "TBEAM" in t:
        return "t_beam"
    if "I_GIRDER" in t or "IGIRDER" in t or "PSC" in t:
        return "i_girder"
    if "SLAB" in t:
        return "slab"
    return "unknown"


# ---------------------------------------------------------------------------
# Section profiles (LOCAL coordinates, mm; X transverse, Y positive DOWN,
# origin at top-centre of the section)
# ---------------------------------------------------------------------------

def solid_slab_profile(spec: DerivedDefaults) -> list[tuple[float, float]]:
    """Rectangular slab section outline with soffit haunch shoulders.

    Returns the closed polygon of one slab cross-section: constant thickness
    with small triangular haunches at each soffit edge (standard RC detailing
    transition to the cantilever/kerb line)."""
    t = float(spec.deck_slab_thickness_mm or 450)
    w = 1000.0  # local unit width for a typical band; sheet module tiles it
    return [
        (-w / 2.0, 0.0), (w / 2.0, 0.0), (w / 2.0, t),
        (w / 2.0 - 150.0, t), (w / 2.0, t + 150.0),  # right haunch step
        (-w / 2.0, t + 150.0), (-w / 2.0 + 150.0, t), (-w / 2.0, t),
    ]


def tbeam_profile(spec: DerivedDefaults) -> list[tuple[float, float]]:
    """RCC T-beam section: monolithic slab flange + stem + soffit haunch.

    Stem width and slab flange come from the derived defaults; the haunch
    (150 mm x 150 mm) is the standard slab-to-stem transition.
    """
    stem = float(spec.stem_width_mm or 250)
    slab_t = float(spec.deck_slab_thickness_mm or 250)
    flange_half = 500.0  # half of the slab strip tributary to one girder
    d = float(spec.girder_depth_mm or 1250)
    pts: list[tuple[float, float]] = [
        (-flange_half, 0.0), (flange_half, 0.0),          # slab top
        (flange_half, slab_t),                             # slab underside right
        (stem / 2.0 + 150.0, slab_t),                      # haunch start
        (stem / 2.0, slab_t + 150.0),                      # haunch
        (stem / 2.0, d), (-(stem / 2.0), d),               # stem soffit
        (-(stem / 2.0), slab_t + 150.0),
        (-(stem / 2.0 + 150.0), slab_t),
        (-flange_half, slab_t),
    ]
    return pts


def igirder_profile(spec: DerivedDefaults) -> list[tuple[float, float]]:
    """PSC I-girder section: top flange / web / bottom flange with fillets.

    Dimensions from the derived defaults; fillet radii are approximated by
    45-degree chamfers at the standard transition widths.
    """
    tf_w = float(spec.top_flange_width_mm or 1000)
    tf_t = 180.0                                   # top flange thickness (practice)
    web = float(spec.web_thickness_mm or 200)
    bf_w = float(spec.bottom_flange_width_mm or 650)
    bf_t = 300.0                                   # bottom flange thickness (practice)
    d = float(spec.girder_depth_mm or 1800)
    ch = 80.0                                      # chamfer leg (approx. fillet)
    pts: list[tuple[float, float]] = [
        (-tf_w / 2.0, 0.0), (tf_w / 2.0, 0.0),
        (tf_w / 2.0, tf_t),
        (web / 2.0 + ch, tf_t + ch),
        (web / 2.0, d - bf_t - ch),
        (bf_w / 2.0, d - bf_t),
        (bf_w / 2.0, d), (-bf_w / 2.0, d), (-bf_w / 2.0, d - bf_t),
        (-web / 2.0, d - bf_t - ch),
        (-web / 2.0 - ch, tf_t + ch),
        (-tf_w / 2.0, tf_t),
    ]
    return pts


def section_profile(spec: DerivedDefaults) -> list[tuple[float, float]]:
    kind = _classify(spec.bridge_type)
    if kind == "slab":
        return solid_slab_profile(spec)
    if kind == "t_beam":
        return tbeam_profile(spec)
    if kind in ("i_girder", "box", "box_cell"):
        return igirder_profile(spec)
    return []


# ---------------------------------------------------------------------------
# Longitudinal component stations
# ---------------------------------------------------------------------------

def diaphragm_stations(span_m: float, max_spacing_m: float = 6.0,
                       end_diaphragms: bool = True) -> list[float]:
    """Cross-girder/diaphragm stations along one span (metres from bearing).

    End diaphragms over the bearings plus intermediate diaphragms at <= max
    spacing (practice: 5-6 m for T-beam and PSC I-girder decks).
    """
    inner: list[float] = []
    start = 0.5 if end_diaphragms else 0.0
    x = start * max_spacing_m
    while x < span_m - 1.0:
        inner.append(round(x, 3))
        x += max_spacing_m
    stations = inner[:]
    if end_diaphragms:
        return [0.0] + inner + [span_m] if inner else [0.0, span_m]
    return inner


def bearing_positions(n_girders: int, girder_spacing_m: float,
                      girder_width_mm: float = 0.0) -> list[float]:
    """Transverse bearing centreline positions (metres) one per girder.

    Symmetric about the deck centreline; each bearing sits under its girder.
    """
    n = max(int(n_girders), 2)
    span_of_girders = (n - 1) * girder_spacing_m
    start = -span_of_girders / 2.0
    return [start + i * girder_spacing_m for i in range(n)]


def skew_adjusted_support_chainage(chainage_m: float, skew_deg: float,
                                   deck_width_m: float) -> tuple[float, float]:
    """Chainages of the two support-line ends at a skew.

    The support line (pier/abutment) is rotated by the skew from the normal;
    its ends shift along the bridge axis by +/- (deck_width/2) * tan(skew).
    Returns (upstream_chainage, downstream_chainage) in metres.
    """
    import math
    shift = (deck_width_m / 2.0) * math.tan(math.radians(skew_deg))
    return (chainage_m - shift, chainage_m + shift)