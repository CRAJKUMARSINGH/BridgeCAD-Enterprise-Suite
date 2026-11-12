"""
bridgecad_draw.layout_audit — read the *rendered* sheet, not the intent.

The QA rows that police the drawing itself (``QA-SH-TEXT-NO-OVERLAP``,
``QA-SH-ENTITY-IN-FRAME``, ``QA-SH-SCALE-ON-LADDER``, ``QA-DR-LAYER-COVERAGE``,
``QA-SH-BAND-COUNT``, ``QA-DR-NTS-CLAIM``) cannot be answered from the
``BridgeProject`` model: the model says what the engineer asked for, the DXF
says what the draughtsman actually put on the paper. Auditing the intent is how
a sheet passes QA while looking wrong.

Rendering the whole 9-sheet package is expensive — far too expensive to run
inside every :func:`bridgecad_core.validation.run_all` call. The audit is
therefore **opt-in**: ``set_enabled(True)`` (or ``BRIDGECAD_LAYOUT_AUDIT=1``)
turns it on for the booklet gate and for the fail-proving tests. While it is
off every accessor returns an empty result, so the QA rows report "not
evaluated" rather than a false PASS.

Results are cached per project instance, so the six rows that read the audit
pay for one render between them.
"""

from __future__ import annotations

import math
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "BBox",
    "LayoutAudit",
    "audit_enabled",
    "collect",
    "set_enabled",
]

#: Environment switch — the CI/booklet gate sets this; interactive runs leave it
#: unset so a validation sweep does not render 135 sheets to answer six rows.
_ENV_FLAG = "BRIDGECAD_LAYOUT_AUDIT"

#: ``None`` → follow the environment. ``True``/``False`` → explicit override,
#: used by tests that must force the audit on without mutating the process env.
_override: bool | None = None

#: id(project) → LayoutAudit. Keyed by identity, not equality: the audit is a
#: function of the object graph that produced it, and a rebuilt project is a
#: different drawing.
_CACHE: dict[int, LayoutAudit] = {}

#: First rung of the scale ladder — kept in step with ``fit.LADDER``. Duplicated
#: rather than imported so ``layout_audit`` stays importable when ``fit`` is
#: mid-refactor; ``test_scale_ladder`` asserts the two agree.
_SCALE_LADDER = (20, 25, 50, 75, 100, 150, 200, 250, 300, 400, 500)

#: A1 landscape, matching ``titleblocks._SHEET_SIZES["A1"]``.
_SHEET_W_MM = 841.0
_SHEET_H_MM = 594.0

#: Inner drawing border, ``titleblocks._MARGIN``.
_FRAME_MARGIN_MM = 10.0


def set_enabled(flag: bool | None) -> None:
    """Force the audit on/off, or ``None`` to follow the environment."""
    global _override
    _override = flag
    _CACHE.clear()


def audit_enabled() -> bool:
    """True when a layout audit should actually render the package."""
    if _override is not None:
        return _override
    return os.environ.get(_ENV_FLAG, "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class BBox:
    """Axis-aligned text bounding box, in sheet millimetres."""

    x0: float
    y0: float
    x1: float
    y1: float
    text: str = ""
    sheet: str = ""

    @property
    def width(self) -> float:
        return max(0.0, self.x1 - self.x0)

    @property
    def height(self) -> float:
        return max(0.0, self.y1 - self.y0)

    def overlaps(self, other: BBox, tol: float = 0.5) -> bool:
        """True when the two boxes intersect by more than *tol* mm on each axis.

        ``tol`` absorbs the half-millimetre of slop inherent in estimating a
        text width from its character count — without it every adjacent label
        on a dense sheet reads as a collision.
        """
        return (
            self.x0 < other.x1 - tol
            and other.x0 < self.x1 - tol
            and self.y0 < other.y1 - tol
            and other.y0 < self.y1 - tol
        )

    @classmethod
    def from_entity(cls, e: Any, sheet: str = "") -> BBox:
        """Build a box from a live ``TEXT``/``MTEXT`` entity."""
        dxf = e.dxf
        content = getattr(dxf, "text", None) or getattr(e, "text", "") or ""
        height = float(getattr(dxf, "height", None) or getattr(dxf, "char_height", 0.0) or 0.0)
        point = getattr(dxf, "insert", None) or getattr(dxf, "align_point", None) or (0, 0, 0)
        x, y = float(point[0]), float(point[1])
        # 0.6 em is the usual mean glyph advance for a condensed CAD stroke font;
        # it only has to be good enough to decide "do these two labels collide".
        width = 0.6 * height * max(len(str(content)), 1)
        rotation = math.radians(float(getattr(dxf, "rotation", 0.0) or 0.0))
        dx = width * math.cos(rotation)
        dy = abs(width * math.sin(rotation))
        return cls(
            x0=min(x, x + dx),
            x1=max(x, x + dx),
            y0=min(y, y + dy) - (height if dy else 0.0),
            y1=max(y, y + dy) + (0.0 if dy else height),
            text=str(content),
            sheet=sheet,
        )


@dataclass
class LayoutAudit:
    """Everything the drawing-side QA rows need, gathered from the DXF once."""

    rendered: bool = False
    error: str = ""
    text_boxes: list[BBox] = field(default_factory=list)
    outside_frame: list[str] = field(default_factory=list)
    layers_drawn: set[str] = field(default_factory=set)
    printed_scales: list[tuple[str, int]] = field(default_factory=list)
    band_counts: dict[str, int] = field(default_factory=dict)
    nts_claims: list[tuple[str, bool]] = field(default_factory=list)


def _frame() -> tuple[float, float, float, float]:
    """Inner drawing border as ``(x0, y0, x1, y1)`` in millimetres."""
    m = _FRAME_MARGIN_MM
    return m, m, _SHEET_W_MM - m, _SHEET_H_MM - m


def _parse_scale(text: str) -> int | None:
    """Pull the denominator out of ``SCALE 1:100`` / ``SCALE: 1:100``."""
    upper = text.upper()
    marker = upper.find("1:")
    if marker < 0:
        return None
    digits = ""
    for ch in upper[marker + 2 :]:
        if ch.isdigit():
            digits += ch
        else:
            break
    return int(digits) if digits else None


def _render_to_tempdir(project: Any) -> list[Path]:
    """Render the 9-sheet package into a scratch directory and return the DXFs."""
    from .booklet import generate_package

    tmp = Path(tempfile.mkdtemp(prefix="bridgecad_audit_"))
    return list(generate_package(project, tmp, prefix="AUDIT"))


def collect(project: Any) -> LayoutAudit:
    """Return the cached :class:`LayoutAudit` for *project*.

    While the audit is disabled this is an empty, ``rendered=False`` record —
    callers must treat that as "unknown", never as "clean".
    """
    if not audit_enabled():
        return LayoutAudit()

    key = id(project)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    audit = _collect_uncached(project)
    _CACHE[key] = audit
    return audit


def _collect_uncached(project: Any) -> LayoutAudit:
    import ezdxf
    from ezdxf import bbox as ezbbox

    audit = LayoutAudit()
    try:
        dxf_paths = _render_to_tempdir(project)
    except Exception as exc:  # noqa: BLE001 — a failed render must not mask a QA row
        audit.error = f"{type(exc).__name__}: {exc}"
        return audit

    audit.rendered = True
    x0, y0, x1, y1 = _frame()

    for path in dxf_paths:
        try:
            doc = ezdxf.readfile(str(path))
        except Exception as exc:  # noqa: BLE001
            audit.error = f"{path.name}: {type(exc).__name__}: {exc}"
            continue
        msp = doc.modelspace()
        sheet = path.stem

        for e in msp:
            layer = e.dxf.layer
            audit.layers_drawn.add(layer)
            if layer == "BORDER-OUTER" or e.dxftype() == "DIMENSION":
                continue
            try:
                ext = ezbbox.extents([e])
            except Exception:  # noqa: BLE001 — entities without extents are skipped
                continue
            # An entity with no computable extent (e.g. an empty polyline) yields
            # an empty BoundingBox whose unpack raises; it has nothing to test.
            if not getattr(ext, "has_data", True):
                continue
            lo, hi = ext.extmin, ext.extmax
            if lo.x < x0 - 1.0 or lo.y < y0 - 1.0 or hi.x > x1 + 1.0 or hi.y > y1 + 1.0:
                audit.outside_frame.append(f"{sheet}:{e.dxftype()}({layer})")

        for e in msp.query("TEXT MTEXT"):
            box = BBox.from_entity(e, sheet=sheet)
            audit.text_boxes.append(box)
            denom = _parse_scale(box.text)
            if denom is not None:
                audit.printed_scales.append((sheet, denom))

        for text_ent in msp.query("TEXT MTEXT"):
            content = (
                getattr(text_ent.dxf, "text", None)
                or getattr(text_ent, "text", "")
                or ""
            ).upper()
            if "BAND" in content and "/" in content:
                audit.band_counts[sheet] = audit.band_counts.get(sheet, 0) + 1
            if "NTS" in content or "NOT TO SCALE" in content:
                audit.nts_claims.append((sheet, True))

    return audit


def scale_on_ladder(denom: int) -> bool:
    """True when *denom* is a rung of the standard scale ladder (ISO 5455)."""
    return denom in _SCALE_LADDER
