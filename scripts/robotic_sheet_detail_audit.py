"""Robotic randomized audit for sheet 4 (foundation) and sheet 5 (pier/abutment/wing wall).

Runs the Node core (frontend/src/sheets/detailGeometry.js) over seeded random
parameter sets, checks the emitted primitive contract with an independent Python
oracle, and exits non-zero on any violation.

    python scripts/robotic_sheet_detail_audit.py --cases 2000 --seed 20261104
    python scripts/robotic_sheet_detail_audit.py --mutate all --cases 200
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "frontend" / "src" / "sheets" / "detailGeometry.js"

#: Harness-side mutations. Each one breaks a contract the audit must catch, so a
#: mutation that survives means the gate is blind — see the failure drills.
MUTATIONS = {
    "splay-clamp": "const clampSplay = (v) => v;",
    "one-wall": "const ONLY = true;",
    "no-abtl-clamp": "const NOABTL = true;",
    "flat-grid": "const FLAT = true;",
    # Drawn-geometry mutations: they perturb the emitted wing-wall polygons, not
    # just the wall metadata, so they prove the audit reads the drawing itself.
    "axes-swap": "transpose each wing-wall polygon about its nose (run <-> return)",
    "corner-anchor": "spring both wing walls from one shared nose",
}

#: Remediation hints keyed by audit code, echoed when a failure is printed.
FIXES = {
    "E_OVERLAP": "panels collided — retune the band or shrink the clamp",
    "E_EXTENTS": "geometry left the drawing frame — check the mm() scale",
    "E_WALL_COUNT": "expected exactly two wing walls (left and right)",
    "E_WALL_ANCHOR": "both wing walls spring from one nose — anchor each at its own abutment end",
    "E_FACE_RUN": "the drawn wall's horizontal extent is not the face run — run and return are swapped",
    "E_ABTL_SHORT": "ABTL must exceed the carriageway by at least 2 m",
}

DRIVER = """
import fs from "node:fs";
import { buildSheet4, buildSheet5, audit, normalizeParams, wingWallGeometry } from "%s";
const cases = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const MUT = process.env.MUT || "";
const out = [];
for (const c of cases) {
  const rec = { seed: c.seed, sheet4: null, sheet5: null };
  try {
    const s4 = buildSheet4(c.params);
    const s5 = buildSheet5(c.params);
    wingWallGeometry(normalizeParams(c.params));
    if (MUT === "one-wall") s5.meta.walls = s5.meta.walls.slice(0, 1);
    if (MUT === "flat-grid") {
      const flat = { ...s5.meta.foundation, rows: 1, cols: 1, nPiles: 2 };
      s5.meta.foundation = flat;
      s4.meta.foundation = flat;
    }
    if (MUT === "no-abtl-clamp") s5.meta.params = { ...s5.meta.params, abtl: c.params.abtl };
    if (MUT === "splay-clamp") s5.meta.walls = s5.meta.walls.map((x) => ({ ...x, splayDeg: c.params.splay }));
    if (MUT === "axes-swap") {
      // Turn each wing wall a quarter-turn about its own nose: its drawn
      // horizontal extent then measures the return, not the face run. This is
      // the item-1 "run and return swapped" defect, injected into the drawing.
      s5.prims = s5.prims.map((q) => {
        if (!(q.k === "poly" && q.layer === "SUB-ABUT")) return q;
        const nx = q.pts[0], ny = q.pts[1], pts = [];
        for (let i = 0; i < q.pts.length; i += 2) pts.push(nx + (q.pts[i + 1] - ny), ny + (q.pts[i] - nx));
        return { ...q, pts };
      });
    }
    if (MUT === "corner-anchor") {
      // Spring both walls from the left wall's nose — the item-1 "both walls
      // anchored to one corner" defect. The two noses collapse to one point.
      const wallPolys = s5.prims.filter((q) => q.k === "poly" && q.layer === "SUB-ABUT");
      if (wallPolys.length > 1) {
        const nx = wallPolys[0].pts[0], ny = wallPolys[0].pts[1];
        for (const q of wallPolys) { q.pts[0] = nx; q.pts[1] = ny; }
      }
    }
    rec.sheet4 = { audit: audit(s4), n: s4.prims.length };
    rec.sheet5 = { audit: audit(s5), walls: s5.meta.walls.map((x) => ({ ...x })), p: s5.meta.params, n: s5.prims.length };
  } catch (e) { rec.error = String((e && e.message) || e); }
  out.push(rec);
}
process.stdout.write(JSON.stringify(out));
"""


def rand_params(rng: random.Random) -> dict:
    cw = rng.uniform(5, 12)
    return {
        "carriageway": cw,
        "abtl": rng.uniform(6, 26),
        "splay": rng.uniform(0, 89),
        "deckRl": rng.uniform(100, 140),
        "hflRl": rng.uniform(90, 110),
        "lwlRl": rng.uniform(80, 100),
        "foundingRl": rng.uniform(70, 95),
        "pileDiaMm": rng.uniform(400, 1800),
        "pileLenM": rng.uniform(2, 30),
        "capTMm": rng.uniform(600, 2000),
        "spacingM": rng.uniform(1.0, 5.0),
        "rows": rng.randint(1, 4),
        "cols": rng.randint(1, 4),
        "wellDiaM": rng.choice([0, 0, 0, rng.uniform(1, 6)]),
        "pierLenM": rng.uniform(2, 12),
        "pierWidM": rng.uniform(0.6, 3.0),
        "pierHgtM": rng.uniform(2, 14),
        "capWidM": rng.uniform(1.0, 3.5),
        "capDepM": rng.uniform(0.3, 1.4),
        "abtHgtM": rng.uniform(1.0, 7.0),
        "retHgtM": rng.uniform(1.0, 6.0),
        "girders": rng.randint(2, 9),
        "girderDepthMm": rng.uniform(500, 2000),
        "deckThickMm": rng.uniform(120, 450),
        "bearingsPerPier": rng.randint(2, 9),
        "spans": rng.randint(1, 12),
        "mainBarMm": rng.uniform(10, 36),
        "sbckPa": rng.uniform(60, 650),
    }


def oracle(wall: dict, p: dict) -> list[str]:
    """Independent invariant check on one wing wall.

    The wall is a right triangle measured from the abutment face: the face run and
    the return are its legs and the wall length is the hypotenuse. Checking
    Pythagoras, the angle recovered from the two drawn legs, and the face-run
    definition catches a wrong length or a swapped run/return *without* restating
    the implementation's own ``face / cos(splay)`` expression.
    """
    bad: list[str] = []
    face = (p["abtl"] - p["carriageway"]) / 2.0
    if abs(face - wall["faceRunM"]) > 1e-6:
        bad.append(f"E_ORACLE_FACE {face:.4f} != {wall['faceRunM']:.4f}")

    lhs = wall["lengthM"] ** 2
    rhs = wall["faceRunM"] ** 2 + wall["returnM"] ** 2
    if abs(lhs - rhs) > 1e-6 * max(1.0, lhs):
        bad.append(f"E_ORACLE_PYTHAGORAS {lhs:.4f} != {rhs:.4f}")

    # The angle recovered from the drawn legs must equal the declared splay.
    drawn_angle = math.degrees(math.atan2(wall["returnM"], wall["faceRunM"]))
    if abs(drawn_angle - wall["splayDeg"]) > 1e-6:
        bad.append(f"E_ORACLE_ANGLE {drawn_angle:.4f} != {wall['splayDeg']:.4f}")
    return bad


def run_cases(cases: list[dict], mutate: str = "") -> tuple[subprocess.CompletedProcess, list[str]]:
    with tempfile.TemporaryDirectory() as tmp:
        drv = Path(tmp) / "drv.mjs"
        drv.write_text(DRIVER % CORE.as_uri(), encoding="utf-8")
        # Cases travel by file, not argv: a few hundred seeded params blow past
        # the ~32k Windows CreateProcess command-line limit (WinError 206).
        cases_file = Path(tmp) / "cases.json"
        cases_file.write_text(json.dumps(cases), encoding="utf-8")
        proc = subprocess.run(
            ["node", str(drv), str(cases_file)],
            capture_output=True,
            text=True,
            timeout=900,
            env={**os.environ, "MUT": mutate},
        )
    if proc.returncode != 0:
        return proc, []

    fails: list[str] = []
    for rec in json.loads(proc.stdout):
        if rec.get("error"):
            fails.append(f"seed {rec['seed']}: E_THROW {rec['error']}")
            continue
        for sheet in ("sheet4", "sheet5"):
            blob = rec[sheet]
            for issue in blob["audit"]["issues"]:
                fails.append(f"seed {rec['seed']} S{sheet[-1]}: {issue['code']} {issue['detail']}")
            if blob["n"] < 60:
                fails.append(f"seed {rec['seed']} S{sheet[-1]}: E_THIN_SHEET {blob['n']} prims")
        for wall in rec["sheet5"]["walls"]:
            for bad in oracle(wall, rec["sheet5"]["p"]):
                fails.append(f"seed {rec['seed']} S5: {bad}")
    return proc, fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=20261104)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--mutate", default="", help="mutation name, or 'all'")
    args = ap.parse_args()

    if not CORE.exists():
        print(f"missing core: {CORE}")
        return 2

    def make_cases(count: int) -> list[dict]:
        rng = random.Random(args.seed)
        return [
            {"seed": rng.randint(1, 2**31 - 1), "params": rand_params(rng)} for _ in range(count)
        ]

    if args.mutate == "all":
        caught = 0
        for name in MUTATIONS:
            _proc, fails = run_cases(make_cases(args.cases), mutate=name)
            ok = len(fails) > 0
            caught += int(ok)
            print(
                f"  mutation {name:14s} {'caught' if ok else 'SURVIVED'} ({len(fails)} failure(s))"
            )
        print(f"mutation score {caught}/{len(MUTATIONS)}")
        return 0 if caught == len(MUTATIONS) else 1

    proc, fails = run_cases(make_cases(args.cases), mutate=args.mutate)
    if proc.returncode != 0:
        print(proc.stderr[:4000])
        return 2

    if args.mutate:
        print(f"mutation={args.mutate} cases={args.cases} failures={len(fails)}")
        for f in fails[:40]:
            print(" ", f)
        return 0 if fails else 1

    print(f"cases={args.cases} sheet-renders={args.cases * 2} failures={len(fails)}")
    for f in fails[:40]:
        print(" ", f)
    if args.keep and fails:
        Path("robotic_failures.json").write_text(json.dumps(fails, indent=2), encoding="utf-8")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
