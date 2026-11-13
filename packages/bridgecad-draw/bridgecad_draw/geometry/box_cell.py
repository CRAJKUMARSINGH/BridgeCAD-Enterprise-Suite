"""Multi-unit R.C.C. box cell lattice (booklet type 004).

Geometry only — no DXF.  The lattice is fully determined by the cell counts per
unit, the clear cell size and the wall thickness; nothing is hand-placed.  A cell
is closed by exactly four boundary bands plus four corner haunches, and that
count is what the QA row asserts, so a dropped wall cannot pass unnoticed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from ._errors import Violation

Band = tuple[float, float, float, float]  # x0, y0, x1, y1
Pt = tuple[float, float]


@dataclass(frozen=True)
class Cell:
    x0: float
    x1: float
    y_b: float
    y_t: float
    haunch: float

    def bands(self) -> tuple[Band, Band, Band, Band]:
        """Top slab, bottom slab, left wall, right wall — the four closures."""
        return (
            (self.x0, self.y_t, self.x1, self.y_t),  # top
            (self.x0, self.y_b, self.x1, self.y_b),  # bottom
            (self.x0, self.y_b, self.x0, self.y_t),  # left
            (self.x1, self.y_b, self.x1, self.y_t),  # right
        )

    def haunches(self) -> tuple[list[Pt], list[Pt], list[Pt], list[Pt]]:
        """Four 45° fillets, one per internal corner."""
        h = self.haunch
        return (
            [(self.x0, self.y_t - h), (self.x0 + h, self.y_t)],
            [(self.x1 - h, self.y_t), (self.x1, self.y_t - h)],
            [(self.x1, self.y_b + h), (self.x1 - h, self.y_b)],
            [(self.x0 + h, self.y_b), (self.x0, self.y_b + h)],
        )


@dataclass(frozen=True)
class CellGrid:
    unit_cell_counts: tuple[int, ...]
    clear_m: float
    wall_m: float
    haunch_m: float
    soffit_rl: float
    origin_ch: float = 0.0

    @property
    def pitch(self) -> float:
        return self.clear_m + self.wall_m

    def unit_lengths(self) -> list[float]:
        """A unit is ``n`` cells on ``n`` pitches; the boundary wall is shared.

        Units abut, so consecutive units share the wall at their junction and
        the unit length is ``n × pitch`` — counting an end wall per unit would
        draw a double wall at every junction and make the lattice 3 × 0.55 m
        longer than the deck it sits under.
        """
        return [n * self.pitch for n in self.unit_cell_counts]

    def total_length(self) -> float:
        return sum(self.unit_lengths())

    def cells(self) -> Iterator[Cell]:
        x = self.origin_ch
        for n in self.unit_cell_counts:
            for _ in range(n):
                yield Cell(
                    x,
                    x + self.clear_m,
                    self.soffit_rl - self.clear_m,
                    self.soffit_rl,
                    self.haunch_m,
                )
                x += self.pitch

    def cutoff_wall(self, raft_bottom_rl: float, scour_rl: float) -> tuple[float, float, float]:
        """Detached cut-off wall: ``(chainage, length, depth)``.

        Depth runs from the raft *underside* down to scour + 0.30 m — measured
        from the soffit it over-deepened every tall box, because the raft sits
        a clear cell lower again.  Length is 2.5 × depth with a 5.0 m floor
        (booklet note 14).
        """
        depth = (raft_bottom_rl - scour_rl) + 0.30
        if depth <= 0:
            raise Violation(f"cut-off depth {depth:.2f} m — raft is above scour")
        return self.origin_ch, max(2.5 * depth, 5.0), depth


def assert_closed(grid: CellGrid) -> None:
    """Every cell must carry 4 bands and 4 haunches."""
    for i, cell in enumerate(grid.cells(), 1):
        if len(cell.bands()) != 4 or len(cell.haunches()) != 4:
            raise AssertionError(f"cell {i} is not closed")
