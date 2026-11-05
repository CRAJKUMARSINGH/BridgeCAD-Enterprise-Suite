"""Geometry parity: JS deploy mirror vs Python source of truth.

pip install -e packages/bridgecad-core
python scripts/parity_detail_sheets.py --fixtures tests/e2e/fixtures --tolerance 1e-6
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "bridgecad-core"))

from bridgecad_core.geometry.abutment import wing_wall_geometry  # noqa: E402

CORE = ROOT / "frontend" / "src" / "sheets" / "detailGeometry.js"

DRIVER = """
import { normalizeParams, wingWallGeometry, foundationLayout } from "%s";
const cases = JSON.parse(process.argv[2]);
process.stdout.write(JSON.stringify(cases.map((p) => {
  const n = normalizeParams(p);
  const w = wingWallGeometry(n);
  const f = foundationLayout(n);
  return { face: w.faceRunM, length: w.lengthM, ret: w.returnM, splay: w.splayDeg, n: f.nPiles };
})));
"""


def stub(p: dict) -> SimpleNamespace:
    return SimpleNamespace(
        foundation_details=SimpleNamespace(
            abtl=p["abtl"], futl=0, footl=0, futrl=0, alcl=0, alcw=0
        ),
        geometry_input=SimpleNamespace(carriageway_width_m=p["carriageway"]),
        drawing_control=SimpleNamespace(splay_deg=p["splay"]),
        levels=SimpleNamespace(deck_level_m=p["deckRl"], founding_level_m=p["foundingRl"]),
        hydraulic_data=SimpleNamespace(scour_level_m=p["foundingRl"]),
        substructure=SimpleNamespace(),
    )


def python_facts(p: dict) -> dict:
    w = wing_wall_geometry(stub(p))[0]
    return {
        "face": float(w.face_run_m),
        "length": float(w.length_m),
        "ret": float(w.return_m),
        "splay": float(w.splay_deg),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", required=True)
    ap.add_argument("--tolerance", type=float, default=1e-6)
    args = ap.parse_args()

    params: list[dict] = []
    for path in sorted(Path(args.fixtures).glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        gi = raw.get("geometry_input") or raw
        fd = raw.get("foundation_details") or {}
        dc = raw.get("drawing_control") or {}
        params.append(
            {
                "carriageway": gi.get("carriageway_width_m", 7.5),
                "abtl": fd.get("abtl", 13),
                "splay": dc.get("splay_deg", 45),
                "deckRl": gi.get("deck_level_m", 112.4),
                "foundingRl": (raw.get("levels") or {}).get("founding_level_m", 96.2),
            }
        )

    if not params:
        print("no fixtures found")
        return 2

    with tempfile.TemporaryDirectory() as tmp:
        drv = Path(tmp) / "drv.mjs"
        drv.write_text(DRIVER % CORE.as_uri(), encoding="utf-8")
        proc = subprocess.run(
            ["node", str(drv), json.dumps(params)], capture_output=True, text=True, timeout=120
        )
    if proc.returncode != 0:
        print(proc.stderr[:3000])
        return 2

    fails = []
    for p, js in zip(params, json.loads(proc.stdout), strict=False):
        py = python_facts(p)
        for key in ("face", "length", "ret"):
            if abs(py[key] - js[key]) > args.tolerance:
                fails.append(
                    f"abtl={p['abtl']} cw={p['carriageway']} splay={p['splay']} {key}: py {py[key]:.6f} vs js {js[key]:.6f}"
                )

    print(f"fixtures={len(params)} divergences={len(fails)}")
    for f in fails[:40]:
        print(" ", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
