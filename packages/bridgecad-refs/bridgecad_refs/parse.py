"""Pure parsers for text pulled off reference drawings.

Everything here returns Decimal, never float. Dimension arithmetic at 0.1 mm
resolution on floats accumulates error that shows up as a 0.1 mm mismatch and
gets "fixed" by loosening a tolerance, which is how tolerances stop meaning
anything.

`precision` is carried, not discarded. "104.5" off a drawing is a 1 dp statement
and is treated as less precise than "104.500". A reference that only gives 1 dp
must not be used to justify a 0.1 mm assertion.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

LEVEL_LABEL = re.compile(
    r"^\s*(HFL|LWL|DECK\s*LEVEL|FOUNDING\s*LEVEL|GROUND\s*LEVEL|SOFFIT\s*LEVEL|BEARING\s*LEVEL)"
    r"\s*[:=]?\s*(\d{1,4}\.\d{1,3})\s*m?\s*$",
    re.IGNORECASE,
)
KEYED_DIM = re.compile(
    r"^\s*(ABTL|SPLAY|CARRIAGEWAY|CROSS\s*FALL|KERB|WIDTH|SPAN|WING\s*WALL)\s*[:=]?\s*"
    r"(\d{1,4}(?:\.\d{1,3})?)\s*(m|deg|°|%|MM|MM)?\s*$",
    re.IGNORECASE,
)
SCALE = re.compile(r"\b1\s*:\s*(\d{1,4})\b")
REVISION = re.compile(r"\b([PCA]\d{1,2})\b")

LEVEL_KEYS = {
    "HFL": "hfl_m", "LWL": "lwl_m",
    "DECKLEVEL": "deck_level_m", "FOUNDINGLEVEL": "founding_level_m",
    "GROUNDLEVEL": "ground_level_m", "SOFFITLEVEL": "soffit_level_m",
    "BEARINGLEVEL": "bearing_level_m",
}


@dataclass(frozen=True)
class Fact:
    kind: str            # level | dimension | scale | revision
    key: str
    value: Decimal
    unit: str
    precision: int       # decimal places as stated on the drawing
    raw: str


def _dec(text: str) -> tuple[Decimal, int]:
    d = Decimal(text)
    return d, -d.as_tuple().exponent


def parse_level(line: str) -> Fact | None:
    m = LEVEL_LABEL.match(line)
    if not m:
        return None
    label = re.sub(r"\s+", "", m.group(1)).upper()
    val, prec = _dec(m.group(2))
    return Fact("level", LEVEL_KEYS[label], val, "m", prec, line.strip())


def parse_keyed_dimension(line: str) -> Fact | None:
    m = KEYED_DIM.match(line)
    if not m:
        return None
    key = re.sub(r"\s+", "_", m.group(1).strip().lower())
    unit = (m.group(3) or "m").lower().replace("°", "deg")
    if unit == "mm":
        unit = "mm"
    val, prec = _dec(m.group(2))
    return Fact("dimension", key, val, unit, prec, line.strip())


def parse_scale(line: str) -> Fact | None:
    m = SCALE.search(line)
    if not m:
        return None
    return Fact("scale", "plot_scale", Decimal(m.group(1)), "1:n", 0, line.strip())


def parse_revision(line: str) -> Fact | None:
    m = REVISION.search(line)
    if not m:
        return None
    return Fact("revision", "revision", Decimal(0), "code", 0, m.group(1))


PARSERS = (parse_level, parse_keyed_dimension, parse_scale, parse_revision)


def parse_lines(lines: list[str]) -> list[Fact]:
    """First parser that claims a line wins. Order matters: levels before dims,
    because 'DECK LEVEL 108.200' is also a bare number."""
    out: list[Fact] = []
    for line in lines:
        for parser in PARSERS:
            fact = parser(line)
            if fact is not None:
                out.append(fact)
                break
    return out


def agree(a: Decimal, b: Decimal, tolerance_mm: Decimal = Decimal("1")) -> bool:
    """Compare in millimetres. A 1 mm tolerance is the drawing's resolution, not
    a fudge factor."""
    return abs(a - b) * Decimal(1000) <= tolerance_mm


def min_precision(*precisions: int) -> int:
    """The weakest link. Two 1 dp sources agreeing to 1 mm is a coincidence."""
    return min(precisions) if precisions else 0
