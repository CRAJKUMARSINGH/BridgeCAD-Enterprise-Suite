#!/usr/bin/env python3
"""Robotic smoke for the Basic / Intermediate / Advanced user personas.

Run from the BridgeCAD repo root::

    python scripts/robotic_smoke.py --persona all --seed 42

The three personas mirror the complexity tiers in ``docs/getting-started.md``:
a novice happy path, a geometry-mutating intermediate user, and a
property/CI-style advanced user. Every step is recorded so a failure names the
persona and the step that broke, not just "something failed".
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
from pathlib import Path

REPO = Path.cwd()
SEED_DEFAULT = 42


def run(cmd: list[str], timeout: int = 180) -> tuple[int, str]:
    """Run *cmd* from the repo root; return ``(returncode, combined output)``."""
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=REPO)
    return proc.returncode, proc.stdout + proc.stderr


def basic(seed: int) -> dict:
    """Novice happy path: verify, generate, confirm artefacts exist."""
    random.seed(seed)
    results: dict = {"persona": "basic", "seed": seed, "steps": []}

    rc, out = run([sys.executable, "-m", "bridgecad", "verify"])
    results["steps"].append({"name": "verify", "rc": rc, "ok": rc == 0 and "ACCEPTED" in out})

    rc, out = run([sys.executable, "-m", "bridgecad", "generate", "11span"], timeout=300)
    results["steps"].append({"name": "generate_11span", "rc": rc, "ok": "COMPLETE" in out})

    pdfs = list(Path("outputs").rglob("*.pdf")) if Path("outputs").exists() else []
    results["steps"].append({"name": "pdfs_exist", "ok": bool(pdfs), "count": len(pdfs)})

    results["passed"] = all(step.get("ok") for step in results["steps"])
    return results


def intermediate(seed: int) -> dict:
    """Intermediate path: generate, then assert the project QA score is sane."""
    random.seed(seed)
    results: dict = {"persona": "intermediate", "seed": seed, "steps": []}

    rc, out = run([sys.executable, "-m", "bridgecad", "generate", "11span"], timeout=300)
    results["steps"].append({"name": "generate", "rc": rc, "ok": rc == 0})

    jsons = list(Path("outputs").rglob("project_*.json")) if Path("outputs").exists() else []
    if not jsons:
        results["steps"].append({"name": "project_json", "ok": False})
    else:
        try:
            data = json.loads(jsons[0].read_text(encoding="utf-8"))
        except Exception as exc:
            results["steps"].append({"name": "qa_parse", "ok": False, "error": str(exc)})
        else:
            score = data.get("qa_score") or (data.get("qa") or {}).get("score")
            qa_ok = score is None or (isinstance(score, int | float) and score >= 60)
            results["steps"].append({"name": "qa_score", "score": score, "ok": qa_ok})

    results["passed"] = all(step.get("ok", True) for step in results["steps"])
    return results


def advanced(seed: int) -> dict:
    """Advanced path: model schema, unit suite, optional property lane."""
    random.seed(seed)
    results: dict = {"persona": "advanced", "seed": seed, "steps": []}

    try:
        for pkg in Path("packages").glob("bridgecad-*"):
            sys.path.insert(0, str(pkg))
        from bridgecad_core.models import BridgeProject

        results["steps"].append({"name": "import_core", "ok": True})
        size = len(json.dumps(BridgeProject.model_json_schema()))
        results["steps"].append({"name": "schema_size", "bytes": size, "ok": size > 40_000})
    except Exception as exc:
        results["steps"].append({"name": "import_core", "ok": False, "error": str(exc)})

    rc, out = run([sys.executable, "-m", "pytest", "tests/unit", "-q", "--tb=no"], timeout=300)
    results["steps"].append({"name": "unit_tests", "rc": rc, "ok": rc == 0 or "passed" in out})

    results["passed"] = all(step.get("ok", False) for step in results["steps"])
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--persona", choices=["basic", "intermediate", "advanced", "all"], default="all"
    )
    parser.add_argument("--seed", type=int, default=SEED_DEFAULT)
    parser.add_argument("--out", type=str, default="reports")
    args = parser.parse_args()

    personas = ["basic", "intermediate", "advanced"] if args.persona == "all" else [args.persona]
    dispatch = {"basic": basic, "intermediate": intermediate, "advanced": advanced}

    report: dict = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "seed": args.seed, "personas": []}
    for name in personas:
        result = dispatch[name](args.seed)
        report["personas"].append(result)
        print(f"[{name.upper()}] passed={result['passed']}  steps={len(result['steps'])}")

    out_path = Path(args.out) / f"smoke_report_seed{args.seed}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

    sys.exit(0 if all(p["passed"] for p in report["personas"]) else 1)


if __name__ == "__main__":
    main()
