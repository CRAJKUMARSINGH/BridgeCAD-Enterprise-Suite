"""Pure-function tests for foundation / plan geometry helpers."""

from __future__ import annotations

import math
from itertools import combinations

import pytest

from bridgecad_core.geometry.foundation import (
    PileGroupLayout,
    _rectangular_grid,
    _std_cruciform_5,
    _std_hexagonal_7,
    _std_triangular_3,
    compute_pile_group_layout,
)
from bridgecad_core.geometry.plan import _rotate
from bridgecad_core.types import FoundationType


def _centroid(points: list[tuple[float, float]]) -> tuple[float, float]:
    n = len(points)
    return (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n)


def _pairwise_distances(points: list[tuple[float, float]]) -> list[float]:
    return [math.dist(a, b) for a, b in combinations(points, 2)]


# ---------------------------------------------------------------------------
# Standard non-grid layouts
# ---------------------------------------------------------------------------


def test_triangular_3_is_equilateral_and_centred():
    points = _std_triangular_3(2.5)
    assert len(points) == 3
    for distance in _pairwise_distances(points):
        assert distance == pytest.approx(2.5)
    assert _centroid(points) == pytest.approx((0.0, 0.0))


def test_cruciform_5_layout():
    points = _std_cruciform_5(2.0)
    assert len(points) == 5
    assert points[0] == (0.0, 0.0)  # centre pile
    for outer in points[1:]:
        assert math.dist(outer, (0.0, 0.0)) == pytest.approx(2.0)
    assert _centroid(points) == pytest.approx((0.0, 0.0))


def test_hexagonal_7_layout():
    points = _std_hexagonal_7(2.0)
    assert len(points) == 7
    assert points[0] == (0.0, 0.0)  # centre pile
    outer = points[1:]
    for p in outer:
        assert math.dist(p, (0.0, 0.0)) == pytest.approx(2.0)
    for i in range(6):  # regular hexagon: adjacent vertices 1 spacing apart
        assert math.dist(outer[i], outer[(i + 1) % 6]) == pytest.approx(2.0)
    assert _centroid(points) == pytest.approx((0.0, 0.0), abs=1e-9)


@pytest.mark.parametrize("n", [1, 2, 3, 4, 6, 8])
def test_rectangular_grid_produces_n_positions(n):
    rows, cols, positions = _rectangular_grid(n, 2.0)
    assert len(positions) == n
    assert rows * cols >= n
    assert cols == math.ceil(math.sqrt(n))


@pytest.mark.parametrize("n", [2, 4, 6])
def test_rectangular_grid_perfect_grids_use_exact_cells(n):
    rows, cols, _positions = _rectangular_grid(n, 2.0)
    assert rows * cols == n


def test_rectangular_grid_is_centred_and_honours_spacing():
    _rows, _cols, positions = _rectangular_grid(4, 2.0)
    assert _centroid(positions) == pytest.approx((0.0, 0.0))
    xs = sorted({p[0] for p in positions})
    assert xs[1] - xs[0] == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# PileGroupLayout dataclass + factory
# ---------------------------------------------------------------------------


def test_pile_group_layout_defaults_are_empty():
    layout = PileGroupLayout()
    assert layout.pile_positions == []
    assert layout.pile_cap_corners == []
    assert layout.piles_per_group == 0


def test_compute_pile_group_layout_from_fixture(project):
    layout = compute_pile_group_layout(project)
    assert len(layout.pile_positions) == project.foundation_details.piles_per_pier
    assert layout.pile_diameter_m == pytest.approx(1.0)  # 1000 mm
    assert layout.pile_spacing_m == pytest.approx(2.0)
    assert layout.pile_cap_width_m > 0
    assert layout.pile_cap_length_m > 0


def test_compute_pile_group_layout_cap_has_four_wound_corners(project):
    layout = compute_pile_group_layout(project)
    assert len(layout.pile_cap_corners) == 4
    # BL, BR, TR, TL winding: first two share the bottom edge y.
    assert layout.pile_cap_corners[0][1] == pytest.approx(layout.pile_cap_corners[1][1])


def test_compute_pile_group_layout_well_branch(blank_project):
    blank_project.foundation_details.type = FoundationType.WELL
    layout = compute_pile_group_layout(blank_project)
    assert layout.pile_positions == []
    assert layout.well_outer_radius_m >= 1.5
    assert layout.well_inner_radius_m == pytest.approx(layout.well_outer_radius_m * 0.55)
    assert layout.well_total_depth_m > 0


# ---------------------------------------------------------------------------
# plan._rotate
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "angle_deg, expected",
    [(0.0, (1.0, 0.0)), (90.0, (0.0, 1.0)), (180.0, (-1.0, 0.0)), (360.0, (1.0, 0.0))],
)
def test_rotate_unit_x_axis(angle_deg, expected):
    assert _rotate(1.0, 0.0, math.radians(angle_deg)) == pytest.approx(expected)


def test_rotate_preserves_distance_from_origin():
    x, y = _rotate(3.0, 4.0, math.radians(37.0))
    assert math.hypot(x, y) == pytest.approx(5.0)
