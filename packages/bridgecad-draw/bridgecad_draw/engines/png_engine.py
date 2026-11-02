"""PNG raster engine (matplotlib)."""

from __future__ import annotations

from pathlib import Path

from ._render import render_figure


def render_png(dxf_path: str | Path, output_png: str | Path, dpi: int = 150) -> Path:
    """Rasterise one DXF sheet to PNG."""
    import matplotlib.pyplot as plt

    out = Path(output_png)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig = render_figure(dxf_path)
    fig.savefig(str(out), dpi=dpi)
    plt.close(fig)
    return out


__all__ = ["render_png"]
