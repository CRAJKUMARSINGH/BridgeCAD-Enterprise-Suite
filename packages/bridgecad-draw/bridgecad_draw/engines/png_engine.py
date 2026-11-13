"""PNG raster engine (matplotlib)."""

from __future__ import annotations

from pathlib import Path

from ._render import render_figure


PAPER_MM = {"A0": (1189, 841), "A1": (841, 594), "A2": (594, 420), "A3": (420, 297), "A4": (297, 210)}


def paper_size_inches(paper: str, orientation: str) -> tuple[float, float]:
    """Raster output media only; does not alter CAD coordinates or view scales."""
    if paper not in PAPER_MM or orientation not in ("landscape", "portrait"):
        raise ValueError("Choose A0-A4 and landscape/portrait")
    width, height = PAPER_MM[paper]
    if orientation == "portrait":
        width, height = height, width
    return width / 25.4, height / 25.4


def render_png(dxf_path: str | Path, output_png: str | Path, dpi: int = 150,
               *, size_in: tuple[float, float] = (23.39, 16.54)) -> Path:
    """Rasterise one DXF sheet to PNG."""
    import matplotlib.pyplot as plt

    out = Path(output_png)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig = render_figure(dxf_path, size_in=size_in)
    fig.savefig(str(out), dpi=dpi)
    plt.close(fig)
    return out


__all__ = ["render_png", "paper_size_inches"]
