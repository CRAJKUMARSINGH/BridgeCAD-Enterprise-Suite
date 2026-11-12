"""Render the asset-pack DXFs to PNG for visual verification.

    python scripts/render_asset_pack.py out/ [--dpi 150]

Uses ezdxf's matplotlib backend, so it needs matplotlib only — no external CAD.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def render(dxf_paths: list[Path], out_dir: Path, dpi: int = 150) -> list[Path]:
    from ezdxf.addons.drawing import Frontend, RenderContext, matplotlib as mp
    from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for dxf in dxf_paths:
        import ezdxf

        doc = ezdxf.readfile(str(dxf))
        msp = doc.modelspace()
        fig = plt.figure(figsize=(16.54, 11.69))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        ctx = RenderContext(doc)
        cfg = Configuration(background_policy=BackgroundPolicy.WHITE)
        fe = Frontend(ctx, mp.MatplotlibBackend(ax), config=cfg)
        fe.draw_layout(msp)
        png = out_dir / (dxf.stem + ".png")
        fig.savefig(png, dpi=dpi, facecolor="white")
        plt.close(fig)
        written.append(png)
        print(f"rendered {png}")
    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dpi", type=int, default=150)
    a = ap.parse_args()
    dxfs: list[Path] = []
    for p in a.paths:
        pth = Path(p)
        dxfs.extend(sorted(pth.glob("*.dxf")) if pth.is_dir() else [pth])
    out = Path(a.out) if a.out else (Path(a.paths[0]).parent / "png")
    render(dxfs, out, a.dpi)
    return 0


if __name__ == "__main__":
    sys.exit(main())
