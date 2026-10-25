"""
bridgecad_qa.rules_engine — Thin adapter between bridgecad_core.validation
and the QA package. Runs all 30 checks and returns a ValidationReport.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def run_qa(project: Any):
    """Run all registered checks against *project* and return ValidationReport."""
    from bridgecad_core.validation import run_all
    return run_all(project)


@dataclass(frozen=True)
class RuleFinding:
    """A ValidationFinding tagged with its stable registry rule ID (V###)."""

    rule_id: str
    description: str
    severity: Any
    passed: bool
    message: str = ""


def run_rules(project: Any) -> list[RuleFinding]:
    """Run every check and tag each finding with its registry rule ID.

    A finding that never carries its rule ID is indistinguishable from a rule
    that never fires; tagging is what lets the QA output be traced back to the
    registry. Findings with no registry entry (technical ``ERR`` rows, or
    checks outside the 150-rule spec) are dropped — they are not rules.
    """
    from bridgecad_core.validation_registry import RULE_ID_BY_CHECK

    findings: list[RuleFinding] = []
    for f in run_qa(project).findings:
        rule_id = RULE_ID_BY_CHECK.get(f.check_id)
        if rule_id is None:
            continue
        findings.append(RuleFinding(
            rule_id=rule_id,
            description=f.description,
            severity=f.severity,
            passed=f.passed,
            message=f.message,
        ))
    return findings


__all__ = ["run_qa", "run_rules", "RuleFinding"]
