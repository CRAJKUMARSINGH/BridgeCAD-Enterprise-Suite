#!/usr/bin/env python3
"""Simulate a basic (novice) user who copy-pastes and runs the happy path.

Run from the BridgeCAD repo root::

    python scripts/basic_user_robot.py --seed 123 --iterations 3
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], timeout: int = 180) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--iterations", type=int, default=3)
    args = parser.parse_args()
    random.seed(args.seed)

    results: list[dict] = []
    for i in range(args.iterations):
        print(f"=== Basic iteration {i + 1}/{args.iterations} ===")

        _, out = run([sys.executable, "-m", "bridgecad", "verify"])
        ok_verify = "ACCEPTED" in out
        print(f"  verify: {'PASS' if ok_verify else 'FAIL'}")

        _, out = run([sys.executable, "-m", "bridgecad", "generate", "11span"], timeout=300)
        ok_gen = "COMPLETE" in out or "OK" in out
        print(f"  generate: {'PASS' if ok_gen else 'FAIL'}")

        pdfs = list(Path("outputs").rglob("*.pdf")) if Path("outputs").exists() else []
        ok_out = len(pdfs) >= 1
        print(f"  outputs: {len(pdfs)} PDFs  {'PASS' if ok_out else 'FAIL'}")

        results.append({"iter": i, "verify": ok_verify, "generate": ok_gen, "outputs": ok_out})

    all_ok = all(r["verify"] and r["generate"] and r["outputs"] for r in results)
    Path("reports").mkdir(exist_ok=True)
    Path("reports/basic_robot.json").write_text(
        json.dumps({"seed": args.seed, "results": results, "all_ok": all_ok}, indent=2),
        encoding="utf-8",
    )
    print("ALL OK" if all_ok else "SOME FAILURES")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
