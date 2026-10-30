"""W06 · load-combination engine (IRC:6-2017 / EN 1990:2002) — property checks.

Every assertion is a closed-form identity or a structural invariant over the
registered tables — no external expected value is copied.
"""

from __future__ import annotations

import pytest

from bridgecad_core.standards.load_combinations import (
    DEAD,
    EN1990_LOAD_CASES,
    IRC6_LOAD_CASES,
    LIVE,
    SUPERIMPOSED_DEAD,
    WIND,
    LoadCombination,
    combinations_for,
    en1990_combinations,
    envelope,
    irc6_combinations,
)

IRC6 = irc6_combinations()
EN1990 = en1990_combinations()


def test_irc6_registers_the_table_one_combinations():
    ids = {combo.id for combo in IRC6}
    assert ids == {
        "IRC6-ULS-1",
        "IRC6-ULS-2",
        "IRC6-ULS-3",
        "IRC6-ULS-4",
        "IRC6-ULS-5",
        "IRC6-ULS-6",
        "IRC6-SEISMIC-1",
        "IRC6-SLS-1",
        "IRC6-SLS-2",
        "IRC6-SLS-3",
    }


def test_en1990_registers_the_table_a1_2_combinations():
    ids = {combo.id for combo in EN1990}
    assert ids == {
        "EN1990-6.10",
        "EN1990-6.10b",
        "EN1990-6.10-wind",
        "EN1990-6.10-thermal",
        "EN1990-6.12b",
        "EN1990-6.14b",
        "EN1990-6.15b",
    }


@pytest.mark.parametrize("combos", [IRC6, EN1990], ids=["irc6", "en1990"])
def test_every_combination_is_well_formed(combos: tuple[LoadCombination, ...]):
    for combo in combos:
        assert combo.standard and combo.limit_state and combo.description
        assert combo.terms, f"{combo.id} has no terms"
        case_ids = [term.case_id for term in combo.terms]
        assert len(case_ids) == len(set(case_ids)), f"{combo.id} repeats a case"
        assert all(term.factor > 0 for term in combo.terms), f"{combo.id} has a non-positive factor"


@pytest.mark.parametrize("combos", [IRC6, EN1990], ids=["irc6", "en1990"])
def test_combinations_only_reference_registered_cases(combos: tuple[LoadCombination, ...]):
    registered = {case.id for case in IRC6_LOAD_CASES} | {case.id for case in EN1990_LOAD_CASES}
    for combo in combos:
        assert combo.case_ids() <= registered, f"{combo.id} names an unregistered case"


@pytest.mark.parametrize("combos", [IRC6, EN1990], ids=["irc6", "en1990"])
def test_ids_are_unique(combos: tuple[LoadCombination, ...]):
    ids = [combo.id for combo in combos]
    assert len(ids) == len(set(ids))


def test_case_registries_have_unique_ids():
    for registry in (IRC6_LOAD_CASES, EN1990_LOAD_CASES):
        ids = [case.id for case in registry]
        assert ids and len(ids) == len(set(ids))
        assert all(case.description and case.kind for case in registry)


def test_factor_sums_duplicate_terms_and_reads_zero_when_absent():
    combo = LoadCombination(
        id="X",
        standard="IRC:6-2017",
        limit_state="ULS",
        description="diagram",
        terms=irc6_combinations()[0].terms,
    )
    assert combo.factor(DEAD) == 1.5
    assert combo.factor(SUPERIMPOSED_DEAD) == 1.5
    assert combo.factor(WIND) == 0.0


def test_factored_effect_is_the_dot_product():
    combo = IRC6[0]  # 1.5 DL + 1.5 SIDL + 1.5 LL
    effects = {DEAD: 10.0, SUPERIMPOSED_DEAD: 4.0, LIVE: 6.0, WIND: 100.0}
    assert combo.factored_effect(effects) == 1.5 * (10.0 + 4.0 + 6.0)
    # A case with no term in the combination cannot influence the result.
    assert combo.factored_effect({**effects, "ZZ": 1e9}) == 1.5 * 20.0


def test_missing_cases_contribute_zero():
    combo = IRC6[0]
    assert combo.factored_effect({}) == 0.0
    assert combo.factored_effect({DEAD: 2.0}) == 3.0


def test_permanent_factor_bands_by_limit_state():
    for combo in IRC6:
        if combo.limit_state == "ULS":
            assert combo.factor(DEAD) == 1.5
        elif combo.limit_state == "SLS":
            assert combo.factor(DEAD) == 1.0
        else:  # SEISMIC
            assert combo.factor(DEAD) == 1.0


def test_envelope_returns_the_extreme_combinations():
    effects = {DEAD: 10.0, SUPERIMPOSED_DEAD: 5.0, LIVE: 4.0}
    env = envelope(IRC6, effects)
    # Largest factored effect across the set, computed independently.
    values = {combo.id: combo.factored_effect(effects) for combo in IRC6}
    assert env.maximum == max(values.values())
    assert env.governing_max_id == max(values, key=lambda k: values[k])
    assert env.minimum == min(values.values())
    assert env.governing_min_id == min(values, key=lambda k: values[k])


def test_envelope_is_monotonic_in_live_load():
    base = {DEAD: 10.0, SUPERIMPOSED_DEAD: 5.0, LIVE: 1.0}
    heavier = {**base, LIVE: 50.0}
    assert envelope(IRC6, heavier).maximum >= envelope(IRC6, base).maximum


def test_envelope_rejects_an_empty_set():
    with pytest.raises(ValueError):
        envelope((), {})


def test_combinations_for_dispatch():
    assert combinations_for("IRC:6") == IRC6
    assert combinations_for("irc") == IRC6
    assert combinations_for("EN 1990") == EN1990
    assert combinations_for("EN1990:2002") == EN1990
    with pytest.raises(ValueError):
        combinations_for("AASHTO LRFD")
