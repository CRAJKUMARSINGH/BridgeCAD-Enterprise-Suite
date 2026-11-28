import pandas as pd
import ezdxf
from pathlib import Path


def read_lisp_sheet(xlsx_path: Path) -> dict:
    """Read Lisp parameters from Excel, handling units in cells.

    Args:
        xlsx_path: Path to Excel file with parameters

    Returns:
        dict: {parameter_name: float_value}
    """
    df = pd.read_excel(xlsx_path, header=0, engine='openpyxl')
    out = {}
    for _, row in df.iterrows():
        if len(row) >= 2:  # Ensure we have at least 2 columns
            key = str(row.iloc[0]).strip()
            # Extract numeric part from value (handles "10.8 m" -> 10.8)
            val_str = str(row.iloc[1]).split()[0]  # Get first part before space
            try:
                out[key] = float(val_str)
            except (ValueError, IndexError):
                print(f"Warning: Could not convert value '{row.iloc[1]}' to float for parameter '{key}'")
    return out


def draw_lisp_bridge(xlsx_path: Path, out_dxf: Path) -> Path:
    """
    Generate DXF drawing from Lisp parameters in Excel.

    Args:
        xlsx_path: Path to Excel file with Lisp parameters
        out_dxf: Path to save the output DXF file

    Returns:
        Path to the generated DXF file
    """
    # Read parameters
    params = read_lisp_sheet(xlsx_path)

    # Initialize DXF document
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()

    # Extract parameters with defaults for missing keys
    try:
        # Global geometry
        _ = params["LBRIDGE"]
        n_span = int(params["NSPAN"])
        spans = [params[f"SPAN{i+1}"] for i in range(n_span)]
        W = params["CCBR"]

        # Kerbs
        kerb_w = params.get("KERBW", 0.3)
        kerb_d = params.get("KERBD", 0.2)

        # Levels
        top_rl = params["TOPRL"]
        soffit = params["SOFL"]

        # Pier & footing
        pier_w = params["CAPW"]
        _ = params.get("FUTW", pier_w * 1.5)
        _ = params.get("FUTL", W * 0.8)
        _ = params.get("FUTD", 0.5)

        # Approach slab
        _ = params.get("LASLAB", 3.0)

    except KeyError as e:
        raise ValueError(f"Missing required parameter: {e}")

    # Draw bridge elements
    x = 0.0
    for span in spans:
        # Deck slab with camber (2.5%)
        camber = span * 0.025

        # Top face
        pts_top = [
            (x, 0, top_rl),
            (x + span, 0, top_rl + camber),
            (x + span, W, top_rl + camber),
            (x, W, top_rl)
        ]

        # Bottom face
        pts_bot = [(p[0], p[1], soffit) for p in pts_top]

        # Add deck faces
        msp.add_3dface(pts_top, dxfattribs={"layer": "DECK"})
        msp.add_3dface(pts_bot, dxfattribs={"layer": "DECK"})

        # Add side faces
        for i in range(4):
            j = (i + 1) % 4
            face = [
                pts_top[i], pts_top[j],
                pts_bot[j], pts_bot[i]
            ]
            msp.add_3dface(face, dxfattribs={"layer": "DECK_SIDE"})

        # Kerbs
        for y in [0, W]:
            k_top = [
                (x, y, top_rl),
                (x + span, y, top_rl + camber),
                (x + span, y + kerb_w, top_rl + camber + kerb_d),
                (x, y + kerb_w, top_rl + kerb_d)
            ]
            msp.add_3dface(k_top, dxfattribs={"layer": "KERB"})

        # Move to next span
        x += span

    # Save DXF
    doc.saveas(out_dxf)
    return out_dxf
