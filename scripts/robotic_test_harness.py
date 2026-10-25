#!/usr/bin/env python3
"""Phase 9 — Robotic Test Execution & Bug Fix Loop.

Automatically discovers TEST* and INPUT* files, feeds them through the
full pipeline (ingestion → calculation → rendering), validates outputs,
and logs failures for iterative bug fixing.

Usage:
    python scripts/robotic_test_harness.py
    python scripts/robotic_test_harness.py --fix-mode  # auto-retry on failure
"""

import argparse
import contextlib
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Windows consoles are often cp1252; keep harness logs ASCII-safe.
if hasattr(sys.stdout, "reconfigure"):
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bridge_gad.bridge_generator import BridgeGADGenerator
from bridge_gad.calc_engine import CalcEngine
from bridge_gad.enhanced_io_utils import SmartInputProcessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,  # stdout to avoid Windows stderr exit-code issue
)
logger = logging.getLogger(__name__)

BUG_LOG = Path("BUG_FIX_LOG.json")


def discover_inputs() -> list[Path]:
    """Auto-discover all test input files (TEST*, INPUT*, inputs/*.xlsx)."""
    candidates = []
    root = Path()
    candidates.extend(root.glob("TEST*.xlsx"))
    candidates.extend(root.glob("INPUT*.xlsx"))
    candidates.extend(root.glob("inputs/*.xlsx"))
    candidates.extend(root.glob("inputs/*.xls"))
    return sorted(set(candidates))


def run_pipeline(input_file: Path, output_dir: Path) -> dict[str, Any]:
    """Run full pipeline: ingestion → calculation → rendering → validation.

    Returns:
        Dict with keys: success, stage, error, output_file, metrics.
    """
    result: dict[str, Any] = {
        "input": str(input_file),
        "success": False,
        "stage": "init",
        "error": None,
        "output_file": None,
        "metrics": {},
    }
    start = time.perf_counter()

    try:
        # Stage 1: Ingestion
        result["stage"] = "ingestion"
        processor = SmartInputProcessor()
        params = processor.read_input(input_file)
        params = processor.validate_parameters(params)
        result["metrics"]["param_count"] = len(params)
        logger.info("  ✅ Ingestion: %d params", len(params))

        # Stage 2: Calculation
        result["stage"] = "calculation"
        engine = CalcEngine.with_bridge_defaults()
        engine.load(params)
        calculated = engine.recalculate()
        result["metrics"]["calculated_count"] = len(calculated)
        logger.info("  ✅ Calculation: %d values", len(calculated))

        # Stage 3: Rendering
        result["stage"] = "rendering"
        gen = BridgeGADGenerator()
        output_file = output_dir / f"{input_file.stem}_robotic.dxf"
        ok = gen.generate_complete_drawing(input_file, output_file)
        if not ok or not output_file.exists():
            raise RuntimeError("Rendering produced no output")
        result["output_file"] = str(output_file)
        result["metrics"]["output_size_kb"] = output_file.stat().st_size / 1024
        logger.info("  ✅ Rendering: %.1f KB", result["metrics"]["output_size_kb"])

        # Stage 4: Validation
        result["stage"] = "validation"
        if output_file.stat().st_size < 1024:
            raise RuntimeError("Output file suspiciously small (<1 KB)")
        logger.info("  ✅ Validation: passed")

        result["success"] = True
        result["stage"] = "complete"

    except Exception as exc:
        result["error"] = str(exc)
        logger.error("  ❌ %s failed: %s", result["stage"], exc)

    result["metrics"]["elapsed_sec"] = round(time.perf_counter() - start, 2)
    return result


def log_bug(result: dict[str, Any]) -> None:
    """Append failure to BUG_FIX_LOG.json."""
    bugs = []
    if BUG_LOG.exists():
        with contextlib.suppress(Exception):
            bugs = json.loads(BUG_LOG.read_text())
    bugs.append(
        {
            "timestamp": datetime.now().isoformat(),
            "input": result["input"],
            "stage": result["stage"],
            "error": result["error"],
        }
    )
    BUG_LOG.write_text(json.dumps(bugs, indent=2))
    logger.info("  📝 Bug logged to %s", BUG_LOG)


def main():
    parser = argparse.ArgumentParser(description="Robotic test harness")
    parser.add_argument("--fix-mode", action="store_true", help="Auto-retry on failure")
    args = parser.parse_args()

    logger.info("🤖 Robotic Test Harness — Phase 9")
    logger.info("─" * 70)

    inputs = discover_inputs()
    if not inputs:
        logger.error("No input files found (TEST*, INPUT*, inputs/*.xlsx)")
        return 1

    logger.info("Discovered %d input file(s):", len(inputs))
    for inp in inputs:
        logger.info("  • %s", inp)
    logger.info("")

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    results: list[dict[str, Any]] = []
    for idx, inp in enumerate(inputs, 1):
        logger.info("[%d/%d] Testing: %s", idx, len(inputs), inp.name)
        result = run_pipeline(inp, output_dir)
        results.append(result)
        if not result["success"]:
            log_bug(result)
            if args.fix_mode:
                logger.info("  🔄 Fix mode: retrying...")
                time.sleep(1)
                result = run_pipeline(inp, output_dir)
                results[-1] = result
        logger.info("")

    # Summary
    passed = sum(1 for r in results if r["success"])
    logger.info("─" * 70)
    logger.info("Summary: %d/%d passed", passed, len(results))
    if passed < len(results):
        logger.info("Failed inputs:")
        for r in results:
            if not r["success"]:
                logger.info("  • %s (stage: %s, error: %s)", r["input"], r["stage"], r["error"])
        return 1

    logger.info("✅ All tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
