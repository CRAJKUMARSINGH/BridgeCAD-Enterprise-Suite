"""The fail-closed quality manifest must default to "not accepted".

These tests pin the two properties the acceptance spec asks for: the gate
vocabulary is closed (an invalid pair raises rather than serialising), and
acceptance is only ever reached when every required gate passed *and* the
engineering review is recorded. An unset gate reads NOT_TESTED, never "fine".

Gate-name convention (item 4 of the owner's review):
- ``generation_gates_passed`` — the three mechanically verifiable gates
  (generation, model_validation, geometry_contract).
- ``quality_and_layout_passed`` — generation gates + content + layout.
- ``accepted`` — everything: quality/layout + reference fidelity + engineering review.
These are separate flags with separate meanings; collapsing them into one boolean
would hide which of the four verdict groups is pending.
"""
from __future__ import annotations

import pytest

from bridgecad_qa.quality_manifest import Gate, QualityManifest, Verdict


def test_unset_gates_read_not_tested_and_are_not_accepted():
    m = QualityManifest(fixture="x", commit="abc")
    assert m.verdicts[Gate.LAYOUT] is Verdict.NOT_TESTED
    # The generation gate is unset too, so even the narrower flag is False.
    assert m.generation_gates_passed is False
    assert m.quality_and_layout_passed is False
    assert m.accepted is False
    assert m.status.startswith("DRAFT")


def test_an_invalid_verdict_for_a_gate_raises():
    m = QualityManifest()
    # GENERATION is binary: "not tested" is not a legitimate generation state.
    with pytest.raises(ValueError):
        m.set(Gate.GENERATION, Verdict.NOT_TESTED)
    # A review is never "PASSED" — it is pending or approved.
    with pytest.raises(ValueError):
        m.set(Gate.ENGINEERING_REVIEW, Verdict.PASSED)


def test_an_unknown_gate_raises():
    with pytest.raises(KeyError):
        QualityManifest().set("not_a_gate", Verdict.PASSED)  # type: ignore[arg-type]


def test_generation_gates_pass_while_acceptance_stays_pending():
    """generation_gates_passed and quality_and_layout_passed can both be True
    while accepted is False — reference fidelity and engineering review are
    separate gates, not rolled into the generation/quality pass."""
    m = QualityManifest()
    m.set(Gate.GENERATION, Verdict.SUCCEEDED)
    m.set(Gate.MODEL_VALIDATION, Verdict.PASSED)
    m.set(Gate.GEOMETRY_CONTRACT, Verdict.PASSED)
    m.set(Gate.REQUIRED_CONTENT, Verdict.PASSED)
    m.set(Gate.LAYOUT, Verdict.PASSED)
    m.set(Gate.REFERENCE_FIDELITY, Verdict.BLOCKED)
    m.set(Gate.ENGINEERING_REVIEW, Verdict.PENDING)
    assert m.generation_gates_passed is True
    assert m.quality_and_layout_passed is True
    # Reference fidelity is blocked and the review is pending: not accepted.
    assert m.accepted is False
    assert "pending" in m.status.lower()


def test_acceptance_requires_reference_fidelity_and_an_approved_review():
    m = QualityManifest()
    for gate, verdict in (
        (Gate.GENERATION, Verdict.SUCCEEDED),
        (Gate.MODEL_VALIDATION, Verdict.PASSED),
        (Gate.GEOMETRY_CONTRACT, Verdict.PASSED),
        (Gate.REQUIRED_CONTENT, Verdict.PASSED),
        (Gate.LAYOUT, Verdict.PASSED),
    ):
        m.set(gate, verdict)
    m.set(Gate.REFERENCE_FIDELITY, Verdict.PASSED)
    assert m.accepted is False  # review still PENDING
    m.set(Gate.ENGINEERING_REVIEW, Verdict.APPROVED)
    assert m.accepted is True
    assert m.status == "ACCEPTED"


def test_unresolved_model_validation_blocks_the_generation_pass():
    m = QualityManifest()
    m.set(Gate.GENERATION, Verdict.SUCCEEDED)
    m.set(Gate.MODEL_VALIDATION, Verdict.UNRESOLVED)
    m.set(Gate.GEOMETRY_CONTRACT, Verdict.PASSED)
    m.set(Gate.REQUIRED_CONTENT, Verdict.PASSED)
    m.set(Gate.LAYOUT, Verdict.PASSED)
    assert m.generation_gates_passed is False
    assert m.quality_and_layout_passed is False
    assert m.accepted is False


def test_to_json_serialises_every_gate_by_value():
    m = QualityManifest(fixture="nine_span_slab", commit="deadbeef")
    m.set(Gate.GENERATION, Verdict.SUCCEEDED)
    payload = m.to_json()
    for gate in Gate:
        assert payload[gate.value] == m.verdicts[gate].value
    assert payload["generation"] == "SUCCEEDED"
    assert payload["layout"] == "NOT_TESTED"
    # The JSON carries the explicit, separate flags — not a single gates_passed.
    assert payload["generation_gates_passed"] is False  # layout is still NOT_TESTED
    assert payload["quality_and_layout_passed"] is False
    assert payload["accepted"] is False
    # annotation_overlap_count is present and defaults to -1 (not measured).
    assert payload["annotation_overlap_count"] == -1


def test_annotation_overlap_count_is_carried_in_json():
    m = QualityManifest(fixture="x", commit="abc", annotation_overlap_count=3)
    payload = m.to_json()
    assert payload["annotation_overlap_count"] == 3


def test_issues_are_carried_with_their_gate():
    m = QualityManifest()
    m.add_issue(Gate.MODEL_VALIDATION, "E-MISSING-FOOTING-DEPTH", "no footing thickness")
    payload = m.to_json()
    assert payload["issues"] == [
        {
            "gate": "model_validation",
            "code": "E-MISSING-FOOTING-DEPTH",
            "message": "no footing thickness",
            "detail": "",
        }
    ]


@pytest.mark.parametrize("missing", list(Gate))
def test_acceptance_fails_when_any_single_gate_lacks_evidence(missing):
    evidence = {
        Gate.GENERATION: Verdict.SUCCEEDED,
        Gate.MODEL_VALIDATION: Verdict.PASSED,
        Gate.GEOMETRY_CONTRACT: Verdict.PASSED,
        Gate.REQUIRED_CONTENT: Verdict.PASSED,
        Gate.LAYOUT: Verdict.PASSED,
        Gate.REFERENCE_FIDELITY: Verdict.PASSED,
        Gate.ENGINEERING_REVIEW: Verdict.APPROVED,
    }
    evidence.pop(missing)
    manifest = QualityManifest(verdicts=evidence)
    assert manifest.accepted is False
    assert manifest.to_json()["accepted"] is False
