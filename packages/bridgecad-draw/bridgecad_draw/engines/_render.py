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
    from ezdxf.addons.drawing.config import BackgroundPolicy, Configuration
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

    doc = ezdxf.readfile(str(dxf_path))
    fig = plt.figure(figsize=size_in)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    # Export to white paper explicitly. The default modelspace context chooses
    # white ACI-7 strokes for a dark background, but an axis-off matplotlib
    # export exposes the white figure underneath, making schedules disappear.
    fig.patch.set_facecolor("white")
    config = Configuration(background_policy=BackgroundPolicy.WHITE)
    Frontend(RenderContext(doc), MatplotlibBackend(ax, adjust_figure=False), config=config).draw_layout(doc.modelspace(), finalize=True)
    return fig
