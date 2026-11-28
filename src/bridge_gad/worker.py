"""ARQ async worker — background job processing for Bridge GAD Generator.

Phase 7: Background job abstraction using ARQ (async-native, Redis-backed).
Provides non-blocking Excel → DXF/PDF generation with SSE-ready status updates.

Usage:
    python -m bridge_gad.worker          # start worker process
    make worker                          # via Makefile
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379")


# ── Job functions ─────────────────────────────────────────────────────────────

async def generate_drawing_job(
    ctx: Dict[str, Any],
    excel_bytes: bytes,
    filename: str,
    acad_version: str = "R2010",
    output_format: str = "dxf",
) -> Dict[str, Any]:
    """Background job: Excel bytes → DXF/PDF generation.

    Args:
        ctx:           ARQ context (injected by worker).
        excel_bytes:   Raw bytes of the uploaded Excel file.
        filename:      Original filename (sanitised before use).
        acad_version:  AutoCAD version string (R2010 or R2006).
        output_format: Desired output format (dxf, pdf, png, svg, html, csv).

    Returns:
        Dict with keys: success, output_bytes, output_format, error.
    """
    from .bridge_generator import BridgeGADGenerator

    safe_name = Path(filename).name  # strip any path traversal
    logger.info("Job started: %s → %s (%s)", safe_name, output_format, acad_version)

    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            excel_path = tmp_path / safe_name
            excel_path.write_bytes(excel_bytes)

            output_path = tmp_path / f"output.{output_format}"
            gen = BridgeGADGenerator(acad_version=acad_version)

            success = gen.generate_complete_drawing(excel_path, output_path)
            if not success or not output_path.exists():
                return {"success": False, "error": "Generation returned no output file"}

            output_bytes = output_path.read_bytes()
            logger.info(
                "Job complete: %s → %d bytes", safe_name, len(output_bytes)
            )
            return {
                "success": True,
                "output_bytes": output_bytes,
                "output_format": output_format,
                "filename": f"bridge_drawing.{output_format}",
            }

    except Exception as exc:
        logger.exception("Job failed for %s: %s", safe_name, exc)
        return {"success": False, "error": str(exc)}


# ── Worker settings ───────────────────────────────────────────────────────────

class WorkerSettings:
    """ARQ WorkerSettings — configure via environment variables."""

    functions = [generate_drawing_job]
    redis_settings = None  # set dynamically below
    max_jobs = int(os.environ.get("ARQ_MAX_JOBS", "10"))
    job_timeout = int(os.environ.get("ARQ_JOB_TIMEOUT", "120"))  # seconds
    keep_result = int(os.environ.get("ARQ_KEEP_RESULT", "3600"))  # 1 hour


# Attach Redis settings at import time so ARQ CLI can discover them
try:
    from arq.connections import RedisSettings as _RedisSettings
    WorkerSettings.redis_settings = _RedisSettings.from_dsn(REDIS_URL)
except ImportError:
    logger.warning("arq not installed — worker will not start. Install with: pip install arq")


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        from arq import run_worker
        run_worker(WorkerSettings)
    except ImportError:
        print("arq is not installed. Run: pip install arq")
