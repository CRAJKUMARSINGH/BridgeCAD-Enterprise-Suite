#!/usr/bin/env python3
"""Dump measurable facts about a DXF into JSON.

Week-1 instrument. Emits only facts, never opinions, so the baseline is
reproducible and diffable. One JSON file per input.

    python scripts/dump_dxf_facts.py build/baseline/*.dxf --out build/baseline/facts
    python scripts/dump_dxf_facts.py --selftest
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import ezdxf
    from ezdxf import bbox as ezbbox
except ImportError:  # pragma: no cover
    sys.exit("ezdxf is required: pip install 'ezdxf>=1.3'")

SCHEMA = "dxf-facts/1"


def _handle(entity: Any) -> str:
    try:
        return entity.dxf.handle
    except Exception:
        return "?"


def _text_height(entity: Any) -> float | None:
    t = entity.dxftype()
    try:
        if t == "TEXT":
            return round(float(entity.dxf.height), 4)
        if t == "MTEXT":
            return round(float(entity.dxf.char_height), 4)
    except Exception:
        return None
    return None


def _extents(msp: Any) -> dict[str, float] | None:
    try:
        box = ezbbox.extents(msp, fast=True)
        if not box.has_data:
            return None
        return {
            "x_min": round(box.extmin.x, 3),
            "y_min": round(box.extmin.y, 3),
            "x_max": round(box.extmax.x, 3),
            "y_max": round(box.extmax.y, 3),
        }
    except Exception:
        return None


def _line_key(e: Any) -> tuple:
    a = (round(e.dxf.start.x, 3), round(e.dxf.start.y, 3))
    b = (round(e.dxf.end.x, 3), round(e.dxf.end.y, 3))
    return (e.dxf.layer, min(a, b), max(a, b))


def facts_for(path: Path) -> dict:
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()

    types: Counter[str] = Counter()
    layers: Counter[str] = Counter()
    heights: Counter[float] = Counter()
    line_keys: Counter[tuple] = Counter()
    zero_len: list[str] = []
    dimlfac: dict[str, float] = {}
    dim_handles: list[str] = []

    for e in msp:
        t = e.dxftype()
        types[t] += 1
        layer = getattr(e.dxf, "layer", "0")
        layers[layer] += 1

        h = _text_height(e)
        if h is not None:
            heights[h] += 1

        if t == "LINE":
            line_keys[_line_key(e)] += 1
            try:
                if e.dxf.start.distance(e.dxf.end) < 1e-9:
                    zero_len.append(_handle(e))
            except Exception:
                pass

        if t == "DIMENSION":
            dim_handles.append(_handle(e))

    for style in doc.dimstyles:
        try:
            dimlfac[style.dxf.name] = float(style.dxf.dimlfac)
        except Exception:
            dimlfac[style.dxf.name] = 1.0

    duplicates = [k for k, n in line_keys.items() if n > 1]

    return {
        "schema": SCHEMA,
        "file": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "units": int(doc.header.get("$INSUNITS", 0)),
        "entity_total": sum(types.values()),
        "entity_types": dict(types),
        "layers_used": sorted(layers),
        "layer_entity_counts": dict(layers),
        "text_heights": {f"{k:g}": v for k, v in sorted(heights.items())},
        "text_height_distinct": len(heights),
        "dimension_count": len(dim_handles),
        "dimstyle_lfac": dimlfac,
        "dimensions_without_lfac_1000": sum(
            1 for s in dimlfac.values() if abs(s - 1000.0) > 1e-9
        ) if dim_handles else 0,
        "duplicate_line_count": len(duplicates),
        "duplicate_lines": [
            {"layer": k[0], "a": list(k[1]), "b": list(k[2]), "n": line_keys[k]}
            for k in duplicates[:50]
        ],
        "zero_length_lines": zero_len,
        "layout_count": len(list(doc.layouts)),
        "extents": _extents(msp),
    }


def _selftest() -> int:
    doc = ezdxf.new("R2018", setup="drafting")
    doc.layers.add("TEST")
    msp = doc.modelspace()
    msp.add_line((0, 0), (100, 0), dxfattribs={"layer": "TEST"})
    msp.add_line((0, 0), (100, 0), dxfattribs={"layer": "TEST"})  # duplicate
    msp.add_line((5, 5), (5, 5), dxfattribs={"layer": "TEST"})  # zero length
    msp.add_text("x", dxfattribs={"height": 2.5, "layer": "TEST"})

    tmp = Path("build/_selftest.dxf")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(tmp)

    f = facts_for(tmp)
    checks = {
        "duplicate detected": f["duplicate_line_count"] == 1,
        "zero length detected": len(f["zero_length_lines"]) == 1,
        "text height captured": f["text_heights"] == {"2.5": 1},
        "extents captured": f["extents"] is not None,
        "schema stamped": f["schema"] == SCHEMA,
    }
    ok = all(checks.values())
    for name, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    tmp.unlink(missing_ok=True)
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("inputs", nargs="*", type=Path)
    ap.add_argument("--out", type=Path, default=Path("build/facts"))
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()
    if not args.inputs:
        ap.error("no inputs and no --selftest")

    args.out.mkdir(parents=True, exist_ok=True)
    rc = 0
    for p in args.inputs:
        try:
            data = facts_for(p)
        except Exception as exc:
            print(f"  [FAIL] {p}: {exc}")
            rc = 1
            continue
        dest = args.out / f"{p.stem}.json"
        dest.write_text(json.dumps(data, indent=2, sort_keys=True))
        print(f"  [ok] {p} -> {dest}  ({data['entity_total']} entities)")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
