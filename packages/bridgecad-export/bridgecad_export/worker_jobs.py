"""Synchronous job handlers for drawing, bill, and export artifacts."""

from __future__ import annotations

import base64
import io
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any


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


def generate_drawing(
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


def generate_bill(
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


def export_package(
    project_data: dict[str, Any],
    prefix: str,
    state: str | None,
    scale_denom: int | None,
    allow_fail: bool,
) -> dict[str, Any]:
    from .orchestrator import export_all

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
