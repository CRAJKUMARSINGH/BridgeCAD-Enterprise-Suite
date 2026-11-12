"""The booklet defaults are frozen.

A sweep must never become the new baseline: whatever an engineer varies at the
CLI, `resolve(card, {})` must still reproduce the Maharashtra PWD booklet.
"""
from __future__ import annotations

import pytest

from bridgecad_catalogue import registry
from bridgecad_catalogue.resolve import resolve

# (span_count, span_lengths, total_length_m, bearing_type) — the booklet values.
FROZEN: dict[str, tuple[int, list[str], str, str]] = {
    "BR-I-2022-001": (4, ["10.0"] * 4, "40.0", "ELASTOMERIC"),
    "BR-I-2022-002": (4, ["10.0"] * 4, "40.0", "ELASTOMERIC"),
    "BR-I-2022-003": (5, ["10.0"] * 5, "50.0", "ELASTOMERIC"),
    "BR-I-2022-004": (3, ["22.2", "16.8", "22.25"], "61.25", "NONE"),
    "BR-I-2022-005": (6, ["15.0"] * 6, "90.0", "NONE"),
    "BR-I-2022-006": (5, ["10.0"] * 5, "50.0", "ELASTOMERIC"),
    "BR-I-2022-007": (4, ["15.0"] * 4, "60.0", "ELASTOMERIC"),
    "BR-I-2022-008": (3, ["25.0"] * 3, "75.0", "ELASTOMERIC"),
    "BR-I-2022-009": (4, ["25.0"] * 4, "100.0", "POT"),
    "BR-I-2022-010": (9, ["30.0"] * 9, "270.0", "POT"),
    "BR-I-2022-011": (3, ["35.0", "50.0", "35.0"], "120.0", "POT"),
    "BR-I-2022-012": (2, ["32.5", "32.5"], "65.0", "POT"),
    "BR-I-2022-013": (2, ["47.5", "47.5"], "95.0", "POT"),
    "BR-I-2022-014": (3, ["11.3", "25.7", "11.3"], "48.3", "NONE"),
    "BR-I-2022-015": (1, ["61.94"], "61.94", "NONE"),
}


@pytest.mark.parametrize("card", registry.load(), ids=lambda c: c["id"])
def test_default_resolution_is_pinned(card: dict) -> None:
    p = resolve(card, {})
    assert (
        p["span_count"],
        [str(s) for s in p["span_lengths"]],
        str(p["total_length_m"]),
        p["bearing_type"],
    ) == FROZEN[card["id"]]


def test_every_card_is_pinned() -> None:
    assert {c["id"] for c in registry.load()} == set(FROZEN)
