from __future__ import annotations
from pathlib import Path

import ezdxf
import pandas as pd
from ezdxf.math import Vec2
from .config import Settings


class BridgeDrawing:
    def __init__(self, settings=None):
        self.settings = settings or Settings()


def generate_bridge_drawing(*, excel_file: Path, output_path: Path) -> Path:
    _ = pd.read_excel(excel_file)
    doc = ezdxf.new()
    _ = doc.modelspace()
    # TODO: actual drawing logic
    doc.saveas(output_path)
    return output_path


class SlabBridgeGAD:
    """Slab bridge general-arrangement drawing from Excel."""

    def __init__(self, df: pd.DataFrame):
        self.rows = df.to_dict("records")

    def generate(self, out_path: Path) -> Path:
        doc = ezdxf.new("R2018")
        msp = doc.modelspace()
        x_cursor = 0.0
        text_h = 0.25

        for idx, row in enumerate(self.rows, 1):
            L = float(row["Length (m)"])
            W = float(row["Width (m)"])
            _ = float(row["Thickness (m)"])
            # Handle both possible column names for pier width
            pier_width_cols = ["Pier_Width (m)", "Pier\\_Width (m)", "Pier Width (m)"]
            P = None
            for col in pier_width_cols:
                if col in row:
                    P = float(row[col])
                    break
            if P is None:
                P = 1.0  # Default pier width

            # deck slab rectangle (top view)
            p1 = Vec2(x_cursor, 0)
            p2 = Vec2(x_cursor + L, 0)
            p3 = Vec2(x_cursor + L, W)
            p4 = Vec2(x_cursor, W)
            msp.add_lwpolyline([p1, p2, p3, p4, p1], close=True)

            # centre-line
            msp.add_line(
                (x_cursor + L / 2, 0),
                (x_cursor + L / 2, W),
                dxfattribs={"linetype": "CENTER"},
            )

            # span annotation
            msp.add_text(
                f"{idx}: {L} m",
                dxfattribs={"height": text_h, "layer": "TEXT"},
            ).set_placement(Vec2(x_cursor + L / 2, W + 0.5), align="MIDDLE_CENTER")

            # pier rectangle
            pier_x = x_cursor + L
            msp.add_lwpolyline(
                [
                    (pier_x - P / 2, -0.5),
                    (pier_x + P / 2, -0.5),
                    (pier_x + P / 2, W + 0.5),
                    (pier_x - P / 2, W + 0.5),
                ],
                close=True,
            )

            x_cursor += L + P

        doc.saveas(out_path)
        return out_path
