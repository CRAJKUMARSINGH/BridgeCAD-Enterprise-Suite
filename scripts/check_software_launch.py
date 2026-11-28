"""Run the browser build and the focused BridgeCAD software launch checks."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    npm = shutil.which("npm")
    if npm is None:
        print("Install Node.js and npm before running the software launch checks.", file=sys.stderr)
        return 1

    checks = [
        ("Browser tests", [npm, "--prefix", "frontend", "test"]),
        ("Browser typecheck and production build", [npm, "--prefix", "frontend", "run", "build"]),
        (
            "Static browser demo and downloads",
            [sys.executable, "scripts/check_browser_drafting.py"],
        ),
        (
            "Drawing API test dependencies",
            [sys.executable, "-c", "import ezdxf, fastapi, httpx, matplotlib, pymupdf, reportlab"],
        ),
        (
            "Engineering acceptance and drawing API regressions",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "tests/unit/test_quality_manifest.py",
                "tests/draw/test_superstructure_section.py",
                "tests/integration/test_ga_sheet_download.py",
                "tests/integration/test_workbook_pdf_download.py",
            ],
        ),
    ]
    passed = True
    for label, command in checks:
        print(f"\n{label}", flush=True)
        if subprocess.run(command, cwd=ROOT, check=False).returncode != 0:
            passed = False
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
