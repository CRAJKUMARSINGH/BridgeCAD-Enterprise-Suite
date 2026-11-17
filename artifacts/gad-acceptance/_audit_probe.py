"""Probe layout_audit for the nine-span package: scales, frame, text floor, overlaps."""
from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

SUITE = Path(__file__).resolve().parents[2]
for pkg in ["bridgecad-core", "bridgecad-draw", "bridgecad-catalogue"]:
    p = SUITE / "packages" / pkg
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def load_gen():
    spec = importlib.util.spec_from_file_location(
        "bridgecad_pwd_gen", SUITE / "scripts" / "generate_all_pwd_gads.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    from bridgecad_catalogue import registry
    from bridgecad_catalogue.resolve import resolve
    from bridgecad_draw import layout_audit as LA

    gen = load_gen()
    card = registry.by_id("BR-I-2022-002")
    params = resolve(card, {"span_count": "9", "span_length_m": "10"})
    params["id"] = card["id"]
    project = gen._build_project(params)

    LA.set_enabled(True)
    audit = LA.collect(project)
    LA.set_enabled(None)

    print("rendered:", audit.rendered, "error:", repr(audit.error))
    print("outside_frame:", audit.outside_frame[:10], "count", len(audit.outside_frame))
    print("printed_scales:", audit.printed_scales)
    print("nts_claims:", audit.nts_claims)
    print("band_counts:", audit.band_counts)
    print("layers_drawn:", len(audit.layers_drawn))

    by_sheet = Counter(b.sheet for b in audit.text_boxes)
    print("text_boxes per sheet:", dict(by_sheet))

    # Overlap pairs per sheet (using the audit's own tol=0.5)
    sheets = sorted({b.sheet for b in audit.text_boxes})
    for s in sheets:
        boxes = [b for b in audit.text_boxes if b.sheet == s]
        pairs = []
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if boxes[i].overlaps(boxes[j]):
                    pairs.append((boxes[i], boxes[j]))
        print(f"  {s}: {len(boxes)} boxes, {len(pairs)} overlapping pairs")
        for a, b in pairs:
            ix = max(0.0, min(a.x1, b.x1) - max(a.x0, b.x0))
            iy = max(0.0, min(a.y1, b.y1) - max(a.y0, b.y0))
            inter = ix * iy
            small = max(1e-9, min(a.width * a.height, b.width * b.height))
            print(f"      OVERLAP frac={inter/small:.3f} {a.text!r} x {b.text!r}")

    heights = [b.height for b in audit.text_boxes if b.height > 0]
    print("min text height:", min(heights), "max:", max(heights))
    tiny = sorted({round(b.height, 3) for b in audit.text_boxes if 0 < b.height < 1.8})
    print("heights < 1.8:", tiny)

    # ── measured regions + region gating (layout_audit §5 extensions) ──────
    print("sheet_regions:", {
        k: (round(v.width, 1), round(v.height, 1)) for k, v in audit.sheet_regions.items()})
    print("title_block_regions:", {
        k: tuple(round(x, 1) for x in v.as_tuple())
        for k, v in audit.title_block_regions.items()})
    print("notes_regions:", {
        k: tuple(round(x, 1) for x in v.as_tuple())
        for k, v in audit.notes_regions.items()})
    print("title_block_intrusions:", len(audit.title_block_intrusions),
          audit.title_block_intrusions[:20])
    print("notes_intrusions:", len(audit.notes_intrusions), audit.notes_intrusions[:20])
    checks = LA.layout_checks(audit)
    print("layout_checks.passed:", checks.passed)
    for name in ("rendered", "clipping_ok", "title_block_ok", "notes_zone_declared",
                 "notes_zone_ok", "scales_ok", "text_floor_ok", "min_text_height_paper_mm"):
        print(f"   {name} = {getattr(checks, name)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
