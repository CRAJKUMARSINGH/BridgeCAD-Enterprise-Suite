"""Box Culvert plugin — draw overrides and typical value helpers."""
from __future__ import annotations


def describe() -> str:
    return (
        "RCC Box Culvert (IRC SP:13 / IRC:112-2020)\n"
        "  Span range  : 2–8 m (single or multi-cell)\n"
        "  Deck        : M25 RCC monolithic box section\n"
        "  Wall/slab   : 300 mm sidewalls, 400 mm bottom slab\n"
        "  Foundation  : Open raft footing M20 on prepared sub-grade\n"
        "  Bearing     : Continuous deck — no discrete bearings\n"
        "  Joint       : Buried continuous (no expansion joint)\n"
    )


def get_typical_values() -> dict:
    return {
        "span_count":              1,
        "span_lengths_m":          [3.0],
        "carriageway_width_m":     7.5,
        "deck_thickness_mm":       300,
        "girder_depth_mm":         0,
        "girder_spacing_m":        0,
        "girders_per_deck_count":  0,
        "pile_diameter_mm":        0,
        "pile_length_m":           0,
        "piles_per_pier":          0,
        "bearing_type":            "ELASTOMERIC_NEOPRENE",
    }


def apply_defaults(project_dict: dict) -> dict:
    for section, key, value in [
        ("superstructure",   "deck_thickness_mm",     300),
        ("superstructure",   "girder_depth_mm",          0),
        ("superstructure",   "camber_mm",                0),
        ("foundation_details","piles_per_pier",          0),
    ]:
        sec = project_dict.setdefault(section, {})
        if sec.get(key) is None:
            sec[key] = value
    return project_dict
