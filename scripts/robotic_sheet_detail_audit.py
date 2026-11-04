"""Robotic randomized audit for sheet 4 (foundation) and sheet 5 (pier/abutment/wing wall).

Runs the Node core (frontend/src/sheets/detailGeometry.js) over seeded random
parameter sets, checks the emitted primitive contract with an independent Python
oracle, and exits non-zero on any violation.

    python scripts/robotic_sheet_detail_audit.py --cases 2000 --seed 20261104
"""

from __future__ import annotations

import argparse
import json
import math
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "frontend" / "src" / "sheets" / "detailGeometry.js"

DRIVER = """
import fs from "node:fs";
import { buildSheet4, buildSheet5, audit, normalizeParams, wingWallGeometry } from "%s";
const cases = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const out = [];
for (const c of cases) {
  const rec = { seed: c.seed, sheet4: null, sheet5: null };
  try {
    const s4 = buildSheet4(c.params);
    rec.sheet4 = { audit: audit(s4), n: s4.prims.length };
    const s5 = buildSheet5(c.params);
    const w = wingWallGeometry(normalizeParams(c.params));
    rec.sheet5 = { audit: audit(s5), walls: w.walls.map(x => ({ ...x })), p: normalizeParams(c.params), n: s5.prims.length };
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
    bad = []
    face = max((p["abtl"] - p["carriageway"]) / 2.0, 0.0)
    if abs(face - wall["faceRunM"]) > 1e-6:
        bad.append(f"E_ORACLE_FACE {face:.4f} != {wall['faceRunM']:.4f}")
    rad = math.radians(wall["splayDeg"])
    hyp = face / math.cos(rad) if math.cos(rad) else 0.0
    if abs(hyp - wall["lengthM"]) > 1e-6:
        bad.append(f"E_ORACLE_LENGTH {hyp:.4f} != {wall['lengthM']:.4f}")
    if abs(hyp * math.sin(rad) - wall["returnM"]) > 1e-6:
        bad.append("E_ORACLE_RETURN")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=20261104)
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    if not CORE.exists():
        print(f"missing core: {CORE}")
        return 2
    rng = random.Random(args.seed)
    cases = [
        {"seed": rng.randint(1, 2**31 - 1), "params": rand_params(rng)} for _ in range(args.cases)
    ]

    with tempfile.TemporaryDirectory() as tmp:
        drv = Path(tmp) / "drv.mjs"
        drv.write_text(DRIVER % CORE.as_uri(), encoding="utf-8")
        # Cases travel by file, not argv: a few hundred seeded params blow past
        # the ~32k Windows CreateProcess command-line limit (WinError 206).
        cases_file = Path(tmp) / "cases.json"
        cases_file.write_text(json.dumps(cases), encoding="utf-8")
        proc = subprocess.run(
            ["node", str(drv), str(cases_file)], capture_output=True, text=True, timeout=900
        )
    if proc.returncode != 0:
        print(proc.stderr[:4000])
        return 2

    records = json.loads(proc.stdout)
    fails: list[str] = []
    for rec in records:
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

    print(f"cases={len(records)} sheet-renders={len(records) * 2} failures={len(fails)}")
    for f in fails[:40]:
        print(" ", f)
    if args.keep and fails:
        Path("robotic_failures.json").write_text(json.dumps(fails, indent=2), encoding="utf-8")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
