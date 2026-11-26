"""ARQ worker for BridgeCAD drawing, bill, and export jobs.

Jobs accept a JSON-safe ``BridgeProject`` mapping. Binary results are returned as
base64 so callers never depend on a worker-local temporary path.
"""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


def _env_int(*names: str, default: int) -> int:
    for name in names:
        raw = os.getenv(name)
        if raw:
            try:
                return max(1, int(raw))
            except ValueError:
                logger.warning("Ignoring non-integer %s=%r", name, raw)
    return default


def _redis_url() -> str:
    return (
        os.getenv("WORKER_REDIS_URL")
        or os.getenv("REDIS_URL")
        or os.getenv("CACHE_URL")
        or "redis://localhost:6379/0"
    )


def _safe_prefix(prefix: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", prefix):
        raise ValueError("prefix must be 1-64 letters, digits, underscores, or hyphens")
    return prefix


def _load_project(project_data: dict[str, Any]) -> Any:
    from bridgecad_io.json_adapter import project_from_dict

    return project_from_dict(project_data)


def _zip_bytes(paths: list[Path]) -> bytes:
    if not paths:
        raise ValueError("job produced no files")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, path.name)
    return buffer.getvalue()


def _artifact(payload: bytes, filename: str, output_format: str, **metadata: Any) -> dict[str, Any]:
    return {
        "success": True,
        "filename": filename,
        "output_format": output_format,
        "output_b64": base64.b64encode(payload).decode("ascii"),
        **metadata,
    }


def _generate_drawing(
    project_data: dict[str, Any],
    prefix: str,
    scale_denom: int | None,
    output_format: str,
) -> dict[str, Any]:
    from bridgecad_draw.booklet import generate_package

    prefix = _safe_prefix(prefix)
    if scale_denom is not None and scale_denom <= 0:
        raise ValueError("scale_denom must be positive")
    project = _load_project(project_data)
    output_format = output_format.lower()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        if output_format == "dxf":
            sheets = generate_package(project, root / "dxf", prefix=prefix, scale_denom=scale_denom)
            return _artifact(
                _zip_bytes(sheets),
                f"{prefix}_drawings.zip",
                "zip",
                sheet_count=len(sheets),
            )
        if output_format == "pdf":
            from bridgecad_draw.engines.pdf_engine import generate_pdf_booklet

            sheets = generate_package(project, root / "dxf", prefix=prefix, scale_denom=scale_denom)
            pdf = generate_pdf_booklet(sheets, root / f"{prefix}_booklet.pdf")
            return _artifact(
                pdf.read_bytes(),
                pdf.name,
                "pdf",
                sheet_count=len(sheets),
            )
        if output_format == "png":
            from bridgecad_draw.engines.png_engine import render_png
            from bridgecad_draw.sheet1_plan import generate

            dxf = generate(project, root / f"{prefix}_plan.dxf", scale_denom=scale_denom)
            png = render_png(dxf, root / f"{prefix}_plan.png")
            return _artifact(png.read_bytes(), png.name, "png")
        raise ValueError(f"unsupported drawing output_format: {output_format!r}")


def _generate_bill(
    project_data: dict[str, Any],
    prefix: str,
    state: str | None,
) -> dict[str, Any]:
    from bridgecad_bill.formatters.excel_formatter import format_excel
    from bridgecad_bill.processor import extract_and_price

    prefix = _safe_prefix(prefix)
    project = _load_project(project_data)
    boq = extract_and_price(project, state=state)
    with tempfile.TemporaryDirectory() as tmp:
        workbook = format_excel(boq, Path(tmp) / f"{prefix}_BOQ.xlsx")
        return _artifact(
            workbook.read_bytes(),
            workbook.name,
            "xlsx",
            grand_total_inr=str(boq.grand_total),
        )


def _export_package(
    project_data: dict[str, Any],
    prefix: str,
    state: str | None,
    scale_denom: int | None,
    allow_fail: bool,
) -> dict[str, Any]:
    from bridgecad_export.orchestrator import export_all

    prefix = _safe_prefix(prefix)
    if scale_denom is not None and scale_denom <= 0:
        raise ValueError("scale_denom must be positive")
    project = _load_project(project_data)
    with tempfile.TemporaryDirectory() as tmp:
        bundle = export_all(
            project,
            Path(tmp),
            prefix=prefix,
            state=state,
            scale_denom=scale_denom,
            allow_fail=allow_fail,
        )
        return _artifact(bundle.read_bytes(), bundle.name, "zip")


async def generate_drawing_job(
    _ctx: dict[str, Any],
    project_data: dict[str, Any],
    prefix: str = "GAD",
    scale_denom: int | None = None,
    output_format: str = "dxf",
) -> dict[str, Any]:
    """Generate a DXF ZIP, PDF booklet, or plan PNG from project JSON."""
    return await asyncio.to_thread(
        _generate_drawing, project_data, prefix, scale_denom, output_format
    )


async def generate_bill_job(
    _ctx: dict[str, Any],
    project_data: dict[str, Any],
    prefix: str = "GAD",
    state: str | None = None,
) -> dict[str, Any]:
    """Generate a priced BOQ workbook from project JSON."""
    return await asyncio.to_thread(_generate_bill, project_data, prefix, state)


async def export_package_job(
    _ctx: dict[str, Any],
    project_data: dict[str, Any],
    prefix: str = "GAD",
    state: str | None = None,
    scale_denom: int | None = None,
    allow_fail: bool = False,
) -> dict[str, Any]:
    """Generate the full DXF + BOQ + QA export bundle from project JSON."""
    return await asyncio.to_thread(
        _export_package, project_data, prefix, state, scale_denom, allow_fail
    )


class WorkerSettings:
    """ARQ settings; Redis is resolved at startup to keep facade imports optional."""

    functions: ClassVar[list[Any]] = [
        generate_drawing_job,
        generate_bill_job,
        export_package_job,
    ]
    redis_settings: ClassVar[Any] = None
    max_jobs = _env_int("WORKER_CONCURRENCY", "ARQ_MAX_JOBS", default=4)
    job_timeout = _env_int("WORKER_JOB_TIMEOUT", "ARQ_JOB_TIMEOUT", default=300)
    keep_result = _env_int("WORKER_KEEP_RESULT", "ARQ_KEEP_RESULT", default=3600)


def run_worker(settings: type[WorkerSettings] = WorkerSettings) -> None:
    """Start the ARQ worker using the configured Redis connection."""
    try:
        from arq import run_worker as arq_run_worker
        from arq.connections import RedisSettings
    except ImportError as exc:  # pragma: no cover - depends on optional install
        raise RuntimeError(
            "ARQ worker dependencies are missing. Install bridgecad-enterprise-suite[infra]."
        ) from exc

    if settings.redis_settings is None:
        settings.redis_settings = RedisSettings.from_dsn(_redis_url())
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
    )
    logger.info("Starting BridgeCAD ARQ worker with %d registered jobs", len(settings.functions))
    arq_run_worker(settings)


if __name__ == "__main__":  # pragma: no cover - process entrypoint
    run_worker()


__all__ = [
    "WorkerSettings",
    "export_package_job",
    "generate_bill_job",
    "generate_drawing_job",
    "run_worker",
]
