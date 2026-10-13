"""
bridgecad_ai.param_suggester — Suggest default parameter values based on
the 28 Scribd reference GAD drawing corpus + IRC standard proportioning rules.

For a given bridge type, span, and carriageway width, returns a dict of
recommended starting values (not enforced — user always overrides).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SuggestedParams:
    """Recommended parameter values for a bridge configuration."""
    superstructure_type:          str
    span_lengths_m:               list[float]
    deck_thickness_mm:            int
    girder_depth_mm:              int
    girder_spacing_m:             float
    girders_per_deck_count:       int
    wearing_coat_thickness_mm:    int
    parapet_height_mm:            int
    pier_type:                    str
    pier_shaft_width_m:           float
    pier_height_typical_m:        float
    abutment_type:                str
    pile_diameter_mm:             int
    pile_length_m:                float
    piles_per_pier:               int
    pile_spacing_m:               float
    concrete_grade_deck:          str
    concrete_grade_sub:           str
    bearing_type:                 str
    expansion_joint_type:         str
    camber_mm:                    int
    source:                       str = "IRC heuristics + Scribd corpus"
    confidence:                   str = "MEDIUM"


# ---------------------------------------------------------------------------
# Reference corpus (condensed from 28 Scribd GADs)
# ---------------------------------------------------------------------------
# Key: (superstructure_type, span_range_bucket)
#      span_range_bucket: "short"=≤15m, "medium"=16-30m, "long"=31-45m

_CORPUS: dict[tuple[str, str], dict] = {
    ("RCC_TBEAM", "short"): {
        "deck_thickness_mm": 200, "girder_depth_mm": 900,
        "girder_spacing_m": 2.0, "girders_per_deck_count": 4,
        "pier_type": "WALL", "pier_shaft_width_m": 1.2,
        "abutment_type": "CANTILEVER",
        "pile_diameter_mm": 1000, "pile_length_m": 12.0, "piles_per_pier": 4,
        "pile_spacing_m": 2.0, "concrete_grade_deck": "M30",
        "concrete_grade_sub": "M25", "bearing_type": "ELASTOMERIC_NEOPRENE",
        "expansion_joint_type": "COMPRESSION_SEAL",
        "wearing_coat_thickness_mm": 65, "parapet_height_mm": 900,
        "camber_mm": 15, "confidence": "HIGH",
        "source": "IRC SP:13 + 8 Scribd minor bridge GADs",
    },
    ("RCC_TBEAM", "medium"): {
        "deck_thickness_mm": 220, "girder_depth_mm": 1500,
        "girder_spacing_m": 2.5, "girders_per_deck_count": 4,
        "pier_type": "WALL", "pier_shaft_width_m": 1.5,
        "abutment_type": "CANTILEVER",
        "pile_diameter_mm": 1200, "pile_length_m": 16.0, "piles_per_pier": 6,
        "pile_spacing_m": 2.4, "concrete_grade_deck": "M30",
        "concrete_grade_sub": "M30", "bearing_type": "ELASTOMERIC_NEOPRENE",
        "expansion_joint_type": "STRIP_SEAL",
        "wearing_coat_thickness_mm": 65, "parapet_height_mm": 1000,
        "camber_mm": 25, "confidence": "HIGH",
        "source": "IRC:21 + 6 Scribd major bridge GADs",
    },
    ("PSC_IGIRDER", "medium"): {
        "deck_thickness_mm": 250, "girder_depth_mm": 1800,
        "girder_spacing_m": 2.5, "girders_per_deck_count": 4,
        "pier_type": "HAMMERHEAD", "pier_shaft_width_m": 1.5,
        "abutment_type": "CANTILEVER",
        "pile_diameter_mm": 1200, "pile_length_m": 18.0, "piles_per_pier": 6,
        "pile_spacing_m": 2.4, "concrete_grade_deck": "M40",
        "concrete_grade_sub": "M30", "bearing_type": "POT_PTFE",
        "expansion_joint_type": "STRIP_SEAL",
        "wearing_coat_thickness_mm": 50, "parapet_height_mm": 1100,
        "camber_mm": 35, "confidence": "HIGH",
        "source": "IRC:112 + 7 Scribd PSC GADs (Chambakkara, Shiwalay, Newaj…)",
    },
    ("PSC_IGIRDER", "long"): {
        "deck_thickness_mm": 280, "girder_depth_mm": 2400,
        "girder_spacing_m": 3.0, "girders_per_deck_count": 3,
        "pier_type": "HAMMERHEAD", "pier_shaft_width_m": 2.0,
        "abutment_type": "CANTILEVER",
        "pile_diameter_mm": 1500, "pile_length_m": 22.0, "piles_per_pier": 8,
        "pile_spacing_m": 3.0, "concrete_grade_deck": "M45",
        "concrete_grade_sub": "M35", "bearing_type": "POT_PTFE",
        "expansion_joint_type": "SINGLE_MODULAR",
        "wearing_coat_thickness_mm": 50, "parapet_height_mm": 1150,
        "camber_mm": 50, "confidence": "MEDIUM",
        "source": "IRC:112 + 4 Scribd long-span GADs",
    },
    ("PSC_BOX_GIRDER", "medium"): {
        "deck_thickness_mm": 260, "girder_depth_mm": 2000,
        "girder_spacing_m": 0.0, "girders_per_deck_count": 1,
        "pier_type": "HAMMERHEAD", "pier_shaft_width_m": 2.2,
        "abutment_type": "CANTILEVER",
        "pile_diameter_mm": 1350, "pile_length_m": 20.0, "piles_per_pier": 6,
        "pile_spacing_m": 2.8, "concrete_grade_deck": "M45",
        "concrete_grade_sub": "M35", "bearing_type": "POT_PTFE",
        "expansion_joint_type": "SINGLE_MODULAR",
        "wearing_coat_thickness_mm": 50, "parapet_height_mm": 1150,
        "camber_mm": 60, "confidence": "HIGH",
        "source": "IRC:112 + 6 Scribd medium-span PSC box GADs",
    },
    ("PSC_BOX_GIRDER", "long"): {
        "deck_thickness_mm": 300, "girder_depth_mm": 3000,
        "girder_spacing_m": 0.0, "girders_per_deck_count": 1,
        "pier_type": "HAMMERHEAD", "pier_shaft_width_m": 2.5,
        "abutment_type": "CANTILEVER",
        "pile_diameter_mm": 1500, "pile_length_m": 25.0, "piles_per_pier": 8,
        "pile_spacing_m": 3.0, "concrete_grade_deck": "M50",
        "concrete_grade_sub": "M40", "bearing_type": "POT_PTFE",
        "expansion_joint_type": "SINGLE_MODULAR",
        "wearing_coat_thickness_mm": 50, "parapet_height_mm": 1200,
        "camber_mm": 80, "confidence": "MEDIUM",
        "source": "IRC:112 balanced cantilever norms + 3 Scribd box GADs",
    },
    ("BOX_CULVERT", "short"): {
        "deck_thickness_mm": 300, "girder_depth_mm": 0,
        "girder_spacing_m": 0.0, "girders_per_deck_count": 0,
        "pier_type": "WALL", "pier_shaft_width_m": 0.3,
        "abutment_type": "CANTILEVER",
        "pile_diameter_mm": 0, "pile_length_m": 0.0, "piles_per_pier": 0,
        "pile_spacing_m": 0.0, "concrete_grade_deck": "M25",
        "concrete_grade_sub": "M25", "bearing_type": "ELASTOMERIC_NEOPRENE",
        "expansion_joint_type": "BURIED_CONTINUOUS_DECK",
        "wearing_coat_thickness_mm": 65, "parapet_height_mm": 600,
        "camber_mm": 0, "confidence": "HIGH",
        "source": "IRC SP:13 + 4 Scribd culvert GADs",
    },
}

# Default fallback
_DEFAULT = _CORPUS[("RCC_TBEAM", "medium")]


def _span_bucket(span_m: float) -> str:
    if span_m <= 15:  return "short"
    if span_m <= 30:  return "medium"
    return "long"


def suggest(
    total_length_m:       float,
    n_spans:              int            = 1,
    superstructure_type:  str            = "RCC_TBEAM",
    carriageway_width_m:  float          = 7.5,
) -> SuggestedParams:
    """Return recommended parameters for a given bridge configuration.

    Parameters
    ----------
    total_length_m : float
    n_spans : int
    superstructure_type : str
        One of: RCC_TBEAM / PSC_IGIRDER / PSC_BOX_GIRDER / BOX_CULVERT
    carriageway_width_m : float

    Returns
    -------
    SuggestedParams
    """
    span_m  = total_length_m / max(n_spans, 1)
    bucket  = _span_bucket(span_m)
    key     = (superstructure_type.upper(), bucket)
    data    = _CORPUS.get(key, _CORPUS.get((superstructure_type.upper(), "medium"), _DEFAULT))

    # Compute span lengths array
    span_lengths = [round(total_length_m / n_spans, 3)] * n_spans

    # Adaptive girder depth from IRC span/depth norms
    if data["girder_depth_mm"] == 0:
        girder_d_mm = 0
    else:
        sd_ratio = 15 if "PSC" in superstructure_type else 13
        girder_d_mm = max(data["girder_depth_mm"],
                          round(span_m / sd_ratio * 1000 / 50) * 50)

    # Adaptive girder count from carriageway width
    if data["girder_spacing_m"] > 0:
        girders = max(3, round(carriageway_width_m / data["girder_spacing_m"]))
    else:
        girders = 0

    return SuggestedParams(
        superstructure_type       = superstructure_type,
        span_lengths_m            = span_lengths,
        deck_thickness_mm         = data["deck_thickness_mm"],
        girder_depth_mm           = girder_d_mm,
        girder_spacing_m          = data["girder_spacing_m"],
        girders_per_deck_count    = girders,
        wearing_coat_thickness_mm = data["wearing_coat_thickness_mm"],
        parapet_height_mm         = data["parapet_height_mm"],
        pier_type                 = data["pier_type"],
        pier_shaft_width_m        = data["pier_shaft_width_m"],
        pier_height_typical_m     = max(6.0, span_m * 0.4),
        abutment_type             = data["abutment_type"],
        pile_diameter_mm          = data["pile_diameter_mm"],
        pile_length_m             = data["pile_length_m"],
        piles_per_pier            = data["piles_per_pier"],
        pile_spacing_m            = data["pile_spacing_m"],
        concrete_grade_deck       = data["concrete_grade_deck"],
        concrete_grade_sub        = data["concrete_grade_sub"],
        bearing_type              = data["bearing_type"],
        expansion_joint_type      = data["expansion_joint_type"],
        camber_mm                 = data["camber_mm"],
        source                    = data["source"],
        confidence                = data["confidence"],
    )


__all__ = ["SuggestedParams", "suggest"]
