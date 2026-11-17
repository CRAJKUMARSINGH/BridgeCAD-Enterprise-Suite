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
    "Region",
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
from .fit import LADDER as _SCALE_LADDER

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
        """Build a box from a live ``TEXT``/``MTEXT`` entity.

        The anchor is not always the left edge: DXF ``halign`` 1/4 anchors a
        label at its centre and ``halign`` 2 at its right edge, while ``valign``
        2/3 anchor it vertically at the centre/top.  A box built on a fixed
        "text runs right and up from the insert point" assumption over-reports
        every centred/right-aligned label — which manufactures collisions that
        are not on the paper.  Reading the flags gives the box the glyphs
        actually occupy; it makes the count *truer*, it does not suppress a
        real overlap.
        """
        dxf = e.dxf
        content = getattr(dxf, "text", None) or getattr(e, "text", "") or ""
        height = float(getattr(dxf, "height", None) or getattr(dxf, "char_height", 0.0) or 0.0)
        point = getattr(dxf, "insert", None) or getattr(dxf, "align_point", None) or (0, 0, 0)
        x, y = float(point[0]), float(point[1])
        # 0.6 em is the usual mean glyph advance for a condensed CAD stroke font;
        # it only has to be good enough to decide "do these two labels collide".
        width = 0.6 * height * max(len(str(content)), 1)
        rotation = math.radians(float(getattr(dxf, "rotation", 0.0) or 0.0))

        # Horizontal anchor offset from the insert point (DXF group 72).
        halign = int(getattr(dxf, "halign", 0) or 0)
        if halign in (1, 4):  # centred / middle
            anchor_u = -width / 2.0
        elif halign == 2:  # right edge
            anchor_u = -width
        else:  # left, aligned, fit
            anchor_u = 0.0
        # Vertical anchor offset from the insert point (DXF group 73).
        valign = int(getattr(dxf, "valign", 0) or 0)
        if valign == 2:  # middle
            anchor_v = -height / 2.0
        elif valign == 3:  # top edge
            anchor_v = -height
        else:  # baseline / bottom
            anchor_v = 0.0

        cos_r, sin_r = math.cos(rotation), math.sin(rotation)
        corners = [
            (x + along * cos_r - up * sin_r, y + along * sin_r + up * cos_r)
            for along in (anchor_u, anchor_u + width)
            for up in (anchor_v, anchor_v + height)
        ]
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        return cls(
            x0=min(xs),
            x1=max(xs),
            y0=min(ys),
            y1=max(ys),
            text=str(content),
            sheet=sheet,
        )


@dataclass(frozen=True)
class Region:
    """A measured rectangle on the sheet, in millimetres.

    Used for the layout zones the specification requires to be *reserved*
    (§5.1: printable border, title block, notes/schedule zones). The rectangles
    are measured from the drawn DXF rather than assumed from a paper constant,
    so a sheet that is laid out on a different paper size cannot silently pass
    the region gate against the wrong frame.
    """

    x0: float
    y0: float
    x1: float
    y1: float
    name: str = ""

    @property
    def width(self) -> float:
        return max(0.0, self.x1 - self.x0)

    @property
    def height(self) -> float:
        return max(0.0, self.y1 - self.y0)

    @property
    def area(self) -> float:
        return self.width * self.height

    def intersects(self, other: Region, tol: float = 0.5) -> bool:
        """True when the two rectangles overlap by more than *tol* mm per axis."""
        return (
            self.x0 < other.x1 - tol
            and other.x0 < self.x1 - tol
            and self.y0 < other.y1 - tol
            and other.y0 < self.y1 - tol
        )

    def as_tuple(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)


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
    #: Measured layout zones, per sheet name.
    sheet_regions: dict[str, Region] = field(default_factory=dict)
    frame_regions: dict[str, Region] = field(default_factory=dict)
    title_block_regions: dict[str, Region] = field(default_factory=dict)
    notes_regions: dict[str, Region] = field(default_factory=dict)
    #: Entities on a drawing layer that intrude into a reserved zone.
    title_block_intrusions: list[str] = field(default_factory=list)
    notes_intrusions: list[str] = field(default_factory=list)


#: Layers that belong to the sheet furniture rather than to a view. An entity on
#: one of these is allowed inside a reserved zone; anything else is a view
#: primitive that has been placed over the title block or the notes.
_FURNITURE_PREFIXES = ("BORDER-", "TITLEBLK-")
_FURNITURE_LAYERS = frozenset({"TEXT-SPEC", "TEXT-HEADER", "TEXT-TITLE"})



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
    fb_x0, fb_y0, fb_x1, fb_y1 = _frame()  # fallback when a DXF carries no border

    for path in dxf_paths:
        try:
            doc = ezdxf.readfile(str(path))
        except Exception as exc:  # noqa: BLE001
            audit.error = f"{path.name}: {type(exc).__name__}: {exc}"
            continue
        msp = doc.modelspace()
        sheet = path.stem

        # -- pass 1: geometry extents and the sheet's own furniture --------
        extents: list[tuple[Any, str, tuple[float, float, float, float]]] = []
        sheet_rect: tuple[float, float, float, float] | None = None
        frame_rect: tuple[float, float, float, float] | None = None
        tb_candidates: list[tuple[float, float, float, float]] = []

        for e in msp:
            layer = e.dxf.layer
            audit.layers_drawn.add(layer)
            ext = _extent(e, ezbbox)
            if ext is None:
                continue
            extents.append((e, layer, ext))
            x0, y0, x1, y1 = ext
            if layer == "BORDER-OUTER":
                sheet_rect = _union(sheet_rect, (x0, y0, x1, y1))
                continue
            if layer == "BORDER-INNER":
                frame_rect = _union(frame_rect, (x0, y0, x1, y1))
                continue
            if layer == "TITLEBLK-BOX" and e.dxftype() in {"LWPOLYLINE", "POLYLINE"}:
                tb_candidates.append((x0, y0, x1, y1))

        # The heavy outer title-block rectangle is the largest TITLEBLK-BOX
        # rectangle; the internal rules are thin lines and never form a loop.
        tb_rect = max(tb_candidates, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]), default=None)

        # -- text boxes and the reserved zones ----------------------------
        note_corners: list[float] = []
        for e in msp.query("TEXT MTEXT"):
            box = BBox.from_entity(e, sheet=sheet)
            audit.text_boxes.append(box)
            denom = _parse_scale(box.text)
            if denom is not None:
                audit.printed_scales.append((sheet, denom))
            if _is_note_line(box.text):
                note_corners.extend((box.x0, box.y0, box.x1, box.y1))

        if sheet_rect is not None:
            audit.sheet_regions[sheet] = Region(*sheet_rect, name=sheet)
        if frame_rect is not None:
            audit.frame_regions[sheet] = Region(*frame_rect, name=sheet)
        if tb_rect is not None:
            audit.title_block_regions[sheet] = Region(*tb_rect, name=sheet)
        if len(note_corners) >= 4:
            nx0 = min(note_corners[0::4])
            ny0 = min(note_corners[1::4])
            nx1 = max(note_corners[2::4])
            ny1 = max(note_corners[3::4])
            pad = 2.0
            audit.notes_regions[sheet] = Region(
                nx0 - pad, ny0 - pad, nx1 + pad, ny1 + pad, name=sheet
            )

        # -- pass 2: clipping and reserved-zone intrusions ----------------
        bx0, by0, bx1, by1 = frame_rect or (fb_x0, fb_y0, fb_x1, fb_y1)
        for e, layer, (x0, y0, x1, y1) in extents:
            if layer == "BORDER-OUTER":
                continue
            if x0 < bx0 - 1.0 or y0 < by0 - 1.0 or x1 > bx1 + 1.0 or y1 > by1 + 1.0:
                audit.outside_frame.append(f"{sheet}:{e.dxftype()}({layer})")
            if _is_furniture(layer) or e.dxftype() in {"TEXT", "MTEXT"}:
                continue
            ent = Region(x0, y0, x1, y1, name=f"{e.dxftype()}({layer})")
            if tb_rect is not None and ent.intersects(Region(*tb_rect)):
                audit.title_block_intrusions.append(f"{sheet}:{e.dxftype()}({layer})")
            notes = audit.notes_regions.get(sheet)
            if notes is not None and ent.intersects(notes):
                audit.notes_intrusions.append(f"{sheet}:{e.dxftype()}({layer})")

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


def _extent(e: Any, ezbbox: Any) -> tuple[float, float, float, float] | None:
    """A DXF entity's extents as ``(x0, y0, x1, y1)``, or ``None``.

    A ``DIMENSION`` carries its captured block and would report the dimension
    text's own box, not the measured geometry, so it is excluded from every
    geometric gate. An entity with no computable extent (an empty polyline)
    yields an empty ``BoundingBox`` and is likewise skipped.
    """
    if e.dxftype() == "DIMENSION":
        return None
    try:
        ext = ezbbox.extents([e])
    except Exception:  # noqa: BLE001 — entities without extents are skipped
        return None
    if not getattr(ext, "has_data", True):
        return None
    lo, hi = ext.extmin, ext.extmax
    return (float(lo.x), float(lo.y), float(hi.x), float(hi.y))


def _union(
    a: tuple[float, float, float, float] | None, b: tuple[float, float, float, float]
) -> tuple[float, float, float, float]:
    if a is None:
        return b
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def _is_furniture(layer: str) -> bool:
    """True when *layer* is sheet furniture rather than a view primitive."""
    return layer in _FURNITURE_LAYERS or layer.startswith(_FURNITURE_PREFIXES)


_NOTE_LINE_MARKERS = ("NOTES", "NOTE :-", "NOTE:")


def _is_note_line(content: str) -> bool:
    """True when *content* is a footnote line, so the notes zone can be measured.

    The notes block is a text block with a heading and numbered lines; matching
    that shape gives a reserved zone that is *measured* from what the sheet
    actually drew, rather than assumed from a hard-coded rectangle.

    A numbered line is ``"<n>. <text>"`` — a *decimal number is not a note*. The
    old ``head.isdigit()`` test also accepted ``"10.0 m (eff 9.7)"`` (a
    span-length dimension label), which manufactured a phantom notes zone across
    the top of sheet 2 and then reported the deck hatching drawn there as a
    notes-zone intrusion — a layout failure on a sheet that had drawn no notes
    at all. Requiring the ``". "`` separator that every note generator emits
    (``notes.py`` and ``_sheetkit.notes``) keeps the real lines and rejects
    decimals.
    """
    s = content.strip()
    if not s:
        return False
    if any(s.upper().startswith(m) for m in _NOTE_LINE_MARKERS):
        return True
    head, sep, rest = s.partition(".")
    return (
        head.isdigit()
        and sep == "."
        and rest[:1].isspace()
        and bool(rest.strip())
        and len(s) > 12
    )



def scale_on_ladder(denom: int) -> bool:
    """True when *denom* is a rung of the standard scale ladder (ISO 5455)."""
    return denom in _SCALE_LADDER


#: Minimum legible text height on PAPER, millimetres.
TEXT_FLOOR_PAPER_MM = 1.8


@dataclass(frozen=True)
class LayoutChecks:
    """The measurable layout verdicts required by the specification §5.

    ``passed`` is the gate. A sub-check that does not apply to a sheet set (no
    declared notes zone) is reported as not applicable rather than as a pass, so
    the manifest can state what was and was not measured.
    """

    rendered: bool
    clipping_ok: bool
    title_block_ok: bool
    notes_zone_declared: bool
    notes_zone_ok: bool
    scales_ok: bool
    text_floor_ok: bool
    min_text_height_paper_mm: float | None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return (
            self.rendered
            and self.clipping_ok
            and self.title_block_ok
            and (self.notes_zone_ok if self.notes_zone_declared else True)
            and self.scales_ok
            and self.text_floor_ok
        )


def layout_checks(audit: LayoutAudit) -> LayoutChecks:
    """Evaluate the required layout checks against a collected audit.

    The text floor is normalised to PAPER millimetres by the ratio of the
    measured sheet width to A1 (841 mm). Two unit policies coexist in this
    codebase — a paper-space 1:1 sheet and a scaled model-space sheet — and the
    ratio converts either to the paper size the check is stated in, instead of
    silently trusting one policy.
    """
    heights: list[float] = []
    for sheet, box in ((b.sheet, b) for b in audit.text_boxes):
        if box.height <= 0:
            continue
        region = audit.sheet_regions.get(sheet)
        if region is None or region.width <= 0:
            continue
        heights.append(box.height * (_SHEET_W_MM / region.width))
    min_h = round(min(heights), 4) if heights else None

    details = {
        "sheets_audited": sorted(audit.sheet_regions),
        "clipping_violations": audit.outside_frame,
        "title_block_intrusions": audit.title_block_intrusions,
        "notes_intrusions": audit.notes_intrusions,
        "notes_zone_sheets": sorted(audit.notes_regions),
        "title_block_sheets": sorted(audit.title_block_regions),
        "printed_scales": sorted({d for _, d in audit.printed_scales}),
        "text_floor_paper_mm": TEXT_FLOOR_PAPER_MM,
    }
    return LayoutChecks(
        rendered=audit.rendered and not audit.error,
        clipping_ok=audit.rendered and not audit.outside_frame,
        title_block_ok=audit.rendered and not audit.title_block_intrusions,
        notes_zone_declared=bool(audit.notes_regions),
        notes_zone_ok=not audit.notes_intrusions,
        scales_ok=bool(audit.printed_scales)
        and all(scale_on_ladder(d) for _, d in audit.printed_scales),
        text_floor_ok=min_h is not None and min_h >= TEXT_FLOOR_PAPER_MM - 1e-6,
        min_text_height_paper_mm=min_h,
        details=details,
    )
