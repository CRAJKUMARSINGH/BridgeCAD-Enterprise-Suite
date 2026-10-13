"""
bridgecad_draw.layers — IRC SP:55-2019 layer registry for bridge GAD drawings.

Every layer has:
  name        — canonical DXF layer name  (matches IRC SP:55 Annex F)
  color       — AutoCAD colour index (1–255)
  linetype    — DXF linetype string
  lineweight  — lineweight in hundredths of mm (ezdxf integer)
  description — human-readable purpose

Usage
-----
    from bridgecad_draw.layers import LAYER_REGISTRY, setup_layers
    setup_layers(doc)   # registers all layers on an ezdxf Drawing
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LayerDef:
    name: str
    color: int          # ACI colour index
    linetype: str       # DXF linetype name
    lineweight: int     # 1/100 mm  (e.g. 25 = 0.25 mm)
    description: str


# ---------------------------------------------------------------------------
# IRC SP:55-2019 layer definitions (Annex F)
# ---------------------------------------------------------------------------
LAYER_REGISTRY: dict[str, LayerDef] = {ld.name: ld for ld in [
    # ── Structural outline ──────────────────────────────────────────────────
    LayerDef("STRUC-OUTLINE",    1,  "Continuous", 50,  "Primary structural outline — deck, piers, abutments"),
    LayerDef("STRUC-HIDDEN",     8,  "HIDDEN",     25,  "Hidden structural lines"),
    LayerDef("STRUC-CENTRE",     6,  "CENTER",     18,  "Centrelines and axis lines"),
    LayerDef("STRUC-SECTION",    2,  "Continuous", 40,  "Section cut boundaries"),
    LayerDef("STRUC-HATCHING",   8,  "Continuous", 18,  "Section hatching (concrete, soil)"),
    LayerDef("STRUC-DETAIL",     4,  "Continuous", 30,  "Detail view outlines (scale 1:20 or finer)"),

    # ── Civil / ground ───────────────────────────────────────────────────────
    LayerDef("CIVIL-GROUND",     3,  "Continuous", 35,  "Existing ground profile (EG polyline)"),
    LayerDef("CIVIL-HFL",        5,  "DASHED",     25,  "Highest Flood Level line"),
    LayerDef("CIVIL-LWL",        4,  "DASHED",     18,  "Low Water Level line"),
    LayerDef("CIVIL-SCOUR",      1,  "DASHED2",    18,  "Design scour level"),
    LayerDef("CIVIL-ROAD",       7,  "Continuous", 25,  "Approach road alignment and surface"),
    LayerDef("CIVIL-CHAINAGE",   7,  "Continuous", 18,  "Chainage markers along alignment"),
    LayerDef("CIVIL-CONTOUR",   30,  "Continuous", 13,  "Site contour lines"),

    # ── Foundation ───────────────────────────────────────────────────────────
    LayerDef("FOUND-PILE",       4,  "Continuous", 40,  "Pile circles and cap outline"),
    LayerDef("FOUND-CAP",        2,  "Continuous", 35,  "Pile cap / raft / footing outline"),
    LayerDef("FOUND-WELL",       4,  "Continuous", 35,  "Well steining circles"),
    LayerDef("FOUND-OPEN",       2,  "Continuous", 30,  "Open foundation stepped outline"),
    LayerDef("FOUND-SOIL",      34,  "Continuous", 18,  "Soil stratigraphy (hatch + label)"),

    # ── Substructure ─────────────────────────────────────────────────────────
    LayerDef("SUB-PIER",         2,  "Continuous", 40,  "Pier shaft and cap outline"),
    LayerDef("SUB-ABUT",         3,  "Continuous", 40,  "Abutment wall and wing wall outline"),
    LayerDef("SUB-BEARING",      5,  "Continuous", 25,  "Bearing pad outlines and schedule"),
    LayerDef("SUB-EXPJOINT",     6,  "Continuous", 25,  "Expansion joint locations"),
    LayerDef("SUB-BACKFILL",    34,  "Continuous", 18,  "Backfill hatch (earth/granular)"),

    # ── Superstructure ───────────────────────────────────────────────────────
    LayerDef("SUPER-DECK",       2,  "Continuous", 50,  "Deck slab top and bottom face"),
    LayerDef("SUPER-GIRDER",     1,  "Continuous", 40,  "Girder webs and flanges"),
    LayerDef("SUPER-PARAPET",    2,  "Continuous", 35,  "Parapet and railing outline"),
    LayerDef("SUPER-WEARING",    8,  "Continuous", 25,  "Wearing coat cross-section"),
    LayerDef("SUPER-CAMBER",     6,  "DASHED",     18,  "Pre-camber reference profile"),
    LayerDef("SUPER-KERB",       7,  "Continuous", 25,  "Kerb cross-section"),
    LayerDef("SUPER-FOOTPATH",   7,  "Continuous", 25,  "Footpath / pedestrian zone"),
    LayerDef("SUPER-CRASH",      1,  "Continuous", 30,  "Crash barrier / median barrier"),
    LayerDef("SUPER-DRAINAGE",   4,  "Continuous", 20,  "Deck drainage scupper and pipes"),

    # ── Dimensions & annotations ─────────────────────────────────────────────
    LayerDef("DIM-LINEAR",       3,  "Continuous", 18,  "Linear dimension strings"),
    LayerDef("DIM-LEADER",       3,  "Continuous", 18,  "Leader lines and callouts"),
    LayerDef("DIM-LEVEL",        3,  "Continuous", 18,  "Level / RL annotation arrows"),
    LayerDef("DIM-CHAINAGE",     3,  "Continuous", 18,  "Chainage annotation"),
    LayerDef("DIM-SLOPE",        3,  "Continuous", 18,  "Slope / gradient ratio labels"),

    # ── Text ─────────────────────────────────────────────────────────────────
    LayerDef("TEXT-GENERAL",     7,  "Continuous", 18,  "General notes and labels"),
    LayerDef("TEXT-TITLE",       7,  "Continuous", 25,  "Title block text"),
    LayerDef("TEXT-HEADER",      7,  "Continuous", 25,  "Sheet header / zone label"),
    LayerDef("TEXT-LEVEL",       5,  "Continuous", 18,  "Reduced level tags (+RL)"),
    LayerDef("TEXT-SPEC",        7,  "Continuous", 13,  "Specification notes (small)"),

    # ── Title block & border ─────────────────────────────────────────────────
    LayerDef("BORDER-OUTER",     7,  "Continuous", 70,  "Sheet outer border"),
    LayerDef("BORDER-INNER",     7,  "Continuous", 35,  "Sheet inner border / margin"),
    LayerDef("TITLEBLK-BOX",     7,  "Continuous", 50,  "Title block cell outlines"),
    LayerDef("TITLEBLK-TEXT",    7,  "Continuous", 18,  "Title block text fields"),
    LayerDef("TITLEBLK-LOGO",    7,  "Continuous", 25,  "Client / consultant logo area"),

    # ── Symbols & references ─────────────────────────────────────────────────
    LayerDef("SYM-NORTHARROW",   7,  "Continuous", 18,  "North arrow symbol"),
    LayerDef("SYM-SECTIONMARK",  1,  "Continuous", 18,  "Section A-A cut markers"),
    LayerDef("SYM-REVISION",     6,  "Continuous", 18,  "Revision cloud / delta markers"),
    LayerDef("SYM-SCALE",        7,  "Continuous", 13,  "Graphic scale bar"),

    # ── Miscellaneous ────────────────────────────────────────────────────────
    LayerDef("MISC-GRID",        8,  "DASHED",     13,  "Construction grid / reference"),
    LayerDef("MISC-SETOUT",      5,  "CENTER2",    13,  "Set-out points and traverse"),
    LayerDef("MISC-DEFPOINTS",   7,  "Continuous",  0,  "Definition points (non-printing)"),
    LayerDef("0",                7,  "Continuous", 25,  "Default layer (ezdxf baseline)"),
]}

# Short aliases used by drawing modules
L = LAYER_REGISTRY   # e.g.  L["STRUC-OUTLINE"]

# Grouped sets for quick access
STRUCTURAL_LAYERS = {k: v for k, v in L.items() if k.startswith("STRUC")}
ANNOTATION_LAYERS = {k: v for k, v in L.items() if k.startswith(("DIM", "TEXT"))}
TITLEBLOCK_LAYERS  = {k: v for k, v in L.items() if k.startswith(("BORDER", "TITLEBLK"))}


def setup_layers(doc: Any) -> None:
    """Register all IRC SP:55 layers on an ezdxf Drawing document.

    Parameters
    ----------
    doc : ezdxf.Drawing
        An ezdxf document returned by ``ezdxf.new()``.
    """
    layers = doc.layers
    for ld in LAYER_REGISTRY.values():
        if ld.name == "0":
            continue  # layer "0" already exists in every ezdxf doc
        if not layers.has_entry(ld.name):
            layer = layers.add(ld.name, color=ld.color, linetype=ld.linetype)
            layer.dxf.lineweight = ld.lineweight
        # Register linetype if non-standard
        if ld.linetype not in ("Continuous",):
            if not doc.linetypes.has_entry(ld.linetype):
                try:
                    doc.linetypes.add(ld.linetype)
                except Exception:
                    pass  # ezdxf may have it built-in; safe to ignore


__all__ = ["LayerDef", "LAYER_REGISTRY", "L", "setup_layers",
           "STRUCTURAL_LAYERS", "ANNOTATION_LAYERS", "TITLEBLOCK_LAYERS"]
