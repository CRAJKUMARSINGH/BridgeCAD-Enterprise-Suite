"""Contract tests for the span/pier loop helpers in ``geometry.long_section``."""

from __future__ import annotations

from itertools import pairwise

import pytest

from bridgecad_core.geometry.long_section import (
    pier_positions,
    span_boundaries,
    span_lengths_m,
)

LAYOUTS = [[12.0], [12.0, 15.0], [10.0, 12.0, 14.0], [8.0, 10.0, 12.0, 14.0, 16.0]]


@pytest.mark.parametrize("lengths", LAYOUTS)
def test_span_lengths_count_and_values(span_variant, lengths):
    project = span_variant(lengths)
    # CONTRACT: len(span_lengths_m(project)) == nspan, values preserved in order.
    assert len(span_lengths_m(project)) == len(lengths)
    assert span_lengths_m(project) == pytest.approx([float(x) for x in lengths])


@pytest.mark.parametrize("lengths", LAYOUTS)
def test_boundaries_contract(span_variant, lengths):
    project = span_variant(lengths)
    boundaries = span_boundaries(project)
    # CONTRACT: nspan + 1 boundaries, start at 0, strictly increasing, end at total.
    assert len(boundaries) == len(lengths) + 1
    assert boundaries[0] == 0.0
    assert all(b < a for b, a in pairwise(boundaries))
    assert boundaries[-1] == pytest.approx(sum(lengths))


@pytest.mark.parametrize("lengths", LAYOUTS)
def test_pier_contract(span_variant, lengths):
    project = span_variant(lengths)
    piers = pier_positions(project)
    boundaries = span_boundaries(project)
    # CONTRACT: max(nspan - 1, 0) piers, each coincident with an interior boundary.
    assert len(piers) == max(len(lengths) - 1, 0)
    for pier in piers:
        assert pier in boundaries[1:-1]


def test_single_span_has_no_interior_piers(span_variant):
    assert pier_positions(span_variant([12.0])) == []


def test_five_span_layout_boundary_chainage(span_variant):
    project = span_variant([8.0, 10.0, 12.0, 14.0, 16.0])
    assert span_boundaries(project) == pytest.approx([0.0, 8.0, 18.0, 30.0, 44.0, 60.0])
    assert pier_positions(project) == pytest.approx([8.0, 18.0, 30.0, 44.0])
