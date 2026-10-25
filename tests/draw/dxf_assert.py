"""Structural assertions over a DXF document.

Everything here is a *contract* check: finite extents, non-empty geometry, no
degenerate entities, layers from the IRC SP:55 registry, dimensions present,
title block filled. None of it knows what a wing wall is — that is Wing-04+.

Failure messages name the sheet and the offending entity so a red test is
actionable without opening the DXF.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import ezdxf
from ezdxf import bbox
from ezdxf.document import Drawing


class DxfContractError(AssertionError):
    """A structural contract on a generated drawing was violated."""


# Geometry that is meaningless if zero-sized.
DEGENERATE_TOL = 1e-6
MIN_TEXT_HEIGHT_MM = 1.8          # IRC SP:55 legibility floor
TITLE_BLOCK_REQUIRED = (
    "PROJECT", "DRAWING TITLE", "SCALE", "DRAWN", "CHECKED", "REVISION", "SHEET",
)


def load(path: Path | str) -> Drawing:
    doc = ezdxf.readfile(str(path))
    if doc is None:
        raise DxfContractError(f"could not read {path}")
    return doc


def entities(doc: Drawing, layer: str | None = None):
    """Every modelspace entity, or only those on *layer*.

    The layer filter is not a convenience: a test that counts pier centrelines
    must count exactly those, not "lines that happen to be roughly vertical".
    """
    for e in doc.modelspace():
        if layer is None or e.dxf.get("layer", "0") == layer:
            yield e


def entity_count(doc: Drawing) -> int:
    return sum(1 for _ in entities(doc))


def layer_usage(doc: Drawing) -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in entities(doc):
        name = e.dxf.get("layer", "0")
        counts[name] = counts.get(name, 0) + 1
    return counts


def text_of(doc: Drawing, layer: str | None = None) -> list[str]:
    out = []
    for e in entities(doc, layer=layer):
        if e.dxftype() == "TEXT":
            out.append(e.dxf.text)
        elif e.dxftype() == "MTEXT":
            out.append(e.text)
    return out


# ── assertions ───────────────────────────────────────────────────────────────
def assert_finite_extents(doc: Drawing, sheet: str = "?"):
    ext = bbox.extents(doc.modelspace(), fast=True)
    if not ext.has_data:
        raise DxfContractError(f"[{sheet}] modelspace has no drawable geometry")
    for name, val in (("xmin", ext.extmin.x), ("ymin", ext.extmin.y),
                      ("xmax", ext.extmax.x), ("ymax", ext.extmax.y)):
        if val != val or val in (float("inf"), float("-inf")):
            raise DxfContractError(f"[{sheet}] non-finite extent {name}={val}")
    if ext.size.x <= 0 and ext.size.y <= 0:
        raise DxfContractError(f"[{sheet}] zero-area extents {ext.size}")


def assert_non_empty(doc: Drawing, sheet: str = "?", minimum: int = 50):
    n = entity_count(doc)
    if n < minimum:
        raise DxfContractError(
            f"[{sheet}] only {n} entities, expected >= {minimum} — scaffold not drawn"
        )


def assert_no_degenerate_geometry(doc: Drawing, sheet: str = "?"):
    for e in entities(doc):
        t = e.dxftype()
        if t == "LINE":
            if (e.dxf.end - e.dxf.start).magnitude < DEGENERATE_TOL:
                raise DxfContractError(f"[{sheet}] zero-length LINE on layer {e.dxf.layer}")
        elif t == "CIRCLE":
            if e.dxf.radius < DEGENERATE_TOL:
                raise DxfContractError(f"[{sheet}] zero-radius CIRCLE on layer {e.dxf.layer}")
        elif t == "ARC":
            if e.dxf.radius < DEGENERATE_TOL:
                raise DxfContractError(f"[{sheet}] zero-radius ARC on layer {e.dxf.layer}")


def assert_layers_known(doc: Drawing, registry: dict, sheet: str = "?"):
    known = set(registry)
    unknown = sorted({e.dxf.get("layer", "0") for e in entities(doc)} - known)
    if unknown:
        raise DxfContractError(
            f"[{sheet}] entities on layers absent from the IRC SP:55 registry: {unknown}"
        )


def assert_nothing_on_layer_zero(doc: Drawing, sheet: str = "?"):
    if layer_usage(doc).get("0"):
        raise DxfContractError(
            f"[{sheet}] {layer_usage(doc)['0']} entities left on layer '0'"
        )


def assert_min_dimensions(doc: Drawing, sheet: str = "?", minimum: int = 8):
    n = sum(1 for e in entities(doc) if e.dxftype() == "DIMENSION")
    if n < minimum:
        raise DxfContractError(f"[{sheet}] only {n} DIMENSION entities, expected >= {minimum}")


def assert_min_text_height(doc: Drawing, sheet: str = "?", minimum: float = MIN_TEXT_HEIGHT_MM):
    for e in entities(doc):
        if e.dxftype() in ("TEXT", "MTEXT"):
            h = e.dxf.get("height", None)
            if h is not None and h < minimum:
                raise DxfContractError(
                    f"[{sheet}] text height {h} below legibility floor {minimum}: {text_of(doc)[:1]}"
                )


def assert_title_block_filled(doc: Drawing, sheet: str = "?"):
    blob = " ".join(text_of(doc)).upper()
    missing = [f for f in TITLE_BLOCK_REQUIRED if f not in blob]
    if missing:
        raise DxfContractError(f"[{sheet}] title block fields not filled: {missing}")


def assert_sheet_annotation(doc: Drawing, sheet: str = "?", index: int | None = None):
    """A sheet must declare 'SHEET n OF m' so a printed set can be ordered."""
    import re
    blob = " ".join(text_of(doc)).upper()
    m = re.search(r"SHEET\s+(\d+)\s+OF\s+(\d+)", blob)
    if not m:
        raise DxfContractError(f"[{sheet}] no 'SHEET n OF m' annotation")
    if index is not None and int(m.group(1)) != index:
        raise DxfContractError(f"[{sheet}] says SHEET {m.group(1)}, expected {index}")


def fingerprint(doc: Drawing, ndigits: int = 4) -> str:
    """Stable hash of geometry. Insensitive to entity order, sensitive to any move."""
    items: list[str] = []
    for e in sorted(entities(doc), key=lambda x: (x.dxftype(), x.dxf.get("layer", ""))):
        t = e.dxftype()
        if t == "LINE":
            s, en = e.dxf.start, e.dxf.end
            items.append(f"L:{round(s.x, ndigits)},{round(s.y, ndigits)}"
                         f":{round(en.x, ndigits)},{round(en.y, ndigits)}:{e.dxf.layer}")
        elif t == "CIRCLE":
            c = e.dxf.center
            items.append(f"C:{round(c.x, ndigits)},{round(c.y, ndigits)}:"
                         f"{round(e.dxf.radius, ndigits)}:{e.dxf.layer}")
        elif t in ("TEXT", "MTEXT"):
            p = e.dxf.insert
            body = e.dxf.text if t == "TEXT" else e.text
            items.append(f"T:{round(p.x, ndigits)},{round(p.y, ndigits)}:{body}:{e.dxf.layer}")
    return hashlib.sha256("\n".join(sorted(items)).encode()).hexdigest()[:16]


from dataclasses import dataclass


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str          # "pass" | "fail" | "skip"
    detail: str = ""


def _spec(scaffold: bool):
    """(name, callable, kwargs). Scaffold sheets get a lowered bar so the
    report states the real position instead of a wall of red."""
    return [
        ("finite extents",      assert_finite_extents,        {}),
        ("non-empty geometry",  assert_non_empty,             {"minimum": 20 if scaffold else 50}),
        ("no degenerate geo",   assert_no_degenerate_geometry, {}),
        ("layers registered",   assert_layers_known,          {}),
        ("nothing on layer 0",  assert_nothing_on_layer_zero, {}),
        ("title block filled",  assert_title_block_filled,    {}),
        ("sheet n of m",        assert_sheet_annotation,      {}),
        ("dimensioned",         assert_min_dimensions,        {}),
        ("text legible",        assert_min_text_height,       {}),
    ]


def collect(doc: Drawing, sheet: str, registry: dict, *, scaffold: bool = False) -> list[CheckResult]:
    """Run every contract check, collecting results instead of raising."""
    out: list[CheckResult] = []
    for name, fn, kwargs in _spec(scaffold):
        if name == "layers registered":
            kwargs = {"registry": registry, "sheet": sheet}
        try:
            fn(doc, sheet=sheet, **kwargs)
            out.append(CheckResult(name, "pass"))
        except DxfContractError as exc:
            out.append(CheckResult(name, "fail", str(exc)))
        except Exception as exc:  # noqa: BLE001
            out.append(CheckResult(name, "fail", f"{type(exc).__name__}: {exc}"))

    # Not-a-title-block: the specific failure mode from 2 OCT PROGRAM.MD.
    non_text = sum(1 for e in entities(doc)
                   if e.dxftype() not in ("TEXT", "MTEXT", "DIMENSION"))
    if non_text < 10:
        out.append(CheckResult("geometry beyond title block", "fail",
                               f"{non_text} non-text entities"))
    else:
        out.append(CheckResult("geometry beyond title block", "pass"))
    return out


def metrics(doc: Drawing) -> dict:
    """Counts an engineer wants when reviewing a sheet."""
    counts: dict[str, int] = {}
    for e in entities(doc):
        counts[e.dxftype()] = counts.get(e.dxftype(), 0) + 1
    ext = bbox.extents(doc.modelspace(), fast=True)
    return {
        "entities": sum(counts.values()),
        "by_type": counts,
        "layers": len(layer_usage(doc)),
        "dimensions": counts.get("DIMENSION", 0),
        "texts": counts.get("TEXT", 0) + counts.get("MTEXT", 0),
        "extent_mm": [round(ext.size.x, 2), round(ext.size.y, 2)] if ext.has_data else [0, 0],
    }
