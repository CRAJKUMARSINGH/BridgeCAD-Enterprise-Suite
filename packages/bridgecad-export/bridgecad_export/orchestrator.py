"""
bridgecad_export.orchestrator — Unified export: DXF + BOQ + QA report → ZIP bundle.

Each pipeline stage distinguishes **three** failure categories so callers can
triage problems instead of seeing a single opaque "something failed" warning:

* ``ImportError`` / ``ModuleNotFoundError`` — missing optional dependency or
  package not on ``sys.path`` (configuration / environment issue).
* ``OSError`` (``FileNotFoundError``, ``PermissionError``, …) — disk / path /
  filesystem write failure (output directory not writable).
* Any other ``Exception`` — runtime / logic / data bug (regression in one of
  the generators).  These are logged with full traceback.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

BASE = Path(__file__).parents[4]  # repo root


def _core_path():
    p = BASE / "packages" / "bridgecad-core"
    if p not in [Path(s) for s in sys.path]:
        sys.path.insert(0, str(p))


def _stage_failure(
    stage: str, exc: Exception, *, results_key: str, results: dict[str, list[Path]]
) -> None:
    """Record a pipeline-stage failure with structured log data.

    Uses ``logger.exception`` for any unexpected ``Exception`` so the full
    traceback is emitted into the application log, enabling post-mortem
    debugging without having to re-run the pipeline under a debugger.
    """
    import_err = isinstance(exc, ImportError | ModuleNotFoundError)
    io_err = isinstance(exc, OSError)

    if import_err:
        logger.warning(
            "%s skipped — package not importable: %s",
            stage,
            exc,
        )
    elif io_err:
        logger.warning(
            "%s failed — filesystem error (%s): %s",
            stage,
            type(exc).__name__,
            exc,
        )
    else:
        logger.exception(
            "%s failed — %s: %s  (traceback captured)",
            stage,
            type(exc).__name__,
            exc,
        )
    results[results_key] = []


def export_all(
    project: Any,
    output_dir: str | Path,
    prefix: str = "GAD",
    state: str | None = None,
    scale_denom: int | None = None,
    allow_fail: bool = False,
) -> Path:
    """Run the full export pipeline and return path to the ZIP bundle.

    Steps
    -----
    1. Generate 8-sheet DXF package (bridgecad-draw)
    2. Extract and price BOQ → Excel + CSV + PDF (bridgecad-bill)
    3. Run QA checks → HTML report (bridgecad-qa)
    4. Bundle everything into a ZIP (bridgecad-export.bundler)

    Individual stages that fail leave a clearly marked empty list in
    ``results`` so the downstream bundler can annotate the ZIP manifest
    instead of crashing with ``KeyError``.

    Returns
    -------
    Path
        Path to the generated ``{prefix}_bundle.zip``.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    results: dict[str, list[Path]] = {"dxf": [], "bill": [], "qa": [], "bbs": []}
    failures: dict[str, str] = {}

    # ── Step 1: DXF drawings ──────────────────────────────────────────────
    try:
        draw_out = out / "drawings"
        sys.path.insert(0, str(BASE / "packages" / "bridgecad-draw"))
        from bridgecad_draw.booklet import generate_package

        dxf_files = generate_package(project, draw_out, prefix=prefix, scale_denom=scale_denom)
        results["dxf"] = dxf_files
        logger.info("DXF: %d sheets generated", len(dxf_files))
    except Exception as exc:
        _stage_failure("DXF generation", exc, results_key="dxf", results=results)
        failures["dxf"] = f"{type(exc).__name__}: {exc}"

    # ── Step 2: Bill of Quantities ────────────────────────────────────────
    try:
        bill_out = out / "bill"
        bill_out.mkdir(exist_ok=True)
        sys.path.insert(0, str(BASE / "packages" / "bridgecad-bill"))
        from bridgecad_bill.formatters.csv_formatter import format_csv
        from bridgecad_bill.formatters.excel_formatter import format_excel
        from bridgecad_bill.formatters.pdf_formatter import format_pdf
        from bridgecad_bill.processor import extract_and_price

        boq = extract_and_price(project, state=state)
        xlsx_path = format_excel(boq, bill_out / f"{prefix}_BOQ.xlsx")
        csv_path = format_csv(boq, bill_out / f"{prefix}_BOQ.csv")
        pdf_path = format_pdf(boq, bill_out / f"{prefix}_BOQ.pdf")
        results["bill"] = [xlsx_path, csv_path, pdf_path]
        logger.info("BOQ: grand total INR %s  (xlsx+csv+pdf)", f"{float(boq.grand_total):,.0f}")
    except Exception as exc:
        _stage_failure("BOQ generation", exc, results_key="bill", results=results)
        failures["bill"] = f"{type(exc).__name__}: {exc}"

    # ── Step 3: Bar bending schedule ──────────────────────────────────────
    try:
        bbs_out = out / "bbs"
        bbs_out.mkdir(exist_ok=True)
        sys.path.insert(0, str(BASE / "packages" / "bridgecad-export"))
        from bridgecad_export.bbs import write_csv as bbs_csv
        from bridgecad_export.bbs import write_xlsx as bbs_xlsx

        bbs_csv_path = bbs_csv(project, bbs_out / f"{prefix}_BBS.csv")
        bbs_xlsx_path = bbs_xlsx(project, bbs_out / f"{prefix}_BBS.xlsx")
        results["bbs"] = [bbs_csv_path, bbs_xlsx_path]
        logger.info("BBS: %d bar marks", len(bbs_csv_path.read_text().splitlines()) - 2)
    except Exception as exc:
        _stage_failure("BBS generation", exc, results_key="bbs", results=results)
        failures["bbs"] = f"{type(exc).__name__}: {exc}"

    # ── Step 4: QA report ─────────────────────────────────────────────────
    try:
        qa_out = out / "qa"
        qa_out.mkdir(exist_ok=True)
        sys.path.insert(0, str(BASE / "packages" / "bridgecad-core"))
        from bridgecad_core.validation import run_all

        report = run_all(project)

        sys.path.insert(0, str(BASE / "packages" / "bridgecad-qa"))
        from bridgecad_qa.reports import generate_html_report

        html_path = generate_html_report(report, qa_out / f"{prefix}_QA.html", project)
        results["qa"] = [html_path]
        logger.info("QA: score=%d  critical_fails=%d", report.score, report.critical_fail_count)
    except Exception as exc:
        _stage_failure("QA report", exc, results_key="qa", results=results)
        failures["qa"] = f"{type(exc).__name__}: {exc}"

    # ── Reinforcement gate: over-utilised items block a clean export ──────
    try:
        sys.path.insert(0, str(BASE / "packages" / "bridgecad-core"))
        from bridgecad_core.detailing import failing_count

        failing = failing_count(project)
        if failing and not allow_fail:
            failures["reinforcement"] = (
                f"{failing} reinforcement item(s) over-utilised — "
                "pass allow_fail=True to ship anyway"
            )
            logger.warning("Export flagged: %d over-utilised rebar item(s)", failing)
    except Exception as exc:
        _stage_failure("reinforcement gate", exc, results_key="bbs", results=results)

    # ── Step 4: ZIP bundle ────────────────────────────────────────────────
    from .bundler import create_bundle

    bundle_path = create_bundle(out, prefix, results, project=project, failures=failures or None)
    logger.info("Bundle: %s  (%.1f KB)", bundle_path.name, bundle_path.stat().st_size / 1024)
    return bundle_path


__all__ = ["export_all"]
