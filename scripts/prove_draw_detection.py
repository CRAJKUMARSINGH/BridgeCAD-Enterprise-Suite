#!/usr/bin/env python3
"""Prove the Wing suite detects broken geometry, not just consistent geometry.

Difference from prove_detection.py: that one mutates documentation content.
This one mutates *product source* — constants, loop bounds, layer tables — and
asserts the drawing tests fail. A test suite that stays green while
`nspan - 1` becomes `nspan` is decorative.

Control run first: the unmutated copy must pass `-m "draw and not visual"`.
Otherwise a guard failing for unrelated reasons scores as "detected".

Usage:
    python scripts/prove_draw_detection.py
    python scripts/prove_draw_detection.py --json
    python scripts/prove_draw_detection.py --only G01,G05 --jobs 8
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAW_TESTS = "tests/draw"
SELECTION = "draw and not visual"

IGNORE_DIRS = frozenset(
    {
        ".git",
        "site",
        "site-wing",
        "site-api",
        "node_modules",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "htmlcov",
        ".benchmarks",
        "03_outputs",
        "outputs",
        "test_run_sample",
        "docs/api/_build",
    }
)

# Where the geometry actually lives. Update if the product moves.
GEOM = "packages/bridgecad-core/bridgecad_core/geometry/"
ABUT = GEOM + "abutment.py"
LONG = GEOM + "long_section.py"
LAYERS = "packages/bridgecad-draw/bridgecad_draw/layers.py"
TITLE = "packages/bridgecad-draw/bridgecad_draw/titleblocks.py"


def replace(root: Path, rel: str, old: str, new: str, count: int = -1) -> None:
    p = root / rel
    body = p.read_text(encoding="utf-8")
    if old not in body:
        raise AssertionError(f"{old!r} not found in {rel} — repo drifted from the harness")
    p.write_text(body.replace(old, new, count), encoding="utf-8")


def append(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.write_text(p.read_text(encoding="utf-8") + "\n" + text + "\n", encoding="utf-8")


def create(root: Path, rel: str, text: str = "") -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


@dataclass
class Mutation:
    id: str
    what: str
    guard: str  # pytest node id, or "" for whole-suite
    apply: Callable[[Path], None]
    severity: str = "high"
    detected: bool = field(default=False, init=False)
    ms: int = field(default=0, init=False)
    detail: str = field(default="", init=False)


# ── the mutations ────────────────────────────────────────────────────────────
# Each is a single plausible mistake a contributor could actually make.


def _g01(root):  # ABTL terminal default drifts
    replace(root, ABUT, "13.0", "15.0")


def _g02(root):  # splay default drifts off 45
    replace(root, ABUT, "splay_deg=45.0", "splay_deg=30.0")


def _g03(root):  # pier off-by-one — the documented NSPAN bug, reintroduced
    replace(root, LONG, "nspan - 1", "nspan")


def _g04(root):  # boundary count off-by-one
    replace(root, LONG, "nspan + 1", "nspan")


def _g05(root):  # face_run divided by 3 instead of 2
    replace(root, ABUT, "abtl_m - carriageway_width_m) / 2", "abtl_m - carriageway_width_m) / 3")


def _g06(root):  # cos swapped for sin in the wall length
    replace(root, ABUT, "math.cos(", "math.sin(")


def _g07(root):  # return projection loses the splay entirely
    replace(root, ABUT, "length_m * math.sin(", "length_m * 1.0 * math.sin(")
    replace(root, ABUT, "sin(math.radians(splay_deg))", "1.0")


def _g08(root):  # a layer is dropped from the registry
    append(root, LAYERS, "\nLAYERS.pop('DIM', None)\n")


def _g09(root):  # title block field renamed
    replace(root, TITLE, "CHECKED", "CHKD")


def _g10(root):  # sheet annotation index off by one
    replace(root, TITLE, "sheet_index", "sheet_index + 1")


def _g11(root):  # text drops below the legibility floor
    replace(root, TITLE, "TEXT_HEIGHT_MM = 2.5", "TEXT_HEIGHT_MM = 1.2")


def _g12(root):  # geometry leaks onto layer 0
    append(root, TITLE, "\n# leak: force everything onto 0\nLAYER_OVERRIDE = '0'\n")


def _g13(root):  # determinism broken by a timestamp in the title block
    replace(root, TITLE, "revision:", "revision: str(time.time()),")


def _g14(root):  # sign-off placeholder left in
    replace(
        root,
        "tests/draw/signoff/simple_12m__sheet5_pier_abutment_details.json",
        '"reviewed_by": "R.K. Singh"',
        '"reviewed_by": "REPLACE_ME"',
    )


def _g15(root):  # manifest claims construction-ready unconditionally
    replace(
        root,
        "packages/bridgecad-export/bridgecad_export/bundler.py",
        'return "Generated — not reviewed for construction"',
        'return "Construction ready"',
    )


def _g16(root):  # golden case reviewed_by set with no signoff record
    replace(
        root, "tests/draw/golden/simple_12m.json", '"reviewed_by": null', '"reviewed_by": "someone"'
    )


MUTATIONS = [
    Mutation("G01", "ABTL terminal default 13.0 -> 15.0", "", _g01, "critical"),
    Mutation("G02", "default splay 45 -> 30 deg", "", _g02, "critical"),
    Mutation("G03", "pier count nspan-1 -> nspan (the NSPAN bug)", "", _g03, "critical"),
    Mutation("G04", "span boundary count nspan+1 -> nspan", "", _g04, "critical"),
    Mutation("G05", "face_run /2 -> /3", "", _g05, "critical"),
    Mutation("G06", "wing length cos -> sin", "", _g06, "critical"),
    Mutation("G07", "return projection loses sin(splay)", "", _g07, "high"),
    Mutation("G08", "layer removed from the SP:55 registry", "", _g08, "high"),
    Mutation("G09", "title block field renamed CHECKED -> CHKD", "", _g09, "medium"),
    Mutation("G10", "sheet annotation index off by one", "", _g10, "medium"),
    Mutation("G11", "text height below legibility floor", "", _g11, "medium"),
    Mutation("G12", "geometry leaked onto layer 0", "", _g12, "medium"),
    Mutation("G13", "non-deterministic title block revision", "", _g13, "high"),
    Mutation("G14", "sign-off placeholder reviewer reintroduced", "", _g14, "medium"),
    Mutation("G15", "manifest claims construction-ready", "", _g15, "high"),
    Mutation("G16", "golden claims review with no signoff record", "", _g16, "low"),
]


# ── harness ──────────────────────────────────────────────────────────────────
def _ignore(_d: str, names: list[str]) -> list[str]:
    return [n for n in names if n in IGNORE_DIRS or n.endswith(".egg-info")]


def _copy(dest: Path) -> Path:
    target = dest / "repo"
    shutil.copytree(ROOT, target, ignore=_ignore, symlinks=True)
    return target


def _pytest(root: Path, target: str = DRAW_TESTS, timeout: int = 600) -> tuple[int, str]:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        target,
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "--tb=line",
        "-m",
        SELECTION,
    ]
    proc = subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=timeout,
        env={
            "PYTHONDONTWRITEBYTECODE": "1",
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "MPLBACKEND": "Agg",
        },
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def run_control(tmp: Path) -> tuple[bool, str]:
    root = _copy(tmp / "control")
    code, out = _pytest(root)
    return code == 0, out


def run_one(mut: Mutation, tmp: Path) -> Mutation:
    started = time.monotonic()
    try:
        root = _copy(tmp / mut.id)
        mut.apply(root)
        code, out = _pytest(root)
        mut.detected = code != 0
        mut.detail = (
            "guard fired"
            if mut.detected
            else ("SUITE STAYED GREEN — the tests do not constrain this")
        )
    except Exception as exc:
        mut.detected = False
        mut.detail = f"harness error: {type(exc).__name__}: {exc}"
    mut.ms = int((time.monotonic() - started) * 1000)
    return mut


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--only", default=None)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--skip-control", action="store_true")
    args = ap.parse_args()

    selected = MUTATIONS
    if args.only:
        wanted = {x.strip().upper() for x in args.only.split(",")}
        selected = [m for m in MUTATIONS if m.id in wanted]
        if not selected:
            print(f"no matching mutation in {sorted(wanted)}", file=sys.stderr)
            return 2

    tmp = Path(tempfile.mkdtemp(prefix="bridgecad-draw-proof-"))
    try:
        control_ok, control_out = True, ""
        if not args.skip_control:
            if not args.json:
                print(
                    "control: unmutated copy must pass the Wing suite ...",
                    file=sys.stderr,
                    flush=True,
                )
            control_ok, control_out = run_control(tmp)

        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            results = list(pool.map(lambda m: run_one(m, tmp), selected))

        detected = sum(1 for m in results if m.detected)
        undetected = [m.id for m in results if not m.detected]
        ok = control_ok and detected == len(results)

        payload = {
            "control_passed": control_ok,
            "detected": detected,
            "total": len(results),
            "undetected": undetected,
            "ok": ok,
            "results": [
                {
                    "id": m.id,
                    "mutation": m.what,
                    "severity": m.severity,
                    "detected": m.detected,
                    "detail": m.detail,
                    "duration_ms": m.ms,
                }
                for m in results
            ],
        }
        if not control_ok:
            payload["control_output"] = control_out[-2000:]

        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"\n  control run: {'PASS' if control_ok else 'FAIL'}")
            for m in results:
                print(f"  [{'DETECTED' if m.detected else 'MISSED  '}] {m.id}  {m.what}")
                if not m.detected:
                    print(f"            {m.detail}")
            print(f"\n  {detected}/{len(results)} geometry mutations detectable")
            if undetected:
                print(f"  holes in the Wing suite: {', '.join(undetected)}")
            print("  PROOF PASSED" if ok else "  PROOF FAILED")

        return 0 if ok else 1
    finally:
        if args.keep:
            print(f"\n  kept: {tmp}", file=sys.stderr)
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
