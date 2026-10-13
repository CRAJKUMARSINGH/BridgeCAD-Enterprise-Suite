"""
bridgecad_draw.dxf_engine — ezdxf document factory and coordinate helpers.

Every drawing sheet module calls ``new_sheet()`` to get a fresh (doc, msp) pair,
then uses ``hpos/vpos`` to convert real-world metres to drawing-space units.

Drawing-space convention
------------------------
- 1 drawing unit = 1 mm in model space (standard CAD practice).
- Horizontal scale (hscale) and vertical scale (vscale) are usually equal (1:1
  for details, 1:100 for GAD long-section), applied at plot time.
- ``hpos(x_m)`` → x_m * 1000  (metres → mm in model space)
- ``vpos(y_rl)`` → (y_rl - datum_rl) * 1000  (RL → mm offset from datum)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
    _EZDXF_OK = True
except ImportError:
    _EZDXF_OK = False

from .layers import setup_layers


# ---------------------------------------------------------------------------
# Document factory
# ---------------------------------------------------------------------------

ACAD_VERSION = "R2018"


def new_sheet(title: str = "", acad_ver: str = ACAD_VERSION) -> tuple[Any, Any]:
    """Create a new ezdxf Drawing with all IRC SP:55 layers pre-registered.

    Returns
    -------
    (doc, msp) : tuple
        ``doc``  — ezdxf Drawing object
        ``msp``  — ModelSpace of that document
    """
    if not _EZDXF_OK:
        raise ImportError("ezdxf is required: pip install ezdxf>=1.3")

    doc = ezdxf.new(acad_ver, setup="drafting")

    # Register all IRC SP:55 layers
    setup_layers(doc)

    # Text styles
    _setup_text_styles(doc)

    # Linetype definitions (non-standard ones)
    _setup_linetypes(doc)

    msp = doc.modelspace()
    return doc, msp


def _setup_text_styles(doc: Any) -> None:
    """Register standard text styles."""
    styles = doc.styles
    for name, font in [
        ("BRIDGE_STD",  "Arial.ttf"),
        ("BRIDGE_BOLD", "Arial Bold.ttf"),
        ("BRIDGE_MONO", "Courier New.ttf"),
    ]:
        if not styles.has_entry(name):
            try:
                styles.add(name, font=font)
            except Exception:
                pass


def _setup_linetypes(doc: Any) -> None:
    """Register common non-standard linetypes if missing."""
    lts = doc.linetypes
    defs = {
        "CENTER":   "A,.75,-.25,.25,-.25",
        "CENTER2":  "A,.375,-.125,.125,-.125",
        "DASHED":   "A,.375,-.125",
        "DASHED2":  "A,.1875,-.0625",
        "HIDDEN":   "A,.1875,-.0625",
        "PHANTOM":  "A,.625,-.125,.125,-.125,.125,-.125",
    }
    for name, pattern in defs.items():
        if not lts.has_entry(name):
            try:
                lts.add(name, pattern=pattern)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Coordinate mapper
# ---------------------------------------------------------------------------

class CoordMapper:
    """Maps real-world metres + RL values to drawing mm units.

    Parameters
    ----------
    datum_rl : float
        The reference reduced-level (m).  ``vpos(datum_rl)`` returns 0.
    origin_ch : float
        The reference chainage (m).  ``hpos(origin_ch)`` returns 0.
    h_scale : float
        Horizontal model-space scale (1.0 = 1 m → 1000 mm).
    v_scale : float
        Vertical model-space scale (1.0 = 1 m → 1000 mm).
        Use >1.0 for exaggerated vertical scale on long sections.
    x_offset : float
        Additional X offset in mm (to place the drawing on the sheet).
    y_offset : float
        Additional Y offset in mm.
    """

    def __init__(
        self,
        datum_rl: float = 0.0,
        origin_ch: float = 0.0,
        h_scale: float = 1.0,
        v_scale: float = 1.0,
        x_offset: float = 0.0,
        y_offset: float = 0.0,
    ) -> None:
        self.datum_rl  = datum_rl
        self.origin_ch = origin_ch
        self.h_scale   = h_scale
        self.v_scale   = v_scale
        self.x_offset  = x_offset
        self.y_offset  = y_offset

    def hpos(self, ch_m: float) -> float:
        """Chainage in metres → drawing X in mm."""
        return (ch_m - self.origin_ch) * 1000.0 * self.h_scale + self.x_offset

    def vpos(self, rl_m: float) -> float:
        """Reduced level in metres → drawing Y in mm."""
        return (rl_m - self.datum_rl) * 1000.0 * self.v_scale + self.y_offset

    def pt(self, ch_m: float, rl_m: float) -> tuple[float, float]:
        """Convert (chainage, RL) → drawing (x, y) mm."""
        return (self.hpos(ch_m), self.vpos(rl_m))

    def h_len(self, metres: float) -> float:
        """Convert a horizontal length (m) to drawing length (mm)."""
        return metres * 1000.0 * self.h_scale

    def v_len(self, metres: float) -> float:
        """Convert a vertical length (m) to drawing length (mm)."""
        return metres * 1000.0 * self.v_scale


# ---------------------------------------------------------------------------
# Save helpers
# ---------------------------------------------------------------------------

def save(doc: Any, output_path: str | Path) -> Path:
    """Save the DXF document and return the resolved path."""
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(p))
    return p


__all__ = ["new_sheet", "CoordMapper", "save", "ACAD_VERSION"]
