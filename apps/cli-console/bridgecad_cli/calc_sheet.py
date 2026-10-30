"""
bridgecad_cli.calc_sheet — render a clause-mapped calculation sheet.

Runnable as a module::

    python -m bridgecad_cli.calc_sheet --demo
    python -m bridgecad_cli.calc_sheet project.xlsx -o sheet.md

The sheet is deterministic: identical input produces identical bytes, so it can
be diffed across revisions like any other deliverable.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def _demo_project() -> Any:
    """Build the canonical 1 × 12 m project from the e2e fixture."""
    repo = Path(__file__).resolve().parents[3]
    runner = repo / "tests" / "e2e" / "run_e2e.py"
    fixture = repo / "tests" / "e2e" / "fixtures" / "simple_12m.json"
    if not (runner.is_file() and fixture.is_file()):
        raise FileNotFoundError("demo fixture tests/e2e/fixtures/simple_12m.json not found")
    spec = importlib.util.spec_from_file_location("bridgecad_e2e_calc_sheet", runner)
    if spec is None or spec.loader is None:  # pragma: no cover - import fault
        raise ImportError("cannot load the e2e fixture builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = json.loads(fixture.read_text(encoding="utf-8"))
    return module._build_from_fixture(data)


def _load_project(path: Path) -> Any:
    from bridgecad_io.excel_reader import read_excel

    return read_excel(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bridgecad calc-sheet", description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, help="BridgeCAD Excel workbook")
    parser.add_argument("--demo", action="store_true", help="use the bundled demo project")
    parser.add_argument("-o", "--output", type=Path, help="write markdown here (default stdout)")
    args = parser.parse_args(argv)

    if args.demo or args.input is None:
        project = _demo_project()
    else:
        if not args.input.exists():
            sys.stderr.write(f"[bridgecad] calc-sheet :: not found: {args.input}\n")
            return 1
        project = _load_project(args.input)

    from bridgecad_qa.compliance_engine import calc_sheet_markdown

    markdown = calc_sheet_markdown(project)
    if args.output:
        args.output.write_text(markdown, encoding="utf-8")
        sys.stderr.write(f"[bridgecad] calc-sheet :: {args.output}\n")
    else:
        sys.stdout.write(markdown + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
