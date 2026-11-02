"""RCC Arch Bridge plugin — draw overrides and typical value helpers."""

from __future__ import annotations

STANDARD = "IRC:112-2020"
SPAN_RANGE_M = (20, 60)
DECK_THICKNESS_MM = 250
SPAN_DEPTH_RATIO = 45


def _girder_depth_mm() -> int:
    """arch rib depth = mid-band span / L/d ratio (0 when no band applies)."""
    if SPAN_DEPTH_RATIO <= 0:
        return 0
    mid_span_m = (SPAN_RANGE_M[0] + SPAN_RANGE_M[1]) / 2.0
    return int(round(mid_span_m * 1000.0 / SPAN_DEPTH_RATIO))


def describe() -> str:
    return (
        "RCC Arch Bridge (IRC:112-2020)\n"
        "  Span range  : 20-60 m\n"
        "  Deck        : M35 concrete\n"
        "  Arch rib  : depth = span/45\n"
        "  Bearing     : POT_PTFE\n"
        "  Joint       : SINGLE_MODULAR\n"
    )


def get_typical_values() -> dict:
    """Return typical design values dict (for UI pre-fill)."""
    return {
        "span_count": 1,
        "span_lengths_m": [(SPAN_RANGE_M[0] + SPAN_RANGE_M[1]) / 2.0],
        "carriageway_width_m": 7.5,
        "deck_thickness_mm": DECK_THICKNESS_MM,
        "girder_depth_mm": _girder_depth_mm(),
        "bearing_type": "POT_PTFE",
        "expansion_joint_type": "SINGLE_MODULAR",
    }


def apply_defaults(project_dict: dict) -> dict:
    """Merge defaults into *project_dict* without overwriting existing values."""
    typical = get_typical_values()
    for section, key, value in [
        ("superstructure", "deck_thickness_mm", typical["deck_thickness_mm"]),
        ("superstructure", "girder_depth_mm", typical["girder_depth_mm"]),
        ("materials", "bearing_type", typical["bearing_type"]),
        ("materials", "expansion_joint_type", typical["expansion_joint_type"]),
    ]:
        sec = project_dict.setdefault(section, {})
        if sec.get(key) is None:
            sec[key] = value
    return project_dict
