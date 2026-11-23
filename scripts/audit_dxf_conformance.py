#!/usr/bin/env python3
"""audit_dxf_conformance.py — audit generated sheet DXFs against IRC drafting practice.

Catches the concrete defects found in the 2026-01 drawing audit (see
CODE-JUNCTION/2026-01-irc-standards-enrichment/GUIDE.md Part 5):

  DXF-01  superstructure coherence — no girders drawn/labelled on a slab bridge
  DXF-02  text-height discipline — heights cluster on the SP:55-style hierarchy
  DXF-03  title block completeness — DRAWN/CHECKED/APPROVED/DATE/CLIENT non-empty
  DXF-04  scale consistency — one declared scale, no contradicting scale texts
  DXF-05  no chainage ticks beyond the bridge length (wrong-axis leakage)
  DXF-06  entity density floor — schematic stubs are caught, not shipped
  DXF-07  layer naming — SP:55-style layer names, no bare geometry on layer "0"
  DXF-08  units sanity — $INSUNITS matches the drawing-space intent

Usage:
    python scripts/audit_dxf_conformance.py SHEET.dxf \
        --bridge-type slab --bridge-length-m 12 [--sheet-type cross_section] [--json]

Exit code 0 = pass, 1 = at least one fail.  Warnings never fail the run.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:
    import ezdxf  # type: ignore
except ImportError:  # pragma: no cover
    print("ezdxf is required: pip install ezdxf", file=sys.stderr)
    raise

# Standard paper-space text heights (mm) used across the drawing set.
STANDARD_TEXT_HEIGHTS_MM = (1.8, 2.5, 3.5, 5.0, 7.0, 10.0)

# Minimum entity counts per sheet type (schematic stub detection).
MIN_ENTITIES = {
    "plan": 250,
    "long_section": 250,
    "cross_section": 300,
    "foundation": 250,
    "pier_abutment": 300,
    "bearings_joints": 250,
    "boq": 200,
    "side_elevations": 250,
    "reinforcement": 300,
}

SCALE_RE = re.compile(r"1\s*[:/]\s*(\d+)")
CHAINAGE_TICK_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*m$", re.IGNORECASE)


@dataclass
class Finding:
    id: str
    status: str            # "pass" | "fail" | "warn"
    detail: str = ""
    severity: str = "major"


@dataclass
class Audit:
    file: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return any(f.status == "fail" for f in self.findings)


def _texts(msp: Any) -> list[tuple[str, float, str]]:
    out: list[tuple[str, float, str]] = []
    for e in msp:
        if e.dxftype() in ("TEXT", "MTEXT"):
            raw = e.dxf.text if e.dxftype() == "MTEXT" else e.dxf.text
            plain = re.sub(r"\\[Ppi][^;]*;?", " ", str(raw)).replace("\\A1;", "")
            plain = re.sub(r"\{?\\[A-Za-z0-9.]+;?", "", plain).replace("{", "").replace("}", "")
            h = float(e.dxf.get("height", 0.0) or e.dxf.get("char_height", 0.0) or 0.0)
            out.append((plain.strip(), h, e.dxf.layer))
    return out


def check_d01_superstructure(msp: Any, bridge_type: str) -> Finding:
    """Slab bridges must not carry girder entities or girder labels."""
    bt = bridge_type.strip().lower()
    if "slab" not in bt:
        return Finding("DXF-01", "pass", f"bridge type '{bridge_type}' — girder check not applicable")
    girder_texts, girder_entities = [], 0
    for e in msp:
        layer = str(e.dxf.layer).upper()
        if "GIRDER" in layer:
            girder_entities += 1
        if e.dxftype() in ("TEXT", "MTEXT"):
            t = str(e.dxf.text).upper()
            if "GIRDER" in t or "T-BEAM" in t or "IGIRDER" in t:
                girder_texts.append(t[:60])
    if girder_entities or girder_texts:
        return Finding("DXF-01", "fail",
                       f"slab bridge carries {girder_entities} girder entities and "
                       f"{len(girder_texts)} girder label(s): {girder_texts[:3]}")
    return Finding("DXF-01", "pass", "no girder entities/labels on a slab bridge")


def check_d02_text_heights(texts: list[tuple[str, float, str]]) -> Finding:
    heights = sorted({round(h, 2) for _, h, _ in texts if h > 0})
    if not heights:
        return Finding("DXF-02", "warn", "no sized text entities found")
    tol = 0.15
    off = [h for h in heights if not any(abs(h - s) <= tol for s in STANDARD_TEXT_HEIGHTS_MM)]
    if len(heights) > 4 and off:
        return Finding("DXF-02", "fail",
                       f"{len(heights)} distinct heights; off-hierarchy: {off[:6]} "
                       f"(allowed paper heights {STANDARD_TEXT_HEIGHTS_MM})")
    if off:
        return Finding("DXF-02", "warn", f"heights off the standard set: {off[:6]}")
    return Finding("DXF-02", "pass", f"{len(heights)} distinct heights, all standard")


def check_d03_title_block(texts: list[tuple[str, float, str]]) -> Finding:
    required = ("DRAWN", "CHECKED", "APPROVED", "DATE", "CLIENT")
    joined = " || ".join(t for t, _, _ in texts).upper()
    empty = []
    for key in required:
        # A field followed by another label or end-of-line with no value counts as empty.
        m = re.search(rf"{key}\s*:\s*(?:(?=[A-Z]+ ?:)|$)", joined)
        if m:
            empty.append(key)
    if empty:
        return Finding("DXF-03", "fail", f"empty title-block fields: {', '.join(empty)}")
    return Finding("DXF-03", "pass", "all required title-block fields carry values")


def check_d04_scale(texts: list[tuple[str, float, str]]) -> Finding:
    declared, bars = [], []
    for t, _, _ in texts:
        m = SCALE_RE.search(t)
        if not m:
            continue
        n = int(m.group(1))
        if "SCALE" in t.upper():
            declared.append(n)
        else:
            bars.append(n)
    if not declared:
        return Finding("DXF-04", "warn", "no SCALE: 1:n text found")
    if len(set(declared)) > 1:
        return Finding("DXF-04", "fail", f"multiple declared scales: {declared}")
    if bars and any(b != declared[0] for b in bars):
        return Finding("DXF-04", "fail",
                       f"title-block scale 1:{declared[0]} contradicts scale-bar text(s) 1:{bars}")
    return Finding("DXF-04", "pass", f"single scale 1:{declared[0]}")


def check_d05_chainage(msp: Any, bridge_length_m: float, sheet_type: str) -> Finding:
    """Chainage-style tick labels must stay within the bridge and stay off
    cross-section sheets (a transverse section has no chainage axis)."""
    over: list[float] = []
    for t, _, _ in _texts(msp):
        m = CHAINAGE_TICK_RE.match(t)
        if m and float(m.group(1)) > bridge_length_m + 1e-6:
            over.append(float(m.group(1)))
    if sheet_type == "cross_section":
        # any chainage-like label at all is a defect here
        any_tick = [float(CHAINAGE_TICK_RE.match(t).group(1))  # type: ignore[union-attr]
                    for t, _, _ in _texts(msp) if CHAINAGE_TICK_RE.match(t)]
        if any_tick:
            return Finding("DXF-05", "fail",
                           f"cross-section carries chainage ticks {any_tick[:6]} — transverse "
                           "sections have no chainage axis")
        return Finding("DXF-05", "pass", "no chainage ticks on cross-section")
    if over:
        return Finding("DXF-05", "fail", f"chainage ticks exceed bridge length: {over[:6]}")
    return Finding("DXF-05", "pass", "chainage ticks within bridge length")


def check_d06_density(msp: Any, sheet_type: str) -> Finding:
    floor = MIN_ENTITIES.get(sheet_type)
    if floor is None:
        return Finding("DXF-06", "warn", f"no density floor configured for '{sheet_type}'")
    n = len(list(msp))
    if n < floor:
        return Finding("DXF-06", "fail", f"{n} entities < floor {floor} for '{sheet_type}' — schematic stub")
    return Finding("DXF-06", "pass", f"{n} entities >= floor {floor}")


def check_d07_layers(msp: Any) -> Finding:
    bare0, bad_names = 0, []
    for e in msp:
        layer = str(e.dxf.layer)
        if e.dxftype() in ("LINE", "LWPOLYLINE", "CIRCLE", "ARC", "SOLID") and layer == "0":
            bare0 += 1
        if layer and layer != "0" and not re.match(r"^[A-Z0-9]+(-[A-Z0-9]+)*$", layer.upper()):
            bad_names.append(layer)
    if bare0 > 5:
        return Finding("DXF-07", "warn", f"{bare0} entities on layer '0'")
    if bad_names:
        return Finding("DXF-07", "warn", f"non-standard layer names: {sorted(set(bad_names))[:5]}")
    return Finding("DXF-07", "pass", "layer usage conforms")


def check_d08_units(doc: Any) -> Finding:
    insunits = int(doc.header.get("$INSUNITS", 0) or 0)
    # 6 = metres, 4 = millimetres.  Drawing generators that draw in paper mm
    # inside a metre-unit template must be flagged for verification.
    if insunits == 6:
        return Finding("DXF-08", "warn",
                       "$INSUNITS=6 (metres) while sheet geometry is drawn in paper mm — "
                       "verify the unit contract on export/import")
    if insunits == 4:
        return Finding("DXF-08", "pass", "$INSUNITS=4 (millimetres) consistent with paper-space drafting")
    return Finding("DXF-08", "warn", f"$INSUNITS={insunits} — verify")


def audit_file(path: Path, bridge_type: str, bridge_length_m: float,
               sheet_type: str) -> Audit:
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    texts = _texts(msp)
    a = Audit(file=str(path))
    a.findings.append(check_d01_superstructure(msp, bridge_type))
    a.findings.append(check_d02_text_heights(texts))
    a.findings.append(check_d03_title_block(texts))
    a.findings.append(check_d04_scale(texts))
    a.findings.append(check_d05_chainage(msp, bridge_length_m, sheet_type))
    a.findings.append(check_d06_density(msp, sheet_type))
    a.findings.append(check_d07_layers(msp))
    a.findings.append(check_d08_units(doc))
    return a


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dxf", type=Path)
    ap.add_argument("--bridge-type", required=True, help="slab | t_beam | i_girder | box | box_cell | arch ...")
    ap.add_argument("--bridge-length-m", type=float, required=True)
    ap.add_argument("--sheet-type", default="cross_section",
                    help=f"one of {sorted(MIN_ENTITIES)}")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    audit = audit_file(args.dxf, args.bridge_type, args.bridge_length_m, args.sheet_type)
    if args.as_json:
        print(json.dumps({"file": audit.file,
                          "failed": audit.failed,
                          "findings": [asdict(f) for f in audit.findings]}, indent=2))
    else:
        print(f"== {audit.file} ==")
        for f in audit.findings:
            mark = {"pass": "PASS", "fail": "FAIL", "warn": "WARN"}[f.status]
            print(f"  [{mark}] {f.id}  {f.detail}")
    return 1 if audit.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())