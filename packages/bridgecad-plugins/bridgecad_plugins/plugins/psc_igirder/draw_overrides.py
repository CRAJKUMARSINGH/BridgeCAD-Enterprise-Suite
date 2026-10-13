"""PSC I-Girder plugin — draw overrides and typical value helpers."""
from __future__ import annotations


def describe() -> str:
    return (
        "PSC I-Girder Bridge (IRC:112-2020 / IRC:18-2000)\n"
        "  Span range  : 20–45 m (simply supported / continuous)\n"
        "  Deck        : M40 RCC, 250 mm composite slab\n"
        "  Girders     : Precast PSC I-girder, depth span/17, spacing 2.5 m\n"
        "  Prestress   : 13-strand tendons, 75% UTS jacking stress\n"
        "  Substructure: Hammerhead pier M30, cantilever abutment M30\n"
        "  Foundation  : Bored pile 1200 mm dia, 6 piles per support\n"
        "  Bearing     : POT-PTFE\n"
        "  Joint       : Strip seal\n"
    )


def get_typical_values() -> dict:
    return {
        "span_count":              3,
        "span_lengths_m":          [30.0, 30.0, 30.0],
        "carriageway_width_m":     7.5,
        "deck_thickness_mm":       250,
        "girder_depth_mm":         1800,
        "girder_spacing_m":        2.5,
        "girders_per_deck_count":  4,
        "pile_diameter_mm":        1200,
        "pile_length_m":           18.0,
        "piles_per_pier":          6,
        "bearing_type":            "POT_PTFE",
    }


def apply_defaults(project_dict: dict) -> dict:
    for section, key, value in [
        ("superstructure", "deck_thickness_mm",     250),
        ("superstructure", "girder_depth_mm",       1800),
        ("superstructure", "girder_spacing_m",      2.5),
        ("superstructure", "girders_per_deck_count", 4),
        ("superstructure", "camber_mm",              35),
        ("foundation_details", "pile_diameter_mm",  1200),
        ("foundation_details", "piles_per_pier",    6),
    ]:
        sec = project_dict.setdefault(section, {})
        if sec.get(key) is None:
            sec[key] = value
    return project_dict
