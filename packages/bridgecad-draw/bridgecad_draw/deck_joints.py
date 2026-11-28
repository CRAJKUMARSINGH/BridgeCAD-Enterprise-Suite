"""Intermediate deck joints shared by GAD plan and elevation renderers."""

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

from bridgecad_core.types import SpanConfiguration, SuperstructureType

if TYPE_CHECKING:
    from bridgecad_core.models import BridgeProject

_DISCONTINUOUS_DECKS = frozenset(
    {
        SuperstructureType.SOLID_SLAB,
        SuperstructureType.VOIDED_SLAB,
        SuperstructureType.PREFAB_PSC_SLAB,
        SuperstructureType.RCC_TBEAM,
        SuperstructureType.PSC_IGIRDER,
        SuperstructureType.PSC_I_GIRDER_COMPOSITE,
        SuperstructureType.PSC_U_GIRDER,
        SuperstructureType.PSC_BOX_GIRDER,
    }
)


@dataclass(frozen=True)
class PierJoint:
    pier: int
    station: float
    gap_mm: int | None
    scheduled: bool

    @property
    def half_gap_m(self) -> float:
        return (self.gap_mm or 0) / 2000

    @property
    def faces(self) -> tuple[float, ...]:
        half_gap = self.half_gap_m
        return (self.station - half_gap, self.station + half_gap) if half_gap else (self.station,)


def pier_joints(project: "BridgeProject", pier_stations: Iterable[float]) -> list[PierJoint]:
    """Locate pier breaks required by the deck family or joint schedule.

    Slab, T-beam and PSC girder decks are detailed span by span, including
    workbooks marked continuous. A schedule row supplies the gap when it
    identifies one pier centre unambiguously.
    """
    scheduled = {}
    for row in project.bearings_joints.expansion_joint_schedule:
        location = re.fullmatch(
            r"P(?:IER\s*)?(\d+)(?:[\s-]+(?:CENTRE(?:LINE)?|CENTER(?:LINE)?|CL))?",
            row.location.strip(),
            re.IGNORECASE,
        )
        if location and row.quantity == 1:
            scheduled.setdefault(int(location[1]), set()).add(row.gap_mm)

    separate = (
        project.superstructure.type in _DISCONTINUOUS_DECKS
        or project.bridge_selection.span_configuration == SpanConfiguration.SIMPLY_SUPPORTED
    )
    joints = []
    for pier, station in enumerate(pier_stations, 1):
        gaps = scheduled.get(pier, set())
        if separate or gaps:
            joints.append(
                PierJoint(pier, station, next(iter(gaps)) if len(gaps) == 1 else None, bool(gaps))
            )
    return joints


def deck_intervals(
    start: float, end: float, joints: Iterable[PierJoint]
) -> Iterator[tuple[float, float]]:
    """Deck extents between consecutive joint faces."""
    for joint in joints:
        yield start, joint.station - joint.half_gap_m
        start = joint.station + joint.half_gap_m
    yield start, end
