"""Pure-function tests for the validation registry builders."""

from __future__ import annotations

import re

import pytest

from bridgecad_core.types import ENUM_REGISTRY, ValidationSeverity
from bridgecad_core.validation_registry import (
    RULES,
    RegistryRule,
    RuleSpec,
    _a,
    _build_rules,
    _standard_and_clause,
)

# ---------------------------------------------------------------------------
# _a — filter to known enum names
# ---------------------------------------------------------------------------


def test_a_keeps_only_known_enum_names():
    assert _a(["ConcreteGrade", "FoundationType"]) == frozenset({"ConcreteGrade", "FoundationType"})
    assert _a(["ConcreteGrade", "NO_SUCH_ENUM_XYZ"]) == frozenset({"ConcreteGrade"})
    assert _a(["NO_SUCH_ENUM_XYZ"]) == frozenset()
    assert isinstance(_a(["ConcreteGrade"]), frozenset)


# ---------------------------------------------------------------------------
# _standard_and_clause — reference splitting
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "reference, expected",
    [
        ("IRC SP-55 Clause 1.2", ("IRC SP-55", "Clause 1.2")),
        ("MORTH 5th Rev Clause 101.2", ("MORTH 5th Rev", "Clause 101.2")),
        ("IS:456-2000 Table 5", ("IS:456-2000", "Table 5")),
        ("IRC:112-2020 Clause 3.1", ("IRC:112-2020", "Clause 3.1")),
        ("IRC:78-2014 Clause 9", ("IRC:78-2014", "Clause 9")),
        ("IRC:6 Annex B", ("IRC:6", "Annex B")),
    ],
)
def test_standard_and_clause_splits_known_formats(reference, expected):
    assert _standard_and_clause(reference) == expected


def test_standard_and_clause_without_keyword_keeps_whole_citation():
    assert _standard_and_clause("Plain Citation 12") == ("Plain Citation 12", "Plain Citation 12")


def test_standard_and_clause_strips_whitespace():
    assert _standard_and_clause("  IRC SP-55 Clause 1.2  ") == ("IRC SP-55", "Clause 1.2")


# ---------------------------------------------------------------------------
# _build_rules / RULES
# ---------------------------------------------------------------------------


def test_build_rules_is_non_empty():
    rules = _build_rules()
    assert rules
    assert len(rules) == len(RULES)


def test_every_rule_has_id_and_reference():
    for rule in _build_rules():
        assert rule.id
        assert rule.standard
        assert rule.clause
        assert rule.source_rule_id


def test_rule_ids_are_unique_and_formatted():
    ids = [r.id for r in _build_rules()]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"V\d{3}", rid) for rid in ids)


def test_rule_tiers_and_implemented_count():
    rules = _build_rules()
    assert {r.tier for r in rules} <= {"critical", "warning", "info"}
    assert sum(1 for r in rules if r.implemented) == 30
    assert rules[0].tier == "critical"
    assert rules[0].implemented is True


# ---------------------------------------------------------------------------
# dataclasses
# ---------------------------------------------------------------------------


def test_registry_dataclasses_round_trip():
    rule = RegistryRule(
        id="V001",
        tier="critical",
        standard="IRC SP-55",
        clause="Clause 1.2",
        source_rule_id="C01",
        implemented=True,
    )
    assert rule.deprecated is False
    assert rule.deprecation_note is None
    spec = RuleSpec(
        rule_id="C01",
        severity=ValidationSeverity.CRITICAL,
        applies_to=frozenset({"ProjectStage"}),
        description="d",
        reference_clause="IRC SP-55 Clause 1.2",
    )
    assert spec.severity is ValidationSeverity.CRITICAL


def test_registry_enum_names_resolve():
    assert "ConcreteGrade" in ENUM_REGISTRY
    assert "FoundationType" in ENUM_REGISTRY
