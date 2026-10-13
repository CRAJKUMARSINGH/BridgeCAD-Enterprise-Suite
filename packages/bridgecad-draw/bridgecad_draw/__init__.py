"""
bridgecad_draw — Drawing engine package (M3).

Submodules:
  layers        IRC SP:55 layer registry
  primitives    DXF drawing helpers (lines, hatching, dimensions, text)
  dxf_engine    ezdxf document factory + coordinate mapper
  titleblocks   IRC / NHAI title block + sheet border
  sheet1_plan   Sheet 1: Plan View
  sheet2_long_section   Sheet 2: Longitudinal Section
  booklet       7-sheet DXF package generator
"""

from .layers import LAYER_REGISTRY, setup_layers
from .dxf_engine import new_sheet, CoordMapper, save
from .booklet import generate_package

__version__ = "0.1.0-rc1"
__all__ = ["LAYER_REGISTRY", "setup_layers", "new_sheet", "CoordMapper",
           "save", "generate_package"]
