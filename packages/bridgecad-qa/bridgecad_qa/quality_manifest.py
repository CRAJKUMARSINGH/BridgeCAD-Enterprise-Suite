"""bridgecad_qa.quality_manifest — fail-closed acceptance gates for a GAD package.

The acceptance spec (``CODE-JUNCTION/BRIDGECAD_GAD_ACCEPTANCE_RESOLUTION.md`` §4)
defines completeness by *required content*, not by sheet count, and asks for a
manifest whose every gate is a closed enumeration rather than a literal
``"FAILED|PASSED|NOT_TESTED"`` string a reviewer has to interpret.

Two properties matter here and are the reason this lives in code rather than in
a writer script:

* **Closed vocabulary.** Each gate accepts only the verdicts that are meaningful
  for it (``GENERATION`` cannot be ``NOT_TESTED``; ``ENGINEERING_REVIEW`` is
  never ``PASSED`` without a named reviewer). A verdict outside the set is a
  programming error and :meth:`QualityManifest.set` raises instead of emitting a
  value nobody can compare.
* **Fail-closed acceptance.** :attr:`QualityManifest.accepted` is ``True`` only
  when every required gate has actually passed *and* the engineering review is
  recorded as approved. Anything untested, unresolved, blocked or pending keeps
  the drawing a DRAFT — the default for a package whose evidence is incomplete
  is "not accepted", never "probably fine".

Gate separation — four distinct verdict groups, never collapsed into one boolean:

* **Generation gates** (``generation_gates_passed``): generation,
  model validation, geometry contract — what the engine can prove
  deterministically about the package it has just produced.
* **Content and layout gates** (``quality_and_layout_passed`` adds these):
  required content and measured layout.  A package can generate perfectly and
  still be missing a required detail or collide on the sheet.
* **Reference fidelity** — requires the approved reference drawing and is
  currently BLOCKED for the nine-span fixture (the booklet contains no nine-span
  sheet).
* **Engineering review** — a human verdict; PENDING until a named reviewer
  approves.

``accepted`` is ``True`` only when all four groups are satisfied.  Deliberately
there is no single ``gates_passed`` flag: reporting one boolean invited "the
gates passed, so the drawing is fine".

Annotation overlap (label-label, dimension-geometry, schedule) is *measured* and
reported in ``annotation_overlap_count``, but is not a gate: the width estimator
in ``bridgecad_draw.layout_audit`` over-reports adjacent labels, and turning it
into a pass/fail needs per-view rectangles that no sheet declares yet.  Reporting
the number keeps it visible without a false pass.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Gate(str, Enum):
    """The acceptance gates of the fail-closed manifest."""

    GENERATION = "generation"
    MODEL_VALIDATION = "model_validation"
    GEOMETRY_CONTRACT = "geometry_contract"
    REQUIRED_CONTENT = "required_content"
    LAYOUT = "layout"
    REFERENCE_FIDELITY = "reference_fidelity"
    ENGINEERING_REVIEW = "engineering_review"


class Verdict(str, Enum):
    """Every verdict any gate may carry."""

    SUCCEEDED = "SUCCEEDED"
    PASSED = "PASSED"
    FAILED = "FAILED"
    UNRESOLVED = "UNRESOLVED"
    NOT_TESTED = "NOT_TESTED"
    BLOCKED = "BLOCKED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"


#: Verdicts each gate may legitimately carry. A value outside its gate's set is
#: rejected by :meth:`QualityManifest.set`, so a typo cannot masquerade as a
#: clean pass.
_ALLOWED: dict[Gate, frozenset[Verdict]] = {
    Gate.GENERATION: frozenset({Verdict.SUCCEEDED, Verdict.FAILED}),
    Gate.MODEL_VALIDATION: frozenset(
        {Verdict.PASSED, Verdict.FAILED, Verdict.UNRESOLVED}
    ),
    Gate.GEOMETRY_CONTRACT: frozenset(
        {Verdict.PASSED, Verdict.FAILED, Verdict.NOT_TESTED}
    ),
    Gate.REQUIRED_CONTENT: frozenset(
        {Verdict.PASSED, Verdict.FAILED, Verdict.NOT_TESTED}
    ),
    Gate.LAYOUT: frozenset({Verdict.PASSED, Verdict.FAILED, Verdict.NOT_TESTED}),
    Gate.REFERENCE_FIDELITY: frozenset(
        {Verdict.PASSED, Verdict.FAILED, Verdict.NOT_TESTED, Verdict.BLOCKED}
    ),
    Gate.ENGINEERING_REVIEW: frozenset(
        {Verdict.PENDING, Verdict.APPROVED, Verdict.FAILED}
    ),
}

#: The gates that must pass before the drawing is quality/layout complete. The
#: reference-fidelity and engineering-review gates are recorded alongside but do
#: not form part of this pass set: reference comparison needs the approved PDF,
#: and a structural review is a human verdict.
NULLABLE_GATE_ORDER: tuple[Gate, ...] = (
    Gate.GENERATION,
    Gate.MODEL_VALIDATION,
    Gate.GEOMETRY_CONTRACT,
    Gate.REQUIRED_CONTENT,
    Gate.LAYOUT,
    Gate.REFERENCE_FIDELITY,
    Gate.ENGINEERING_REVIEW,
)

#: Verdicts that count as "this gate did not fail".
_NON_FAILING = frozenset({Verdict.SUCCEEDED, Verdict.PASSED})

#: The *generation* gates: what the engine can prove deterministically about the
#: package it just produced — it generated, the model validated and the vertical
#: contract is internally consistent. They are deliberately a separate set from
#: required content, layout, reference fidelity and the engineering review,
#: which measure different things: a drawing can generate perfectly and still be
#: missing a required detail, collide, differ from its reference or await review.
#: Reporting them as one `gates_passed` flag invited "gates pass ⇒ the drawing is
#: fine"; the two questions are answered separately here.
GENERATION_GATES: tuple[Gate, ...] = (
    Gate.GENERATION,
    Gate.MODEL_VALIDATION,
    Gate.GEOMETRY_CONTRACT,
)

#: The gates `accepted` additionally requires on top of the generation gates.
ACCEPTANCE_GATES: tuple[Gate, ...] = (
    Gate.REQUIRED_CONTENT,
    Gate.LAYOUT,
    Gate.REFERENCE_FIDELITY,
    Gate.ENGINEERING_REVIEW,
)

#: The fail-closed starting point for each gate. An unset gate must never read
#: as "fine": generation defaults to FAILED (nothing has been generated yet),
#: validation to UNRESOLVED, every testable gate to NOT_TESTED and the review to
#: PENDING. :meth:`QualityManifest.set` is the only way to upgrade a gate.
_DEFAULT: dict[Gate, Verdict] = {
    Gate.GENERATION: Verdict.FAILED,
    Gate.MODEL_VALIDATION: Verdict.UNRESOLVED,
    Gate.GEOMETRY_CONTRACT: Verdict.NOT_TESTED,
    Gate.REQUIRED_CONTENT: Verdict.NOT_TESTED,
    Gate.LAYOUT: Verdict.NOT_TESTED,
    Gate.REFERENCE_FIDELITY: Verdict.NOT_TESTED,
    Gate.ENGINEERING_REVIEW: Verdict.PENDING,
}


@dataclass
class QualityIssue:
    """One unresolved input, assumption or finding attached to a gate."""

    gate: Gate
    code: str
    message: str
    detail: str = ""

    def to_json(self) -> dict[str, str]:
        return {
            "gate": self.gate.value,
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
        }


@dataclass
class QualityManifest:
    """Fail-closed gate verdicts for one generated package."""

    verdicts: dict[Gate, Verdict] = field(default_factory=dict)
    issues: list[QualityIssue] = field(default_factory=list)
    fixture: str = ""
    commit: str = ""
    notes: list[str] = field(default_factory=list)
    #: Measured label-label / dimension-geometry / schedule text-pair overlap
    #: count from layout_audit.  Reported alongside the gate verdicts so a
    #: reviewer sees the number without the manifest claiming a pass or fail on
    #: a check that view-rectangle gating has not yet closed.  -1 means not
    #: measured (audit disabled or did not render).
    annotation_overlap_count: int = -1

    def __post_init__(self) -> None:
        # An unset gate is the single most dangerous state: it must read as its
        # fail-closed default, never as absent-and-therefore-ignored.
        for gate in NULLABLE_GATE_ORDER:
            self.verdicts.setdefault(gate, _DEFAULT[gate])
        for gate, verdict in list(self.verdicts.items()):
            self._check(gate, verdict)

    @staticmethod
    def _check(gate: Gate, verdict: Verdict) -> None:
        if gate not in _ALLOWED:
            raise KeyError(f"unknown quality gate {gate!r}")
        if verdict not in _ALLOWED[gate]:
            allowed = ", ".join(sorted(v.value for v in _ALLOWED[gate]))
            raise ValueError(
                f"{gate.value} cannot be {verdict.value}; allowed: {allowed}"
            )

    def set(self, gate: Gate, verdict: Verdict, reason: str = "") -> "QualityManifest":
        """Record one gate verdict (fail-closed: an invalid pair raises)."""
        self._check(gate, verdict)
        self.verdicts[gate] = verdict
        if reason:
            self.notes.append(f"{gate.value}={verdict.value}: {reason}")
        return self

    def add_issue(self, gate: Gate, code: str, message: str, detail: str = "") -> None:
        self.issues.append(QualityIssue(gate=gate, code=code, message=message, detail=detail))

    @property
    def generation_gates_passed(self) -> bool:
        """True when the package generated and its model/geometry contract is
        internally consistent.

        This is the *generation* verdict only. It deliberately says nothing
        about required content, layout, reference fidelity or the engineering
        review — each of those is reported as its own gate, because a package
        can generate and validate perfectly while still missing a required
        detail, colliding on the sheet, differing from its reference, or
        awaiting a structural review. ``accepted`` is the composite.
        """
        return all(self.verdicts[g] in _NON_FAILING for g in GENERATION_GATES)

    @property
    def quality_and_layout_passed(self) -> bool:
        """True when the generation gates pass *and* the measured content and
        layout gates pass. Still excludes reference fidelity and the review."""
        return (
            self.generation_gates_passed
            and self.verdicts[Gate.REQUIRED_CONTENT] in _NON_FAILING
            and self.verdicts[Gate.LAYOUT] in _NON_FAILING
        )

    @property
    def accepted(self) -> bool:
        """True only when the package is fully accepted: the generation gates
        and the content/layout gates pass AND reference fidelity passed AND the
        engineering review is recorded as approved."""
        return (
            self.quality_and_layout_passed
            and self.verdicts[Gate.REFERENCE_FIDELITY] is Verdict.PASSED
            and self.verdicts[Gate.ENGINEERING_REVIEW] is Verdict.APPROVED
        )

    @property
    def status(self) -> str:
        """A single human-readable status, never overstating the evidence."""
        if self.accepted:
            return "ACCEPTED"
        if self.quality_and_layout_passed:
            return ("GENERATION/CONTENT/LAYOUT GATES PASSED — acceptance pending "
                    "reference/review")
        if self.generation_gates_passed:
            return ("GENERATION GATES PASSED — acceptance pending "
                    "content/layout/reference/review")
        return "DRAFT — generation gates not all passed"

    def to_json(self) -> dict[str, Any]:
        """Ordered JSON with every gate present and its verdict as a plain
        string (the enum is serialised by value, not by repr).

        The two composite flags stay distinguishable: ``generation_gates_passed``
        covers only generation/model/geometry, ``accepted`` covers everything.
        Every individual gate verdict is present alongside them, so a reader can
        see exactly which of content/layout/reference/review is holding.
        """
        out: dict[str, Any] = {
            gate.value: self.verdicts[gate].value for gate in NULLABLE_GATE_ORDER
        }
        out["generation_gates_passed"] = self.generation_gates_passed
        out["quality_and_layout_passed"] = self.quality_and_layout_passed
        out["accepted"] = self.accepted
        out["status"] = self.status
        out["fixture"] = self.fixture
        out["commit"] = self.commit
        out["annotation_overlap_count"] = self.annotation_overlap_count
        out["issues"] = [i.to_json() for i in self.issues]
        out["notes"] = list(self.notes)
        return out


__all__ = [
    "ACCEPTANCE_GATES",
    "GENERATION_GATES",
    "Gate",
    "QualityIssue",
    "QualityManifest",
    "Verdict",
]
