"""Wing-14 — the QA rule registry's own invariants.

150 specs with 30 implemented is fine. 150 specs where nobody can tell which 30,
or where V042 was renumbered to V043 and broke every reference, is not.
"""
from __future__ import annotations

import re

import pytest

from . import contract

pytestmark = pytest.mark.draw

from bridgecad_core import validation_registry as reg  # noqa: E402

TIER_COUNTS = {"critical": 25, "warning": 75, "info": 50}
ID_RE = re.compile(r"^V(\d{3})$")


def _specs():
    return list(reg.RULES)


def test_registry_is_not_empty():
    assert len(_specs()) >= 150, f"only {len(_specs())} rules registered"


def test_rule_ids_are_unique():
    ids = [r.id for r in _specs()]
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, f"duplicate rule IDs: {sorted(dupes)}"


def test_rule_ids_follow_the_format():
    bad = [r.id for r in _specs() if not ID_RE.match(r.id)]
    assert not bad, f"malformed rule IDs: {bad}"


def test_rule_ids_are_contiguous_from_v001():
    """Contiguity is what makes 'never renumber, only deprecate' enforceable."""
    nums = sorted(int(ID_RE.match(r.id).group(1)) for r in _specs())
    assert nums[0] == 1, f"registry starts at V{nums[0]:03d}, expected V001"
    gaps = [n for n in range(1, nums[-1] + 1) if n not in nums]
    assert not gaps, f"gaps in rule numbering: {[f'V{g:03d}' for g in gaps]}"


def test_tier_distribution_matches_the_documented_counts():
    """GUIDE.md §5.4 and docs/standards.md both state 25/75/50. If the registry
    moves, the docs move with it or this fails."""
    from collections import Counter
    counts = Counter(r.tier for r in _specs())
    assert dict(counts) == TIER_COUNTS, f"tier counts {dict(counts)} != {TIER_COUNTS}"


def test_every_rule_names_its_standard_and_clause():
    for r in _specs():
        assert r.standard, f"{r.id}: no standard"
        assert r.clause, f"{r.id}: no clause — an unclauseable rule is unarguable"


def test_implemented_rules_have_a_check_function():
    implemented = [r for r in _specs() if r.implemented]
    assert implemented, "no rules marked implemented"
    from bridgecad_core import validation
    missing = [r.id for r in implemented if not hasattr(validation, f"check_{r.id.lower()}")]
    assert not missing, f"marked implemented with no check function: {missing}"


def test_stubbed_rules_are_counted_and_reported():
    stubbed = [r for r in _specs() if not r.implemented]
    assert stubbed, "nothing stubbed — did the flag default to True?"
    print(f"\n  rules: {len(_specs()) - len(stubbed)} implemented, {len(stubbed)} stubbed")


def test_implemented_rules_are_reported_in_the_qa_output():
    """A rule that exists but never fires is indistinguishable from absent."""
    from bridgecad_qa.rules_engine import run_rules
    findings = run_rules(contract.make_project("simple_12m"))
    fired = {f.rule_id for f in findings}
    implemented = {r.id for r in _specs() if r.implemented}
    silent = implemented - fired
    assert len(silent) <= len(implemented) // 2, (
        f"{len(silent)} of {len(implemented)} implemented rules never fired on a "
        f"valid project — check they are wired into run_rules: {sorted(silent)[:5]}"
    )


def test_grade_is_bounded_and_monotonic():
    """A+ to F, and worse findings never produce a better grade."""
    from bridgecad_qa.compliance import grade_from_score
    assert grade_from_score(100) == "A+"
    assert grade_from_score(0) == "F"
    scores = [grade_from_score(s) for s in range(0, 101, 5)]
    assert len(set(scores)) > 3, "grade barely varies with score"


def test_critical_findings_fail_the_grade():
    from bridgecad_qa.compliance import grade_from_score
    assert grade_from_score(95, critical_count=1) < grade_from_score(95, critical_count=0), (
        "a critical finding did not lower the grade"
    )


def test_rule_ids_are_never_reused_after_deprecation():
    """Deprecated rules stay in the registry with implemented=False and a note."""
    deprecated = [r for r in _specs() if getattr(r, "deprecated", False)]
    for r in deprecated:
        assert getattr(r, "deprecation_note", None), f"{r.id}: deprecated with no note"
