"""
bridgecad_qa.compliance — Weighted 0–100 compliance scorer.
Breaks the overall score into three IRC/MORTH sub-scores.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class ComplianceScore:
    overall:   int   # 0-100
    irc05:     int   # Hydraulic (IRC:5)
    irc21:     int   # Structural (IRC:21/IRC:112)
    irc_sp55:  int   # Drawing standards (IRC SP:55)
    critical_fails: int
    warning_fails:  int
    grade: str       # A+ A B C D F


_GRADE = [(95,"A+"), (85,"A"), (75,"B"), (65,"C"), (55,"D"), (0,"F")]


def score(report: Any) -> ComplianceScore:
    """Compute compliance scores from a ValidationReport."""
    overall = report.score

    # Approximate sub-scores: hydraulic checks = C12-C14, C24
    hyd_ids  = {"C12","C13","C14","C24"}
    drw_ids  = {"C19","C20","C21","C22"}
    str_ids  = {"C04","C05","C06","C07","C08","C09","C10","C15","C16","C17","C18","C25"}

    def _subscore(check_ids: set[str]) -> int:
        total = 100
        for f in report.findings:
            if f.check_id in check_ids and not f.passed:
                total -= 20
        return max(0, total)

    irc05    = _subscore(hyd_ids)
    irc_sp55 = _subscore(drw_ids)
    irc21    = _subscore(str_ids)

    grade = next(g for threshold, g in _GRADE if overall >= threshold)

    return ComplianceScore(
        overall=overall, irc05=irc05, irc21=irc21, irc_sp55=irc_sp55,
        critical_fails=report.critical_fail_count,
        warning_fails=report.warning_fail_count,
        grade=grade,
    )


__all__ = ["ComplianceScore", "score"]
