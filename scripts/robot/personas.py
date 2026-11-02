"""Persona action policies and value generators. Seeded, reproducible.

Ported from the Venice-patch robotic test plan and adapted to this flat repo.
Fixes the upstream ``__WIDTHS`` typo (name-mangled, would raise NameError).
Lives under ``scripts/`` so it is inside the CI lint scope.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum


class Tier(str, Enum):
    BASIC = "P1_basic"
    INTER = "P2_intermediate"
    ADV = "P3_advanced"


@dataclass(frozen=True)
class Persona:
    tier: Tier
    seed: int
    w_interact: float
    w_tab: float
    w_export: float
    w_submit: float
    max_steps: int


PERSONAS = {
    Tier.BASIC: Persona(Tier.BASIC, 1001, 0.70, 0.20, 0.05, 0.05, 120),
    Tier.INTER: Persona(Tier.INTER, 2002, 0.60, 0.15, 0.15, 0.10, 250),
    Tier.ADV: Persona(Tier.ADV, 3003, 0.50, 0.12, 0.15, 0.23, 400),
}

# --- value generators: persona-shaped, not uniform-random -------------------

_SPANS = {
    Tier.BASIC: [10, 15, 20, 25, 30, 40, 50],
    Tier.INTER: [18.5, 21.0, 24.5, 27.75, 31.0, 36.25],
    Tier.ADV: [0.0, 0.5, 1.0, 8.0, 99.99, 150.0, 200.0],
}
_WIDTHS = {
    Tier.BASIC: [7.5, 10.0, 12.0],
    Tier.INTER: [7.5, 8.75, 11.25, 14.0],
    Tier.ADV: [0.0, 0.1, 7.5, 60.0, 999.0],
}
# Guard so the table cannot silently drift out of step with the tier enum the
# way the upstream ``__WIDTHS`` name did.
assert set(_WIDTHS) == set(Tier), "every tier needs a width table"

_GRADES = {
    Tier.BASIC: ["M25", "M30", "M35"],
    Tier.INTER: ["M30", "M35", "M40", "M45"],
    Tier.ADV: ["M20", "M60", "M100", "", "m30"],
}
_UNICODE_NAMES = ["पुल–૭", "橋梁 №3", "Bri dge/01", "x" * 200, "", "  ", "'; DROP--"]


def num(rng: random.Random, tier: Tier, kind: str) -> str:
    table = {"span": _SPANS, "width": _WIDTHS, "grade": _GRADES}[kind]
    return str(rng.choice(table[tier]))


def text(rng: random.Random, tier: Tier) -> str:
    if tier is Tier.ADV and rng.random() < 0.5:
        return rng.choice(_UNICODE_NAMES)
    return rng.choice(["Pul-1", "Bridge A", "Test", "NH-48 ROB"])


def pick_persona(tier: Tier) -> tuple[Persona, random.Random]:
    p = PERSONAS[tier]
    return p, random.Random(p.seed)
