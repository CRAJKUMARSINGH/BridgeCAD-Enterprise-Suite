"""Probe layout_audit text-box extents to size the layout assertions safely."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for _pkg in ["bridgecad-core", "bridgecad-draw", "bridgecad-catalogue"]:
    _p = REPO / "packages" / _pkg
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from bridgecad_catalogue import registry  # noqa: E402
from bridgecad_catalogue.resolve import resolve  # noqa: E402
from bridgecad_draw import layout_audit as LA  # noqa: E402


def load_gen():
    spec = importlib.util.spec_from_file_location("_gen", REPO / "scripts" / "generate_all_pwd_gads.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    gen = load_gen()
    card = registry.by_id("BR-I-2022-002")
    params = resolve(card, {"span_count": "9", "span_length_m": "10"})
    params["id"] = card["id"]
    project = gen._build_project(params)

    LA.set_enabled(True)
    try:
        audit = LA.collect(project)
    finally:
        LA.set_enabled(None)

    print("rendered", audit.rendered, "error", repr(audit.error))
    print("outside_frame", audit.outside_frame)
    print("printed_scales", audit.printed_scales)
    by_sheet: dict[str, list] = {}
    for b in audit.text_boxes:
        by_sheet.setdefault(b.sheet, []).append(b)
    for sheet in sorted(by_sheet):
        bs = by_sheet[sheet]
        print(f"{sheet}: n={len(bs)} x0min={min(b.x0 for b in bs):.2f} y0min={min(b.y0 for b in bs):.2f}"
              f" x1max={max(b.x1 for b in bs):.2f} y1max={max(b.y1 for b in bs):.2f}"
              f" hmin={min(b.height for b in bs):.4f} hmax={max(b.height for b in bs):.4f}")
    # per-sheet overlap pairs (audit tolerance)
    for sheet in sorted(by_sheet):
        bs = by_sheet[sheet]
        pairs = []
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                if bs[i].overlaps(bs[j]):
                    pairs.append((bs[i].text, bs[j].text))
        print(f"  {sheet}: overlaps={len(pairs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
