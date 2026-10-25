#!/usr/bin/env python3
"""Build a PDF from the repository's own sample workbooks and DXF generator.

The catalogue intentionally does not invent bridge names or dimensions. Each
page is sourced from one workbook already present in this repository.
"""

from __future__ import annotations

import sys
from itertools import pairwise
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import ezdxf
from ezdxf import bbox

from bridge_gad.bridge_generator import BridgeGADGenerator

SOURCES = [
    Path("public/samples/bridge_23span.xlsx"),
    Path("public/samples/bridge_comprehensive.xlsx"),
    Path("public/samples/bridge_large.xlsx"),
    Path("public/samples/bridge_simple_12m.xlsx"),
    Path("public/samples/sample_input.xlsx"),
    Path("public/samples/template_arch_24m.xlsx"),
    Path("public/samples/template_box_culvert_8m.xlsx"),
    Path("public/samples/template_continuous_3x12m.xlsx"),
    Path("public/samples/template_girder_4x18m.xlsx"),
    Path("public/samples/template_simple_12m.xlsx"),
    Path("inputs/large_bridge.xlsx"),
]

OUTPUT = ROOT / "frontend/public/bridge-catalogue-11.pdf"
PAGE_W, PAGE_H = landscape(A4)
INK = colors.HexColor("#16383c")
MUTED = colors.HexColor("#6a7f81")
TEAL = colors.HexColor("#2b8b87")
AMBER = colors.HexColor("#d99846")
GRID = colors.HexColor("#c5d4d0")
PAPER = colors.HexColor("#f7faf7")


def xy(point) -> tuple[float, float]:
    return float(point[0]), float(point[1])


def draw_dxf_geometry(pdf: canvas.Canvas, doc, box: tuple[float, float, float, float]) -> int:
    x, y, width, height = box
    pdf.setFillColor(colors.white)
    pdf.setStrokeColor(GRID)
    pdf.roundRect(x, y, width, height, 5, fill=1, stroke=1)
    modelspace = doc.modelspace()
    extents = bbox.extents(modelspace)
    min_x, min_y = float(extents.extmin[0]), float(extents.extmin[1])
    max_x, max_y = float(extents.extmax[0]), float(extents.extmax[1])
    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)
    scale = min((width - 18) / span_x, (height - 18) / span_y)
    offset_x = x + (width - span_x * scale) / 2
    offset_y = y + (height - span_y * scale) / 2

    def map_point(point) -> tuple[float, float]:
        px, py = xy(point)
        return offset_x + (px - min_x) * scale, offset_y + (py - min_y) * scale

    count = 0
    pdf.setLineWidth(0.45)
    for entity in modelspace:
        kind = entity.dxftype()
        if kind == "LINE":
            start = map_point(entity.dxf.start)
            end = map_point(entity.dxf.end)
            pdf.setStrokeColor(TEAL)
            pdf.line(*start, *end)
            count += 1
        elif kind == "LWPOLYLINE":
            points = [map_point(point) for point in entity.get_points("xy")]
            if len(points) >= 2:
                pdf.setStrokeColor(TEAL)
                for start, end in pairwise(points):
                    pdf.line(*start, *end)
                if entity.closed:
                    pdf.line(*points[-1], *points[0])
                count += 1
        elif kind == "CIRCLE":
            center = map_point(entity.dxf.center)
            radius = float(entity.dxf.radius) * scale
            pdf.setStrokeColor(AMBER)
            pdf.circle(center[0], center[1], max(radius, 0.4), stroke=1, fill=0)
            count += 1
    return count


def draw_page(
    pdf: canvas.Canvas, index: int, source: Path, dxf_path: Path, entity_count: int
) -> None:
    pdf.setFillColor(PAPER)
    pdf.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    pdf.setStrokeColor(INK)
    pdf.setLineWidth(1.2)
    pdf.rect(13 * mm, 13 * mm, PAGE_W - 26 * mm, PAGE_H - 26 * mm, fill=0, stroke=1)
    pdf.setStrokeColor(GRID)
    pdf.setLineWidth(0.4)
    pdf.rect(17 * mm, 17 * mm, PAGE_W - 34 * mm, PAGE_H - 34 * mm, fill=0, stroke=1)

    pdf.setFillColor(INK)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(22 * mm, PAGE_H - 23 * mm, "BRIDGE GAD · REPOSITORY SAMPLE OUTPUT")
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 7)
    pdf.drawRightString(PAGE_W - 22 * mm, PAGE_H - 23 * mm, f"SHEET {index}/11 · SOURCE-DRIVEN")
    pdf.setStrokeColor(GRID)
    pdf.line(22 * mm, PAGE_H - 28 * mm, PAGE_W - 22 * mm, PAGE_H - 28 * mm)

    pdf.setFillColor(INK)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(22 * mm, PAGE_H - 45 * mm, source.stem)
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(22 * mm, PAGE_H - 53 * mm, f"Workbook: {source.as_posix()}")
    pdf.drawString(
        22 * mm,
        PAGE_H - 60 * mm,
        f"Native generator output: {dxf_path.name} · DXF entities rendered: {entity_count}",
    )

    draw_dxf_geometry(
        pdf,
        dxf_path and ezdxf.readfile(dxf_path),
        (22 * mm, 45 * mm, PAGE_W - 44 * mm, PAGE_H - 115 * mm),
    )

    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 6.5)
    pdf.drawString(
        22 * mm,
        20 * mm,
        "Generated only from files already present in this repository. Review engineering inputs before construction use.",
    )
    pdf.drawRightString(PAGE_W - 22 * mm, 20 * mm, "BRIDGE GAD · PDF EXPORT")
    pdf.showPage()


def build() -> int:
    work_dir = ROOT / ".bridge_repo_pdf_work"
    dxf_dir = work_dir / "dxf"
    dxf_dir.mkdir(parents=True, exist_ok=True)
    generator = BridgeGADGenerator()
    generated: list[tuple[Path, Path]] = []

    for source in SOURCES:
        source_path = ROOT / source
        if not source_path.exists():
            raise FileNotFoundError(source_path)
        dxf_path = dxf_dir / f"{source.stem}.dxf"
        if not generator.generate_complete_drawing(source_path, dxf_path) or not dxf_path.exists():
            raise RuntimeError(f"Native bridge generator failed for {source}")
        generated.append((source, dxf_path))

    pdf = canvas.Canvas(str(OUTPUT), pagesize=landscape(A4), pageCompression=1)
    pdf.setTitle("Bridge GAD · Repository Sample Output · 11 Sheets")
    pdf.setAuthor("Bridge GAD repository generator")
    for index, (source, dxf_path) in enumerate(generated, start=1):
        doc = ezdxf.readfile(dxf_path)
        entity_count = len(doc.modelspace())
        draw_page(pdf, index, source, dxf_path, entity_count)
    pdf.save()
    print(
        f"Created {OUTPUT} from {len(generated)} repository workbooks ({OUTPUT.stat().st_size} bytes)"
    )
    return len(generated)


if __name__ == "__main__":
    raise SystemExit(0 if build() == 11 else 1)
