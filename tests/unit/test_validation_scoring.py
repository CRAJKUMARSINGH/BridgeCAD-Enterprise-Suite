"""Hand-built ValidationReport arithmetic and status-mapping tests."""

from __future__ import annotations

from bridgecad_core.types import ConcreteGrade, ValidationSeverity
from bridgecad_core.validation import ValidationFinding, ValidationReport, _concrete_ordinal


def _finding(severity, passed, check_id="C01"):
    return ValidationFinding(
        check_id=check_id, description="d", severity=severity, passed=passed, message=""
    )


# ---------------------------------------------------------------------------
# score
# ---------------------------------------------------------------------------


def test_empty_report_scores_100():
    assert ValidationReport().score == 100


def test_one_critical_fail_deducts_15():
    assert ValidationReport([_finding(ValidationSeverity.CRITICAL, False)]).score == 85


def test_one_warning_fail_deducts_3():
    assert ValidationReport([_finding(ValidationSeverity.WARNING, False)]).score == 97


def test_passed_findings_do_not_deduct():
    report = ValidationReport(
        [_finding(ValidationSeverity.CRITICAL, True), _finding(ValidationSeverity.WARNING, True)]
    )
    assert report.score == 100


def test_err_findings_are_not_deducted():
    report = ValidationReport([_finding(ValidationSeverity.CRITICAL, False, check_id="ERR")])
    assert report.score == 100


def test_score_mixes_critical_and_warning():
    report = ValidationReport(
        [_finding(ValidationSeverity.CRITICAL, False), _finding(ValidationSeverity.WARNING, False)]
    )
    assert report.score == 82


def test_score_floors_at_zero():
    report = ValidationReport([_finding(ValidationSeverity.CRITICAL, False) for _ in range(8)])
    assert report.score == 0


# ---------------------------------------------------------------------------
# overall_status
# ---------------------------------------------------------------------------


def test_status_mapping():
    assert ValidationReport([_finding(ValidationSeverity.CRITICAL, True)]).overall_status == "PASS"
    assert ValidationReport([_finding(ValidationSeverity.WARNING, False)]).overall_status == "WARN"
    assert ValidationReport([_finding(ValidationSeverity.CRITICAL, False)]).overall_status == "FAIL"
    # A critical fail outranks any warning.
    mixed = ValidationReport(
        [_finding(ValidationSeverity.WARNING, False), _finding(ValidationSeverity.CRITICAL, False)]
    )
    assert mixed.overall_status == "FAIL"


# ---------------------------------------------------------------------------
# counts / partitions
# ---------------------------------------------------------------------------


def test_passed_and_failed_partition():
    passed = _finding(ValidationSeverity.CRITICAL, True)
    failed = _finding(ValidationSeverity.CRITICAL, False)
    report = ValidationReport([passed, failed, passed])
    assert report.passed_findings() == [passed, passed]
    assert report.failed_findings() == [failed]


def test_critical_and_warning_fail_counts():
    report = ValidationReport(
        [
            _finding(ValidationSeverity.CRITICAL, False),
            _finding(ValidationSeverity.CRITICAL, False),
            _finding(ValidationSeverity.WARNING, False),
            _finding(ValidationSeverity.CRITICAL, True),
        ]
    )
    assert report.critical_fail_count == 2
    assert report.warning_fail_count == 1


# ---------------------------------------------------------------------------
# _concrete_ordinal
# ---------------------------------------------------------------------------


def test_concrete_ordinal_none_is_minus_one():
    assert _concrete_ordinal(None) == -1


def test_concrete_ordinal_ordering():
    grades = [ConcreteGrade.M20, ConcreteGrade.M25, ConcreteGrade.M30, ConcreteGrade.M40]
    ordinals = [_concrete_ordinal(g) for g in grades]
    assert ordinals == sorted(ordinals)
    assert len(set(ordinals)) == len(ordinals)


def test_concrete_ordinal_values_are_zero_based():
    assert _concrete_ordinal(ConcreteGrade.M20) == 2
    assert _concrete_ordinal(ConcreteGrade.M40) == 6


def test_concrete_ordinal_unknown_sorts_high():
    # M100 is not in the ordered table; unknowns sort above the known set.
    assert _concrete_ordinal(ConcreteGrade.M100) == 14
