#!/usr/bin/env python3
"""Simple DXF to PDF conversion test with error handling."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import matplotlib

matplotlib.use("Agg")
import ezdxf
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import Frontend, RenderContext, config
from ezdxf.addons.drawing import matplotlib as ez_matplotlib
from matplotlib.backends.backend_pdf import PdfPages


def simple_convert(dxf_path, pdf_path):
    """Simplified DXF to PDF conversion with detailed error handling."""

    print(f"Converting {dxf_path} to {pdf_path}")

    try:
        doc = ezdxf.readfile(str(dxf_path))
    except Exception as e:
        print(f"Error reading DXF: {e}")
        return False

    if not doc.modelspace():
        print("Empty modelspace")
        return False

    print(f"Modelspace has {len(list(doc.modelspace()))} entities")

    try:
        context = RenderContext(doc)
    except Exception as e:
        print(f"Error creating RenderContext: {e}")
        context = RenderContext.new(doc)

    cfg = config.Configuration(
        background_policy=config.BackgroundPolicy.WHITE,
        color_policy=config.ColorPolicy.COLOR,
        lineweight_scaling=0.7,
        min_lineweight=0.25,
        hatch_policy=config.HatchPolicy.SHOW_OUTLINE,
    )

    # Create figure
    fig = plt.figure(figsize=(11.69, 8.27), dpi=150, facecolor="white")
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])

    try:
        print("Starting rendering...")
        out = ez_matplotlib.MatplotlibBackend(ax)

        # Try to render with more detailed error handling
        try:
            Frontend(context, out, config=cfg).draw_layout(
                doc.modelspace(),
                finalize=True,
            )
            print("Rendering completed")
        except Exception as render_error:
            print(f"Render error: {render_error}")
            print(f"Error type: {type(render_error)}")
            import traceback

            traceback.print_exc()

            # Try rendering without finalize
            try:
                print("Trying without finalize...")
                Frontend(context, out, config=cfg).draw_layout(
                    doc.modelspace(),
                    finalize=False,
                )
                print("Rendering without finalize completed")
            except Exception as e2:
                print(f"Second render attempt failed: {e2}")
                ax.text(
                    0.5,
                    0.5,
                    f"Render failed: {render_error}",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )

        # Force draw
        ax.figure.canvas.draw()

    except Exception as e:
        print(f"Backend error: {e}")
        import traceback

        traceback.print_exc()
        ax.text(0.5, 0.5, f"Backend error: {e}", ha="center", va="center", transform=ax.transAxes)

    # Remove axes
    ax.set_xticks([])
    ax.set_yticks([])

    # Save PDF
    try:
        with PdfPages(str(pdf_path)) as pdf:
            pdf.savefig(fig, dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)

        # Check file size
        size = Path(pdf_path).stat().st_size
        print(f"PDF created: {size} bytes")
        return size > 1000  # Consider it successful if > 1KB

    except Exception as e:
        print(f"PDF save error: {e}")
        plt.close(fig)
        return False


if __name__ == "__main__":
    result = simple_convert("downloads/sample_input_local.dxf", "downloads/simple_test.pdf")
    print(f"Success: {result}")
