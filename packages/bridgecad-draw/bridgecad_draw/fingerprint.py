"""bridgecad_draw.fingerprint — stable entity fingerprints for revision diff.

Quantised to ``quantum_mm`` (default 1 mm — at 1:100 it hides nothing an
engineer cares about; on 1:20 details take the quantum from
``drawing_scale`` and record it in the manifest).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any


def _q(v: float, quantum: float) -> float:
    return round(float(v) / quantum) * quantum


def _points(e: Any, quantum: float) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    try:
        if e.dxftype() == "LWPOLYLINE":
            pts = [(_q(p[0], quantum), _q(p[1], quantum)) for p in e.get_points("xy")]
        elif e.dxftype() in ("LINE",):
            pts = [
                (_q(e.dxf.start.x, quantum), _q(e.dxf.start.y, quantum)),
                (_q(e.dxf.end.x, quantum), _q(e.dxf.end.y, quantum)),
            ]
        elif e.dxftype() == "CIRCLE":
            pts = [
                (_q(e.dxf.center.x, quantum), _q(e.dxf.center.y, quantum)),
                (_q(e.dxf.radius, quantum), 0.0),
            ]
        elif e.dxftype() == "ARC":
            pts = [
                (_q(e.dxf.center.x, quantum), _q(e.dxf.center.y, quantum)),
                (_q(e.dxf.radius, quantum), 0.0),
                (round(e.dxf.start_angle, 1), round(e.dxf.end_angle, 1)),
            ]
        elif e.dxftype() in ("TEXT", "MTEXT"):
            ins = getattr(e.dxf, "insert", None)
            pts = [(_q(ins.x, quantum), _q(ins.y, quantum))] if ins else []
        elif e.dxftype() == "INSERT":
            ins = e.dxf.insert
            pts = [(_q(ins.x, quantum), _q(ins.y, quantum))]
    except Exception:
        return []
    return pts


def entity_fingerprint(e: Any, quantum_mm: float = 1.0) -> str:
    """Stable sha256 of (dxftype, layer, quantised geometry, text content)."""
    try:
        dxftype = e.dxftype()
    except Exception:
        return ""
    layer = str(getattr(e.dxf, "layer", "") or "")
    pts = _points(e, quantum_mm)
    text_content = ""
    if dxftype in ("TEXT", "MTEXT"):
        text_content = str(getattr(e.dxf, "text", "") or "").strip()
    elif dxftype == "INSERT":
        text_content = str(getattr(e.dxf, "name", "") or "")
    raw = "|".join([dxftype, layer, text_content, ";".join(f"{x:.3f},{y:.3f}" for x, y in pts)])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def entity_geometry_fingerprint(e: Any, quantum_mm: float = 1.0) -> str:
    """sha256 of quantised geometry only — style changes keep this stable."""
    try:
        dxftype = e.dxftype()
    except Exception:
        return ""
    pts = _points(e, quantum_mm)
    raw = "|".join([dxftype, ";".join(f"{x:.3f},{y:.3f}" for x, y in pts)])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class EntitySig:
    """Fingerprint plus the centroid needed for MOVED pairing."""

    fp: str
    geo_fp: str
    dxftype: str
    layer: str
    cx: float
    cy: float


def _centroid(e: Any) -> tuple[float, float]:
    try:
        if e.dxftype() == "CIRCLE":
            return float(e.dxf.center.x), float(e.dxf.center.y)
        if e.dxftype() in ("LINE", "LWPOLYLINE", "TEXT", "MTEXT", "INSERT", "ARC"):
            bb = e.bounding_box()
            if bb:
                return (bb.extmin.x + bb.extmax.x) / 2.0, (bb.extmin.y + bb.extmax.y) / 2.0
    except Exception:
        pass
    return 0.0, 0.0


def _sort_key(e: Any) -> tuple:
    layer = str(getattr(e.dxf, "layer", "") or "")
    try:
        dxftype = e.dxftype()
    except Exception:
        dxftype = ""
    cx, cy = _centroid(e)
    return (layer, dxftype, round(cx, 1), round(cy, 1))


def sheet_signatures(msp: Any, quantum_mm: float = 1.0) -> dict[str, EntitySig]:
    """``E0001``-style keys in sorted draw order -> signature.

    Handles are reassigned on every render, so keys are positional in the
    deterministic sort order, never the DXF handle.
    """
    entities = [e for e in msp if e.dxftype() != "VIEWPORT"]
    entities.sort(key=_sort_key)
    out: dict[str, EntitySig] = {}
    for i, e in enumerate(entities):
        try:
            dxftype = e.dxftype()
            layer = str(getattr(e.dxf, "layer", "") or "")
        except Exception:
            continue
        cx, cy = _centroid(e)
        out[f"E{i:04d}"] = EntitySig(
            fp=entity_fingerprint(e, quantum_mm),
            geo_fp=entity_geometry_fingerprint(e, quantum_mm),
            dxftype=dxftype,
            layer=layer,
            cx=cx,
            cy=cy,
        )
    return out


def sheet_fingerprint(msp: Any, quantum_mm: float = 1.0) -> dict[str, str]:
    """``key -> fingerprint`` view of :func:`sheet_signatures`."""
    return {k: v.fp for k, v in sheet_signatures(msp, quantum_mm).items()}


__all__ = [
    "EntitySig",
    "entity_fingerprint",
    "entity_geometry_fingerprint",
    "sheet_fingerprint",
    "sheet_signatures",
]
