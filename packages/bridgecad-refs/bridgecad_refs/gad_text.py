"""Strict numeric input codec for the archived gad.lsp read sequence.

This preserves data; it does not execute AutoLISP or claim drawing parity.
Extensions belong in a separate sidecar, never in the positional legacy file.
"""

from dataclasses import dataclass
from math import isfinite
from pathlib import Path

HEADER = ("scale1", "scale2", "skew", "datum", "toprl", "left", "right", "xincr", "yincr", "noch")
BRIDGE = (
    "nspan",
    "lbridge",
    "abtl",
    "rtl",
    "sofl",
    "kerbw",
    "kerbd",
    "ccbr",
    "slbthc",
    "slbthe",
    "slbtht",
    "capt",
    "capb",
    "capw",
    "piertw",
    "battr",
    "pierst",
    "piern",
)
SPAN = ("span1", "futrl", "futd", "futw", "futl")
ABUTMENT = (
    "dwth",
    "alcw",
    "alcd",
    "alfb",
    "alfbl",
    "altb",
    "altbl",
    "alfo",
    "alfd",
    "albb",
    "albbl",
)
INTEGER_FIELDS = frozenset(("datum", "toprl", "noch", "nspan", "piern"))


@dataclass(frozen=True)
class GadText:
    header: tuple[float, ...]
    survey: tuple[tuple[float, float], ...]
    bridge: tuple[float, ...]
    span_records: tuple[tuple[float, ...], ...]
    abutment: tuple[float, ...]


def loads(text: str) -> GadText:
    """Read the archive's reed → cs → pier → abt1 order, without defaults.

    Unlike AutoLISP atof/atoi, invalid numbers and fractional integer inputs
    are rejected rather than silently becoming zero or being truncated.
    nspan records are consumed as written in the archive; no inferred extra
    span or pier record is inserted.
    """
    lines = text.removeprefix("\ufeff").splitlines()
    index = 0

    def number(name):
        nonlocal index
        index += 1
        if index > len(lines):
            raise ValueError(f"line {index}: missing {name}")
        try:
            value = float(lines[index - 1].strip())
        except ValueError:
            raise ValueError(f"line {index}: invalid {name}") from None
        if not isfinite(value):
            raise ValueError(f"line {index}: non-finite {name}")
        if name in INTEGER_FIELDS and not value.is_integer():
            raise ValueError(f"line {index}: {name} requires an integer")
        return value

    header = tuple(number(k) for k in HEADER)
    h = dict(zip(HEADER, header, strict=False))
    for key in ("scale1", "scale2", "xincr", "yincr"):
        if h[key] <= 0:
            raise ValueError(f"{key} must be positive")
    if abs(h["skew"]) >= 90:
        raise ValueError("skew must lie strictly between -90 and 90 degrees")
    count = int(h["noch"])
    if count < 0 or count * 2 > len(lines) - index:
        raise ValueError("noch does not fit the available survey records")
    survey = tuple((number("chainage"), number("rl")) for _ in range(count))
    bridge = tuple(number(k) for k in BRIDGE)
    b = dict(zip(BRIDGE, bridge, strict=False))
    count = int(b["nspan"])
    if count < 1 or count * len(SPAN) > len(lines) - index:
        raise ValueError("nspan does not fit the available span records")
    spans = tuple(tuple(number(k) for k in SPAN) for _ in range(count))
    abutment = tuple(number(k) for k in ABUTMENT)
    if index != len(lines):
        raise ValueError(
            f"line {index + 1}: unexpected trailing data; use a sidecar for extensions"
        )
    return GadText(header, survey, bridge, spans, abutment)


def dumps(data: GadText) -> str:
    """Write normalized numeric lines; retain numeric values, not whitespace."""
    blocks = (
        (data.header, len(HEADER)),
        (data.bridge, len(BRIDGE)),
        (data.abutment, len(ABUTMENT)),
    )
    if any(len(block) != size for block, size in blocks):
        raise ValueError("incorrect fixed block length")
    if any(len(row) != 2 for row in data.survey) or any(
        len(row) != len(SPAN) for row in data.span_records
    ):
        raise ValueError("incorrect repeated record length")
    if data.header[-1] != len(data.survey) or data.bridge[0] != len(data.span_records):
        raise ValueError("record counts disagree with data")
    values = (
        *data.header,
        *(v for row in data.survey for v in row),
        *data.bridge,
        *(v for row in data.span_records for v in row),
        *data.abutment,
    )
    text = "".join(format(v, ".17g") + "\n" for v in values)
    loads(text)  # Apply exactly the same validation in both directions.
    return text


def read(path: str | Path) -> GadText:
    return loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path: str | Path, data: GadText) -> None:
    text = dumps(data)  # Validate before touching the destination.
    Path(path).write_text(text, encoding="utf-8")
