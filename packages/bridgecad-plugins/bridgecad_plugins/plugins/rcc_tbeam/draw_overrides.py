"""RCC T-Beam plugin — draw overrides and typical value helpers."""
from __future__ import annotations


def describe() -> str:
    return (
        "RCC T-Beam Bridge (IRC:21-2000 / IRC:112-2020)\n"
        "  Span range  : 6–30 m (simply supported)\n"
        "  Deck        : M30 RCC, 200 mm slab\n"
        "  Girders     : T-beam, depth = span/13, spacing 2.0 m\n"
        "  Substructure: Wall pier M25, cantilever abutment M25\n"
        "  Foundation  : Bored pile 1000 mm dia, 4 piles per support\n"
        "  Bearing     : Elastomeric neoprene pad\n"
        "  Joint       : Compression seal\n"
    )


def get_typical_values() -> dict:
    """Return typical design values dict (for UI pre-fill)."""
    return {
        "span_count":              1,
        "span_lengths_m":          [12.0],
        "carriageway_width_m":     7.5,
        "deck_thickness_mm":       200,
        "girder_depth_mm":         900,
        "girder_spacing_m":        2.0,
        "girders_per_deck_count":  4,
        "pile_diameter_mm":        1000,
        "pile_length_m":           12.0,
        "piles_per_pier":          4,
        "bearing_type":            "ELASTOMERIC_NEOPRENE",
    }


def apply_defaults(project_dict: dict) -> dict:
    """Merge RCC T-Beam defaults into *project_dict* without overwriting existing values."""
    typical = get_typical_values()
    # Shallow merge: only set keys that are absent or None
    for section, key, value in [
        ("superstructure", "deck_thickness_mm",      200),
        ("superstructure", "girder_depth_mm",         900),
        ("superstructure", "girder_spacing_m",        2.0),
        ("superstructure", "girders_per_deck_count",  4),
        ("superstructure", "camber_mm",               20),
        ("foundation_details", "pile_diameter_mm",    1000),
        ("foundation_details", "piles_per_pier",      4),
    ]:
        sec = project_dict.setdefault(section, {})
        if sec.get(key) is None:
            sec[key] = value
    return project_dict
