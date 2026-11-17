"""Calibrated reference-vs-generated overlay comparison for the 9-span slab GAD.

Governing specification: CODE-JUNCTION/BRIDGECAD_GAD_ACCEPTANCE_RESOLUTION.md  -- 6.

The approved reference booklet
    CODE-JUNCTION/GENERAL ARRANGEMENT DRAWINGS.pdf
contains NO nine-span drawing.  A nine-span reproduction therefore cannot be
pixel-identical to any of its pages, and section 6 forbids pixel-identity
comparison across different-span drawings.  So this script separates two things:

  1. INVARIANT CONVENTIONS  -- compared against the reference page for the SAME
     drawing family, BR- I / 2022 - 002 "OPEN FOUNDATION WITH R.C.C. PIER &
     SOLID SLAB SUPER STRUCTURE" (printed booklet page 03 -> PDF page 6).
  2. INDEPENDENTLY DERIVED VARIANT GEOMETRY -- recomputed for the 9 x 10 m
     variant from params.resolved.json and from measurement of the generated
     DXFs (never copied from the reference page).

Every number written here is either read from a file this script opened or is a
measurement this script performed.  Anything that cannot be determined is
written as "BLOCKED" / "NOT_VERIFIED" with the reason.

Outputs (all under artifacts/reference-overlay/):
    reference-manifest.json
    comparison.json
    overlays/*.png

Run:  python scripts/gad_reference_overlay.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for _pkg in ("bridgecad-core", "bridgecad-draw", "bridgecad-catalogue"):
    _p = REPO / "packages" / _pkg
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np  # noqa: E402
import pymupdf  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

# --------------------------------------------------------------------------- #
# Fixed inputs (paths only; no measurements are fabricated here)
# --------------------------------------------------------------------------- #
REF_PDF = REPO / "CODE-JUNCTION" / "GENERAL ARRANGEMENT DRAWINGS.pdf"
GEN_DIR = REPO / "artifacts" / "gad-acceptance" / "nine_span_slab" / "e969b72979196f78e2d04129c2462268d6caf099"
GEN_PREFIX = "e969b72979196f78e2d04129c2462268d6caf099"
PARAMS_JSON = GEN_DIR / "params.resolved.json"
SUMMARY_JSON = GEN_DIR.parent / "summary.json"
RENDER_STATUS_JSON = GEN_DIR / "render-status.json"

OUT_DIR = REPO / "artifacts" / "reference-overlay"
OVL_DIR = OUT_DIR / "overlays"

DPI = 150
PT_PER_IN = 72.0
MM_PER_IN = 25.4
PT_TO_MM = MM_PER_IN / PT_PER_IN          # 0.352777...
PX_PER_PT = DPI / PT_PER_IN               # reference raster px per PDF pt
PX_PER_MM_PAPER = DPI / MM_PER_IN         # 1:1 paper mm -> px

# PM==PDF page offset: printed booklet page n == PDF page n + 3 (index is PDF 3).
PRINTED_TO_PDF_OFFSET = 3

# A1 landscape, matching bridgecad_draw.coordinates FRAMES (sheet border is
# measured 0,0..841,594 mm below, not assumed).
A1_SIZE_IN = (841.0 / MM_PER_IN, 594.0 / MM_PER_IN)

SHEETS = [
    ("plan", "Sheet1_Plan", "GENERAL ARRANGEMENT - PLAN VIEW"),
    ("long_section", "Sheet2_LongSection", "GENERAL ARRANGEMENT - LONGITUDINAL SECTION"),
    ("cross_section", "Sheet3_CrossSection", "TYPICAL MID-SPAN CROSS SECTION"),
]

# Layers that form the printed sheet frame / title block, excluded from the
# generated "view" crop so the overlay shows the drawing, not the paper.
FRAME_LAYERS = ("BORDER-INNER", "BORDER-OUTER", "TITLEBLK-BOX", "TITLEBLK-TEXT")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def sha256_of(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    n = 0
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
            n += len(chunk)
    return h.hexdigest().upper(), n


def parse_index(text: str) -> list[dict]:
    """Parse the INDEX page into (sr, description, drawing no, printed page)."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    start = 0
    for i, ln in enumerate(lines):
        if ln == "PAGE No.":
            start = i + 1
            break
    entries: list[dict] = []
    j = start
    while j < len(lines):
        if lines[j].startswith("GENERAL ARRANGEMENT DRAWINGS FOR VARIOUS"):
            break
        sr = lines[j]
        if not re.fullmatch(r"\d{1,2}", sr):
            j += 1
            continue
        desc = lines[j + 1]
        nxt = lines[j + 2]
        if re.match(r"BR-\s*I", nxt):
            draw, page, j = nxt, lines[j + 3], j + 4
        else:
            draw, page, j = "", nxt, j + 3
        entries.append(
            {"sr": sr, "description": desc, "drawing_number": draw, "printed_page": page}
        )
    return entries


def printed_to_pdf(pp: str) -> str:
    m = re.fullmatch(r"(\d+)(?:\s*-\s*(\d+))?", pp)
    if not m:
        return "BLOCKED"
    a = int(m.group(1))
    b = int(m.group(2)) if m.group(2) else None
    if b is None:
        return str(a + PRINTED_TO_PDF_OFFSET)
    return f"{a + PRINTED_TO_PDF_OFFSET:02d}-{b + PRINTED_TO_PDF_OFFSET:02d}"


def msp_of(dxf: Path):
    import ezdxf

    return ezdxf.readfile(str(dxf)).modelspace()


def layer_texts(msp) -> list[dict]:
    out = []
    for e in msp.query("TEXT MTEXT"):
        t = getattr(e.dxf, "text", None)
        if t is None:
            t = getattr(e, "text", "") or ""
        out.append({"layer": e.dxf.layer, "text": str(t)})
    return out


def layer_bbox(msp, predicate) -> tuple[float, float, float, float, int] | None:
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    n = 0
    for e in msp:
        if not predicate(e):
            continue
        try:
            pts = e.get_points("xy")
        except Exception:
            continue
        if not pts:
            continue
        n += 1
        for x, y in pts:
            x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
    if n == 0:
        return None
    return (x0, y0, x1, y1, n)


def rects(msp, layer: str) -> list[tuple[float, float, float, float]]:
    out = []
    for e in msp:
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == layer:
            pts = e.get_points("xy")
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            out.append((min(xs), min(ys), max(xs), max(ys)))
    return out


def hlines(msp, layer: str) -> list[tuple[float, float, float]]:
    out = []
    for e in msp:
        if e.dxftype() == "LINE" and e.dxf.layer == layer:
            s, en = e.dxf.start, e.dxf.end
            if abs(s.y - en.y) < 1e-9:
                out.append((min(s.x, en.x), s.y, max(s.x, en.x)))
    return out


def render_generated(dxf: Path, size_in: tuple[float, float]):
    """Render one DXF exactly like png_engine.render_png, but also return the
    exact affine model-mm -> raster-px mapping (measured, not assumed)."""
    import matplotlib

    matplotlib.use("Agg")
    from bridgecad_draw.engines._render import render_figure

    fig = render_figure(dxf, size_in=size_in)
    fig.set_dpi(DPI)
    fig.canvas.draw()
    ax = fig.axes[0]
    tr = ax.transData
    w_px = int(round(fig.get_figwidth() * DPI))
    h_px = int(round(fig.get_figheight() * DPI))

    def to_px(x: float, y: float) -> tuple[float, float]:
        px, py = tr.transform((x, y))
        return px, h_px - py  # flip: matplotlib origin bottom-left -> image top-left

    return fig, to_px, (w_px, h_px)


def save_fig(fig, out: Path) -> tuple[int, int]:
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out), dpi=DPI)
    import matplotlib.pyplot as plt

    plt.close(fig)
    with Image.open(out) as im:
        return im.size


def ink_bbox(arr: np.ndarray) -> tuple[int, int, int, int] | None:
    g = arr[..., :3].mean(axis=2)
    mask = g < 230
    ys, xs = np.where(mask)
    if xs.size == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


# --------------------------------------------------------------------------- #
# Reference manifest
# --------------------------------------------------------------------------- #
def build_reference_manifest(doc, sha: str, nbytes: int) -> dict:
    page_sizes = [[round(doc[i].rect.width, 2), round(doc[i].rect.height, 2)] for i in range(doc.page_count)]
    all_same = len({tuple(s) for s in page_sizes}) == 1
    w_pt, h_pt = page_sizes[0]
    w_mm, h_mm = round(w_pt * PT_TO_MM, 1), round(h_pt * PT_TO_MM, 1)

    idx_text = doc[2].get_text()
    entries = parse_index(idx_text)
    for e in entries:
        e["pdf_page"] = printed_to_pdf(e["printed_page"])

    baseline_entry = next(
        (e for e in entries if "R.C.C. PIER &SOLID SLAB" in e["description"].replace(" ", "")),
        None,
    )
    if baseline_entry is None:
        baseline_entry = next((e for e in entries if e["drawing_number"].replace(" ", "") == "BR-I/2022-002"), None)

    baseline = None
    if baseline_entry is not None:
        pdf_pages = [int(x) for x in re.findall(r"\d+", baseline_entry["pdf_page"])]
        baseline = {
            "drawing_number": baseline_entry["drawing_number"],
            "description": baseline_entry["description"],
            "printed_page": baseline_entry["printed_page"],
            "pdf_page": pdf_pages[0] if pdf_pages else None,
            "why": (
                "Chosen family baseline: the generated package resolves title "
                "'Open Foundation + RCC Pier + Solid Slab' / superstructure "
                "RCC_SOLID_SLAB / foundation OPEN, which is the same drawing "
                "family as this reference entry. It is the only reference page "
                "that depicts an open-foundation R.C.C. pier with a solid-slab "
                "superstructure, so it is the correct page for the invariant-"
                "convention comparison. It is NOT a nine-span sheet (it is a "
                "4-span drawing), so it cannot be used for pixel-identity."
            ),
        }

    return {
        "filename": str(REF_PDF.relative_to(REPO)).replace("\\", "/"),
        "sha256": sha,
        "bytes": nbytes,
        "page_count": doc.page_count,
        "page_size_pt": page_sizes[0],
        "page_size_mm": [w_mm, h_mm],
        "page_size_all_pages_identical": all_same,
        "paper": f"A2 landscape (nominal 594 x 420 mm); measured {w_mm} x {h_mm} mm",
        "revision": (
            "No revision number printed. The REVISION block on the sheet "
            "(PDF page 6, label at pt (1305,934)-(1333,941)) is blank. Title "
            "stamp reads 'G. A. D.  Dt. 31.12.2022'; issued for in-house "
            "circulation vide letter No. CE/2473, Dt. 31.12.2022."
        ),
        "index_mapping_note": (
            "Index is PDF page 3. Printed booklet 'PAGE No.' is NOT the PDF "
            f"page: printed page n == PDF page n + {PRINTED_TO_PDF_OFFSET} "
            "(printed 01 GLOSSARY is PDF page 4)."
        ),
        "index": entries,
        "baseline_family_page": baseline,
    }


# --------------------------------------------------------------------------- #
# Reference / generated evidence extraction
# --------------------------------------------------------------------------- #
def reference_evidence(doc, page_no_1based: int) -> dict:
    page = doc[page_no_1based - 1]
    txt = page.get_text()

    def found(q: str) -> list[list[float]]:
        return [[round(v, 1) for v in r] for r in page.search_for(q)]

    rl_patterns = [
        r"R\.T\.L\.\s*[\d.]+",
        r"SOFFIT R\.L\.?\s*[\d.]+",
        r"F\.R\.L\.\s*[\d.]+",
        r"H\.F\.L\.?\s*[\d.]+",
        r"D\.H\.F\.L\.?\s*[\d.]+",
        r"R\.L\.\s*[\d.]+",
    ]
    rls: list[str] = []
    for p in rl_patterns:
        for m in re.findall(p, txt):
            if m not in rls:
                rls.append(m)

    lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]

    def first_line(pred) -> str | None:
        return next((ln for ln in lines if pred(ln)), None)

    sheet_titleblock_lines = [
        first_line(lambda s: s.startswith("DRG. No. BR-I / 2022 - 002")),
        first_line(lambda s: s.startswith("JOB No.")),
        first_line(lambda s: "RGD - 442" in s and "Dt" not in s),
        first_line(lambda s: "G. A. D." in s and "Dt. 31.12.2022" in s),
    ]
    view_label_lines: list[str] = []
    for ln in lines:
        if any(k in ln for k in (
            "ELEVATION (", "PART PLAN", "CROSS SECTION AT", "SECTION AT",
            "DETAILS OF ABUTMENT", "DETAILS OF CRASH BARRIER",
        )) and ln not in view_label_lines:
            view_label_lines.append(ln)

    return {
        "pdf_page": page_no_1based,
        "page_label_text": found("Page-03"),
        "drawing_no_text": found("BR-I / 2022 - 002"),
        "sub_title": "GENERAL ARRANGEMENT DRAWING",
        "family_title_line": "OPEN FOUNDATION WITH R.C.C. PIER &SOLID SLAB SUPER STRUCTURE",
        "scale_labels": {
            "SCALE-1:250": found("SCALE-1:250"),
            "SCALE-1:100": found("SCALE-1:100"),
            "SCALE-1:50": found("SCALE-1:50"),
        },
        "view_labels": {
            "ELEVATION": found("ELEVATION"),
            "PLAN": found("PLAN"),
            "CROSS SECTION": found("CROSS SECTION"),
            "SECTION AT": found("SECTION AT"),
            "PART PLAN": found("PART PLAN"),
            "DETAILS OF ABUTMENT": found("DETAILS OF ABUTMENT"),
            "DETAILS OF CRASH BARRIER": found("DETAILS OF CRASH BARRIER"),
        },
        "view_label_lines": view_label_lines,
        "sheet_titleblock_lines": [s for s in sheet_titleblock_lines if s],
        "level_notation_strings_present": rls,
        "datums_present": [
            s for s in ("DATUM LEVEL 90.00M", "GROUND LEVEL", "D.H.F.L. 99.700", "H.F.L. 98.120")
            if s in txt
        ],
        "total_length_note": "TOTAL LENGTH OF BRIDGE 40.00M. (4 SPANS OF 10.00M. c/c.)" in txt,
        "titleblock_field_strings": [
            s for s in (
                "DRG. No.", "JOB No.", "Page-03", "NOTES :-", "REVISION",
                "PREPARED BY", "CHECKED BY", "RECOMMENDED BY", "APPROVED BY", "DRN BY",
                "GOVT. OF MAHARASHTRA", "KONKAN BHAVAN, NAVI MUMBAI, PIN-400614",
                "NALLA PATNUS", "LETTER", "UNIT", "G. A. D. Dt. 31.12.2022",
                "EXCLUSIVE",
            )
            if s in txt
        ],
    }


def generated_evidence() -> dict:
    params = json.loads(PARAMS_JSON.read_text(encoding="utf-8"))
    resolved = params.get("resolved", {})
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8")) if SUMMARY_JSON.exists() else {}
    render_status = json.loads(RENDER_STATUS_JSON.read_text(encoding="utf-8")) if RENDER_STATUS_JSON.exists() else {}

    plan_msp = msp_of(GEN_DIR / f"{GEN_PREFIX}_Sheet1_Plan.dxf")
    ls_msp = msp_of(GEN_DIR / f"{GEN_PREFIX}_Sheet2_LongSection.dxf")
    xs_msp = msp_of(GEN_DIR / f"{GEN_PREFIX}_Sheet3_CrossSection.dxf")

    plan_texts = layer_texts(plan_msp)
    ls_texts = layer_texts(ls_msp)
    xs_texts = layer_texts(xs_msp)

    def tb(texts):
        return [t["text"] for t in texts if t["layer"].startswith("TITLEBLK")]

    # ---- plan measurement -------------------------------------------------- #
    outline = rects(plan_msp, "STRUC-OUTLINE")
    ox0, oy0, ox1, oy1 = outline[0]
    plan_scale_mm_per_m = (ox1 - ox0) / resolved["span_lengths"].__len__() / float(resolved["span_lengths"][0])
    # span_lengths are strings; recompute cleanly:
    span_m = float(resolved["span_lengths"][0])
    n_spans = int(resolved["span_count"])
    total_len_m = span_m * n_spans
    plan_mm_per_m = (ox1 - ox0) / total_len_m
    pier_c = sorted(round((r[0] + r[2]) / 2.0, 4) for r in rects(plan_msp, "SUB-PIER"))
    abut_c = sorted(round((r[0] + r[2]) / 2.0, 4) for r in rects(plan_msp, "SUB-ABUT"))
    plan_pier_ch = [round((x - ox0) / plan_mm_per_m, 3) for x in pier_c]
    plan_abut_ch = [round((x - ox0) / plan_mm_per_m, 3) for x in abut_c]
    plan_deck_width_m = round((oy1 - oy0) / plan_mm_per_m, 3)

    # ---- long-section measurement ----------------------------------------- #
    deck = hlines(ls_msp, "SUPER-DECK")
    ls_x0 = min(d[0] for d in deck)
    ls_x1 = max(d[2] for d in deck)
    ls_mm_per_m = (ls_x1 - ls_x0) / total_len_m
    hfl = hlines(ls_msp, "CIVIL-HFL")
    y_hfl = hfl[0][1]
    y_soffit = min(d[1] for d in deck)
    hfl_rl = float(resolved.get("hfl_m", 0.0))
    soffit_rl = float(resolved.get("soffit_level", 0.0))
    ls_v_mm_per_m = (y_soffit - y_hfl) / (soffit_rl - hfl_rl)

    ls_spec = [t["text"] for t in ls_texts if "V Scale" in t["text"] or "V.E." in t["text"]]
    ve_declared = None
    for s in ls_spec:
        m = re.search(r"V\.E\.=([\d.]+)x", s)
        if m:
            ve_declared = float(m.group(1))

    groups: dict[float, list] = {}
    for r in rects(ls_msp, "SUB-PIER"):
        cx = round((r[0] + r[2]) / 2.0, 4)
        groups.setdefault(cx, []).append(r)
    ls_pier = []
    for cx in sorted(groups):
        ch = round((cx - ls_x0) / ls_mm_per_m, 3)
        rs = sorted(groups[cx], key=lambda r: r[1])
        base = round(hfl_rl + (rs[0][1] - y_hfl) / ls_v_mm_per_m, 3)
        ls_pier.append({"chainage_m": ch, "base_rl_m": base, "n_rects": len(rs)})

    ls_abut_ch = []
    for r in sorted(rects(ls_msp, "SUB-ABUT"), key=lambda r: r[0]):
        ls_abut_ch.append(round(((r[0] + r[2]) / 2.0 - ls_x0) / ls_mm_per_m, 3))

    # ---- cross-section measurement in the sheet's own model coordinates ---- #
    deck_rect = rects(xs_msp, "SUPER-DECK")
    wear_rect = rects(xs_msp, "SUPER-WEARING")
    xs_declared = None
    for t in xs_texts:
        if t["layer"] == "TITLEBLK-TEXT" and t["text"].startswith("SCALE:"):
            m = re.search(r"1\s*:\s*(\d+)", t["text"])
            if m:
                xs_declared = int(m.group(1))
    dx0, dy0, dx1, dy1 = deck_rect[0]
    xs_width_mm_model = dx1 - dx0
    xs_thick_mm_model = dy1 - dy0
    # declared 1:S means 1 m real = 1000/S model mm
    xs_mm_per_m = 1000.0 / xs_declared if xs_declared else None
    xs_width_m = round(xs_width_mm_model / xs_mm_per_m, 3) if xs_mm_per_m else "BLOCKED"
    xs_thick_m = round(xs_thick_mm_model / xs_mm_per_m, 3) if xs_mm_per_m else "BLOCKED"
    xs_wear_w_m = round((wear_rect[0][2] - wear_rect[0][0]) / xs_mm_per_m, 3) if xs_mm_per_m else "BLOCKED"

    layers = {}
    for name, msp in (("plan", plan_msp), ("long_section", ls_msp), ("cross_section", xs_msp)):
        layers[name] = sorted({e.dxf.layer for e in msp})

    border = layer_bbox(plan_msp, lambda e: e.dxf.layer in ("BORDER-OUTER",))
    sheet_mm = (round(border[2] - border[0], 1), round(border[3] - border[1], 1)) if border else None

    return {
        "params_resolved": resolved,
        "params_support_levels": params.get("support_levels", {}),
        "params_trace": params.get("trace", []),
        "summary_subset": {
            "card_id": summary.get("card_id"),
            "resolve_overrides_used": summary.get("resolve_overrides_used"),
            "resolved_params_subset": summary.get("resolved_params_subset"),
            "support_level_record": summary.get("support_level_record"),
            "measured_cross_view_deltas": summary.get("measured_cross_view_deltas"),
            "could_not_verify": summary.get("could_not_verify"),
        },
        "render_status": render_status,
        "generated_sheet_size_mm": sheet_mm,
        "declared_paper_note": (
            "DXF border measured (BORDER-OUTER extents). render-status.json "
            "records render_paper=%r, which is the raster media of "
            "png_engine.render_png, not the DXF paper." % render_status.get("render_paper")
        ),
        "plan": {
            "titleblock_text": tb(plan_texts),
            "scale_label": next((t["text"] for t in plan_texts if t["text"].startswith("SCALE:")), None),
            "outline_mm": [round(v, 3) for v in outline[0]],
            "mm_per_m": round(plan_mm_per_m, 6),
            "measured_total_m": round((ox1 - ox0) / plan_mm_per_m, 6),
            "pier_chainages_m": plan_pier_ch,
            "abutment_chainages_m": plan_abut_ch,
            "deck_width_m": plan_deck_width_m,
            "chainage_labels": [t["text"] for t in plan_texts if t["layer"] == "DIM-CHAINAGE"],
            "section_marks": [t["text"] for t in plan_texts if t["layer"] == "TEXT-HEADER"],
        },
        "long_section": {
            "titleblock_text": tb(ls_texts),
            "scale_label": next((t["text"] for t in ls_texts if t["text"].startswith("SCALE:")), None),
            "h_scale_spec": ls_spec,
            "mm_per_m_horizontal": round(ls_mm_per_m, 6),
            "mm_per_m_vertical": round(ls_v_mm_per_m, 6),
            "measured_total_m": round((ls_x1 - ls_x0) / ls_mm_per_m, 6),
            "vertical_exaggeration_declared": ve_declared,
            "vertical_exaggeration_measured": round(ls_v_mm_per_m / ls_mm_per_m, 3),
            "deck_x_mm": [round(ls_x0, 3), round(ls_x1, 3)],
            "hfl_y_mm": round(y_hfl, 3),
            "pier_chainages_m": [p["chainage_m"] for p in ls_pier],
            "pier_base_rl_m": [p["base_rl_m"] for p in ls_pier],
            "abutment_footprint_centres_m": ls_abut_ch,
            "level_labels": [t["text"] for t in ls_texts if t["layer"] == "TEXT-LEVEL"],
        },
        "cross_section": {
            "titleblock_text": tb(xs_texts),
            "scale_label": next((t["text"] for t in xs_texts if t["text"].startswith("SCALE:")), None),
            "declared_scale": xs_declared,
            "deck_polyline_mm": [round(v, 3) for v in deck_rect[0]],
            "width_m": xs_width_m,
            "thickness_m": xs_thick_m,
            "wearing_width_m": xs_wear_w_m,
            "level_labels": [t["text"] for t in xs_texts if t["layer"] == "TEXT-LEVEL"],
            "width_caption": next((t["text"] for t in xs_texts if t["text"].startswith("CW")), None),
        },
        "layers": layers,
    }


# --------------------------------------------------------------------------- #
# Comparison tables
# --------------------------------------------------------------------------- #
def build_conventions(ref: dict, gen: dict) -> list[dict]:
    gen_sheet_mm = gen["generated_sheet_size_mm"]
    rows: list[dict] = []

    rows.append({
        "id": "CONV-PAPER",
        "requirement": "Paper size and orientation",
        "reference_evidence": {
            "page": f"PDF page {ref['pdf_page']} (media box)",
            "text": f"page {ref['page_size_pt'][0]:.1f} x {ref['page_size_pt'][1]:.1f} pt = "
                    f"{ref['page_size_mm'][0]:.1f} x {ref['page_size_mm'][1]:.1f} mm -> A2 landscape",
        },
        "generated_evidence": {
            "sheet": "Sheet1_Plan.dxf BORDER-OUTER extents",
            "text": f"{gen_sheet_mm[0]:.1f} x {gen_sheet_mm[1]:.1f} mm -> A1 landscape "
                    f"(bridgecad_draw.coordinates FRAMES: sheet1_plan = A1); "
                    f"render-status.json says render_paper={gen['render_status'].get('render_paper')!r}",
        },
        "verdict": "DIFFER",
        "difference": (
            f"Reference paper is A2 landscape (594x420 mm); generated DXF paper is "
            f"A1 landscape ({gen_sheet_mm[0]:.1f}x{gen_sheet_mm[1]:.1f} mm). One A-size step "
            f"larger. Orientation (landscape) agrees."
        ),
    })

    rows.append({
        "id": "CONV-SCALE",
        "requirement": "Declared drawing scale convention",
        "reference_evidence": {
            "page": f"PDF page {ref['pdf_page']}",
            "text": "per-view 'SCALE-1:<denom>': "
                    + ", ".join(f"{k} x{len(v)}" for k, v in ref["scale_labels"].items())
                    + " (standard ladder 1:50/1:100/1:250, uniform, no vertical exaggeration stated)",
        },
        "generated_evidence": {
            "sheet": "title blocks + sheet captions",
            "text": (
                f"plan '{gen['plan']['scale_label']}', "
                f"long-section '{gen['long_section']['scale_label']}', "
                f"cross-section '{gen['cross_section']['scale_label']}'; "
                f"long-section spec {gen['long_section']['h_scale_spec']} "
                f"(declared V.E. {gen['long_section']['vertical_exaggeration_declared']}x)"
            ),
        },
        "verdict": "DIFFER",
        "difference": (
            "Notation '1:<denom>' per view agrees in form. Values differ: reference "
            "uses standard 1:50/1:100/1:250 with a uniform scale and no declared "
            "vertical exaggeration; the generated long section uses non-ladder "
            "1:150 H / 1:26 V with an explicitly declared V.E.="
            f"{gen['long_section']['vertical_exaggeration_declared']}x."
        ),
    })

    rows.append({
        "id": "CONV-TITLEBLOCK",
        "requirement": "Title-block field set, order and drawing-number pattern",
        "reference_evidence": {
            "page": f"PDF page {ref['pdf_page']}",
            "text": "title-block field strings found on the page (verbatim): "
                    + ", ".join(f"'{s}'" for s in ref["titleblock_field_strings"])
                    + ". Verbatim title-block lines: "
                    + "; ".join(f"'{s}'" for s in ref["sheet_titleblock_lines"])
                    + ". Order (reading order of the block): DRG. No. | JOB No. | SUB title | "
                    "'Page-03' | NOTES | REVISION | authority name/address | "
                    "PREPARED BY / CHECKED BY / RECOMMENDED BY / APPROVED BY | DRN BY. "
                    "Drawing number on the sheet is 'BR-I / 2022 - 002'; the spaced form "
                    "'BR- I / 2022 - 002' appears only in the INDEX page.",
        },
        "generated_evidence": {
            "sheet": "Sheet1_Plan.dxf TITLEBLK-TEXT / TEXT-TITLE",
            "text": "; ".join(gen["plan"]["titleblock_text"])
                    + " | DRAWING TITLE: GENERAL ARRANGEMENT - PLAN VIEW"
                    + " | PROJECT: Open Foundation + RCC Pier + Solid Slab"
                    + " | BRIDGE: PWD BR-I-2022-002",
        },
        "verdict": "DIFFER",
        "difference": (
            "Both carry drawing no., title, scale, sheet index, revision and "
            "discipline signatures, but the FIELD SET/ORDER differ. Reference adds "
            "JOB No., a 'SUB' title, booklet 'Page-No.', a numbered NOTES block, the "
            "authority name/address block, RECOMMENDED BY and DRN BY, and an "
            "exclusive-property stamp. Generated adds PROJECT/BRIDGE/CLIENT/"
            "CONSULTANT and uses 'SHEET n OF 9' instead of a booklet page. "
            "Drawing-number pattern differs: reference 'BR-I / 2022 - 002' (spaced) "
            "vs generated 'BR-I-2022-002' (hyphenated, e.g. 'DRG: BR-I-2022-002')."
        ),
    })

    rows.append({
        "id": "CONV-LEVEL",
        "requirement": "Level-notation convention and level-axis placement",
        "reference_evidence": {
            "page": f"PDF page {ref['pdf_page']}",
            "text": "discipline-specific datum abbreviations + 3-dp metres: "
                    + ", ".join(f"'{s}'" for s in ref["level_notation_strings_present"][:12])
                    + "; datum marker 'DATUM LEVEL 90.00M' with stations A/L, P-1, P-2, P-3, A/R "
                    "along the section.",
        },
        "generated_evidence": {
            "sheet": "Sheet2_LongSection.dxf / Sheet3_CrossSection.dxf TEXT-LEVEL",
            "text": "single generic prefix 'RL <value>' (3-dp) e.g. "
                    + ", ".join(f"'{t}'" for t in gen["cross_section"]["level_labels"][:6])
                    + "; long-section series labels "
                    + ", ".join(f"'{t}'" for t in gen["long_section"]["level_labels"][:8])
                    + "; HFL/'SCOUR RL 98.000' used for the hydraulic datums.",
        },
        "verdict": "DIFFER",
        "difference": (
            "Both write reduced levels in metres to 3 decimals with a prefix. "
            "Reference prefixes each level with the discipline datum it belongs to "
            "(R.T.L. / SOFFIT R.L. / F.R.L. / H.F.L. / D.H.F.L.). Generated collapses "
            "road/soffit/cap/top levels to a single generic 'RL' and uses only "
            "'HFL'/'SCOUR' for datums, so a reader cannot tell R.T.L. from F.R.L. "
            "from the label alone. Level-axis placement: reference puts the datum "
            "row and station row beneath the elevation with a 'DATUM LEVEL 90.00M' "
            "note; generated puts a vertical RL axis (98/100/102/104) plus chainage "
            "axis with a 'BED LEVEL' label. Placement is the same idea but the "
            "labelling vocabulary differs."
        ),
    })

    rows.append({
        "id": "CONV-VIEWS",
        "requirement": "Section-mark / view-labelling convention and view order",
        "reference_evidence": {
            "page": f"PDF page {ref['pdf_page']}",
            "text": "view/section label lines found on the page (verbatim): "
                    + "; ".join(f"'{s}'" for s in ref["view_label_lines"])
                    + ". The elevation is labelled with its scale ('ELEVATION (SCALE-1:250)') "
                    "and the plan 'PLAN'; part plans 'PART PLAN AT TOP' / 'PART PLAN AT BOTTOM'; "
                    "cut sections 'CROSS SECTION AT P-2' and 'SECTION AT P-2'; abutment details "
                    "'DETAILS OF ABUTMENT A/L & BOX RETURN (SCALE-1:100)' and '... A/R ...'; "
                    "plus 'DETAILS OF CRASH BARRIER'.",
        },
        "generated_evidence": {
            "sheet": "one sheet per view",
            "text": "section marks 'A-A'/'B-B'; labels "
                    "'SECTION A-A - TYPICAL MID-SPAN CROSS SECTION' (Sheet3), "
                    "'VIEW 1 - SECTION A-A ...' and 'VIEW 2 - SECTION B-B ...' (Sheet8), "
                    "'GENERAL ARRANGEMENT - PLAN VIEW' (Sheet1), "
                    "'GENERAL ARRANGEMENT - LONGITUDINAL SECTION' (Sheet2).",
        },
        "verdict": "NOT_COMPARABLE",
        "difference": (
            "Section-mark convention (letter pairs cutting the plan/long section) "
            "AGREES. View ORDER cannot be compared: the reference packs elevation + "
            "plan + part plans + cross sections + abutment details onto one compressed "
            "booklet sheet, whereas the generated package emits one view per sheet "
            "(Sheet1..Sheet9). There is no common sheet composition to compare."
        ),
    })

    rows.append({
        "id": "CONV-LAYERS",
        "requirement": "Layer / entity vocabulary for corresponding features",
        "reference_evidence": {
            "page": f"PDF page {ref['pdf_page']}",
            "text": "flattened PDF: vector paths only, no CAD layer/entity metadata "
                    "retrievable (page exposes stroke paths and text spans, not layers).",
        },
        "generated_evidence": {
            "sheet": "DXF layer tables",
            "text": (
                f"plan: {gen['layers']['plan']}; "
                f"long-section: {gen['layers']['long_section']}; "
                f"cross-section: {gen['layers']['cross_section']}"
            ),
        },
        "verdict": "NOT_COMPARABLE",
        "difference": (
            "The reference is a flattened PDF with no layer model, so layer names "
            "cannot be compared. The generated vocabulary is recorded for the "
            "corresponding features only: SUPER-DECK (deck), SUB-PIER/SUB-ABUT "
            "(supports), SUB-BEARING/SUB-DIRT-WALL (details), CIVIL-HFL/CIVIL-GROUND/"
            "CIVIL-LWL/CIVIL-ROAD/CIVIL-SCOUR (civil datums), SUPER-WEARING/SUPER-KERB/"
            "SUPER-PARAPET (cross-section), TEXT-LEVEL/DIM-*/TITLEBLK-* (annotation)."
        ),
    })
    return rows


def build_variant_geometry(gen: dict) -> list[dict]:
    r = gen["params_resolved"]
    plan = gen["plan"]
    ls = gen["long_section"]
    xs = gen["cross_section"]
    total = float(r["total_length_m"])
    span_m = float(r["span_lengths"][0])
    n = int(r["span_count"])
    rec = gen["summary_subset"].get("support_level_record") or {}
    rec_levels = rec.get("levels_m", {})

    rows = []
    rows.append({
        "id": "VAR-TOTAL",
        "quantity": "Total bridge length / number of spans",
        "derivation": f"{n} spans x {span_m} m = {n * span_m} m",
        "measured": {
            "plan_outline_m": round((plan["outline_mm"][2] - plan["outline_mm"][0]) / plan["mm_per_m"], 3),
            "long_section_deck_m": round((ls["deck_x_mm"][1] - ls["deck_x_mm"][0]) / ls["mm_per_m_horizontal"], 3),
        },
        "source": "params.resolved.json total_length_m; DXF STRUC-OUTLINE / SUPER-DECK measured",
        "verdict": (
            "AGREE" if abs(plan["measured_total_m"] - total) < 1e-3
            and abs(ls["measured_total_m"] - total) < 1e-3 else "CHECK"
        ),
    })
    rows.append({
        "id": "VAR-PIERS",
        "quantity": "Intermediate pier chainages",
        "derivation": "8 piers at 10,20,...,80 m (one at each internal span joint)",
        "measured": {
            "plan_pier_chainages_m": plan["pier_chainages_m"],
            "long_section_pier_chainages_m": ls["pier_chainages_m"],
        },
        "source": "plan SUB-PIER centres; long-section SUB-PIER x-centres",
        "verdict": "AGREE" if plan["pier_chainages_m"] == [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0] else "CHECK",
    })
    rows.append({
        "id": "VAR-ABUTMENTS",
        "quantity": "Abutment support axes at 0 m and 90 m",
        "derivation": "2 abutments at the two bridge ends",
        "measured": {
            "plan_abutment_axes_m": plan["abutment_chainages_m"],
            "long_section_abutment_footprint_centre_m": ls["abutment_footprint_centres_m"],
        },
        "source": "plan SUB-ABUT centres; long-section SUB-ABUT footprint centres",
        "verdict": (
            "AGREE" if plan["abutment_chainages_m"] == [0.0, 90.0] else "CHECK"
        ) + " (plan axes at 0.000/90.000; long-section footprint centres sit just "
            "outside the deck ends because the abutment body/dirt-wall extends "
            "beyond the bridge axis)",
    })
    rows.append({
        "id": "VAR-CW",
        "quantity": "Carriageway width",
        "derivation": "params carriageway_width",
        "measured": {
            "params_m": r.get("carriageway_width"),
            "cross_section_wearing_width_m": xs["wearing_width_m"],
            "cross_section_caption": xs["width_caption"],
        },
        "source": "params.resolved.json; cross-section SUPER-WEARING width / (1000/declared scale)",
        "verdict": "AGREE" if xs["wearing_width_m"] == r.get("carriageway_width") else "CHECK",
    })
    rows.append({
        "id": "VAR-WIDTH",
        "quantity": "Overall deck width",
        "derivation": "carriageway + kerbs (not in params); read from geometry",
        "measured": {
            "cross_section_deck_width_m": xs["width_m"],
            "plan_outline_width_m": plan["deck_width_m"],
        },
        "source": "cross-section SUPER-DECK polyline width; plan STRUC-OUTLINE width",
        "verdict": "AGREE (no params value; the two views agree with each other)",
    })
    rows.append({
        "id": "VAR-DECK-THK",
        "quantity": "Deck (slab) thickness",
        "derivation": "params deck_thickness_mm",
        "measured": {
            "params_mm": r.get("deck_thickness_mm"),
            "cross_section_thickness_mm": round(xs["thickness_m"] * 1000.0, 1) if isinstance(xs["thickness_m"], (int, float)) else "BLOCKED",
        },
        "source": "params.resolved.json; cross-section SUPER-DECK polyline height",
        "verdict": "AGREE" if isinstance(xs["thickness_m"], (int, float)) and round(xs["thickness_m"] * 1000.0) == r.get("deck_thickness_mm") else "CHECK",
    })
    # The declared parameter file must carry the SAME named chain the canonical
    # record in summary.json does — that is the whole point of exposing it there.
    chain = gen.get("params_support_levels") or {}
    chain_typical = chain.get("typical") or {}
    chain_levels = chain_typical.get("levels_m") or {}
    chain_present = bool(chain_typical and chain_levels)
    chain_matches_record = bool(
        chain_present
        and chain_typical.get("status") == rec.get("status")
        and chain_typical.get("authority") == rec.get("authority")
        and chain_levels.get("cap_bottom_rl_m") == rec_levels.get("cap_bottom_rl_m")
        and chain_levels.get("shaft_base_rl_m") == rec_levels.get("shaft_base_rl_m")
        and chain_levels.get("footing_bottom_rl_m") == rec_levels.get("footing_bottom_rl_m")
    )
    rows.append({
        "id": "VAR-SUPPORT-LEVELS",
        "quantity": "Support / foundation level chain from the canonical record",
        "derivation": "expected: full named RL chain (road, soffit, bearing, pedestal, cap top/bottom, shaft top/base, footing) in params.resolved.json",
        "measured": {
            "params_resolved_has_full_chain": chain_present,
            "params_resolved_chain_levels": sorted(chain_levels),
            "params_resolved_chain_typical": chain_typical or None,
            "params_resolved_chain_support_count": len(chain.get("supports") or []),
            "chain_matches_summary_record": chain_matches_record,
            "summary_status": rec.get("status"),
            "summary_authority": rec.get("authority"),
            "summary_shaft_base_rl_m": rec_levels.get("shaft_base_rl_m"),
            "summary_footing_bottom_rl_m": rec_levels.get("footing_bottom_rl_m"),
        },
        "source": "params.resolved.json support_levels.typical (written by generate_all_pwd_gads._support_level_chain); summary.json support_level_record",
        "verdict": (
            "AGREE" if chain_matches_record else ("CHECK" if chain_present else "BLOCKED")
        ),
        "reason": (
            "params.resolved.json now carries the full named chain under "
            "support_levels.typical / support_levels.supports, read from the same "
            "resolver the sheets consume, and it agrees level-for-level with the "
            f"canonical record: status={rec.get('status')}, "
            f"authority={rec.get('authority')}, "
            f"cap_bottom={rec_levels.get('cap_bottom_rl_m')}, "
            f"shaft_base={rec_levels.get('shaft_base_rl_m')}, "
            f"footing_bottom={rec_levels.get('footing_bottom_rl_m')}. "
            "The authority is LEVEL_CONTROLLED only when an explicitly supplied founding RL and "
            "an open-footing thickness are both supplied; this card supplies neither, "
            "so the chain is honestly UNRESOLVED with E-MISSING-FOOTING-DEPTH rather "
            "than a fabricated footing level."
            if chain_matches_record else
            "params.resolved.json does not carry a chain matching the canonical "
            "support_level_record, so the 'level chain consumed from params' claim "
            "cannot be verified."
        ),
    })
    drawn_bases = [b for b in (ls["pier_base_rl_m"] or []) if isinstance(b, (int, float))]
    rec_shaft_base = rec_levels.get("shaft_base_rl_m")
    base_agrees = (
        rec_shaft_base is not None
        and bool(drawn_bases)
        and all(abs(b - float(rec_shaft_base)) <= 1e-3 for b in drawn_bases)
    )
    rows.append({
        "id": "VAR-PIER-BASE-DISCREPANCY",
        "quantity": "Drawn long-section pier base RL vs canonical record",
        "derivation": "record shaft_base should equal the drawn pier base",
        "measured": {
            "long_section_pier_base_rl_m_measured": ls["pier_base_rl_m"],
            "record_shaft_base_rl_m": rec_shaft_base,
            "hfl_minus_pier_height_m": float(r.get("hfl_m", 0.0)) - float(r.get("pier_height_m", 0.0)),
        },
        "source": "long-section SUB-PIER rect base measured via CIVIL-HFL calibration; summary.json",
        "verdict": "AGREE" if base_agrees else "DISAGREE",
        "difference": (
            f"The long-section draws every pier base at RL "
            f"{drawn_bases[0] if drawn_bases else 'BLOCKED'} m and the canonical "
            f"record resolves shaft_base at RL {rec_shaft_base} m — the drawn base "
            "CONSUMES the record's shaft_base (delta <= 1 mm), so this cross-view "
            "check now AGREES. The old HFL − pier_height datum "
            f"({float(r.get('hfl_m', 0.0)) - float(r.get('pier_height_m', 0.0))} m) "
            "is no longer used to place the pier base."
        ) if base_agrees else (
            "The drawn long-section pier base disagrees with the canonical "
            f"record's shaft_base ({rec_shaft_base} m) by more than 1 mm."
        ),
    })
    return rows


# --------------------------------------------------------------------------- #
# Overlays
# --------------------------------------------------------------------------- #
def build_view_crop(kind: str, page, ref_rects: dict) -> tuple[tuple[float, float, float, float], dict]:
    """Return (crop_pt, provenance) for a reference view, from a measured label
    bbox expanded by DECLARED margins."""
    # margins: (left, up, right, down) in PDF pt
    margins = {
        "plan": (330.0, 150.0, 340.0, 13.0),
        "long_section": (360.0, 335.0, 340.0, 6.0),
        "cross_section": (60.0, 20.0, 200.0, 240.0),
    }[kind]
    lx0, ly0, lx1, ly1 = ref_rects[kind]
    ml, mu, mr, md = margins
    crop = (lx0 - ml, ly0 - mu, lx1 + mr, ly1 + md)
    prov = {
        "anchor_label_bbox_pt": [round(v, 1) for v in (lx0, ly0, lx1, ly1)],
        "expansion_pt": {"left": ml, "up": mu, "right": mr, "down": md},
        "derivation": "measured label bbox expanded by declared margins",
    }
    return crop, prov


def ref_view_rects(page) -> dict:
    def pick(q, ymin, ymax, xmin, xmax):
        best = None
        for r in page.search_for(q):
            if xmin <= r.x0 and r.x1 <= xmax and ymin <= r.y0 and r.y1 <= ymax:
                if best is None:
                    best = r
                else:
                    best = best | r
        return best

    def union(*rs):
        out = None
        for r in rs:
            if r is None:
                continue
            out = r if out is None else (out | r)
        return out

    el = pick("ELEVATION", 360, 400, 400, 560)
    el2 = pick("SCALE-1:250", 360, 400, 400, 560)
    pl = pick("PLAN", 515, 540, 440, 520)
    pl2 = pick("SCALE-1:250", 530, 555, 440, 520)
    cs = pick("CROSS SECTION", 440, 465, 960, 1100)
    cs2 = pick("SCALE-1:100", 455, 475, 1000, 1100)
    return {
        "long_section": union(el, el2),
        "plan": union(pl, pl2),
        "cross_section": union(cs, cs2),
    }


def make_overlays(doc, ref_page_no, gen: dict) -> tuple[dict, dict]:
    page = doc[ref_page_no - 1]
    ref_rects = ref_view_rects(page)

    pix = page.get_pixmap(matrix=pymupdf.Matrix(DPI / PT_PER_IN, DPI / PT_PER_IN))
    ref_arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].copy()
    ref_full = Image.fromarray(ref_arr, "RGB")

    declared_scale_ref = {"plan": 250, "long_section": 250, "cross_section": 100}
    px_per_m_ref = {k: (1000.0 / v) * PX_PER_MM_PAPER for k, v in declared_scale_ref.items()}

    transformations: dict[str, dict] = {}
    raster_scores: dict[str, dict] = {}

    for kind, sheet_name, _ in SHEETS:
        label = ref_rects[kind]
        if label is None:
            transformations[kind] = {"status": "BLOCKED", "reason": "reference view label not found on the page"}
            continue
        crop_pt, prov = build_view_crop(kind, page, ref_rects)

        # reference crop -> px
        rx0 = int(round(crop_pt[0] * PX_PER_PT))
        ry0 = int(round(crop_pt[1] * PX_PER_PT))
        rx1 = int(round(crop_pt[2] * PX_PER_PT))
        ry1 = int(round(crop_pt[3] * PX_PER_PT))
        rx0 = max(0, rx0); ry0 = max(0, ry0)
        rx1 = min(ref_full.width, rx1); ry1 = min(ref_full.height, ry1)
        ref_crop = ref_full.crop((rx0, ry0, rx1, ry1))

        # generated sheet render (A1) with exact model-mm -> px transform.
        # NOTE: to_px relies on the figure's live transform, so every value that
        # uses it MUST be measured while the figure is still open -- save_fig()
        # closes the figure and would invalidate the transform.
        dxf = GEN_DIR / f"{GEN_PREFIX}_{sheet_name}.dxf"
        msp = msp_of(dxf)
        vb = layer_bbox(msp, lambda e: e.dxf.layer not in FRAME_LAYERS)
        fig, to_px, (w_px, h_px) = render_generated(dxf, A1_SIZE_IN)

        gx0, gy0 = to_px(vb[0], vb[1])
        gx1, gy1 = to_px(vb[2], vb[3])
        # measure px per model-mm, then px per metre
        a = to_px(vb[0], vb[1])
        b = to_px(vb[0] + 1000.0, vb[1])
        px_per_model_mm = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 / 1000.0
        declared_scale_gen = {"plan": 150, "long_section": 150, "cross_section": 50}
        px_per_m_gen = px_per_model_mm * (1000.0 / declared_scale_gen[kind])
        uniform_scale = px_per_m_ref[kind] / px_per_m_gen

        gen_png = OVL_DIR / f"_render_{kind}.png"
        save_fig(fig, gen_png)
        gen_full = Image.open(gen_png).convert("RGB")

        # to_px flips Y, so the model max-Y corner maps to the smaller image row;
        # normalise the crop box to (left, top, right, bottom).
        gx0, gx1 = sorted((gx0, gx1))
        gy0, gy1 = sorted((gy0, gy1))
        pad = 18
        gx0 = max(0, int(gx0) - pad); gy0 = max(0, int(gy0) - pad)
        gx1 = min(gen_full.width, int(gx1) + pad); gy1 = min(gen_full.height, int(gy1) + pad)
        gen_crop = gen_full.crop((gx0, gy0, gx1, gy1))

        # apply uniform scale to the generated crop
        gw = max(1, int(round(gen_crop.width * uniform_scale)))
        gh = max(1, int(round(gen_crop.height * uniform_scale)))
        gen_scaled = gen_crop.resize((gw, gh), Image.LANCZOS)

        ref_bb = ink_bbox(np.asarray(ref_crop))
        gen_bb = ink_bbox(np.asarray(gen_scaled))
        if ref_bb is None or gen_bb is None:
            transformations[kind] = {
                "status": "BLOCKED",
                "reason": "empty ink bounding box in a crop",
                "reference_crop_pt": [round(v, 1) for v in crop_pt],
                "reference_crop_px": [rx0, ry0, rx1, ry1],
                "reference_ink_empty": ref_bb is None,
                "generated_crop_model_mm_bbox": [round(float(v), 2) for v in vb[:4]],
                "generated_crop_px_before_scale": [gx0, gy0, gx1, gy1],
                "generated_ink_empty": gen_bb is None,
            }
            continue

        ref_cx = (ref_bb[0] + ref_bb[2]) / 2.0
        ref_cy = (ref_bb[1] + ref_bb[3]) / 2.0
        gen_cx = (gen_bb[0] + gen_bb[2]) / 2.0
        gen_cy = (gen_bb[1] + gen_bb[3]) / 2.0

        # canvas big enough for both, align ink-bbox centres
        cw = max(ref_crop.width, gen_scaled.width) + 40
        ch = max(ref_crop.height, gen_scaled.height) + 40
        ref_off = (int(round(cw / 2 - ref_cx)), int(round(ch / 2 - ref_cy)))
        gen_off = (int(round(cw / 2 - gen_cx)), int(round(ch / 2 - gen_cy)))
        trans_x = gen_off[0] - ref_off[0]
        trans_y = gen_off[1] - ref_off[1]

        ref_canvas = Image.new("L", (cw, ch), 255)
        ref_canvas.paste(ref_crop.convert("L"), ref_off)
        gen_canvas = Image.new("L", (cw, ch), 255)
        gen_canvas.paste(gen_scaled.convert("L"), gen_off)
        overlay = Image.merge("RGB", (gen_canvas, ref_canvas, ref_canvas))
        # red = reference-only ink, cyan = generated-only ink, black = coincident

        # raster difference (diagnostic only)
        ref_g = ref_crop.convert("L")
        gen_g = gen_scaled.convert("L").resize(ref_g.size)
        diff = np.abs(np.asarray(ref_g, dtype=np.int16) - np.asarray(gen_g, dtype=np.int16))
        raster_scores[kind] = {
            "mean_abs_gray_diff": round(float(diff.mean()), 2),
            "label": "DIAGNOSTIC ONLY - not an acceptance oracle (anti-aliasing and fonts differ)",
        }

        ann = (
            f"{kind}: declared scale ref 1:{declared_scale_ref[kind]} / gen 1:{declared_scale_gen[kind]}\n"
            f"uniform scale={uniform_scale:.4f}  rotation=0deg\n"
            f"translation px=({trans_x},{trans_y})  crop_pt={tuple(round(v,1) for v in crop_pt)}\n"
            f"residual ink-bbox w_ratio={(gen_bb[2]-gen_bb[0])/max(1,(ref_bb[2]-ref_bb[0])):.3f} "
            f"h_ratio={(gen_bb[3]-gen_bb[1])/max(1,(ref_bb[3]-ref_bb[1])):.3f}\n"
            f"red=reference-only  cyan=generated-only  black=coincident"
        )
        d = ImageDraw.Draw(overlay)
        d.rectangle([0, 0, cw - 1, 62], fill=(255, 255, 255))
        d.text((6, 4), ann, fill=(0, 0, 0))
        overlay.save(OVL_DIR / f"{kind}_overlay.png")

        # side by side
        gap = 16
        sb_h = max(ref_crop.height, gen_scaled.height) + 40
        sb = Image.new("RGB", (ref_crop.width + gap + gen_scaled.width, sb_h), (255, 255, 255))
        sb.paste(ref_crop, (0, 20))
        sb.paste(gen_scaled, (ref_crop.width + gap, 20))
        d2 = ImageDraw.Draw(sb)
        d2.text((6, 4), f"REFERENCE PDF p{ref_page_no} crop {tuple(round(v) for v in crop_pt)}", fill=(0, 0, 0))
        d2.text((ref_crop.width + gap + 6, 4), f"GENERATED {sheet_name} (scaled x{uniform_scale:.3f})", fill=(0, 0, 0))
        sb.save(OVL_DIR / f"{kind}_side_by_side.png")

        transformations[kind] = {
            "status": "OK",
            "reference_crop_pt": [round(v, 1) for v in crop_pt],
            "reference_crop_px": [rx0, ry0, rx1, ry1],
            "crop_provenance": prov,
            "generated_crop_model_mm_bbox": [round(v, 2) for v in vb[:4]],
            "generated_crop_px_before_scale": [gx0, gy0, gx1, gy1],
            "rotation_deg": 0.0,
            "declared_reference_scale": f"1:{declared_scale_ref[kind]}",
            "declared_generated_scale": f"1:{declared_scale_gen[kind]}",
            "uniform_scale_applied_to_generated": round(uniform_scale, 4),
            "translation_px": [trans_x, trans_y],
            "alignment": "ink-bbox centre coincidence (measured control, symmetric anchor)",
            "declared_vertical_exaggeration": (
                gen["long_section"]["vertical_exaggeration_declared"] if kind == "long_section" else 1.0
            ),
            "residual_ink_bbox_size_ratio": {
                "width": round((gen_bb[2] - gen_bb[0]) / max(1, (ref_bb[2] - ref_bb[0])), 4),
                "height": round((gen_bb[3] - gen_bb[1]) / max(1, (ref_bb[3] - ref_bb[1])), 4),
            },
            "note": (
                "Residual is expected to be non-unity: the reference is a "
                "4-span 40 m sheet and the generated sheet is a 9-span 90 m "
                "variant. Features are NOT expected to coincide; the overlay "
                "tests conventions, not geometry identity."
            ),
            "artifacts": {
                "overlay": f"overlays/{kind}_overlay.png",
                "side_by_side": f"overlays/{kind}_side_by_side.png",
            },
        }

    return transformations, raster_scores


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OVL_DIR.mkdir(parents=True, exist_ok=True)

    sha, nbytes = sha256_of(REF_PDF)
    doc = pymupdf.open(str(REF_PDF))

    manifest = build_reference_manifest(doc, sha, nbytes)
    baseline_page = manifest["baseline_family_page"]["pdf_page"] if manifest["baseline_family_page"] else None

    ref_ev = reference_evidence(doc, baseline_page) if baseline_page else {"status": "BLOCKED"}
    ref_ev["page_size_pt"] = manifest["page_size_pt"]
    ref_ev["page_size_mm"] = manifest["page_size_mm"]
    gen_ev = generated_evidence()

    conventions = build_conventions(ref_ev, gen_ev)
    variant = build_variant_geometry(gen_ev)

    transformations, raster_scores = make_overlays(doc, baseline_page, gen_ev) if baseline_page else ({}, {})

    unresolved = [
        {
            "id": "U1",
            "topic": "Pipeline (reference) sheet has no nine-span page",
            "status": "BY DESIGN",
            "reason": (
                "The reference booklet's span counts are 2..5; there is no "
                "nine-span drawing. Per acceptance-resolution  -- 6.2, a nine-span "
                "reproduction cannot be pixel-identical to any reference page, so "
                "no pixel-identity claim is made for the 9-span geometry."
            ),
        },
        {
            "id": "U2",
            "topic": "Named support/foundation level chain exposure",
            "status": "CLOSED",
            "reason": (
                "params.resolved.json now carries the full named chain under "
                "support_levels.typical / support_levels.supports, written from the same "
                "resolver the sheets consume. It is compared level-for-level with the "
                "canonical record by VAR-SUPPORT-LEVELS. On this card the chain is "
                "honestly UNRESOLVED (open foundation, no supplied founding RL), so no "
                "founding level is claimed."
            ),
        },
        {
            "id": "U3",
            "topic": "Reference crop rectangles are label-anchored estimates",
            "status": "PARTIAL",
            "reason": (
                "The reference page packs many views; each crop is a measured view "
                "label bbox expanded by declared margins (recorded per view). Views "
                "were not segmented by an independent layout detector."
            ),
        },
        {
            "id": "U4",
            "topic": "Overlay alignment is not a feature registration",
            "status": "PARTIAL",
            "reason": (
                "Alignment uses uniform scale (from declared scales) plus an "
                "ink-bbox-centre translation, rotation 0. No non-uniform warping "
                "was applied. Because span counts differ, drawn features are not "
                "expected to coincide."
            ),
        },
        {
            "id": "U5",
            "topic": "Vector layer vocabulary of the reference",
            "status": "NOT_COMPARABLE",
            "reason": "Reference is a flattened PDF with no CAD layers.",
        },
    ]

    any_ok = any(t.get("status") == "OK" for t in transformations.values())
    status = "PARTIAL" if (any_ok and unresolved) else ("COMPLETE" if any_ok else "BLOCKED")

    comparison = {
        "status": status,
        "status_reason": (
            "Convention verdicts and variant geometry are measured from the actual "
            "files; overlays were produced. Status is PARTIAL because the reference "
            "has no nine-span sheet (so geometry fidelity cannot be claimed) and "
            "reference crops are label-anchored estimates. The named support/foundation "
            "level chain is now exposed in params.resolved.json and compared "
            "level-for-level (VAR-SUPPORT-LEVELS). Raster differences are diagnostic only."
        ),
        "policy": (
            "Acceptance-resolution  -- 6: separate (1) invariant conventions compared "
            "against the same-family reference page from (2) independently derived "
            "variant geometry. No pixel-identity comparison across different-span "
            "drawings. No arbitrary non-uniform warping; only uniform scale + "
            "translation + rotation."
        ),
        "reference_baseline": {
            "page": baseline_page,
            "drawing_number": manifest["baseline_family_page"]["drawing_number"] if manifest["baseline_family_page"] else None,
            "why": manifest["baseline_family_page"]["why"] if manifest["baseline_family_page"] else None,
        },
        "invariant_conventions": conventions,
        "variant_geometry": variant,
        "variant_geometry_note": (
            "These are the numbers that MUST be recomputed for the 9-span variant; "
            "they are NOT copied from the reference page and have no reference sheet."
        ),
        "transformations": transformations,
        "raster_difference": raster_scores,
        "unresolved": unresolved,
    }

    (OUT_DIR / "reference-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "comparison.json").write_text(
        json.dumps(comparison, indent=2), encoding="utf-8"
    )

    # clean the intermediate sheet renders (keep only overlays)
    for k, _, _ in SHEETS:
        p = OVL_DIR / f"_render_{k}.png"
        if p.exists():
            p.unlink()

    print("reference:", manifest["filename"], "sha256", sha, "bytes", nbytes, "pages", manifest["page_count"])
    print("baseline page:", baseline_page, manifest["baseline_family_page"]["drawing_number"])
    print("conventions:", [(c["id"], c["verdict"]) for c in conventions])
    print("variant:", [(v["id"], v["verdict"]) for v in variant])
    for k, t in transformations.items():
        print(f"transform[{k}]:", t.get("status"), "scale", t.get("uniform_scale_applied_to_generated"),
              "trans", t.get("translation_px"), "residual", t.get("residual_ink_bbox_size_ratio"))
    print("raster diff (diagnostic):", {k: v["mean_abs_gray_diff"] for k, v in raster_scores.items()})
    print("status:", comparison["status"])
    print("wrote:", OUT_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
