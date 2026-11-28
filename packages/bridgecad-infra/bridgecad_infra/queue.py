"""ARQ worker for BridgeCAD drawing, bill, and export jobs.

Jobs accept a JSON-safe ``BridgeProject`` mapping. Binary results are returned as
base64 so callers never depend on a worker-local temporary path.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Callable
from functools import cache
from importlib.metadata import entry_points
from typing import Any, ClassVar, cast

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


@cache
def _load_job(name: str) -> Callable[..., dict[str, Any]]:
    """Resolve a job supplied by the installed export package."""
    provider = next(iter(entry_points(group="bridgecad.worker_jobs", name=name)), None)
    if provider is None:
        raise RuntimeError(f"Worker job {name!r} is unavailable. Install bridgecad-export.")
    return cast(Callable[..., dict[str, Any]], provider.load())


async def generate_drawing_job(
    _ctx: dict[str, Any],
    project_data: dict[str, Any],
    prefix: str = "GAD",
    scale_denom: int | None = None,
    output_format: str = "dxf",
) -> dict[str, Any]:
    """Generate a DXF ZIP, PDF booklet, or plan PNG from project JSON."""
    return await asyncio.to_thread(
        _load_job("drawing"), project_data, prefix, scale_denom, output_format
    )


async def generate_bill_job(
    _ctx: dict[str, Any],
    project_data: dict[str, Any],
    prefix: str = "GAD",
    state: str | None = None,
) -> dict[str, Any]:
    """Generate a priced BOQ workbook from project JSON."""
    return await asyncio.to_thread(_load_job("bill"), project_data, prefix, state)


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
        _load_job("package"), project_data, prefix, state, scale_denom, allow_fail
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
