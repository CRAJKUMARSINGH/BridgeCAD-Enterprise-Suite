"""Measure a source snapshot and generate three reference drawing manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

FIXTURES = ("simple_12m", "continuous_3x12m", "girder_4x18m")


def git(*arguments: str) -> str:
    return subprocess.check_output(["git", *arguments], text=True)


def measure(checkout: Path, revision: str) -> dict:
    paths = git("ls-tree", "-r", "-z", "--name-only", revision).split("\0")
    python = [checkout / path for path in paths if path.endswith(".py")]
    collection = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:hypothesispytest", "--collect-only", "-q"],
        cwd=checkout,
        capture_output=True,
        text=True,
        check=False,
    )
    summary = (collection.stdout or collection.stderr).strip().splitlines()
    summary = summary[-1] if summary else "No collection output"
    match = re.search(r"(\d+) tests? collected", summary)
    return {
        "tracked_files": len(paths) - 1,
        "python_files": len(python),
        "python_lines": sum(len(path.read_bytes().splitlines()) for path in python),
        "collection": {
            "exit_code": collection.returncode,
            "test_count": int(match[1]) if match else None,
            "summary": summary,
            "hypothesis_plugin": "disabled for the inventory",
        },
    }


def measure_drawings(checkout: Path, output: Path) -> dict:
    sys.path.insert(0, str(checkout / "tests" / "e2e"))
    from run_e2e import _build_from_fixture

    from bridgecad_draw.booklet import generate_package

    results = {}
    for key in FIXTURES:
        fixture = checkout / "tests" / "e2e" / "fixtures" / f"{key}.json"
        project = _build_from_fixture(json.loads(fixture.read_text(encoding="utf-8")))
        start = perf_counter()
        generate_package(project, output / key, prefix=key)
        elapsed = perf_counter() - start
        sheets = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((output / key).glob("*.dxf"))
        }
        if not sheets:
            raise RuntimeError(f"No reference DXFs generated for {key}")
        results[key] = {"wall_seconds": round(elapsed, 3), "sha256": sheets}
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checkout", type=Path, required=True, help="Extracted Git archive of the revision"
    )
    parser.add_argument("--revision", required=True, help="Git revision represented by the archive")
    parser.add_argument(
        "--coverage-json", type=Path, help="Explicit coverage.py JSON report for this revision"
    )
    parser.add_argument("--coverage-scope", help="Test selection used for the coverage report")
    parser.add_argument(
        "--repeat-drawings", action="store_true", help="Compare DXF bytes across two runs"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checkout = args.checkout.resolve()
    revision = git("rev-parse", args.revision).strip()
    report = {
        "revision": revision,
        "python": platform.python_version(),
        "platform": platform.system(),
        "toolchain": {package: version(package) for package in ("ezdxf", "pydantic", "pytest")},
        **measure(checkout, revision),
        "coverage": None,
    }
    if args.coverage_json is not None:
        coverage = json.loads(args.coverage_json.read_text(encoding="utf-8"))
        report["coverage"] = {
            "source": args.coverage_json.name,
            "test_selection": args.coverage_scope,
            "totals": coverage["totals"],
        }
    with TemporaryDirectory() as folder:
        root = Path(folder)
        report["reference_drawings"] = measure_drawings(checkout, root / "first")
        if args.repeat_drawings:
            second = measure_drawings(checkout, root / "second")
            report["repeat_drawings"] = {
                key: {
                    **second[key],
                    "identical": first["sha256"] == second[key]["sha256"],
                }
                for key, first in report["reference_drawings"].items()
            }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return int(report["collection"]["exit_code"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())
