"""SVG vector engine (matplotlib)."""

from __future__ import annotations

from pathlib import Path

from ._render import render_figure


def render_svg(dxf_path: str | Path, output_svg: str | Path) -> Path:
    """Vectorise one DXF sheet to SVG."""
    import matplotlib.pyplot as plt

    out = Path(output_svg)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig = render_figure(dxf_path)
    fig.savefig(str(out), format="svg")
    plt.close(fig)
    return out


__all__ = ["render_svg"]
