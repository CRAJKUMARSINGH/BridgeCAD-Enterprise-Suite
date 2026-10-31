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

import contextlib
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LayerDef:
    name: str
    color: int  # ACI colour index
    linetype: str  # DXF linetype name
    lineweight: int  # 1/100 mm  (e.g. 25 = 0.25 mm)
    description: str


# ---------------------------------------------------------------------------
# IRC SP:55-2019 layer definitions (Annex F)
# ---------------------------------------------------------------------------
LAYER_REGISTRY: dict[str, LayerDef] = {
    ld.name: ld
    for ld in [
        # ── Structural outline ──────────────────────────────────────────────────
        LayerDef(
            "STRUC-OUTLINE",
            1,
            "Continuous",
            50,
            "Primary structural outline — deck, piers, abutments",
        ),
        LayerDef("STRUC-HIDDEN", 8, "HIDDEN", 25, "Hidden structural lines"),
        LayerDef("STRUC-CENTRE", 6, "CENTER", 18, "Centrelines and axis lines"),
        LayerDef("STRUC-SECTION", 2, "Continuous", 35, "Section cut boundaries"),
        LayerDef("STRUC-HATCHING", 8, "Continuous", 18, "Section hatching (concrete, soil)"),
        LayerDef("STRUC-DETAIL", 4, "Continuous", 35, "Detail view outlines (scale 1:20 or finer)"),
        # ── Civil / ground ───────────────────────────────────────────────────────
        LayerDef("CIVIL-GROUND", 3, "Continuous", 35, "Existing ground profile (EG polyline)"),
        LayerDef("CIVIL-HFL", 5, "DASHED", 25, "Highest Flood Level line"),
        LayerDef("CIVIL-LWL", 4, "DASHED", 18, "Low Water Level line"),
        LayerDef("CIVIL-SCOUR", 1, "DASHED2", 18, "Design scour level"),
        LayerDef("CIVIL-ROAD", 7, "Continuous", 25, "Approach road alignment and surface"),
        LayerDef("CIVIL-CHAINAGE", 7, "Continuous", 18, "Chainage markers along alignment"),
        LayerDef("CIVIL-CONTOUR", 30, "Continuous", 13, "Site contour lines"),
        # ── Foundation ───────────────────────────────────────────────────────────
        LayerDef("FOUND-PILE", 4, "Continuous", 35, "Pile circles and cap outline"),
        LayerDef("FOUND-CAP", 2, "Continuous", 35, "Pile cap / raft / footing outline"),
        LayerDef("FOUND-WELL", 4, "Continuous", 35, "Well steining circles"),
        LayerDef("FOUND-OPEN", 2, "Continuous", 35, "Open foundation stepped outline"),
        LayerDef("FOUND-SOIL", 34, "Continuous", 18, "Soil stratigraphy (hatch + label)"),
        # ── Substructure ─────────────────────────────────────────────────────────
        LayerDef("SUB-PIER", 2, "Continuous", 35, "Pier shaft and cap outline"),
        LayerDef("SUB-ABUT", 3, "Continuous", 35, "Abutment wall and wing wall outline"),
        LayerDef("SUB-BEARING", 5, "Continuous", 25, "Bearing pad outlines and schedule"),
        LayerDef("SUB-EXPJOINT", 6, "Continuous", 25, "Expansion joint locations"),
        LayerDef("SUB-BACKFILL", 34, "Continuous", 18, "Backfill hatch (earth/granular)"),
        # ── Superstructure ───────────────────────────────────────────────────────
        LayerDef("SUPER-DECK", 2, "Continuous", 50, "Deck slab top and bottom face"),
        LayerDef("SUPER-GIRDER", 1, "Continuous", 35, "Girder webs and flanges"),
        LayerDef("SUPER-PARAPET", 2, "Continuous", 35, "Parapet and railing outline"),
        LayerDef("SUPER-WEARING", 8, "Continuous", 25, "Wearing coat cross-section"),
        LayerDef("SUPER-CAMBER", 6, "DASHED", 18, "Pre-camber reference profile"),
        LayerDef("SUPER-KERB", 7, "Continuous", 25, "Kerb cross-section"),
        LayerDef("SUPER-FOOTPATH", 7, "Continuous", 25, "Footpath / pedestrian zone"),
        LayerDef("SUPER-CRASH", 1, "Continuous", 35, "Crash barrier / median barrier"),
        LayerDef("SUPER-DRAINAGE", 4, "Continuous", 18, "Deck drainage scupper and pipes"),
        # ── Dimensions & annotations ─────────────────────────────────────────────
        LayerDef("DIM-LINEAR", 3, "Continuous", 18, "Linear dimension strings"),
        LayerDef("DIM-LEADER", 3, "Continuous", 18, "Leader lines and callouts"),
        LayerDef("DIM-LEVEL", 3, "Continuous", 18, "Level / RL annotation arrows"),
        LayerDef("DIM-CHAINAGE", 3, "Continuous", 18, "Chainage annotation"),
        LayerDef("DIM-SLOPE", 3, "Continuous", 18, "Slope / gradient ratio labels"),
        # ── Text ─────────────────────────────────────────────────────────────────
        LayerDef("TEXT-GENERAL", 7, "Continuous", 18, "General notes and labels"),
        LayerDef("TEXT-TITLE", 7, "Continuous", 25, "Title block text"),
        LayerDef("TEXT-HEADER", 7, "Continuous", 25, "Sheet header / zone label"),
        LayerDef("TEXT-LEVEL", 5, "Continuous", 18, "Reduced level tags (+RL)"),
        LayerDef("TEXT-SPEC", 7, "Continuous", 13, "Specification notes (small)"),
        # ── Title block & border ─────────────────────────────────────────────────
        LayerDef("BORDER-OUTER", 7, "Continuous", 70, "Sheet outer border"),
        LayerDef("BORDER-INNER", 7, "Continuous", 35, "Sheet inner border / margin"),
        LayerDef("TITLEBLK-BOX", 7, "Continuous", 50, "Title block cell outlines"),
        LayerDef("TITLEBLK-TEXT", 7, "Continuous", 18, "Title block text fields"),
        LayerDef("TITLEBLK-LOGO", 7, "Continuous", 25, "Client / consultant logo area"),
        # ── Symbols & references ─────────────────────────────────────────────────
        LayerDef("SYM-NORTHARROW", 7, "Continuous", 18, "North arrow symbol"),
        LayerDef("SYM-SECTIONMARK", 1, "Continuous", 18, "Section A-A cut markers"),
        LayerDef("SYM-REVISION", 6, "Continuous", 18, "Revision cloud / delta markers"),
        LayerDef("SYM-SCALE", 7, "Continuous", 13, "Graphic scale bar"),
        # ── Miscellaneous ────────────────────────────────────────────────────────
        LayerDef("MISC-GRID", 8, "DASHED", 13, "Construction grid / reference"),
        LayerDef("MISC-SETOUT", 5, "CENTER2", 13, "Set-out points and traverse"),
        LayerDef("MISC-DEFPOINTS", 7, "Continuous", 0, "Definition points (non-printing)"),
        LayerDef("0", 7, "Continuous", 25, "Default layer (ezdxf baseline)"),
    ]
}

# Short aliases used by drawing modules
L = LAYER_REGISTRY  # e.g.  L["STRUC-OUTLINE"]

# Grouped sets for quick access
STRUCTURAL_LAYERS = {k: v for k, v in L.items() if k.startswith("STRUC")}
ANNOTATION_LAYERS = {k: v for k, v in L.items() if k.startswith(("DIM", "TEXT"))}
TITLEBLOCK_LAYERS = {k: v for k, v in L.items() if k.startswith(("BORDER", "TITLEBLK"))}


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
        if ld.linetype not in ("Continuous",) and not doc.linetypes.has_entry(ld.linetype):
            with contextlib.suppress(Exception):  # ezdxf may have it built-in
                doc.linetypes.add(ld.linetype)


# ---------------------------------------------------------------------------
# Short-name layers used by the sheet builders and the DXF contract tests.
# These are additive aliases: the IRC SP:55 long names above remain canonical.
# ---------------------------------------------------------------------------
LAYER_REGISTRY.update(
    {
        "DECK": LayerDef("DECK", 7, "Continuous", 50, "Deck line on sections and elevations"),
        "GRND": LayerDef("GRND", 8, "DASHED", 18, "Natural ground profile"),
        "TEXT": LayerDef("TEXT", 7, "Continuous", 13, "Generic annotation text"),
        "GRID": LayerDef("GRID", 8, "DASHED", 13, "Construction grid / reference lines"),
        "CL": LayerDef("CL", 6, "CENTER", 18, "Centre lines (piers, axes)"),
        "HIDD": LayerDef("HIDD", 8, "HIDDEN", 18, "Hidden / below-section-plane lines"),
        "DIM": LayerDef("DIM", 3, "Continuous", 18, "Dimension strings"),
        "HTCH": LayerDef("HTCH", 8, "Continuous", 18, "Hatching (concrete, soil, section)"),
        "TABL": LayerDef("TABL", 7, "Continuous", 18, "Schedule / table outlines and text"),
    }
)

# Alias exported for the tests' layer registry lookups.
LAYERS = LAYER_REGISTRY

# ---------------------------------------------------------------------------
# ISO 13567-2 naming — W07 deliverable
# ---------------------------------------------------------------------------
# The canonical names above are the IRC SP:55 spelling used inside the product.
# A foreign CAD system (and a reviewer auditing a transmittal) filters layers by
# *agent*, *discipline* and *revision status*, which is exactly the field
# decomposition ISO 13567-2:1998 defines:
#
#     <Agent> - <MajorGroup> - <MinorGroup> - <Status>
#
# The mapping is explicit rather than derived: auto-truncating ``TEXT-LEVEL``
# and ``DIM-LEVEL`` to three characters produces the same code for two different
# concepts, and a layer scheme whose codes collide is worse than no scheme.
# ``scripts/audit_layers.py`` fails the build if a registry layer has no entry
# here, if two layers claim the same ISO name, or if a name leaves the pattern.

#: ISO 13567 Agent — the author of the drawing. One author, one agent.
ISO_13567_AGENT = "B"

#: ISO 13567 Status — ``N`` = new (current) work. Superseded layers get their
#: own status letter when a revision introduces them.
ISO_13567_STATUS = "N"

#: ISO 13567-2 name per canonical layer. ``"0"`` is deliberately absent: it is
#: the CAD baseline layer, not a project layer, and carries no geometry.
ISO_13567_NAMES: dict[str, str] = {
    # ── Structural ───────────────────────────────────────────────────────────
    "STRUC-OUTLINE": "B-STR-OUC-N",
    "STRUC-HIDDEN": "B-STR-HID-N",
    "STRUC-CENTRE": "B-STR-CLN-N",
    "STRUC-SECTION": "B-STR-SEC-N",
    "STRUC-HATCHING": "B-STR-HAT-N",
    "STRUC-DETAIL": "B-STR-DET-N",
    # ── Civil / ground ───────────────────────────────────────────────────────
    "CIVIL-GROUND": "B-CIV-GND-N",
    "CIVIL-HFL": "B-CIV-HFL-N",
    "CIVIL-LWL": "B-CIV-LWL-N",
    "CIVIL-SCOUR": "B-CIV-SCO-N",
    "CIVIL-ROAD": "B-CIV-ROD-N",
    "CIVIL-CHAINAGE": "B-CIV-CHN-N",
    "CIVIL-CONTOUR": "B-CIV-CON-N",
    # ── Foundation ───────────────────────────────────────────────────────────
    "FOUND-PILE": "B-FND-PIL-N",
    "FOUND-CAP": "B-FND-CAP-N",
    "FOUND-WELL": "B-FND-WEL-N",
    "FOUND-OPEN": "B-FND-OPE-N",
    "FOUND-SOIL": "B-FND-SOI-N",
    # ── Substructure ─────────────────────────────────────────────────────────
    "SUB-PIER": "B-SUB-PIE-N",
    "SUB-ABUT": "B-SUB-ABT-N",
    "SUB-BEARING": "B-SUB-BEA-N",
    "SUB-EXPJOINT": "B-SUB-EXJ-N",
    "SUB-BACKFILL": "B-SUB-BKF-N",
    # ── Superstructure ───────────────────────────────────────────────────────
    "SUPER-DECK": "B-SUP-DCK-N",
    "SUPER-GIRDER": "B-SUP-GIR-N",
    "SUPER-PARAPET": "B-SUP-PAR-N",
    "SUPER-WEARING": "B-SUP-WEA-N",
    "SUPER-CAMBER": "B-SUP-CAM-N",
    "SUPER-KERB": "B-SUP-KER-N",
    "SUPER-FOOTPATH": "B-SUP-FTP-N",
    "SUPER-CRASH": "B-SUP-CRS-N",
    "SUPER-DRAINAGE": "B-SUP-DRA-N",
    # ── Dimensions ───────────────────────────────────────────────────────────
    "DIM-LINEAR": "B-ANN-DIM-N",
    "DIM-LEADER": "B-ANN-LDR-N",
    "DIM-LEVEL": "B-ANN-LVL-N",
    "DIM-CHAINAGE": "B-ANN-DCH-N",
    "DIM-SLOPE": "B-ANN-SLP-N",
    # ── Text ─────────────────────────────────────────────────────────────────
    "TEXT-GENERAL": "B-ANN-GEN-N",
    "TEXT-TITLE": "B-ANN-TTL-N",
    "TEXT-HEADER": "B-ANN-HDR-N",
    "TEXT-LEVEL": "B-ANN-LVT-N",
    "TEXT-SPEC": "B-ANN-SPC-N",
    # ── Border & title block ─────────────────────────────────────────────────
    "BORDER-OUTER": "B-FRM-BOR-N",
    "BORDER-INNER": "B-FRM-BRN-N",
    "TITLEBLK-BOX": "B-FRM-TBB-N",
    "TITLEBLK-TEXT": "B-FRM-TBT-N",
    "TITLEBLK-LOGO": "B-FRM-TBL-N",
    # ── Symbols ──────────────────────────────────────────────────────────────
    "SYM-NORTHARROW": "B-SYM-NAR-N",
    "SYM-SECTIONMARK": "B-SYM-SMK-N",
    "SYM-REVISION": "B-SYM-REV-N",
    "SYM-SCALE": "B-SYM-SCL-N",
    # ── Miscellaneous ────────────────────────────────────────────────────────
    "MISC-GRID": "B-GEN-GRD-N",
    "MISC-SETOUT": "B-GEN-SET-N",
    "MISC-DEFPOINTS": "B-GEN-DEF-N",
    # ── Short aliases used by the sheet builders ─────────────────────────────
    "DECK": "B-SUP-DKD-N",
    "GRND": "B-CIV-GRD-N",
    "TEXT": "B-ANN-TXT-N",
    "GRID": "B-GEN-GRI-N",
    "CL": "B-ANN-CLN-N",
    "HIDD": "B-STR-HDD-N",
    "DIM": "B-ANN-DIN-N",
    "HTCH": "B-STR-HTC-N",
    "TABL": "B-ANN-TAB-N",
}


def iso13567_name(layer: str) -> str:
    """ISO 13567-2 structured name for a canonical layer, or ``""`` if none.

    An empty string is a defect, not a fallback: the audit script reports it.
    """
    return ISO_13567_NAMES.get(layer, "")


#: ``<Agent>-<MajorGroup>-<MinorGroup>-<Status>`` — 1–2 letter agent, three
#: alphanumeric element codes, a one-letter status.
ISO_13567_PATTERN = re.compile(r"^[A-Z]{1,2}(?:-[A-Z0-9]{3}){2}-[A-Z]$")

#: ISO 128 line-weight series (in hundredths of a millimetre). A layer weight
#: outside this set is not a drafting decision, it is a typo.
ISO_128_LINEWEIGHTS: frozenset[int] = frozenset({0, 9, 13, 18, 25, 35, 50, 70, 100, 140, 200})

__all__ = [
    "LayerDef",
    "LAYER_REGISTRY",
    "LAYERS",
    "L",
    "setup_layers",
    "STRUCTURAL_LAYERS",
    "ANNOTATION_LAYERS",
    "TITLEBLOCK_LAYERS",
    "ISO_13567_AGENT",
    "ISO_13567_STATUS",
    "ISO_13567_NAMES",
    "ISO_13567_PATTERN",
    "ISO_128_LINEWEIGHTS",
    "iso13567_name",
]
