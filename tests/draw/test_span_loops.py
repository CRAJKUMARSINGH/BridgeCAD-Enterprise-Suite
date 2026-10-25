"""Wing-06 — span and pier loop counts.

The bug: an off-by-one drew the wrong number of piers, so a 3-span bridge got
2 or 4. The invariant is structural, not cosmetic:
    spans  = nspan
    piers  = nspan - 1   (intermediate only; abutments are not piers)
"""
from __future__ import annotations

import pytest

from . import contract

pytestmark = pytest.mark.draw


@pytest.mark.parametrize("nspan", [1, 2, 3, 5, 11])
def test_span_and_pier_counts_are_exact(nspan: int):
    project = contract.make_project("continuous_3x12m")
    project.geometry_input.nspan = nspan
    project.geometry_input.span_length_m = 12.0

    boundaries = contract.span_boundaries(project)
    piers = contract.pier_positions(project)

    assert len(boundaries) == nspan + 1, (
        f"nspan={nspan}: {len(boundaries)} boundaries, expected {nspan + 1}"
    )
    assert len(piers) == max(nspan - 1, 0), (
        f"nspan={nspan}: {len(piers)} intermediate piers, expected {nspan - 1}"
    )


def test_single_span_has_no_intermediate_piers():
    project = contract.make_project("simple_12m")
    assert contract.pier_positions(project) == []


def test_single_span_still_has_two_boundaries():
    project = contract.make_project("simple_12m")
    assert len(contract.span_boundaries(project)) == 2


def test_boundaries_are_monotonic_and_contiguous():
    project = contract.make_project("continuous_3x12m")
    b = contract.span_boundaries(project)
    assert b == sorted(b), f"boundaries not monotonic: {b}"
    gaps = [b[i + 1] - b[i] for i in range(len(b) - 1)]
    assert all(g > 0 for g in gaps), f"non-positive span: {gaps}"


def test_piers_sit_strictly_inside_the_boundaries():
    project = contract.make_project("continuous_3x12m")
    b = contract.span_boundaries(project)
    for p in contract.pier_positions(project):
        assert b[0] < p < b[-1], f"pier at {p} outside the bridge"


def test_piers_are_offset_from_boundaries_by_half_a_span():
    """A pier sits on a boundary between spans, never on an end."""
    project = contract.make_project("continuous_3x12m")
    b = contract.span_boundaries(project)
    for p in contract.pier_positions(project):
        assert min(abs(p - x) for x in b) == pytest.approx(0.0, abs=1e-9), (
            f"pier at {p} does not coincide with a span boundary"
        )


def test_simple_span_sheet_annotates_absence_explicitly():
    """A blank where a pier should be reads to an auditor as a missing call.
    The simple-span case must say so in text."""
    from .dxf_assert import text_of
    project = contract.make_project("simple_12m")
    doc = contract.build_sheet(project, "sheet5_pier_abutment_details")
    blob = " ".join(text_of(doc)).upper()
    assert "PIER" in blob
    assert any(phrase in blob for phrase in (
        "NO INTERMEDIATE PIER", "NO INTERMEDIATE PIERS", "SIMPLE SPAN",
    )), "simple span does not annotate the absence of intermediate piers"


@pytest.mark.parametrize("nspan", [2, 3, 5])
def test_pier_count_in_the_drawing_matches_the_model(nspan: int):
    """The drawing must agree with the model — a correct model and a wrong
    drawing is still a wrong drawing."""
    from .dxf_assert import text_of
    project = contract.make_project("continuous_3x12m")
    project.geometry_input.nspan = nspan
    doc = contract.build_sheet(project, "sheet2_long_section")
    blob = " ".join(text_of(doc)).upper()
    assert f"PIER {nspan - 1}" in blob or f"P{nspan - 1}" in blob, (
        f"nspan={nspan}: drawing does not label pier {nspan - 1}"
    )
