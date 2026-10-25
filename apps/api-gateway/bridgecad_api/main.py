"""
BridgeCAD Enterprise — FastAPI Gateway (M7).

Routers:
  /bridges  — project CRUD + Excel upload → BridgeProject
  /draw     — trigger 7-sheet DXF package generation
  /bills    — BOQ generation + download
  /qa       — compliance check + HTML report
  /exports  — full ZIP bundle orchestration
  /plugins  — list / info
  /health   — liveness probe
"""

from __future__ import annotations

import sys
import tempfile
import zipfile
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

# ── package path bootstrap ────────────────────────────────────────────────
_SUITE = Path(__file__).parents[3]
for _pkg in [
    "bridgecad-core",
    "bridgecad-io",
    "bridgecad-draw",
    "bridgecad-bill",
    "bridgecad-qa",
    "bridgecad-export",
    "bridgecad-plugins",
]:
    _p = _SUITE / "packages" / _pkg
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

__version__ = "0.1.0-rc1"
__codename__ = "BRIDGECAD-OSS-1.0"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _load_project_from_upload(data: bytes) -> Any:
    """Write upload bytes to a temp file, parse, return BridgeProject."""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tf:
        tf.write(data)
        tmp = Path(tf.name)
    try:
        from bridgecad_io.excel_reader import read_excel

        return read_excel(tmp)
    finally:
        tmp.unlink(missing_ok=True)


def _project_summary(project: Any) -> dict:
    pm = project.project_master
    gi = project.geometry_input
    return {
        "project_title": str(getattr(pm, "project_title", "") or ""),
        "bridge_name": str(getattr(pm, "bridge_name", "") or ""),
        "chainage_km": float(getattr(pm, "chainage_km", 0) or 0),
        "total_length_m": float(gi.total_length_m),
        "span_count": int(gi.span_count),
        "overall_width_m": float(gi.overall_width_m),
    }


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

# /bridges
bridges_router = APIRouter(prefix="/bridges", tags=["Bridges"])


@bridges_router.post("/parse", summary="Parse Excel → BridgeProject summary")
async def parse_bridge(file: UploadFile = File(...)) -> dict:
    """Upload a BridgeCAD Excel workbook; returns project metadata."""
    data = await file.read()
    try:
        project = _load_project_from_upload(data)
        return {"status": "ok", "project": _project_summary(project)}
    except Exception as exc:
        raise HTTPException(422, detail=str(exc)) from exc


@bridges_router.post("/validate", summary="Validate Excel → QA report JSON")
async def validate_bridge(file: UploadFile = File(...)) -> dict:
    """Parse and run all 30 QA checks; returns score + findings list."""
    data = await file.read()
    try:
        project = _load_project_from_upload(data)
        from bridgecad_core.validation import run_all
        from bridgecad_qa.compliance import score as _score

        report = run_all(project)
        comp = _score(report)
        findings = [
            {
                "check_id": f.check_id,
                "severity": f.severity.name if hasattr(f.severity, "name") else str(f.severity),
                "passed": f.passed,
                "description": f.description,
                "message": f.message,
            }
            for f in report.findings
        ]
        return {
            "status": "ok",
            "score": comp.overall,
            "grade": comp.grade,
            "critical_fails": comp.critical_fails,
            "warning_fails": comp.warning_fails,
            "findings": findings,
        }
    except Exception as exc:
        raise HTTPException(422, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Shared helpers for temp-file lifecycle
# ---------------------------------------------------------------------------

# BridgeCAD SP:55-2019 drawing scales are standard 1/n.  Anything outside
# this range is almost certainly a user typo (e.g. scale=1 -> 1 pixel/m).
_ALLOWED_SCALE = (10, 2500)
# Filename / prefix safety — Windows + Linux both disallow <>:"/\|?* and
# control characters; we also cap length so archive members are sensible.
_UNSAFE_PREFIX_CHARS = set('<>:"/\\|?*\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f')


def _validate_scale(scale: int) -> int:
    """Reject clearly-invalid drawing scale denominators."""
    if not isinstance(scale, int) or not (_ALLOWED_SCALE[0] <= scale <= _ALLOWED_SCALE[1]):
        raise HTTPException(
            status_code=400,
            detail=(
                f"scale must be an int drawing denominator between "
                f"{_ALLOWED_SCALE[0]} and {_ALLOWED_SCALE[1]} (got {scale!r}).  "
                f"Common values: 50, 100, 200, 500."
            ),
        )
    return scale


def _validate_prefix(prefix: str, *, max_len: int = 32) -> str:
    """Sanitize user-controlled output prefix — no path separators, no control chars."""
    if not isinstance(prefix, str) or not prefix:
        return "GAD"
    if any(ch in _UNSAFE_PREFIX_CHARS for ch in prefix):
        raise HTTPException(
            status_code=400,
            detail='prefix must not contain path separators, control characters, or <>:"|?*',
        )
    prefix = prefix.strip().replace(" ", "_")
    if len(prefix) > max_len:
        prefix = prefix[:max_len]
    return prefix or "GAD"


def _staged_zip_response(
    source_zip: Path,
    download_name: str,
    background_tasks: BackgroundTasks,
) -> FileResponse:
    """Atomically stage `source_zip` to an OS-cleaned temp file and schedule
    its deletion after the response completes.  This replaces the insecure
    `tempfile.mktemp()` pattern (TOCTOU race + leaked files) and guarantees
    the user-controlled `download_name` is only used for the Content-Disposition
    header, never for the on-disk filename."""
    # Names: use source_zip bytes via NamedTemporaryFile — atomic, no race
    staged = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    try:
        staged.close()  # allow Windows to reopen via shutil.copy
        import shutil as _shutil

        _shutil.copyfile(source_zip, Path(staged.name))
        staged_path = Path(staged.name)

        def _cleanup(p: Path = staged_path) -> None:
            with suppress(OSError):
                p.unlink(missing_ok=True)

        background_tasks.add_task(_cleanup)

        return FileResponse(
            path=str(staged_path),
            media_type="application/zip",
            filename=download_name,
        )
    except Exception:
        Path(staged.name).unlink(missing_ok=True)
        raise


# /draw
draw_router = APIRouter(prefix="/draw", tags=["Drawing"])


@draw_router.post("/gad", summary="Generate 7-sheet GAD DXF package → ZIP download")
async def draw_gad(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    scale: int = 100,
    prefix: str = "GAD",
) -> FileResponse:
    """Upload Excel, generate 7-sheet DXF package, return as ZIP."""
    scale = _validate_scale(scale)
    prefix = _validate_prefix(prefix)
    data = await file.read()
    try:
        project = _load_project_from_upload(data)
        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td)
            from bridgecad_draw.booklet import generate_package

            sheets = generate_package(project, out_dir, prefix=prefix, scale_denom=scale)
            # Zip the sheets inside the TemporaryDirectory (auto-cleaned)
            zip_path = out_dir / f"{prefix}_drawings.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for s in sheets:
                    zf.write(s, s.name)
            # Stage the zip outside of td for FileResponse; schedule cleanup
            return _staged_zip_response(
                source_zip=zip_path,
                download_name=f"{prefix}_drawings.zip",
                background_tasks=background_tasks,
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, detail=str(exc)) from exc


# /bills
bills_router = APIRouter(prefix="/bills", tags=["Bill of Quantities"])


@bills_router.post("/generate", summary="Generate BOQ → JSON")
async def generate_bill(
    file: UploadFile = File(...),
    state: str | None = None,
) -> dict:
    """Generate priced BOQ from uploaded Excel workbook."""
    data = await file.read()
    try:
        project = _load_project_from_upload(data)
        from bridgecad_bill.processor import extract_and_price

        boq = extract_and_price(project, state=state)
        sections = []
        for sec in boq.sections:
            items = []
            for item in sec.items:
                items.append(
                    {
                        "code": item.item_code,
                        "desc": item.description,
                        "unit": item.unit,
                        "qty": float(item.quantity),
                        "rate": float(item.rate) if item.rate else None,
                        "amount": float(item.amount) if item.amount else 0,
                    }
                )
            sections.append(
                {
                    "code": sec.section_code,
                    "title": sec.title,
                    "total": float(sec.total),
                    "items": items,
                }
            )
        return {
            "project_name": boq.project_name,
            "subtotal": float(boq.subtotal),
            "contingency_pct": float(boq.contingency_pct),
            "contingency_amount": float(boq.contingency_amount),
            "grand_total": float(boq.grand_total),
            "sections": sections,
        }
    except Exception as exc:
        raise HTTPException(422, detail=str(exc)) from exc


# /qa
qa_router = APIRouter(prefix="/qa", tags=["QA"])


@qa_router.post("/report", summary="Generate HTML QA report → download")
async def qa_report(file: UploadFile = File(...)) -> HTMLResponse:
    """Upload Excel, run QA, return styled HTML report."""
    data = await file.read()
    try:
        project = _load_project_from_upload(data)
        from bridgecad_core.validation import run_all
        from bridgecad_qa.reports import generate_html_report

        report = run_all(project)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as tf:
            tmp = Path(tf.name)
        generate_html_report(report, tmp, project)
        html = tmp.read_text(encoding="utf-8")
        tmp.unlink(missing_ok=True)
        return HTMLResponse(content=html, status_code=200)
    except Exception as exc:
        raise HTTPException(422, detail=str(exc)) from exc


# /exports
exports_router = APIRouter(prefix="/exports", tags=["Export"])


@exports_router.post("/bundle", summary="Full export → ZIP bundle download")
async def export_bundle(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    state: str | None = None,
    scale: int = 100,
) -> FileResponse:
    """Upload Excel → full export (DXF + BOQ + QA) → ZIP bundle."""
    scale = _validate_scale(scale)
    if state is not None and (len(state) > 16 or any(c in _UNSAFE_PREFIX_CHARS for c in state)):
        raise HTTPException(400, detail="state must be a short safe label (<=16 chars)")
    data = await file.read()
    try:
        project = _load_project_from_upload(data)
        with tempfile.TemporaryDirectory() as td:
            from bridgecad_export.orchestrator import export_all

            bundle = export_all(project, Path(td), prefix="export", state=state, scale_denom=scale)
            return _staged_zip_response(
                source_zip=Path(bundle),
                download_name="bridgecad_bundle.zip",
                background_tasks=background_tasks,
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, detail=str(exc)) from exc


# /plugins
plugins_router = APIRouter(prefix="/plugins", tags=["Plugins"])


@plugins_router.get("/", summary="List available plugins")
async def list_plugins() -> dict:
    from bridgecad_plugins.registry import get_registry

    reg = get_registry()
    return {
        "count": len(reg),
        "plugins": [
            {
                "id": p.plugin_id,
                "name": p.name,
                "version": p.version,
                "bridge_types": p.bridge_types,
                "span_range_m": p.span_range_m,
                "description": p.description,
            }
            for p in reg.all()
        ],
    }


@plugins_router.get("/{plugin_id}", summary="Plugin details")
async def plugin_detail(plugin_id: str) -> dict:
    from bridgecad_plugins.registry import get_registry
    from bridgecad_plugins.runner import PluginRunner

    reg = get_registry()
    m = reg.get(plugin_id)
    if not m:
        raise HTTPException(404, f"Plugin not found: {plugin_id}")
    runner = PluginRunner(m)
    return {
        "id": m.plugin_id,
        "name": m.name,
        "version": m.version,
        "description": runner.describe(),
        "typical_values": runner.get_typical_values(),
    }


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield  # M8: init DB / cache / storage here


app = FastAPI(
    title="BridgeCAD Enterprise API",
    description=(
        "🌉 **BridgeCAD Enterprise Suite** — REST API for automated bridge GAD generation.\n\n"
        "Upload an Excel workbook and get 7-sheet DXF drawings, "
        "priced BOQ, QA reports, and a full ZIP bundle."
    ),
    version=__version__,
    lifespan=lifespan,
    license_info={"name": "MIT"},
    contact={"name": "BridgeCAD Team"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wire routers
app.include_router(bridges_router)
app.include_router(draw_router)
app.include_router(bills_router)
app.include_router(qa_router)
app.include_router(exports_router)
app.include_router(plugins_router)


# Health / meta
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    packages_loaded: list[str] = []


@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    loaded = []
    for pkg in [
        "bridgecad_core",
        "bridgecad_draw",
        "bridgecad_bill",
        "bridgecad_qa",
        "bridgecad_export",
        "bridgecad_plugins",
    ]:
        try:
            __import__(pkg)
            loaded.append(pkg)
        except Exception:
            pass
    return HealthResponse(version=__version__, packages_loaded=loaded)


@app.get("/version", tags=["meta"])
async def version_endpoint() -> dict:
    return {"version": __version__, "codename": __codename__}
