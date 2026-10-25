"""Wing-20 — the parsers, before anything depends on them.

An extractor that is 80% right produces expectations that are 80% right, and the
20% gets debugged as if it were a geometry bug.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from bridgecad_refs.parse import agree, parse_keyed_dimension, parse_level, parse_lines, parse_scale

pytestmark = pytest.mark.refs


@pytest.mark.parametrize("line,key,value,prec", [
    ("HFL 104.500", "hfl_m", "104.500", 3),
    ("LWL 99.200", "lwl_m", "99.200", 3),
    ("DECK LEVEL 108.200", "deck_level_m", "108.200", 3),
    ("Founding Level: 96.00", "founding_level_m", "96.00", 2),
    ("SOFFIT LEVEL = 107.950 m", "soffit_level_m", "107.950", 3),
])
def test_level_labels_parse(line, key, value, prec):
    f = parse_level(line)
    assert f and f.key == key and f.value == Decimal(value) and f.precision == prec


@pytest.mark.parametrize("line,key,value,unit", [
    ("ABTL 13.000 m", "abtl", "13.000", "m"),
    ("SPLAY 45 deg", "splay", "45", "deg"),
    ("CARRIAGEWAY 8.0 m", "carriageway", "8.0", "m"),
    ("CROSS FALL 2.5 %", "cross_fall", "2.5", "%"),
])
def test_keyed_dimensions_parse(line, key, value, unit):
    f = parse_keyed_dimension(line)
    assert f and f.key == key and f.value == Decimal(value) and f.unit == unit


def test_level_parser_wins_over_dimension_parser():
    """'DECK LEVEL 108.200' must not be read as a bare dimension."""
    facts = parse_lines(["DECK LEVEL 108.200", "ABTL 13.000 m"])
    assert [f.kind for f in facts] == ["level", "dimension"]


def test_scale_parses():
    assert parse_scale("SCALE 1:100").value == Decimal(100)


def test_junk_returns_nothing():
    assert parse_lines(["", "  ", "BRIDGE OVER RIVER X", "SHEET 5 OF 7"]) == []


def test_precision_is_carried_not_discarded():
    assert parse_level("HFL 104.5").precision == 1
    assert parse_level("HFL 104.500").precision == 3


def test_agreement_is_millimetre_resolution():
    assert agree(Decimal("13.000"), Decimal("13.0009"))
    assert not agree(Decimal("13.000"), Decimal("13.0011"))


def test_trailing_zero_mismatch_is_not_a_mismatch():
    """13.0 and 13.000 are the same dimension. Only precision differs."""
    assert agree(Decimal("13.0"), Decimal("13.000"))
