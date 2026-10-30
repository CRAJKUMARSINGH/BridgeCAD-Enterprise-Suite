"""Property + example tests for ``bridgecad_core.units``.

The exact anchors pin the conversion factors to their definitions; the property
tests pin the *behaviour* (round trips, linearity, rounding invariants) across a
whole input range, so a factor typo or a sign slip cannot pass unnoticed.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from bridgecad_core.units import (
    FT_TO_M,
    IN_TO_MM,
    KIP_TO_KN,
    KIPFT_TO_KNM,
    KSI_TO_MPA,
    UnitError,
    UnitSystem,
    feet_to_metres,
    inches_to_millimetres,
    kilonewton_metres_to_kip_feet,
    kilonewtons_to_kip_force,
    kip_feet_to_kilonewton_metres,
    kip_force_to_kilonewtons,
    ksi_to_megapascals,
    megapascals_to_ksi,
    metres_to_feet,
    millimetres_to_inches,
    require_unit_system,
    round_engineering,
    round_sig,
    unit_system,
)

_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)

FINITE = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
SIG_FIGS = st.integers(min_value=1, max_value=8)
DECIMALS = st.integers(min_value=0, max_value=6)


# ---------------------------------------------------------------------------
# Known exact anchors
# ---------------------------------------------------------------------------


def test_exact_conversion_anchors():
    assert FT_TO_M == 0.3048
    assert IN_TO_MM == 25.4
    assert KIP_TO_KN == 4.4482216152605
    assert KIPFT_TO_KNM == 1.3558179483314004
    assert KSI_TO_MPA == 6.894757293168361


def test_one_metre_is_3_28084_feet_within_1e_6():
    assert metres_to_feet(1.0) == pytest.approx(3.28084, abs=1e-6)


def test_unit_factors_convert_identity_values():
    assert feet_to_metres(1.0) == FT_TO_M
    assert inches_to_millimetres(1.0) == IN_TO_MM
    assert kilonewtons_to_kip_force(1.0) == pytest.approx(1.0 / KIP_TO_KN)
    assert kilonewton_metres_to_kip_feet(1.0) == pytest.approx(1.0 / KIPFT_TO_KNM)
    assert megapascals_to_ksi(1.0) == pytest.approx(1.0 / KSI_TO_MPA)
    assert kip_force_to_kilonewtons(1.0) == KIP_TO_KN
    assert kip_feet_to_kilonewton_metres(1.0) == KIPFT_TO_KNM
    assert ksi_to_megapascals(1.0) == KSI_TO_MPA


# ---------------------------------------------------------------------------
# Round-trip and linearity properties
# ---------------------------------------------------------------------------


@_SETTINGS
@given(x=FINITE)
def test_length_conversions_round_trip(x):
    assert feet_to_metres(metres_to_feet(x)) == pytest.approx(x, rel=1e-12, abs=1e-12)
    assert inches_to_millimetres(millimetres_to_inches(x)) == pytest.approx(x, rel=1e-12, abs=1e-12)


@_SETTINGS
@given(x=FINITE)
def test_force_moment_stress_conversions_round_trip(x):
    assert kip_force_to_kilonewtons(kilonewtons_to_kip_force(x)) == pytest.approx(
        x, rel=1e-12, abs=1e-12
    )
    assert kip_feet_to_kilonewton_metres(kilonewton_metres_to_kip_feet(x)) == pytest.approx(
        x, rel=1e-12, abs=1e-12
    )
    assert ksi_to_megapascals(megapascals_to_ksi(x)) == pytest.approx(x, rel=1e-12, abs=1e-12)


@_SETTINGS
@given(
    x=FINITE, k=st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False)
)
def test_conversions_are_linear(x, k):
    assert metres_to_feet(k * x) == pytest.approx(k * metres_to_feet(x), rel=1e-9, abs=1e-9)
    assert kip_force_to_kilonewtons(k * x) == pytest.approx(
        k * kip_force_to_kilonewtons(x), rel=1e-9, abs=1e-9
    )


# ---------------------------------------------------------------------------
# Rounding invariants
# ---------------------------------------------------------------------------


@_SETTINGS
@given(x=FINITE, n=SIG_FIGS)
def test_round_sig_is_idempotent(x, n):
    once = round_sig(x, n)
    assert round_sig(once, n) == once


@_SETTINGS
@given(
    x=st.floats(min_value=1e-6, max_value=1e6, allow_nan=False, allow_infinity=False),
    n=st.integers(min_value=1, max_value=6),
)
def test_round_sig_error_within_half_ulp_of_last_figure(x, n):
    result = round_sig(x, n)
    magnitude = Decimal(repr(x)).adjusted()
    bound = 0.5 * 10.0 ** (magnitude - n + 1)
    assert abs(result - x) <= bound * (1 + 1e-9)


def test_round_sig_zero_is_zero():
    assert round_sig(0.0, 3) == 0.0


def test_round_sig_rejects_non_positive_significant_figures():
    for n in (0, -1, -5):
        with pytest.raises(UnitError):
            round_sig(1.2345, n)


@_SETTINGS
@given(x=FINITE, d=DECIMALS)
def test_round_engineering_quantises_to_stated_decimals(x, d):
    result = round_engineering(x, d)
    assert abs(result - x) <= 0.5 * 10.0 ** (-d) * (1 + 1e-9)
    # The result carries at most d decimal places, so re-quantising is exact.
    quantum = Decimal(1).scaleb(-d)
    assert Decimal(repr(result)).quantize(quantum) == Decimal(repr(result))
    assert round_engineering(result, d) == result


def test_round_engineering_half_up_not_bankers():
    # Decimal + ROUND_HALF_UP: the code answer, not the nearest-double answer.
    assert round_engineering(2.345, 2) == 2.35


def test_round_engineering_rejects_negative_decimals():
    with pytest.raises(UnitError):
        round_engineering(1.2345, -1)


# ---------------------------------------------------------------------------
# Domain guards
# ---------------------------------------------------------------------------


def test_conversions_reject_non_finite_input():
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(UnitError):
            metres_to_feet(bad)
        with pytest.raises(UnitError):
            kip_force_to_kilonewtons(bad)


def test_rounding_rejects_non_finite_input():
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(UnitError):
            round_sig(bad, 3)
        with pytest.raises(UnitError):
            round_engineering(bad, 2)


def test_unit_error_is_a_value_error():
    assert issubclass(UnitError, ValueError)


def test_unit_system_classification():
    for symbol in ("m", "mm", "kN", "kN·m", "MPa"):
        assert unit_system(symbol) is UnitSystem.SI
    for symbol in ("ft", "in", "kip", "kip·ft", "ksi"):
        assert unit_system(symbol) is UnitSystem.FPS


def test_require_unit_system_accepts_matching_symbols():
    require_unit_system("kN", UnitSystem.SI)
    require_unit_system("kip", UnitSystem.FPS)


def test_require_unit_system_rejects_mismatch_and_unknown_symbol():
    with pytest.raises(UnitError):
        # A kN value cannot be read as FPS without an explicit error.
        require_unit_system("kN", UnitSystem.FPS)
    with pytest.raises(UnitError):
        require_unit_system("in", UnitSystem.SI)
    with pytest.raises(UnitError):
        unit_system("furlong")
