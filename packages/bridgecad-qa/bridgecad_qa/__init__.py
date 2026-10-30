"""bridgecad_qa — QA compliance engine (M6)."""

from .compliance import ComplianceScore, score
from .compliance_engine import (
    ClauseRef,
    ComplianceCheck,
    ComplianceReport,
    build_compliance_report,
    calc_sheet_markdown,
)
from .reports import generate_html_report
from .rules_engine import run_qa

__version__ = "0.1.0-rc1"
__all__ = [
    "run_qa",
    "ComplianceScore",
    "score",
    "generate_html_report",
    "ClauseRef",
    "ComplianceCheck",
    "ComplianceReport",
    "build_compliance_report",
    "calc_sheet_markdown",
]
