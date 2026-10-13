"""DXF → PDF rendering utilities for the Bridge GAD generator.

Pure-Python rendering using ezdxf's drawing addon with the matplotlib
backend. Produces:

* Single-page PDF per DXF (``convert_dxf_to_pdf``).
* Multi-page booklet PDF combining many DXF files
  (``bundle_drawings_to_pdf`` / ``PdfPages``).

Designed for "1 to infinity in numbers" — the bundle helpers accept any
iterable of DXF paths and page layouts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]


# ---------------------------------------------------------------------------
# Layout presets (landscape A-family sheets)
# ---------------------------------------------------------------------------
# Values in inches for matplotlib figure size.
LAYOUT_PRESETS: Dict[str, Tuple[float, float]] = {
    "A4_landscape": (11.69, 8.27),
    "A4_portrait": (8.27, 11.69),
    "A3_landscape": (16.54, 11.69),
    "A2_landscape": (23.39, 16.54),
    "A1_landscape": (33.11, 23.39),
    "A0_landscape": (46.81, 33.11),
}


@dataclass(frozen=True)
class RenderOptions:
    """Options for rendering one DXF into a single PDF page."""

    layout: str = "A4_landscape"
    dpi: int = 200
    facecolor: str = "white"
    background_color: Optional[str] = None
    lweight_scale: float = 0.7
    title_fontsize: float = 10.0
    show_title: bool = True
    show_page_frame: bool = True
    # Output mode for the matplotlib axes frame.


def _size_for(opts: RenderOptions) -> Tuple[float, float]:
    if opts.layout in LAYOUT_PRESETS:
        return LAYOUT_PRESETS[opts.layout]
    # Fallback: allow explicit "WxH_inches" strings like "16.54x11.69".
    if "x" in opts.layout.lower():
        try:
            w, h = opts.layout.lower().split("x", 1)
            return (float(w), float(h))
        except Exception:
            pass
    return LAYOUT_PRESETS["A4_landscape"]


def _repair_none_insert_text(msp) -> Tuple[int, int]:
    """In-place repair for TEXT / MTEXT / ATTRIB entities whose ``dxf.insert``
    is ``None`` — the exact failure mode hit by
    ``ezdxf.addons.drawing.text._get_wcs_insert`` which raises
    ``TypeError: object of type 'NoneType' has no len()``.

    Strategy: prefer ``align_point`` or a fallback OCS-derived location, else
    drop the entity. Returns the number of repaired / dropped entities as a
    signed tuple delta (repaired, dropped).
    """
    repaired = 0
    dropped = 0
    TEXTY = {"TEXT", "MTEXT", "ATTRIB", "ATTDEF"}
    for entity in list(msp):
        try:
            etype = entity.dxftype()
        except Exception:
            msp.delete_entity(entity)
            dropped += 1
            continue
        if etype not in TEXTY:
            continue
        insert = None
        try:
            insert = entity.dxf.insert
        except Exception:
            insert = None
        if insert is not None:
            continue
        # Try align_point first (many real-world DXF writers populate only
        # this field when alignment != left/baseline).
        alt = None
        try:
            alt = entity.dxf.align_point
        except Exception:
            alt = None
        if alt is None:
            # Try any vertex-like field we can pull.
            for field in ("insert2", "text_align_point", "location",
                          "extrusion", "normal"):
                try:
                    v = getattr(entity.dxf, field, None)
                    if v is not None:
                        alt = v
                        break
                except Exception:
                    pass
        if alt is None:
            # As a last-ditch, if there's any bounding info attached, use
            # its center. Otherwise drop the entity.
            try:
                ext = entity.extents()
                if ext is not None and ext[0] is not None and ext[1] is not None:
                    alt = tuple((a + b) / 2 for a, b in zip(ext[0], ext[1]))
            except Exception:
                alt = None
        if alt is None:
            try:
                msp.delete_entity(entity)
                dropped += 1
            except Exception:
                pass
            continue
        try:
            entity.dxf.insert = alt
            repaired += 1
        except Exception:
            try:
                msp.delete_entity(entity)
                dropped += 1
            except Exception:
                pass
    return repaired, dropped


def _safe_draw_frontend(context, out, cfg, msp) -> Tuple[int, int, List[str]]:
    """Draw modelspace, falling back entity-by-entity so one rogue entity
    cannot blank the whole page. Returns ``(rendered_count, skipped_count,
    skipped_types)``.
    """
    from ezdxf.addons.drawing import Frontend

    rendered = 0
    skipped = 0
    skipped_types: List[str] = []
    entities = list(msp)
    try:
        frontend = Frontend(context, out, config=cfg)
        frontend.draw_layout(msp, finalize=True)
        return len(entities), 0, []
    except Exception:
        pass
    for idx, entity in enumerate(entities):
        etype = "?"
        try:
            etype = entity.dxftype()
        except Exception:
            etype = "<unknown>"
        try:
            frontend = Frontend(context, out, config=cfg)
            if hasattr(frontend, "draw_entities"):
                frontend.draw_entities([entity])
            else:
                frontend.draw_entity(entity)
            rendered += 1
        except Exception:
            skipped += 1
            if len(skipped_types) < 10:
                skipped_types.append(f"{etype}#{idx}")
    return rendered, skipped, skipped_types


# ---------------------------------------------------------------------------
# Single DXF → single PDF
# ---------------------------------------------------------------------------
def convert_dxf_to_pdf(
    dxf_path: PathLike,
    pdf_path: Optional[PathLike] = None,
    opts: Optional[RenderOptions] = None,
    page_title: Optional[str] = None,
) -> Path:
    """Render one DXF file to a single-page PDF.

    Parameters
    ----------
    dxf_path:
        Path to the source DXF.
    pdf_path:
        Destination PDF path. If ``None``, ``<dxf_stem>.pdf`` next to the
        source DXF is used.
    opts:
        Layout / render controls. Defaults are equivalent to
        ``RenderOptions()``.
    page_title:
        Override title shown on the page (filename stem is used when empty).

    Returns
    -------
    Path
        The absolute path of the produced PDF file.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    import ezdxf
    from ezdxf import recover
    from ezdxf.addons.drawing import (
        Frontend,
        RenderContext,
        config,
        matplotlib,
    )

    dxf_path = Path(dxf_path)
    if pdf_path is None:
        pdf_path = dxf_path.with_suffix(".pdf")
    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    opts = opts or RenderOptions()

    try:
        doc = ezdxf.readfile(str(dxf_path))
    except Exception:
        logger.warning("Recovering broken DXF %s", dxf_path.name)
        doc, _audit = recover.readfile(str(dxf_path))

    if not doc.modelspace():
        logger.warning("DXF %s has empty modelspace — rendering empty page.",
                       dxf_path.name)

    msp = doc.modelspace()
    try:
        total_entities = len(list(msp))
    except Exception:
        total_entities = 0

    repaired, dropped = _repair_none_insert_text(msp)
    if repaired or dropped:
        logger.warning("TEXT None-insert repair on %s: repaired=%s dropped=%s",
                       dxf_path.name, repaired, dropped)

    try:
        context = RenderContext(doc)
    except Exception as exc:  # pragma: no cover - fallback
        logger.warning("Falling back to basic RenderContext: %s", exc)
        context = RenderContext.new(doc)

    cfg = config.Configuration(
        background_policy=config.BackgroundPolicy.WHITE,
        color_policy=config.ColorPolicy.COLOR,
        lineweight_scaling=opts.lweight_scale,
        min_lineweight=0.25,
        hatch_policy=config.HatchPolicy.SHOW_OUTLINE,
    )

    fig_w, fig_h = _size_for(opts)
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=opts.dpi,
                     facecolor=opts.facecolor)
    ax = fig.add_axes([0.02, 0.02 + (0.06 if opts.show_title else 0.0),
                       0.96, 0.96 - (0.06 if opts.show_title else 0.0)])

    render_stats = (0, 0, [])
    try:
        out = matplotlib.MatplotlibBackend(ax)
        render_stats = _safe_draw_frontend(context, out, cfg, msp)
        try:
            ax.relim(visible_only=True)
            ax.autoscale_view()
            ax.set_aspect("equal", adjustable="datalim")
        except Exception as exc:
            logger.warning("Autoscale failed on %s: %s", dxf_path.name, exc)
        try:
            ax.figure.canvas.draw()
        except Exception:
            pass
    except Exception as exc:
        logger.warning("Render failed for %s: %s", dxf_path.name, exc)
        ax.text(0.5, 0.5, f"[render failed: {exc}]", ha="center", va="center",
                transform=ax.transAxes, fontsize=opts.title_fontsize,
                color="darkred")
        try:
            ax.figure.canvas.draw()
        except Exception:
            pass

    if opts.show_title:
        title = page_title or dxf_path.stem
        fig.text(0.5, 0.97, title, ha="center", va="top",
                 fontsize=opts.title_fontsize, fontweight="bold")

    if opts.show_page_frame:
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.6)
            spine.set_color("black")
    else:
        for spine in ax.spines.values():
            spine.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])

    rendered_count, skipped_count, skipped_types = render_stats
    footer = (
        f"entities={total_entities}  rendered={rendered_count}"
        f"  skipped={skipped_count}"
        f"  text-repairs(r/d)=({repaired}/{dropped})"
    )
    if skipped_types:
        footer += f"  bad={','.join(skipped_types)}"
    fig.text(0.02, 0.005, footer, ha="left", va="bottom",
             fontsize=opts.title_fontsize * 0.7, color="#555")

    with PdfPages(str(pdf_path)) as pdf:
        pdf.savefig(fig, dpi=opts.dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
    return pdf_path.resolve()


# ---------------------------------------------------------------------------
# Bundle many DXFs → one multi-page PDF
# ---------------------------------------------------------------------------
def bundle_drawings_to_pdf(
    dxf_paths: Sequence[PathLike],
    pdf_path: PathLike,
    opts: Optional[RenderOptions] = None,
    page_titles: Optional[Sequence[Optional[str]]] = None,
    cover_page_title: Optional[str] = None,
) -> Path:
    """Combine many DXF files into one multi-page PDF booklet.

    Accepts **1 to N** drawings — callers can pass lists built from phase
    two sheet directories, batch outputs, etc.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    from ezdxf import recover
    import ezdxf
    from ezdxf.addons.drawing import (
        Frontend,
        RenderContext,
        config,
        matplotlib as ez_matplotlib,
    )

    dxf_paths = [Path(p) for p in dxf_paths]
    pdf_path = Path(pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    opts = opts or RenderOptions()
    fig_w, fig_h = _size_for(opts)
    cfg = config.Configuration(
        background_policy=config.BackgroundPolicy.WHITE,
        color_policy=config.ColorPolicy.COLOR,
        lineweight_scaling=opts.lweight_scale,
        min_lineweight=0.25,
        hatch_policy=config.HatchPolicy.SHOW_OUTLINE,
    )

    titles = list(page_titles) if page_titles else [None] * len(dxf_paths)
    while len(titles) < len(dxf_paths):
        titles.append(None)

    with PdfPages(str(pdf_path)) as pdf:
        # ------------------------------------------------------------------
        # (Optional) Cover page
        # ------------------------------------------------------------------
        if cover_page_title:
            fig = plt.figure(figsize=(fig_w, fig_h), dpi=opts.dpi,
                             facecolor="#f7f4ee")
            ax = fig.add_axes([0.07, 0.08, 0.86, 0.82])
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_facecolor("#fbfaf6")
            for spine in ax.spines.values():
                spine.set_linewidth(1.4)
                spine.set_color("#1f3d2b")
            ax.add_patch(plt.Rectangle((0.0, 0.88), 1.0, 0.12,
                                       transform=ax.transAxes, color="#1f3d2b",
                                       zorder=0, clip_on=False))
            ax.text(0.5, 0.94, "GENERAL ARRANGEMENT DRAWING",
                    ha="center", va="center", color="white",
                    fontsize=max(16.0, opts.title_fontsize * 1.6),
                    fontweight="bold", transform=ax.transAxes)
            ax.text(0.5, 0.72, cover_page_title,
                    ha="center", va="center", color="#1f3d2b",
                    fontsize=max(13.0, opts.title_fontsize * 1.35),
                    fontweight="bold", transform=ax.transAxes, wrap=True)
            ax.text(0.5, 0.52, f"{len(dxf_paths)} coordinated sheet(s)",
                    ha="center", va="center", color="#4a5c50",
                    fontsize=opts.title_fontsize * 1.15,
                    transform=ax.transAxes)
            ax.plot([0.22, 0.78], [0.44, 0.44], color="#c4a35a", lw=1.6,
                    transform=ax.transAxes)
            ax.text(0.5, 0.32, "IRC / MoRTH presentation booklet",
                    ha="center", va="center", color="#6b5a3a",
                    fontsize=opts.title_fontsize, transform=ax.transAxes,
                    style="italic")
            ax.text(0.5, 0.12, "Not a construction IFC issue — GAD for review",
                    ha="center", va="center", color="#7a7a7a",
                    fontsize=opts.title_fontsize * 0.9, transform=ax.transAxes)
            pdf.savefig(fig, dpi=opts.dpi, facecolor=fig.get_facecolor())
            plt.close(fig)

        # ------------------------------------------------------------------
        # One page per DXF
        # ------------------------------------------------------------------
        for idx, dxf_path in enumerate(dxf_paths, start=1):
            try:
                doc = ezdxf.readfile(str(dxf_path))
            except Exception:
                doc, _audit = recover.readfile(str(dxf_path))
            fig = plt.figure(figsize=(fig_w, fig_h), dpi=opts.dpi,
                             facecolor=opts.facecolor)
            ax = fig.add_axes([0.02, 0.04, 0.96, 0.90])

            msp = doc.modelspace()
            try:
                total_entities = len(list(msp))
            except Exception:
                total_entities = 0
            repaired, dropped = _repair_none_insert_text(msp)
            if repaired or dropped:
                logger.warning(
                    "TEXT None-insert repair on %s: repaired=%s dropped=%s",
                    dxf_path.name, repaired, dropped)

            try:
                context = RenderContext(doc)
            except Exception:
                context = RenderContext.new(doc)
            render_stats = (0, 0, [])
            try:
                out = ez_matplotlib.MatplotlibBackend(ax)
                render_stats = _safe_draw_frontend(context, out, cfg, msp)
                try:
                    ax.relim(visible_only=True)
                    ax.autoscale_view()
                    ax.set_aspect("equal", adjustable="datalim")
                except Exception as exc:
                    logger.warning("Autoscale failed on %s: %s",
                                   dxf_path.name, exc)
                try:
                    ax.figure.canvas.draw()
                except Exception:
                    pass
            except Exception as exc:
                logger.warning("Render failed for %s: %s", dxf_path.name, exc)
                ax.text(0.5, 0.5, f"[render failed: {exc}]",
                        ha="center", va="center",
                        transform=ax.transAxes,
                        fontsize=opts.title_fontsize, color="darkred")
                try:
                    ax.figure.canvas.draw()
                except Exception:
                    pass

            title = titles[idx - 1] or dxf_path.stem
            fig.text(0.5, 0.97, f"Sheet {idx}/{len(dxf_paths)}  —  {title}",
                     ha="center", va="top", fontsize=opts.title_fontsize,
                     fontweight="bold")
            footer_right = f"{pdf_path.stem}"
            rendered_count, skipped_count, skipped_types = render_stats
            footer_left = (
                f"{dxf_path.name}   ent={total_entities}"
                f" ren={rendered_count} skip={skipped_count}"
                f" txt-repair(r/d)=({repaired}/{dropped})"
            )
            if skipped_types:
                footer_left += f" bad={','.join(skipped_types)}"
            fig.text(0.02, 0.01, footer_left, ha="left", va="bottom",
                     fontsize=opts.title_fontsize * 0.75, color="0.3")
            fig.text(0.98, 0.01, footer_right, ha="right", va="bottom",
                     fontsize=opts.title_fontsize * 0.75, color="0.3")

            if opts.show_page_frame:
                for spine in ax.spines.values():
                    spine.set_visible(True)
                    spine.set_linewidth(0.6)
                    spine.set_color("black")
            else:
                for spine in ax.spines.values():
                    spine.set_visible(False)
            ax.set_xticks([])
            ax.set_yticks([])
            pdf.savefig(fig, dpi=opts.dpi, facecolor=fig.get_facecolor())
            plt.close(fig)

    return pdf_path.resolve()


# ---------------------------------------------------------------------------
# High-level convenience: convert an output directory, or a list of files
# ---------------------------------------------------------------------------
def convert_directory_to_pdfs(
    dxf_dir: PathLike,
    pdf_dir: Optional[PathLike] = None,
    opts: Optional[RenderOptions] = None,
    pattern: str = "*.dxf",
    recursive: bool = True,
) -> List[Tuple[Path, Path]]:
    """Find every DXF under ``dxf_dir`` and produce a matching PDF tree."""
    dxf_dir = Path(dxf_dir)
    if pdf_dir is None:
        pdf_dir = dxf_dir
    pdf_dir = Path(pdf_dir)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    iterable: Iterable[Path] = (
        dxf_dir.rglob(pattern) if recursive else dxf_dir.glob(pattern)
    )
    pairs: List[Tuple[Path, Path]] = []
    for dxf in iterable:
        rel = dxf.relative_to(dxf_dir)
        out = (pdf_dir / rel).with_suffix(".pdf")
        pairs.append((dxf, out))
        convert_dxf_to_pdf(dxf, out, opts=opts,
                           page_title=rel.with_suffix("").as_posix())
    return pairs
