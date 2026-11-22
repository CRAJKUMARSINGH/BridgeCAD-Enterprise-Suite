"""bridgecad_draw.dim_style — editable native CAD dimension styles and units.

Shortcoming fixed: every sheet emitted real DIMENSION entities, but each one
carried a hard-typed text override (e.g. ``"Cap=2.00m"``) and the global style
``pmb100`` kept ``DIMLFAC = 1`` while geometry is drawn in *paper* mm at 1:N.
So the dimension text never followed the geometry, could not be re-styled, and
switching units (m / mm) meant re-generating every sheet.

``apply_native_dimensions`` rewrites a built document so every DIMENSION:
  * uses one named, editable style (``DimStyleConfig.name``),
  * measures itself (text ``"<>"``) with ``DIMLFAC = scale_denom`` scaled to the
    chosen unit, so CAD shows true site values and re-measures on edit,
  * carries the unit suffix/decimals from the style, not from a string.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Units = Literal["mm", "m"]

_UNIT_FACTOR = {"mm": 1.0, "m": 0.001}  # real-world mm -> unit
_DIMLUNIT_DECIMAL = 2


@dataclass(frozen=True)
class DimStyleConfig:
    name: str = "BRIDGE_DIM"
    units: Units = "m"
    decimals: int = 2
    text_mm: float = 2.5
    arrow_mm: float = 2.0
    ext_beyond_mm: float = 1.5
    ext_offset_mm: float = 1.0
    text_style: str = "BRIDGE_STD"

    def __post_init__(self) -> None:
        if self.units not in _UNIT_FACTOR:
            raise ValueError(f"units must be one of {sorted(_UNIT_FACTOR)}, got {self.units!r}")
        if not 0 <= self.decimals <= 6:
            raise ValueError("decimals must be 0..6")


def dimlfac_for(scale_denom: int, units: Units) -> float:
    """Paper-mm -> displayed value. 1 paper mm at 1:N is N real mm."""
    if scale_denom <= 0:
        raise ValueError("scale_denom must be positive")
    return float(scale_denom) * _UNIT_FACTOR[units]


def configure_dimstyle(doc: Any, cfg: DimStyleConfig, scale_denom: int) -> Any:
    """Create or update the named style; returns the DIMSTYLE table entry."""
    ds = doc.dimstyles.get(cfg.name) if doc.dimstyles.has_entry(cfg.name) else doc.dimstyles.add(cfg.name)
    if doc.styles.has_entry(cfg.text_style):
        ds.dxf.dimtxsty = cfg.text_style
    ds.dxf.dimtxt = cfg.text_mm
    ds.dxf.dimasz = cfg.arrow_mm
    ds.dxf.dimexe = cfg.ext_beyond_mm
    ds.dxf.dimexo = cfg.ext_offset_mm
    ds.dxf.dimgap = cfg.text_mm * 0.4
    ds.dxf.dimlunit = _DIMLUNIT_DECIMAL
    ds.dxf.dimdec = cfg.decimals
    ds.dxf.dimlfac = dimlfac_for(scale_denom, cfg.units)
    ds.dxf.dimpost = f"<> {cfg.units}" if cfg.units == "m" else "<>"
    ds.dxf.dimtad = 1
    ds.dxf.dimtih = 0
    return ds


def apply_native_dimensions(doc: Any, cfg: DimStyleConfig, scale_denom: int) -> int:
    """Re-style every modelspace DIMENSION to measured text. Returns count."""
    configure_dimstyle(doc, cfg, scale_denom)
    n = 0
    for dim in doc.modelspace().query("DIMENSION"):
        dim.dxf.dimstyle = cfg.name
        dim.dxf.text = "<>"
        # Drop per-entity overrides of the values the style now owns.
        ov = dim.override()
        for key in ("dimtxt", "dimasz", "dimgap", "dimlfac", "dimdec", "dimpost"):
            ov.dimstyle_attribs.pop(key, None)
        ov.commit()
        try:
            ov.render()
        except Exception:  # geometry block stays as before; entity still valid
            pass
        n += 1
    doc.header["$DIMSTYLE"] = cfg.name
    return n


def displayed_value(dim: Any, doc: Any) -> float:
    """The number CAD will print for *dim* (measurement × style DIMLFAC)."""
    ds = doc.dimstyles.get(dim.dxf.dimstyle)
    return float(dim.get_measurement()) * float(ds.dxf.dimlfac)
