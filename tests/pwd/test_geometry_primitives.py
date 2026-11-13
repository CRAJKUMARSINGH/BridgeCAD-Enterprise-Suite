"""The booklet primitives, asserted against the booklet's own numbers.

Types 004, 014 and 015 are the three families the generic span/depth engine
cannot express, so each has a geometry module under
``bridgecad_draw.geometry``.  These tests pin the counts the sheets and the QA
rows are built on — 11 cells, 25 schedule stations, 5 ribs, 27 blocks, 52 gaps
— using the values printed in ``booklet_oracle.json`` and
``arch_schedule_014.json`` rather than values that merely satisfy the code.

Two numbers in the patch series do not survive contact with the booklet, and
the assertions below record the corrected ones instead of bending the modules:

* ``parabola_deviation`` — the series quotes 3469 mm, which is the *drop from
  the crown* at the X = 5229 mm station (7805 − 4336), not a deviation; it also
  pairs X = 4183 with the tabulated 4336, which is the X = 5229 row.  Measured
  the only self-consistent way — X from the crown, which is what makes the
  booklet's claim that the equation "reproduces the crown" true — the printed
  flanks run **825 mm** proud of the parabola.
* ``block_count`` — the series quotes 27, but its own rule (arc length in
  2.0–2.5 m, midpoint 2.25 m) gives 28 for the 61.94 m span, and 28's mean
  block of 2.218 m is inside the stated window.  27 is the booklet's *printed*
  count and is carried as the card's locked default; the derivation is only the
  fallback when no book value is given.

Run:  pytest tests/pwd/test_geometry_primitives.py -q
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from bridgecad_draw.geometry import (
    BLOCK_LEN_MAX_M,
    BLOCK_LEN_MIN_M,
    PARABOLA_A,
    CellGrid,
    Violation,
    assert_closed,
    block_count,
    blocks,
    gap_pairs,
    gap_segments,
    offset,
    parabola_deviation,
    rib_stations,
    ring_outline,
    socket,
    stations,
    strip_offsets,
)

pytestmark = pytest.mark.draw

SCHEDULE = json.loads(
    (Path(__file__).parent / "arch_schedule_014.json").read_text(encoding="utf-8")
)["schedule_mm"]

SPRINGING_CH, SPRINGING_RL = 0.0, 101.5


# ── 004 — multi-unit box cell lattice ────────────────────────────────────────
def test_004_lattice_matches_booklet():
    """4 + 3 + 4 cells on a 61.05 m run, 44 haunches — the booklet's own layout."""
    grid = CellGrid((4, 3, 4), 5.0, 0.55, 0.5, 100.415)

    assert len(list(grid.cells())) == 11
    assert grid.unit_lengths() == pytest.approx([22.2, 16.65, 22.2], abs=0.01)
    assert grid.total_length() == pytest.approx(61.05, abs=0.01)
    assert sum(len(c.haunches()) for c in grid.cells()) == 44


def test_004_units_share_their_junction_wall():
    """A unit is n cells on n pitches — an end wall per unit would double it."""
    grid = CellGrid((4, 3, 4), 5.0, 0.55, 0.5, 100.415)

    assert grid.pitch == pytest.approx(5.55)
    assert grid.total_length() == pytest.approx(sum(grid.unit_lengths()))
    assert all(n * grid.pitch == pytest.approx(length)
               for n, length in zip(grid.unit_cell_counts, grid.unit_lengths()))


def test_004_every_cell_is_closed():
    grid = CellGrid((4, 3, 4), 5.0, 0.55, 0.5, 100.415)
    assert_closed(grid)

    for cell in grid.cells():
        assert len(cell.bands()) == 4
        assert len(cell.haunches()) == 4
        assert cell.x1 - cell.x0 == pytest.approx(5.0)
        assert cell.y_t - cell.y_b == pytest.approx(5.0)


def test_004_cutoff_wall_is_measured_from_the_raft_underside():
    """0.6 m of raft face + 0.30 m below scour, 2.5×d with a 5.0 m floor."""
    grid = CellGrid((4, 3, 4), 5.0, 0.55, 0.5, 100.415)

    ch, length, depth = grid.cutoff_wall(raft_bottom_rl=99.0, scour_rl=98.4)
    assert (ch, length, depth) == pytest.approx((0.0, 5.0, 0.90))

    deep = grid.cutoff_wall(raft_bottom_rl=96.0, scour_rl=98.4 - 3.0 - 0.30)
    assert deep[1] == pytest.approx(max(2.5 * deep[2], 5.0))


def test_004_cutoff_wall_refuses_a_raft_above_scour():
    grid = CellGrid((4, 3, 4), 5.0, 0.55, 0.5, 100.415)
    with pytest.raises(Violation):
        grid.cutoff_wall(raft_bottom_rl=98.0, scour_rl=99.0)


# ── 014 — open-spandrel arch on the printed coordinate schedule ──────────────
def test_014_schedule_places_25_stations():
    """25 rows, 24 pitches of 1045.833 mm — not the 31 the series first said."""
    sofs = stations(SCHEDULE, SPRINGING_CH, SPRINGING_RL)

    assert len(sofs) == 25
    assert len(SCHEDULE) == 25
    assert sofs[0] == pytest.approx((0.0, 101.5))
    assert sofs[-1] == pytest.approx((25.1, 101.5))
    assert max(y for _, y in sofs) == pytest.approx(101.5 + 7.805)


def test_014_schedule_must_be_a_closed_table():
    with pytest.raises(Violation):
        stations(SCHEDULE[:4], SPRINGING_CH, SPRINGING_RL)

    open_ended = list(SCHEDULE)
    open_ended[-1] = (25100, 500)
    with pytest.raises(Violation):
        stations(open_ended, SPRINGING_CH, SPRINGING_RL)


def test_014_ribs_land_on_schedule_stations():
    """4.183 m is exactly four 1045.833 mm pitches, so no point is interpolated."""
    sofs = stations(SCHEDULE, SPRINGING_CH, SPRINGING_RL)
    ribs = rib_stations(sofs)

    assert len(ribs) == 5
    assert [x for x, _ in ribs] == pytest.approx([4.1833, 8.3667, 12.55, 16.7333, 20.9167], abs=1e-4)


def test_014_rib_spacing_off_the_station_grid_is_a_transcription_error():
    sofs = stations(SCHEDULE, SPRINGING_CH, SPRINGING_RL)
    with pytest.raises(Violation):
        rib_stations(sofs, rib_m=3.0)


def test_014_ring_thickness_is_constant_at_every_station():
    sofs = stations(SCHEDULE, SPRINGING_CH, SPRINGING_RL)
    extrados = offset(sofs, 0.35)

    assert all(math.dist(a, b) == pytest.approx(0.35, abs=0.002)
               for a, b in zip(sofs, extrados))

    ring = ring_outline(sofs, 0.35)
    assert ring[0] == ring[-1], "the ring outline must close"
    assert len(ring) == 2 * len(sofs) + 2


def test_014_parabola_reproduces_the_crown_and_springings_only():
    """The check is real: both ends agree to under 1 mm, the flanks run 825 mm proud."""
    apex = max(SCHEDULE, key=lambda p: p[1])

    assert parabola_deviation(SCHEDULE) == pytest.approx(825.0, abs=1.0)

    for x, y in (SCHEDULE[0], apex, SCHEDULE[-1]):
        assert abs((apex[1] - y) - PARABOLA_A * (x - apex[0]) ** 2 / 1000.0) < 1.0


def test_014_parabola_coefficient_is_the_booklet_four_rise_over_span_squared():
    """A = 4·rise/span² — which is why the equation is a parabola, not a fit."""
    assert PARABOLA_A == pytest.approx(4 * 7.805 / 25.1**2, rel=1e-4)


# ── 015 — precast block arch ─────────────────────────────────────────────────
def test_015_block_count_derives_into_the_declared_window():
    """The series' 27 is the printed book value; its own rule derives 28 here."""
    n = block_count(61.94, 1.996)
    assert n == 28

    mean_block = 62.115 / n
    assert BLOCK_LEN_MIN_M <= mean_block <= BLOCK_LEN_MAX_M


def test_015_blocks_span_the_span_at_the_declared_rise():
    n = block_count(61.94, 1.996)
    arch = blocks(61.94, 1.996, n)

    assert len(arch) == n
    assert arch[0].p0[0] == pytest.approx(-61.94 / 2, abs=1e-6)
    assert arch[-1].p1[0] == pytest.approx(61.94 / 2, abs=1e-6)
    assert max(y for b in arch for _, y in (b.p0, b.p1)) == pytest.approx(1.996, abs=1e-3)


def test_015_gaps_are_52():
    """2 inter-strip gaps × 26 radial joints — the series' ``gap_pairs * 2`` omits the joints."""
    assert gap_pairs(3, 10.0, 0.1) == 2
    assert gap_segments(27, 3) == 52


def test_015_strips_are_symmetric_about_the_centreline():
    assert strip_offsets(3, 10.0, 0.1) == pytest.approx([-10.1, 0.0, 10.1])
    assert sum(strip_offsets(3, 10.0, 0.1)) == pytest.approx(0.0)


def test_015_socket_is_centred_on_its_block():
    arch = blocks(61.94, 1.996, 4)
    x_left, y_mid, w, d = socket(arch[1])

    assert (w, d) == (0.62, 0.20)
    assert x_left + w / 2 == pytest.approx((arch[1].p0[0] + arch[1].p1[0]) / 2)
    assert y_mid == pytest.approx((arch[1].p0[1] + arch[1].p1[1]) / 2)
