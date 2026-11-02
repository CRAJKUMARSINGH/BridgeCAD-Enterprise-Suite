"""Shared DXF → matplotlib figure renderer for the pdf / png / svg engines."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def render_figure(dxf_path: str | Path, size_in: tuple[float, float] = (23.39, 16.54)) -> Any:
    """Render a DXF modelspace to a matplotlib Figure (default A2 landscape)."""
    import ezdxf
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

    doc = ezdxf.readfile(str(dxf_path))
    fig = plt.figure(figsize=size_in)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(doc.modelspace(), finalize=True)
    return fig
