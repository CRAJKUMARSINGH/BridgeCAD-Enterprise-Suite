"""
bridgecad_qa.compliance_engine — clause-level compliance object model.

W06 deliverable. Where :mod:`bridgecad_qa.compliance` reduces a report to a
0–100 score, this engine keeps every check *whole*: the clause it cites, the
edition of the code, the demand, the capacity, and the utilisation ratio that
follows from them. A check that cannot cite its clause and edition is not a
compliance statement — it is an opinion.

The engine is deliberately small and deterministic:

  * :class:`ClauseRef` names a standard, its edition and the clause.
  * :class:`ComplianceCheck` is one demand / capacity / utilisation record.
  * :class:`ComplianceReport` aggregates the checks.
  * :func:`build_compliance_report` maps a ``BridgeProject`` onto the checks.
  * :func:`calc_sheet_markdown` renders the report as a document a checker can
    read — load-combination catalogue, check table, summary.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from bridgecad_core.geometry import long_section as long_section
from bridgecad_core.models import BridgeProject
from bridgecad_core.standards import irc_05, irc_21
from bridgecad_core.standards.load_combinations import (
    LoadCombination,
    en1990_combinations,
    irc6_combinations,
)

#: A demand may exceed its capacity by this much (float noise) and still pass.
UTILISATION_TOL = 1e-9

#: Every check this engine knows how to emit. ``docs/verification/TRACEABILITY.md``
#: must carry a row for each — that is the "no gap" gate.
CHECK_IDS: tuple[str, ...] = (
    "CC-001",
    "CC-002",
    "CC-003",
    "CC-004",
    "CC-005",
    "CC-006",
)


@dataclass(frozen=True)
class ClauseRef:
    """A citation: standard, edition and clause, rendered as one string."""

    standard: str  # e.g. "IRC:21"
    edition: str  # e.g. "2000"
    clause: str  # e.g. "Table 12"

    @property
    def citation(self) -> str:
        return f"{self.standard}-{self.edition} {self.clause}"


@dataclass(frozen=True)
class ComplianceCheck:
    """One clause-mapped check with its demand, capacity and utilisation."""

    check_id: str
    title: str
    clause: ClauseRef
    demand: float
    capacity: float
    unit: str
    note: str = ""

    @property
    def utilisation(self) -> float:
        """``demand / capacity``; ``inf`` when a positive demand meets zero capacity."""
        if self.capacity <= 0.0:
            return 0.0 if self.demand <= 0.0 else float("inf")
        return self.demand / self.capacity

    @property
    def passed(self) -> bool:
        return self.utilisation <= 1.0 + UTILISATION_TOL

    @property
    def verdict(self) -> str:
        return "PASS" if self.passed else "FAIL"


@dataclass
class ComplianceReport:
    """An ordered set of clause-mapped checks for one project."""

    checks: list[ComplianceCheck]

    @property
    def n_checks(self) -> int:
        return len(self.checks)

    @property
    def n_passed(self) -> int:
        return sum(1 for check in self.checks if check.passed)

    @property
    def n_failed(self) -> int:
        return self.n_checks - self.n_passed

    def failed(self) -> list[ComplianceCheck]:
        return [check for check in self.checks if not check.passed]

    @property
    def governing(self) -> ComplianceCheck | None:
        """The check with the highest utilisation (first on a tie)."""
        if not self.checks:
            return None
        return max(self.checks, key=lambda check: check.utilisation)

    @property
    def max_utilisation(self) -> float:
        governing = self.governing
        return governing.utilisation if governing is not None else 0.0

    @property
    def pass_rate(self) -> float:
        return self.n_passed / self.n_checks if self.checks else 1.0


# ---------------------------------------------------------------------------
# Project → checks
# ---------------------------------------------------------------------------


def _grade_number(grade: object) -> float:
    """``"M30"`` / ``ConcreteGrade.M30`` → 30.0; unparseable → 0.0."""
    text = getattr(grade, "value", grade)
    text = str(text).strip().upper().lstrip("M").lstrip("FE")
    try:
        return float(text)
    except ValueError:
        return 0.0


def _span_config(project: BridgeProject) -> str:
    spans = project.geometry_input.span_lengths_m
    return "SIMPLY_SUPPORTED" if len(spans) <= 1 else "CONTINUOUS"


def _longest_span_m(project: BridgeProject) -> float:
    return max(float(span) for span in project.geometry_input.span_lengths_m)


def _effective_depth_mm(project: BridgeProject) -> float:
    """Girder depth where present, else the deck-slab thickness."""
    girder = project.superstructure.girder_depth_mm
    if girder:
        return float(girder)
    return float(project.superstructure.deck_thickness_mm)


def _build_checks(project: BridgeProject) -> list[ComplianceCheck]:
    checks: list[ComplianceCheck] = []
    stype = str(getattr(project.superstructure.type, "value", project.superstructure.type))
    config = _span_config(project)
    span_m = _longest_span_m(project)

    # CC-001 · span / depth ratio — IRC:21-2000 Table 12
    depth_mm = _effective_depth_mm(project)
    status, ratio, _lo, hi, ref = irc_21.classify_span_depth(span_m, depth_mm, config, stype)
    if status not in ("ADVISORY", "INVALID"):
        checks.append(
            ComplianceCheck(
                check_id="CC-001",
                title="Span / depth ratio",
                clause=ClauseRef("IRC:21", "2000", "Table 12"),
                demand=round(ratio, 1),
                capacity=float(hi),
                unit="L/d",
                note=f"{ref}; status {status}",
            )
        )

    # CC-002 · minimum deck slab thickness — IRC:21-2000 Clause 304.7
    required_t = irc_21.min_deck_slab_thickness_mm(
        stype, float(project.geometry_input.carriageway_width_m), span_m
    )
    checks.append(
        ComplianceCheck(
            check_id="CC-002",
            title="Minimum deck slab thickness",
            clause=ClauseRef("IRC:21", "2000", "Clause 304.7"),
            demand=required_t,
            capacity=float(project.superstructure.deck_thickness_mm),
            unit="mm",
            note="required vs provided slab thickness",
        )
    )

    # CC-003 · impact factor ceiling — IRC:6-2017 Clause 3.5
    impact = irc_21.impact_factor(span_m, "CLASS_A")
    checks.append(
        ComplianceCheck(
            check_id="CC-003",
            title="Impact factor",
            clause=ClauseRef("IRC:6", "2017", "Clause 3.5"),
            demand=impact,
            capacity=0.50,
            unit="fraction",
            note="IRC:6-2017 caps the Class A dynamic allowance at 0.50",
        )
    )

    # CC-004 · expansion joint gap — IRC:6-2017 Clause 3.8
    gap_mm = irc_21.expansion_joint_gap_mm(span_m)
    checks.append(
        ComplianceCheck(
            check_id="CC-004",
            title="Expansion joint gap",
            clause=ClauseRef("IRC:6", "2017", "Clause 3.8"),
            demand=gap_mm,
            capacity=100.0,
            unit="mm",
            note="gaps above 100 mm need a modular multi-gap joint",
        )
    )

    # CC-005 · freeboard — IRC:5-2015 Clause 22.1
    geo = long_section.compute_long_section_geometry(project)
    achieved = round(float(geo.freeboard_m), 3)
    required = max(float(project.hydraulic_data.freeboard_m), irc_05.freeboard_min("MAJOR"))
    checks.append(
        ComplianceCheck(
            check_id="CC-005",
            title="Freeboard above HFL",
            clause=ClauseRef("IRC:5", "2015", "Clause 22.1"),
            demand=round(required, 3),
            capacity=achieved,
            unit="m",
            note="required (IRC:5 Clause 22.1) vs achieved soffit − HFL",
        )
    )

    # CC-006 · deck concrete grade — IRC:112-2020 Clause 6.1
    provided_grade = _grade_number(project.materials.concrete_superstructure)
    checks.append(
        ComplianceCheck(
            check_id="CC-006",
            title="Deck concrete grade",
            clause=ClauseRef("IRC:112", "2020", "Clause 6.1"),
            demand=30.0,
            capacity=provided_grade,
            unit="MPa",
            note="IRC:112-2020 requires M30 minimum for an RC deck slab",
        )
    )

    return checks


def build_compliance_report(project: BridgeProject) -> ComplianceReport:
    """Build the clause-mapped :class:`ComplianceReport` for ``project``."""
    return ComplianceReport(checks=_build_checks(project))


# ---------------------------------------------------------------------------
# Calc-sheet rendering
# ---------------------------------------------------------------------------


def _fmt(value: float) -> str:
    return f"{value:.3f}"


def _combination_table(combos: Sequence[LoadCombination]) -> list[str]:
    lines = ["| Combination | Limit state | Factored terms | Citation |", "|---|---|---|---|"]
    for combo in combos:
        terms = ", ".join(f"{term.factor:g}·{term.case_id}" for term in combo.terms)
        lines.append(f"| `{combo.id}` | {combo.limit_state} | {terms} | {combo.standard} |")
    return lines


def calc_sheet_markdown(project: BridgeProject, report: ComplianceReport | None = None) -> str:
    """Render a deterministic calculation sheet (markdown) for ``project``."""
    report = report or build_compliance_report(project)
    master = project.project_master
    heading = f"{master.project_code} — {master.bridge_name}"

    lines: list[str] = [
        "# Calculation Sheet — code compliance",
        "",
        f"**Project:** {heading}",
        "**Standards:** IRC:5-2015 · IRC:6-2017 · IRC:21-2000 · IRC:112-2020 · IS:456-2000",
        "",
        "## 1. Load combinations",
        "",
        "### 1.1 IRC:6-2017 (governing)",
        "",
        *_combination_table(irc6_combinations()),
        "",
        "### 1.2 EN 1990:2002 (cross-check)",
        "",
        *_combination_table(en1990_combinations()),
        "",
        "## 2. Compliance checks",
        "",
        "| Check | Title | Clause | Demand | Capacity | Unit | Utilisation | Verdict |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for check in report.checks:
        utilisation = check.utilisation
        util_text = "—" if utilisation == float("inf") else _fmt(utilisation)
        lines.append(
            f"| `{check.check_id}` | {check.title} | {check.clause.citation} "
            f"| {_fmt(check.demand)} | {_fmt(check.capacity)} | {check.unit} "
            f"| {util_text} | {check.verdict} |"
        )

    governing = report.governing
    governing_text = (
        f"`{governing.check_id}` @ {_fmt(governing.utilisation)}" if governing is not None else "—"
    )
    lines += [
        "",
        "## 3. Summary",
        "",
        f"- Checks: {report.n_checks} · Passed: {report.n_passed} · Failed: {report.n_failed}",
        f"- Governing check: {governing_text}",
        f"- Pass rate: {report.pass_rate * 100:.1f}%",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "UTILISATION_TOL",
    "CHECK_IDS",
    "ClauseRef",
    "ComplianceCheck",
    "ComplianceReport",
    "build_compliance_report",
    "calc_sheet_markdown",
]
