from decimal import Decimal
import pytest
from bridgecad_catalogue import registry
from bridgecad_catalogue.resolve import resolve
from bridgecad_catalogue.schema import VARIABLES, Violation

@pytest.mark.parametrize("order", [dict(span_count="9",span_length_m="10"),dict(span_length_m="10",span_count="9")])
def test_nine_span_order_and_caption(order):
    p=resolve(registry.by_id("BR-I-2022-002"),order)
    assert len(p["span_lengths"])==9 and p["total_length_m"]==90
    assert p["spans"]=="9×10 m"

@pytest.mark.parametrize("raw", ["7.5",7.5,Decimal("7.5")])
def test_cli_numeric_choice(raw):
    assert VARIABLES["carriageway_width"].coerce(raw)==7.5

@pytest.mark.parametrize("raw", ["NaN","Infinity","-Infinity",True])
def test_nonfinite_and_boolean_rejected(raw):
    with pytest.raises(Violation): VARIABLES["span_length_m"].coerce(raw)

@pytest.mark.parametrize("key", ["span_count","girders_per_deck","piles_per_pier"])
def test_fractional_counts_rejected(key):
    with pytest.raises(Violation): VARIABLES[key].coerce("2.5")
