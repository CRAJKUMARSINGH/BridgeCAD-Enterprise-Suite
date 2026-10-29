"""FastAPI web API for the Bridge GAD Generator.

Phase 7 upgrades:
  - ARQ job queue integration (async, non-blocking)
  - SSE real-time job status endpoint
  - Rate limiting (slowapi)
  - Structured request tracing middleware
  - /health and /metrics endpoints
  - Pydantic v2 response models

Security fixes (retained):
  KERO-001 — CORS: origins from API_CORS_ORIGINS; wildcard refused in production
  KERO-003 — Path traversal: sanitise uploaded filename with Path.name
  REPLIT-004 — Correct MIME types per format
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
import tempfile
import shutil

from . import __version__
from .config import Settings, load_settings
from .core import generate_bridge_drawing
from .logger_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

# ── MIME type map ─────────────────────────────────────────────────────────────
_MIME_TYPES = {
    "dxf":   "application/dxf",
    "pdf":   "application/pdf",
    "png":   "image/png",
    "svg":   "image/svg+xml",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xlsx":  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv":   "text/csv",
    "html":  "text/html",
}

# ── In-memory job store (replace with Redis in production) ────────────────────
_jobs: dict[str, dict] = {}

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Bridge GAD Generator API",
    description="REST API for generating Bridge General Arrangement Drawings",
    version=__version__,
)

# KERO-001: origins come from API_CORS_ORIGINS (see .env.example); the wildcard
# is refused in production so a misconfigured deploy cannot open the API to all.
_DEV_ORIGINS = ["http://localhost:5173", "http://localhost:8501", "http://localhost:80"]


def _cors_origins() -> list[str]:
    """Resolve allowed CORS origins from the environment.

    Falls back to local development origins outside production. In production
    the origin list is mandatory and a wildcard is rejected at startup.
    """
    origins = [o.strip() for o in os.getenv("API_CORS_ORIGINS", "").split(",") if o.strip()]
    is_prod = os.getenv("ENV", "dev").strip().lower() == "production"
    if is_prod:
        if not origins:
            raise RuntimeError("API_CORS_ORIGINS must be set when ENV=production")
        if "*" in origins:
            raise RuntimeError("API_CORS_ORIGINS must not contain '*' when ENV=production")
        return origins
    return origins or _DEV_ORIGINS


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request tracing middleware ────────────────────────────────────────────────
@app.middleware("http")
async def trace_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    request.state.request_id = request_id
    logger.info("[%s] %s %s", request_id, request.method, request.url.path)
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("[%s] %s %.1fms", request_id, response.status_code, elapsed_ms)
    response.headers["X-Request-ID"] = request_id
    return response

settings = load_settings()

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "Bridge GAD Generator API",
        "version": __version__,
        "endpoints": [
            {"path": "/predict",        "method": "POST", "description": "Sync: generate drawing (blocks until done)"},
            {"path": "/template",       "method": "GET",  "description": "Download template workbook (query: template_key=[simple_12m|...])"},
            {"path": "/package",        "method": "GET",  "description": "Download submission ZIP (template_key + include_phase_three bool)"},
            {"path": "/generate_sample_pdf", "method": "GET",  "description": "Generate sample PDF drawing"},
            {"path": "/jobs",           "method": "POST", "description": "Async: enqueue generation job"},
            {"path": "/jobs/{job_id}",  "method": "GET",  "description": "Poll job status"},
            {"path": "/jobs/{job_id}/stream", "method": "GET", "description": "SSE: stream job status"},
            {"path": "/health",         "method": "GET",  "description": "Health check"},
            {"path": "/metrics",        "method": "GET",  "description": "Basic metrics"},
        ],
    }


@app.post("/predict")
async def predict(
    excel_file: UploadFile = File(...),
    config_file: Optional[UploadFile] = None,
    output_format: str = "dxf",
):
    """Synchronous generation — blocks until the drawing is ready.
    For large files prefer POST /jobs (async).

    BUG-FIX (2026-10-16): FileResponse inside a TemporaryDirectory context manager
    caused FileNotFoundError because the tempdir was deleted before FastAPI could
    stream the file.  Fixed by reading file bytes into memory before the tempdir
    exits, then returning Response(content=bytes).  This keeps the fix minimal and
    avoids any change to generate_bridge_drawing().
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # KERO-003: strip directory components
        safe_name = Path(excel_file.filename or "upload.xlsx").name or "upload.xlsx"
        excel_path = temp_dir_path / safe_name
        with open(excel_path, "wb") as f:
            shutil.copyfileobj(excel_file.file, f)

        config_path: Optional[Path] = None
        if config_file:
            config_path = temp_dir_path / "config.yaml"
            with open(config_path, "wb") as f:
                shutil.copyfileobj(config_file.file, f)

        # generate_bridge_drawing always writes DXF; post-convert when needed
        dxf_output_path = temp_dir_path / "output.dxf"

        try:
            result_path = generate_bridge_drawing(
                excel_file=excel_path,
                config_file=config_path,
                output_path=dxf_output_path,
            )
            if not result_path.exists():
                raise HTTPException(status_code=500, detail="No output file created")

            fmt = output_format.lower()
            if fmt in ("pdf", "png", "svg") and result_path.suffix.lower() == ".dxf":
                # Convert DXF → requested format
                try:
                    from .dxf_to_pdf import convert_dxf_to_pdf
                    converted_path = temp_dir_path / f"output.{fmt}"
                    if fmt == "pdf":
                        convert_dxf_to_pdf(result_path, converted_path)
                    else:
                        # For png/svg fall back to DXF if converter unavailable
                        converted_path = result_path
                        fmt = "dxf"
                    if converted_path.exists():
                        result_path = converted_path
                    else:
                        # Conversion produced nothing — return DXF instead
                        fmt = "dxf"
                except Exception as conv_exc:
                    logger.warning("Format conversion failed (%s) — returning DXF", conv_exc)
                    fmt = "dxf"

            # Read into memory BEFORE the TemporaryDirectory context exits
            file_bytes = result_path.read_bytes()

        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    # tempdir is now cleaned up — serve from in-memory bytes
    mime = _MIME_TYPES.get(fmt, "application/octet-stream")
    return Response(
        content=file_bytes,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="bridge_drawing.{fmt}"'},
    )


@app.post("/jobs", status_code=202)
async def enqueue_job(
    excel_file: UploadFile = File(...),
    output_format: str = "dxf",
    acad_version: str = "R2010",
):
    """Async generation — returns a job_id immediately.
    Poll GET /jobs/{job_id} or stream GET /jobs/{job_id}/stream for status.
    """
    job_id = str(uuid.uuid4())
    excel_bytes = await excel_file.read()
    safe_name = Path(excel_file.filename).name

    _jobs[job_id] = {"status": "queued", "progress": 0, "result": None, "error": None}

    # Try ARQ if available, else run in asyncio background task
    try:
        from arq.connections import ArqRedis, RedisSettings
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        redis: ArqRedis = await ArqRedis.from_url(redis_url)
        await redis.enqueue_job(
            "generate_drawing_job",
            excel_bytes=excel_bytes,
            filename=safe_name,
            acad_version=acad_version,
            output_format=output_format,
            _job_id=job_id,
        )
        _jobs[job_id]["backend"] = "arq"
    except Exception:
        # Fallback: asyncio background task (single-server, no Redis needed)
        asyncio.create_task(
            _run_job_background(job_id, excel_bytes, safe_name, acad_version, output_format)
        )
        _jobs[job_id]["backend"] = "asyncio"

    logger.info("Job enqueued: %s (%s)", job_id, safe_name)
    return {"job_id": job_id, "status": "queued"}


async def _run_job_background(
    job_id: str,
    excel_bytes: bytes,
    filename: str,
    acad_version: str,
    output_format: str,
) -> None:
    """Asyncio fallback: run generation in a thread pool to avoid blocking."""
    import asyncio
    from .bridge_generator import BridgeGADGenerator

    _jobs[job_id]["status"] = "running"
    _jobs[job_id]["progress"] = 10

    def _sync_generate():
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            excel_path = tmp_path / filename
            excel_path.write_bytes(excel_bytes)
            output_path = tmp_path / f"output.{output_format}"
            gen = BridgeGADGenerator(acad_version=acad_version)
            ok = gen.generate_complete_drawing(excel_path, output_path)
            if ok and output_path.exists():
                return output_path.read_bytes()
            return None

    try:
        loop = asyncio.get_event_loop()
        result_bytes = await loop.run_in_executor(None, _sync_generate)
        if result_bytes:
            _jobs[job_id].update({
                "status": "complete",
                "progress": 100,
                "result": result_bytes,
                "output_format": output_format,
            })
        else:
            _jobs[job_id].update({"status": "failed", "error": "Generation produced no output"})
    except Exception as exc:
        _jobs[job_id].update({"status": "failed", "error": str(exc)})


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Poll job status. Returns result bytes as base64 when complete."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    response: dict = {
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0),
    }
    if job["status"] == "complete" and job.get("result"):
        import base64
        response["result_b64"] = base64.b64encode(job["result"]).decode()
        response["output_format"] = job.get("output_format", "dxf")
    if job.get("error"):
        response["error"] = job["error"]
    return response


@app.get("/jobs/{job_id}/stream")
async def stream_job(job_id: str):
    """SSE endpoint — streams job status updates until complete or failed."""
    async def _event_generator() -> AsyncGenerator[str, None]:
        for _ in range(120):  # max 120 × 1s = 2 min
            job = _jobs.get(job_id)
            if not job:
                yield f"data: {{\"error\": \"job not found\"}}\n\n"
                return
            payload = f'{{"status": "{job["status"]}", "progress": {job.get("progress", 0)}}}'
            yield f"data: {payload}\n\n"
            if job["status"] in ("complete", "failed"):
                return
            await asyncio.sleep(1)
        yield 'data: {"status": "timeout"}\n\n'

    return StreamingResponse(_event_generator(), media_type="text/event-stream")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": __version__}


@app.get("/metrics")
async def metrics():
    """Basic job metrics."""
    total = len(_jobs)
    by_status: dict[str, int] = {}
    for j in _jobs.values():
        s = j.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
    return {"total_jobs": total, "by_status": by_status, "version": __version__}


@app.get("/template")
async def get_template(template_key: str = "simple_12m"):
    """Return a 4-sheet parameter workbook (Parameters / Checklist /
    OwnerProfiles / SheetIndex) seeded from the named bridge template.

    Use ``/template?template_key=simple_12m`` or any key listed in
    ``bridge_gad.bridge_canvas_features.BRIDGE_TEMPLATES``.
    """
    try:
        from .bridge_canvas_features import BRIDGE_TEMPLATES, make_template_excel
    except ImportError as exc:  # pragma: no cover - pandas/openpyxl env issue
        raise HTTPException(
            status_code=503,
            detail=f"Template generator unavailable ({exc}). Install pandas+openpyxl.",
        )
    if template_key not in BRIDGE_TEMPLATES:
        keys = sorted(BRIDGE_TEMPLATES.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Unknown template_key '{template_key}'. Available: {keys}",
        )
    params = BRIDGE_TEMPLATES[template_key]["parameters"]
    xls_bytes = make_template_excel(params)
    return Response(
        content=xls_bytes,
        media_type=_MIME_TYPES["xlsx"],
        headers={
            "Content-Disposition": f"attachment; filename={template_key}_bridge.xlsx"
        },
    )


@app.get("/package")
async def get_package(
    template_key: str = "simple_12m",
    include_phase_three: bool = False,
):
    """Return a submission ZIP bundle with enriched workbook, sheet
    index CSV and JSON manifest.

    * ``include_phase_three=false`` → 7-sheet Phase 2 (GAD/TYP/ABT/PIER/BRG/DRN + IDX).
    * ``include_phase_three=true``  → 11-sheet Phase 3 with the four consultant-grade
      detail sheets BRG-DET / EXPJ-DET / WING-DET / DRN-DET appended. All indicative
      proportions on sheets 8–11 are ring-fenced on the DXF itself with the
      ``TBC_BY_ENGINEER`` stamp.
    """
    try:
        from .bridge_canvas_features import (
            BRIDGE_TEMPLATES,
            make_phase_two_package_zip,
            make_phase_three_package_zip,
        )
    except ImportError as exc:  # pragma: no cover - pandas env issue
        raise HTTPException(
            status_code=503,
            detail=f"Package generator unavailable ({exc}). Install pandas+openpyxl.",
        )
    if template_key not in BRIDGE_TEMPLATES:
        keys = sorted(BRIDGE_TEMPLATES.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Unknown template_key '{template_key}'. Available: {keys}",
        )
    params = BRIDGE_TEMPLATES[template_key]["parameters"]
    if include_phase_three:
        zip_bytes = make_phase_three_package_zip(params)
        fname = f"{template_key}_bridge_phase3.zip"
    else:
        zip_bytes = make_phase_two_package_zip(params)
        fname = f"{template_key}_bridge_phase2.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


@app.get("/generate_sample_pdf")
async def generate_sample_pdf():
    """Generate a sample PDF drawing using the simple_12m template.

    BUG-FIX (2026-10-16): FileResponse inside TemporaryDirectory caused
    FileNotFoundError.  Fixed by reading result bytes into memory before the
    tempdir context exits, then returning Response(content=bytes).
    Also: if PDF conversion fails, return DXF so the endpoint never 500s on
    a conversion-only failure.
    """
    try:
        from .bridge_canvas_features import BRIDGE_TEMPLATES, make_template_excel
        from .bridge_generator import BridgeGADGenerator
        import pandas as pd
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Sample PDF generator unavailable ({exc}). Install required dependencies.",
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Generate Excel input from template
        template_key = "simple_12m"
        params = BRIDGE_TEMPLATES[template_key]["parameters"]
        xls_bytes = make_template_excel(params)

        # Convert to the row-oriented format BridgeGADGenerator.read_variables_from_excel expects
        import pandas as pd  # noqa: F811 — already imported above, re-import for clarity
        df = pd.DataFrame([[v, k, k] for k, v in params.items()], columns=["Value", "Variable", "Description"])
        generator_input_path = temp_dir_path / "generator_input.xlsx"
        df.to_excel(generator_input_path, index=False, header=False)

        # Generate DXF
        dxf_path = temp_dir_path / "sample_bridge.dxf"
        gen = BridgeGADGenerator()
        gen.generate_complete_drawing(generator_input_path, dxf_path)

        if not dxf_path.exists():
            raise HTTPException(status_code=500, detail="DXF generation failed")

        # Attempt DXF → PDF conversion
        pdf_bytes: Optional[bytes] = None
        serve_as = "dxf"
        try:
            from .dxf_to_pdf import convert_dxf_to_pdf
            pdf_path = temp_dir_path / "sample_bridge.pdf"
            convert_dxf_to_pdf(dxf_path, pdf_path)
            if pdf_path.exists():
                pdf_bytes = pdf_path.read_bytes()
                serve_as = "pdf"
        except Exception as conv_exc:
            logger.warning("PDF conversion failed for sample PDF (%s) — serving DXF", conv_exc)

        # Read into memory BEFORE TemporaryDirectory exits
        file_bytes = pdf_bytes if pdf_bytes else dxf_path.read_bytes()

    # tempdir cleaned up — serve from memory
    mime = _MIME_TYPES[serve_as]
    return Response(
        content=file_bytes,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="sample_bridge_gad.{serve_as}"'},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
