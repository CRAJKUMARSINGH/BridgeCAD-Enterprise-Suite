"""Text height hierarchy.

Six classes, paper millimetres, IRC:SP:55-2019 Cl. 8.1. Model height is paper
height x the sheet's plot scale, so a 2.5 mm note is 2.5 mm on every sheet at
every scale.

Usage
-----
    from .text import TextClass as T, TextSizer

    ts = TextSizer(frame)
    text(msp, "NOTE 1 ...", x, y, height=ts.h(T.NOTE))
    text(msp, "PLAN VIEW", x, y, height=ts.h(T.HEAD), halign="CENTER")
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

#: Legible minimum on paper. Below this, an A1 sheet stops being readable in
#: the hand and stops being plottable at reduced size.
MIN_PAPER_MM = 2.5


class TextClass(Enum):
    """Paper heights. Values are millimetres on the printed sheet."""

    NOTE = 2.5      # general notes, specification lines
    LABEL = 2.5     # element labels, leader callouts
    DIM = 2.5       # dimension text
    SUBHEAD = 3.5   # sub-view headings, table headers
    HEAD = 5.0      # view titles (PLAN VIEW, SECTION A-A)
    TITLE = 7.0     # sheet title in the title block

    @property
    def paper_mm(self) -> float:
        return self.value

    @property
    def is_title_block(self) -> bool:
        return self is TextClass.TITLE


def _validate() -> None:
    seen: dict[float, TextClass] = {}
    for cls in TextClass:
        if cls.paper_mm < MIN_PAPER_MM:
            raise ValueError(f"{cls.name}: {cls.paper_mm} mm below the {MIN_PAPER_MM} mm minimum")
    # Duplicate values are permitted only between NOTE/LABEL/DIM, which are
    # semantically distinct at the same size.
    for cls in (TextClass.SUBHEAD, TextClass.HEAD, TextClass.TITLE):
        if cls.paper_mm in seen:
            raise ValueError(f"{cls.name} duplicates {seen[cls.paper_mm].name} at {cls.paper_mm} mm")
        seen[cls.paper_mm] = cls


_validate()


@dataclass(frozen=True)
class TextSizer:
    """Resolves a TextClass to model height for one sheet frame."""

    plot_scale: float

    @classmethod
    def from_frame(cls, frame: Any) -> TextSizer:
        return cls(float(frame.plot_scale))

    def h(self, cls: TextClass) -> float:
        """Model-space height that plots at *cls* paper millimetres."""
        return cls.paper_mm * self.plot_scale

    def allowed(self) -> set[float]:
        """Every legal model height on this sheet — for the harness."""
        return {c.paper_mm * self.plot_scale for c in TextClass}

    # Convenience accessors, for the `height=ts.DIM` migration style.
    @property
    def NOTE(self) -> float:
        return self.h(TextClass.NOTE)

    @property
    def LABEL(self) -> float:
        return self.h(TextClass.LABEL)

    @property
    def DIM(self) -> float:
        return self.h(TextClass.DIM)

    @property
    def SUBHEAD(self) -> float:
        return self.h(TextClass.SUBHEAD)

    @property
    def HEAD(self) -> float:
        return self.h(TextClass.HEAD)

    @property
    def TITLE(self) -> float:
        return self.h(TextClass.TITLE)


__all__ = ["TextClass", "TextSizer", "MIN_PAPER_MM"]
