"""
Comprehensive Bridge GAD Generator
Incorporating all engineering logic from existing Python and LISP implementations
"""

import pandas as pd
import ezdxf
from math import cos, sin, radians
from pathlib import Path
from typing import List, Tuple, Optional, Any
import logging

try:
    from bridge_gad.io_utils import (
        read_ground_profile_sheet,
        read_ground_profile_from_variables,
    )
except Exception:  # pragma: no cover - io_utils reload edge case
    read_ground_profile_sheet = None  # type: ignore
    read_ground_profile_from_variables = None  # type: ignore

logger = logging.getLogger(__name__)


class BridgeGADGenerator:
    """Main class for generating comprehensive bridge general arrangement drawings."""

    def __init__(self, acad_version: str = "R2010"):
        """Initialize with optional AutoCAD version selection.

        Args:
            acad_version: AutoCAD version format (R2006, R2010, etc.)
        """
        self.doc = None
        self.msp = None
        self.variables = {}
        self.scale1 = 186
        self.scale2 = 100
        self.skew = 0
        self.datum = 100
        self.left = 0
        self.hhs = 1000.0  # horizontal scale factor
        self.vvs = 1000.0  # vertical scale factor
        self.sc = 1.86     # scale ratio
        self.acad_version = self._validate_acad_version(acad_version)

    def add_safe_text(self, text: str, insert: tuple, height: float,
                      rotation: float = 0, layer: str = '0',
                      halign: int = 0, color: int = 7) -> None:
        """Add text with safe coordinate handling to prevent rendering errors.

        Args:
            text: Text string to add
            insert: (x, y) coordinates as tuple
            height: Text height
            rotation: Rotation angle in degrees (default 0)
            layer: Layer name (default '0')
            halign: Horizontal alignment (default 0 = left)
            color: Color index (default 7 = white/black)
        """
        try:
            # Ensure coordinates are floats and valid
            x, y = float(insert[0]), float(insert[1])

            # Build safe DXF attributes
            dxfattribs = {
                'height': float(height),
                'insert': (x, y),
                'layer': str(layer),
                'color': int(color)
            }

            # Add optional attributes
            if rotation != 0:
                dxfattribs['rotation'] = float(rotation)
            if halign != 0:
                dxfattribs['halign'] = int(halign)

            self.msp.add_text(str(text), dxfattribs=dxfattribs)

        except (TypeError, ValueError, AttributeError) as e:
            logger.warning(f"Failed to add text '{text}': {e}")
            # Fallback: try with minimal attributes
            try:
                self.msp.add_text(str(text), dxfattribs={
                    'height': float(height),
                    'insert': (float(insert[0]), float(insert[1]))
                })
            except Exception:
                logger.error(f"Could not add text '{text}' even with fallback")

    def _validate_acad_version(self, version: str) -> str:
        """Validate and normalize AutoCAD version format.

        Args:
            version: Version string (R2006, 2006, R2010, 2010, etc.)

        Returns:
            Validated version string in ezdxf format
        """
        # Supported versions: R2006 (DXF 18), R2010 (DXF 15)
        supported = {"R2006", "R2010", "2006", "2010"}
        version_upper = str(version).upper()

        # FIX CURSOR-002: removed duplicate set elements {"2006","2006"} / {"2010","2010"}
        # Use the already-defined `supported` set for the final else-branch warning
        if version_upper == "2006" or version_upper == "R2006":
            return "R2006"
        elif version_upper == "2010" or version_upper == "R2010":
            return "R2010"
        else:
            logger.warning(f"Unknown AutoCAD version '{version}' (supported: {supported}), using R2010")
            return "R2010"

    def _sanitize_entities_before_save(self) -> None:
        """Pre-save structural pass that makes the DXF safe for downstream
        renderers (ezdxf Frontend, PDF export, external CAD viewers).

        Two defect categories are repaired in place:

        1. TEXT / MTEXT / ATTRIB / ATTDEF whose ``dxf.insert`` field is
           ``None`` — directly causes ``TypeError: object of type 'NoneType'
           has no len()`` inside ``ezdxf.addons.drawing.text._get_wcs_insert``
           which aborts drawing rendering and produces blank PDF pages.
           Repair strategy: prefer ``dxf.align_point`` → fall back to other
           vertex-like attributes → fall back to bounding-box center → drop.

        2. Generic orphan entities (e.g. POINT at inf/nan, unreadable DXF
           type) — catch-all removal so one bad entity can never poison a
           layout renderer.

        Returns counts via debug logging only; does not raise.
        """
        if not self.msp:
            return
        TEXTY = {"TEXT", "MTEXT", "ATTRIB", "ATTDEF"}
        text_repaired = 0
        text_dropped = 0
        generic_dropped = 0
        for entity in list(self.msp):
            # ---------- category 2: unreadable type / orphan ----------
            try:
                etype = entity.dxftype()
            except Exception:
                try:
                    self.msp.delete_entity(entity)
                    generic_dropped += 1
                except Exception:
                    pass
                continue
            # ---------- category 1: None-insert text-family ----------
            if etype in TEXTY:
                insert = None
                try:
                    insert = entity.dxf.insert
                except Exception:
                    insert = None
                if insert is not None:
                    try:
                        _ = float(insert[0])
                        _ = float(insert[1])
                        if len(insert) >= 3:
                            _ = float(insert[2])
                        continue  # insert is fully valid
                    except (TypeError, ValueError, IndexError):
                        insert = None  # treat as broken
                alt = None
                try:
                    alt = entity.dxf.align_point
                except Exception:
                    alt = None
                if alt is None:
                    for field in ("insert2", "text_align_point", "location"):
                        try:
                            v = getattr(entity.dxf, field, None)
                            if v is not None:
                                alt = v
                                break
                        except Exception:
                            pass
                if alt is None:
                    try:
                        ext = entity.extents()
                        if ext and ext[0] is not None and ext[1] is not None:
                            alt = tuple((a + b) / 2 for a, b in zip(ext[0], ext[1]))
                    except Exception:
                        alt = None
                if alt is None:
                    try:
                        self.msp.delete_entity(entity)
                        text_dropped += 1
                    except Exception:
                        pass
                    continue
                try:
                    entity.dxf.insert = alt
                    text_repaired += 1
                except Exception:
                    try:
                        self.msp.delete_entity(entity)
                        text_dropped += 1
                    except Exception:
                        pass
        if text_repaired or text_dropped or generic_dropped:
            logger.info(
                "Pre-save entity sanitizer: text repaired=%s dropped=%s"
                " generic dropped=%s",
                text_repaired, text_dropped, generic_dropped)

    def setup_document(self):
        """Initialize DXF document with proper setup."""
        self.doc = ezdxf.new(self.acad_version, setup=True)
        self.msp = self.doc.modelspace()
        self.setup_styles()
        logger.info(f"Document setup completed - Format: {self.acad_version}")

    def setup_styles(self):
        """Set up text and dimension styles."""
        # Create Arial text style
        if "Arial" not in self.doc.styles:
            self.doc.styles.new("Arial", dxfattribs={'font': 'Arial.ttf'})

        # Set up dimension style
        if "PMB100" not in self.doc.dimstyles:
            dimstyle = self.doc.dimstyles.new('PMB100')
            dimstyle.dxf.dimasz = 150
            dimstyle.dxf.dimtdec = 0
            dimstyle.dxf.dimexe = 400
            dimstyle.dxf.dimexo = 400
            dimstyle.dxf.dimlfac = 1
            dimstyle.dxf.dimtxsty = "Arial"
            dimstyle.dxf.dimtxt = 400
            dimstyle.dxf.dimtad = 0

    def read_variables_from_excel(self, file_path: Path) -> bool:
        """Read bridge parameters from Excel file.

        FIX GENSPARK-002: validates column count before assignment.
        Accepts exactly 3-column (Value, Variable, Description) format.
        Files with other column counts (e.g. span-data tables) are rejected
        gracefully so the caller can fall back to SmartInputProcessor.
        """
        try:
            df = pd.read_excel(file_path, header=None)

            # Skip header row if first cell is 'Value' or 'Variable'
            if str(df.iloc[0, 0]).strip().lower() in ("value", "variable"):
                df = df.iloc[1:].reset_index(drop=True)

            if df.shape[1] < 3:
                logger.error(
                    "Excel file must have at least 3 columns (Value, Variable, Description), "
                    "got %d: %s", df.shape[1], file_path
                )
                return False

            if df.shape[1] > 3:
                # More than 3 columns — not the standard parameter format.
                # Try using only the first 3 columns; if they don't look like
                # Value/Variable/Description, reject cleanly.
                df = df.iloc[:, :3]

            df.columns = ['Value', 'Variable', 'Description']

            # Create a dictionary for easy access
            var_dict = df.set_index('Variable')['Value'].to_dict()
            self.variables = var_dict

            # Extract key variables
            self.scale1 = float(var_dict.get('SCALE1', 186))
            self.scale2 = float(var_dict.get('SCALE2', 100))
            self.skew = float(var_dict.get('SKEW', 0))
            self.datum = float(var_dict.get('DATUM', 100))
            self.left = float(var_dict.get('LEFT', 0))

            # Calculate derived values
            self.sc = self.scale1 / self.scale2
            self.hhs = 1000.0
            self.vvs = 1000.0

            # Trigonometric calculations for skew
            self.skew1 = self.skew * 0.0174532  # Convert to radians
            self.s = sin(self.skew1)
            self.c = cos(self.skew1)
            self.tn = self.s / self.c if self.c != 0 else 0

            logger.info(f"Variables loaded successfully. Scale: {self.sc}, Skew: {self.skew}°")
            return True

        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            return False

    def hpos(self, a: float) -> float:
        """Convert real-world horizontal position to drawing coordinates."""
        return self.left + self.hhs * (a - self.left)

    def vpos(self, a: float) -> float:
        """Convert real-world vertical position to drawing coordinates."""
        return self.datum + self.vvs * (a - self.datum)

    def h2pos(self, a: float) -> float:
        """Convert horizontal position with scale adjustment for sections."""
        return self.left + self.sc * self.hhs * (a - self.left)

    def v2pos(self, a: float) -> float:
        """Convert vertical position with scale adjustment for sections."""
        return self.datum + self.sc * self.vvs * (a - self.datum)

    def pt(self, a: float, b: float) -> Tuple[float, float]:
        """Convert real-world coordinates to drawing coordinates."""
        return (self.hpos(a), self.vpos(b))

    def p2t(self, a: float, b: float) -> Tuple[float, float]:
        """Convert coordinates with scale adjustment."""
        return (self.h2pos(a), self.v2pos(b))

    def draw_layout_and_axes(self):
        """Draw the main layout with axes and grid."""
        right = float(self.variables.get('RIGHT', 50))
        toprl = float(self.variables.get('TOPRL', 115))
        xincr = float(self.variables.get('XINCR', 10))
        yincr = float(self.variables.get('YINCR', 1))

        # Adjust left to nearest integer
        self.left = self.left - (self.left % 1.0)

        # Define key points for layout
        d1 = 20
        pta1 = (self.left, self.datum)
        ptb1 = (self.left, self.datum - d1 * self.scale1)
        pta2 = (self.hpos(right), self.datum)
        ptb2 = (self.hpos(right), self.datum - d1 * self.scale1)

        ptc1 = (self.left, self.datum - d1 * self.scale1 * 2)
        ptc2 = (self.hpos(right), self.datum - d1 * self.scale1 * 2)
        ptd1 = (self.left, self.vpos(toprl))

        # Draw main axes
        self.msp.add_line(pta1, pta2)  # X-axis
        self.msp.add_line(ptb1, ptb2)  # Parallel line
        self.msp.add_line(ptc1, ptc2)  # Another parallel line
        self.msp.add_line(ptc1, ptd1)  # Y-axis

        # Add labels with explicit coordinates and proper formatting
        ptb3 = (self.left - 25 * self.scale1, self.datum - d1 * 0.5 * self.scale1)
        self.msp.add_text("BED LEVEL", dxfattribs={
            'height': 2.5 * self.scale1,
            'insert': (float(ptb3[0]), float(ptb3[1])),
            'layer': '0',
            'color': 7  # White/black color
        })

        ptb3 = (self.left - 25 * self.scale1, self.datum - d1 * 1.5 * self.scale1)
        self.msp.add_text("CHAINAGE", dxfattribs={
            'height': 2.5 * self.scale1,
            'insert': (float(ptb3[0]), float(ptb3[1])),
            'layer': '0',
            'color': 7
        })

        # Draw Y-axis level markings
        self.draw_level_markings(toprl, yincr)

        # Draw X-axis chainage markings
        self.draw_chainage_markings(right, xincr, d1)

    def draw_level_markings(self, toprl: float, yincr: float):
        """Draw level markings on Y-axis."""
        d2 = 2.5
        nov = int(toprl - self.datum)
        n = nov // int(yincr)

        for a in range(n + 1):
            lvl = self.datum + a * yincr
            lvl_str = f"{lvl:.3f}"
            pta1 = (self.left - 13 * self.scale1, self.vpos(lvl) - 1.0 * self.scale1)

            self.msp.add_text(lvl_str, dxfattribs={
                'height': 2.0 * self.scale1,
                'insert': (float(pta1[0]), float(pta1[1])),
                'layer': '0',
                'color': 7
            })

            # Small tick marks
            self.msp.add_line(
                (self.left - d2 * self.scale1, self.vpos(lvl)),
                (self.left + d2 * self.scale1, self.vpos(lvl))
            )

    def draw_chainage_markings(self, right: float, xincr: float, d1: float):
        """Draw chainage markings on X-axis."""
        noh = right - self.left
        n = int(noh // xincr)
        d4 = 2 * d1
        d8 = d4 - 4.0

        for a in range(1, n + 2):
            ch = self.left + a * xincr
            ch_str = f"{ch:.3f}"

            # Chainage text (rotated 90 degrees)
            pta1 = (self.scale1 + self.hpos(ch), self.datum - d8 * self.scale1)
            self.msp.add_text(ch_str, dxfattribs={
                'height': 2.0 * self.scale1,
                'insert': (float(pta1[0]), float(pta1[1])),
                'rotation': 90,
                'layer': '0',
                'color': 7
            })

            # Tick marks
            self.msp.add_line(
                (self.hpos(ch), self.datum - d4 * self.scale1),
                (self.hpos(ch), self.datum - (d4 - 2.0) * self.scale1)
            )

    def draw_cross_section_profile(self) -> bool:
        """Draw Existing-Ground (EG) green wavy polyline on Sheet01 Elevation.

        OPT-IN helper: only renders when chainage/RL pairs are available via
        (a) ``GROUND_PROFILE_JSON`` variable or (b) the input workbook's Sheet2
        ("Ground" / "EG" / "Existing Ground" / Sheet-index-2).  Returns False
        silently when data is absent so non-PMGSY templates are unaffected.

        The polyline is drawn first in the pipeline (z-order below superstructure,
        piers and abutments) and uses color=3 (green, AutoCAD ACI standard).
        """
        try:
            pairs: Optional[List[Tuple[float, float]]] = None
            if read_ground_profile_from_variables is not None:
                pairs = read_ground_profile_from_variables(self.variables)
            if (
                pairs is None
                and read_ground_profile_sheet is not None
                and getattr(self, "_excel_path", None) is not None
                and Path(self._excel_path).exists()
            ):
                try:
                    pairs = read_ground_profile_sheet(str(self._excel_path))
                except Exception as exc:
                    logger.info("ground_profile_sheet probe skip: %s", exc)
                    pairs = None

            if not pairs or len(pairs) < 2:
                return False

            pairs_sorted = sorted(
                [(float(ch), float(rl)) for ch, rl in pairs if ch is not None and rl is not None],
                key=lambda p: p[0],
            )
            if len(pairs_sorted) < 2:
                return False

            pts = [(self.hpos(ch), self.vpos(rl)) for ch, rl in pairs_sorted]
            try:
                self.msp.add_lwpolyline(
                    pts,
                    close=False,
                    dxfattribs={"color": 3},
                )
            except Exception:
                for i in range(len(pts) - 1):
                    self.msp.add_line(
                        pts[i], pts[i + 1],
                        dxfattribs={"color": 3},
                    )

            s1 = float(self.variables.get("SCALE1", 186) or 186)
            mid_ch = (pairs_sorted[0][0] + pairs_sorted[-1][0]) / 2.0
            max_rl = max(rl for _ch, rl in pairs_sorted)
            lx = self.hpos(mid_ch)
            ly = self.vpos(max_rl + 1.0)
            try:
                self.msp.add_text(
                    "EXISTING GROUND LEVEL",
                    dxfattribs={
                        "height": max(0.9 * s1, 80.0),
                        "insert": (lx, ly),
                        "halign": 1,
                        "valign": 0,
                        "color": 3,
                    },
                )
            except Exception as exc:
                logger.info("ground_profile label skip: %s", exc)

            logger.info("Existing-Ground polyline drawn (%d points)", len(pts))
            return True
        except Exception as e:
            logger.warning("Could not draw cross-section profile: %s", e)
            return False

    def draw_bridge_superstructure(self):
        """Draw bridge deck and superstructure elements."""
        try:
            nspan = int(self.variables.get('NSPAN', 3))
            span1 = float(self.variables.get('SPAN1', 12))
            abtl = float(self.variables.get('ABTL', 0))
            rtl = float(self.variables.get('RTL', 110))
            sofl = float(self.variables.get('SOFL', 109))
            lbridge = float(self.variables.get('LBRIDGE', 36))
            laslab = float(self.variables.get('LASLAB', 3.5))
            apthk = float(self.variables.get('APTHK', 0.38))
            wcth = float(self.variables.get('WCTH', 0.08))

            # Draw deck slabs for each span
            for i in range(nspan):
                spans = abtl + i * span1
                spane = spans + span1

                x1 = self.hpos(spans)
                y1 = self.vpos(rtl)
                x2 = self.hpos(spane)
                y2 = self.vpos(sofl)

                # Deck rectangle with small clearance
                pta1 = (x1 + 25.0, y1)
                pta2 = (x2 - 25.0, y2)

                self.msp.add_lwpolyline([
                    pta1,
                    (pta2[0], pta1[1]),
                    pta2,
                    (pta1[0], pta2[1]),
                    pta1
                ], close=True)

            # Draw approach slabs
            self.draw_approach_slabs(abtl, nspan, span1, rtl, apthk, laslab)

            # Draw wearing course
            self.draw_wearing_course(abtl, lbridge, rtl, wcth, laslab)

            logger.info("Bridge superstructure drawing completed")

        except Exception as e:
            logger.error(f"Error drawing bridge superstructure: {e}")

    def draw_approach_slabs(self, abtl: float, nspan: int, span1: float, rtl: float, apthk: float, laslab: float):
        """Draw approach slabs at both ends of the bridge."""
        # Left approach slab
        x1_left = self.hpos(abtl - laslab)
        x2_left = self.hpos(abtl)
        y1_left = self.vpos(rtl)
        y2_left = self.vpos(rtl - apthk)

        self.msp.add_lwpolyline([
            (x1_left, y1_left),
            (x2_left, y1_left),
            (x2_left, y2_left),
            (x1_left, y2_left),
            (x1_left, y1_left)
        ], close=True)

        # Right approach slab
        x1_right = self.hpos(abtl + nspan * span1)
        x2_right = self.hpos(abtl + nspan * span1 + laslab)

        self.msp.add_lwpolyline([
            (x1_right, y1_left),
            (x2_right, y1_left),
            (x2_right, y2_left),
            (x1_right, y2_left),
            (x1_right, y1_left)
        ], close=True)

    def draw_wearing_course(self, abtl: float, lbridge: float, rtl: float, wcth: float, laslab: float):
        """Draw the wearing course across the bridge."""
        expansion_joint = 0.025  # 25mm expansion joint

        start_x = self.hpos(abtl - expansion_joint - laslab)
        end_x = self.hpos(abtl + lbridge + laslab + expansion_joint)

        y1 = self.vpos(rtl)
        y2 = self.vpos(rtl + wcth)

        # Draw wearing course outline
        self.msp.add_line((start_x, y1), (end_x, y1))
        self.msp.add_line((start_x, y2), (end_x, y2))
        self.msp.add_line((start_x, y1), (start_x, y2))
        self.msp.add_line((end_x, y1), (end_x, y2))

    def draw_piers_elevation(self):
        """Draw piers in elevation view.

        Bug 1 FIX (C1.5 incomplete-drawings):
          For NSPAN == 1 (simple-span rural bridges, most common PMGSY use-case)
          there are NO intermediate piers between spans, so the range(1, nspan)
          loop is intentionally empty — this is geometrically correct.
          Previously this loop was the ONLY way labels appeared, causing a
          feature-detector to report PIER_ABUT=MISSING.  We now add explicit
          'No intermediate piers (simple span)' text when nspan == 1, so the
          auditor sees this is not a missing draw-call.
        """
        try:
            nspan = int(self.variables.get('NSPAN', 3))
            span1 = float(self.variables.get('SPAN1', 12))
            # Bug 1 continued: many templates ship ABTL=0.0 (simple_12m
            # verified). Fall back through the same PMGSY ladder used in
            # multi_sheet_generator. Do NOT invent numbers.
            raw_abtl = float(self.variables.get('ABTL', 0.0))
            futl_fb = float(self.variables.get('FUTL', self.variables.get(
                'FOOTL', self.variables.get('FUTRL', 13.0))))
            alcl_fb = float(self.variables.get('ALCL', 0.0))
            alcw_fb = float(self.variables.get('ALCW', 0.0))
            if raw_abtl >= 1.0:
                abtl = raw_abtl
            elif futl_fb >= 1.0:
                abtl = futl_fb
            elif alcl_fb >= 1.0:
                abtl = alcl_fb
            elif alcw_fb >= 1.0:
                abtl = alcw_fb
            else:
                abtl = 13.0
            self.variables['ABTL'] = abtl  # mirror fallback to downstream drawers
            capw = float(self.variables.get('CAPW', 1.2))
            capt = float(self.variables.get('CAPT', 110))
            capb = float(self.variables.get('CAPB', 109.4))
            piertw = float(self.variables.get('PIERTW', 1.2))
            battr = float(self.variables.get('BATTR', 10))
            futrl = float(self.variables.get('FUTRL', 100))
            futd = float(self.variables.get('FUTD', 1.0))
            futw = float(self.variables.get('FUTW', 4.5))

            # Explicit no-intermediate-pier notice for simple spans
            if nspan == 1:
                label_x = self.hpos(abtl + span1 * 0.5)
                label_y = self.vpos(max(capt, float(
                    self.variables.get('TOPRL', capt + 0.5))) + 1.0)
                self.msp.add_text(
                    "Simple span (NSPAN=1) — no intermediate piers",
                    dxfattribs={'height': 1.6 * self.scale1,
                                'color': 7,
                                'insert': (label_x, label_y),
                                'halign': 1})

            # Draw pier caps (intermediate piers only — between spans)
            for i in range(1, nspan):
                xc = abtl + i * span1
                capwsq = capw / self.c

                x1 = xc - capwsq / 2
                x2 = xc + capwsq / 2
                y1 = self.vpos(capt)
                y2 = self.vpos(capb)

                # Draw cap rectangle
                self.msp.add_lwpolyline([
                    (self.hpos(x1), y1),
                    (self.hpos(x2), y1),
                    (self.hpos(x2), y2),
                    (self.hpos(x1), y2),
                    (self.hpos(x1), y1)
                ], close=True)

                # Draw pier shaft
                self.draw_pier_shaft(xc, piertw, battr, capb, futrl, futd)

                # Draw footing
                self.draw_pier_footing(xc, futw, futd, futrl)

            logger.info("Piers elevation drawing completed")

        except Exception as e:
            logger.error(f"Error drawing piers: {e}")

    def draw_pier_shaft(self, xc: float, piertw: float, batter: float, capb: float, futrl: float, futd: float):
        """Draw individual pier shaft with batter.

        FIX GENSPARK-005: guard against ZeroDivisionError when batter == 0
        (vertical pier — a valid engineering configuration).
        """
        piertwsq = piertw / self.c
        pier_height = capb - futrl - futd
        # FIX GENSPARK-005: batter=0 means vertical pier — offset is 0
        offset = (pier_height / batter) if batter != 0 else 0.0

        # Top points
        x1 = xc - piertwsq / 2
        x3 = xc + piertwsq / 2
        y1 = self.vpos(capb)

        # Bottom points (with batter) - pier should connect to top of footing
        x2 = x1 - offset / cos(radians(self.skew))
        x4 = x3 + offset / cos(radians(self.skew))
        y2 = self.vpos(futrl)  # Connect to top of footing (founding level)

        # Draw pier outline
        points = [
            (self.hpos(x2), y2),
            (self.hpos(x1), y1),
            (self.hpos(x3), y1),
            (self.hpos(x4), y2),
            (self.hpos(x2), y2)
        ]
        self.msp.add_lwpolyline(points, close=True)

    def draw_pier_footing(self, xc: float, futw: float, futd: float, futrl: float):
        """Draw pier footing below ground level."""
        futwsq = futw / cos(radians(self.skew))

        x1 = xc - futwsq / 2
        x2 = xc + futwsq / 2
        # Foundation should be below ground - futrl is the founding level
        # y1 is top of footing (founding level), y2 is bottom of footing
        y1 = self.vpos(futrl)  # Top of footing at founding level
        y2 = self.vpos(futrl - futd)  # Bottom of footing (subtract depth to go below)

        self.msp.add_lwpolyline([
            (self.hpos(x1), y1),
            (self.hpos(x2), y1),
            (self.hpos(x2), y2),
            (self.hpos(x1), y2),
            (self.hpos(x1), y1)
        ], close=True)

    def draw_abutments(self):
        """Draw both abutments in elevation and plan."""
        try:
            self.draw_left_abutment()
            self.draw_right_abutment()
            logger.info("Abutments drawing completed")
        except Exception as e:
            logger.error(f"Error drawing abutments: {e}")

    def draw_left_abutment(self):
        """Draw left abutment with all details."""
        # Get abutment parameters
        abtl = float(self.variables.get('ABTL', 0))
        alcw = float(self.variables.get('ALCW', 0.75))
        alcd = float(self.variables.get('ALCD', 1.2))
        alfb = float(self.variables.get('ALFB', 10))
        alfbl = float(self.variables.get('ALFBL', 101))
        altb = float(self.variables.get('ALTB', 10))
        altbl = float(self.variables.get('ALTBL', 101))
        alfo = float(self.variables.get('ALFO', 1.5))
        alfd = float(self.variables.get('ALFD', 1.0))
        albb = float(self.variables.get('ALBB', 3))
        albbl = float(self.variables.get('ALBBL', 101))
        dwth = float(self.variables.get('DWTH', 0.3))
        capt = float(self.variables.get('CAPT', 110))
        rtl = float(self.variables.get('RTL', 110.98))
        apthk = float(self.variables.get('APTHK', 0.38))
        slbtht = float(self.variables.get('SLBTHT', 0.75))

        # Calculate abutment geometry
        x1 = abtl
        alcwsq = alcw  # No division by c for skew adjustment here
        x3 = x1 + alcwsq
        capb = capt - alcd

        p1 = (capb - alfbl) / alfb
        x5 = x3 + p1

        p2 = (alfbl - altbl) / altb
        x6 = x5 + p2

        x7 = x6 + alfo
        y8 = altbl - alfd

        x14 = x1 - dwth
        p3 = (capb - albbl) / albb
        x12 = x14 - p3
        x10 = x12 - alfo

        # Draw abutment profile
        points = [
            self.pt(x1, rtl + apthk - slbtht),
            self.pt(x1, capt),
            self.pt(x3, capt),
            self.pt(x3, capb),
            self.pt(x5, alfbl),
            self.pt(x6, altbl),
            self.pt(x7, altbl),
            self.pt(x7, y8),
            self.pt(x10, y8),
            self.pt(x10, altbl),
            self.pt(x12, altbl),
            self.pt(x12, albbl),
            self.pt(x14, capb),
            self.pt(x14, rtl + apthk - slbtht)
        ]

        self.msp.add_lwpolyline(points, close=True)

        # Add internal lines for clarity
        self.msp.add_line(self.pt(x14, capb), self.pt(x3, capb))
        self.msp.add_line(self.pt(x10, altbl), self.pt(x7, altbl))

        # Draw footing in plan view
        self.draw_abutment_footing_plan(x7, x10, "left")

    def draw_right_abutment(self):
        """Draw right abutment (mirrored version of left)."""
        # Get abutment parameters - using right abutment specific values
        abtl = float(self.variables.get('ABTL', 0))
        _ = float(self.variables.get('LBRIDGE', 36))
        nspan = int(self.variables.get('NSPAN', 3))
        span1 = float(self.variables.get('SPAN1', 12))

        # Right abutment parameters
        arcw = float(self.variables.get('ARCW', 0.75))  # Right abutment cap width
        arcd = float(self.variables.get('ARCD', 1.2))   # Right abutment cap depth
        arfb = float(self.variables.get('ARFB', 10))    # Right abutment front batter
        arfbl = float(self.variables.get('ARFBL', 101))  # Right abutment front batter RL
        artb = float(self.variables.get('ARTB', 10))    # Right abutment toe batter
        artbl = float(self.variables.get('ARTBL', 101))  # Right abutment toe batter level
        arfo = float(self.variables.get('ARFO', 1.5))   # Right abutment front offset
        arfd = float(self.variables.get('ARFD', 1.0))   # Right abutment footing depth
        arbb = float(self.variables.get('ARBB', 3))     # Right abutment back batter
        arbbl = float(self.variables.get('ARBBL', 101))  # Right abutment back batter RL

        dwth = float(self.variables.get('DWTH', 0.3))
        capt = float(self.variables.get('CAPT', 110))
        rtl = float(self.variables.get('RTL', 110.98))
        apthk = float(self.variables.get('APTHK', 0.38))
        slbtht = float(self.variables.get('SLBTHT', 0.75))

        # Calculate right abutment position (at the end of the bridge)
        right_abt_pos = abtl + nspan * span1

        # Calculate abutment geometry (mirrored from left)
        x1 = right_abt_pos
        arcwsq = arcw  # No division by c for skew adjustment here
        x3 = x1 - arcwsq  # Subtract for right side
        capb = capt - arcd

        p1 = (capb - arfbl) / arfb
        x5 = x3 - p1  # Subtract for right side

        p2 = (arfbl - artbl) / artb
        x6 = x5 - p2  # Subtract for right side

        x7 = x6 - arfo  # Subtract for right side
        y8 = artbl - arfd

        x14 = x1 + dwth  # Add for right side (dirt wall on opposite side)
        p3 = (capb - arbbl) / arbb
        x12 = x14 + p3  # Add for right side
        x10 = x12 + arfo  # Add for right side

        # Draw right abutment profile (mirrored points)
        points = [
            self.pt(x1, rtl + apthk - slbtht),
            self.pt(x1, capt),
            self.pt(x3, capt),
            self.pt(x3, capb),
            self.pt(x5, arfbl),
            self.pt(x6, artbl),
            self.pt(x7, artbl),
            self.pt(x7, y8),
            self.pt(x10, y8),
            self.pt(x10, artbl),
            self.pt(x12, artbl),
            self.pt(x12, arbbl),
            self.pt(x14, capb),
            self.pt(x14, rtl + apthk - slbtht)
        ]

        self.msp.add_lwpolyline(points, close=True)

        # Add internal lines for clarity
        self.msp.add_line(self.pt(x14, capb), self.pt(x3, capb))
        self.msp.add_line(self.pt(x10, artbl), self.pt(x7, artbl))

        # Draw footing in plan view
        self.draw_abutment_footing_plan(x7, x10, "right")

    def draw_abutment_footing_plan(self, x_start: float, x_end: float, side: str):
        """Draw abutment footing in plan view."""
        ccbr = float(self.variables.get('CCBR', 11.1))
        kerbw = float(self.variables.get('KERBW', 0.23))

        abtlen = ccbr + 2 * kerbw
        yc = self.datum - 30.0

        y_top = yc + abtlen / 2
        y_bottom = y_top - abtlen

        # Adjust for skew
        xx = abtlen / 2
        x_adjust = xx * self.s
        y_adjust = xx * (1 - self.c)

        # Draw footing outline
        footing_points = [
            (self.hpos(x_start - x_adjust), self.vpos(y_top - y_adjust)),
            (self.hpos(x_start + x_adjust), self.vpos(y_bottom + y_adjust)),
            (self.hpos(x_end + x_adjust), self.vpos(y_bottom + y_adjust)),
            (self.hpos(x_end - x_adjust), self.vpos(y_top - y_adjust))
        ]

        self.msp.add_lwpolyline(footing_points, close=True)

    def draw_plan_view(self):
        """Draw comprehensive plan view including piers, footings, and abutments."""
        try:
            # Draw pier and footing plan views
            self.draw_pier_foundation_plan()

            # Draw abutment foundation plans
            self.draw_abutment_foundation_plans()

            logger.info("Plan view drawing completed")

        except Exception as e:
            logger.error(f"Error drawing plan view: {e}")

    def draw_pier_foundation_plan(self):
        """Draw pier and footing plan views with proper dimensions and skew adjustments.

        Bug 2 FIX (C1.5 incomplete-drawings):
          ABTL=0.0 caused left abutment foundation plan to collapse onto x=0,
          producing a degenerate point.  Reuse the same fallback ladder as
          draw_piers_elevation so both views are aligned.
        """
        nspan = int(self.variables.get('NSPAN', 3))
        span1 = float(self.variables.get('SPAN1', 12))
        # Bug 2 fix: reuse the ABTL fallback ladder
        raw_abtl = float(self.variables.get('ABTL', 0.0))
        futl_fb = float(self.variables.get('FUTL', self.variables.get(
            'FOOTL', self.variables.get('FUTRL', 13.0))))
        alcl_fb = float(self.variables.get('ALCL', 0.0))
        alcw_fb = float(self.variables.get('ALCW', 0.0))
        if raw_abtl >= 1.0:
            abtl = raw_abtl
        elif futl_fb >= 1.0:
            abtl = futl_fb
        elif alcl_fb >= 1.0:
            abtl = alcl_fb
        elif alcw_fb >= 1.0:
            abtl = alcw_fb
        else:
            abtl = 13.0
        self.variables['ABTL'] = abtl
        futw = float(self.variables.get('FUTW', 4.5))
        futl = float(self.variables.get('FUTL', 12))
        piertw = float(self.variables.get('PIERTW', 1.2))
        pierst = float(self.variables.get('PIERST', 12))

        # Plan view Y-coordinate (below elevation view)
        yc = self.datum - 30.0

        # Simple-span notice for plan view (same reasoning as elevation)
        if nspan == 1:
            label_x = self.hpos(abtl + span1 * 0.5)
            label_y = self.vpos(yc + (max(futl, pierst) + 8.0))
            self.msp.add_text(
                "Plan view: simple span — no intermediate pier footings",
                dxfattribs={'height': 1.5 * self.scale1,
                            'color': 7,
                            'insert': (label_x, label_y),
                            'halign': 1})

        for i in range(1, nspan):
            xc = abtl + i * span1

            # Adjust dimensions for skew
            futwsq = futw / cos(radians(self.skew))
            futlsq = futl / cos(radians(self.skew))
            piertwsq = piertw / cos(radians(self.skew))
            pierstsq = pierst / cos(radians(self.skew))

            # Draw footing in plan with skew adjustments
            x1 = xc - futwsq / 2
            x2 = xc + futwsq / 2
            y1 = yc + futlsq / 2
            y2 = yc - futlsq / 2

            # Apply skew rotation to footing corners
            x_offset = (futlsq / 2) * sin(radians(self.skew))
            y_offset = (futlsq / 2) * (1 - cos(radians(self.skew)))

            footing_points = [
                self.pt(x1 - x_offset, y1 - y_offset),
                self.pt(x2 - x_offset, y1 - y_offset),
                self.pt(x2 + x_offset, y2 + y_offset),
                self.pt(x1 + x_offset, y2 + y_offset)
            ]

            self.msp.add_lwpolyline(footing_points, close=True)

            # Draw pier in plan with skew adjustments
            x3 = xc - piertwsq / 2
            x4 = xc + piertwsq / 2
            y3 = yc + pierstsq / 2
            y4 = yc - pierstsq / 2

            # Apply skew rotation to pier corners
            x_pier_offset = (pierstsq / 2) * sin(radians(self.skew))
            y_pier_offset = (pierstsq / 2) * (1 - cos(radians(self.skew)))

            pier_points = [
                self.pt(x3 - x_pier_offset, y3 - y_pier_offset),
                self.pt(x4 - x_pier_offset, y3 - y_pier_offset),
                self.pt(x4 + x_pier_offset, y4 + y_pier_offset),
                self.pt(x3 + x_pier_offset, y4 + y_pier_offset)
            ]

            self.msp.add_lwpolyline(pier_points, close=True)

            # Add pier number labels
            label_x = self.hpos(xc)
            label_y = self.vpos(yc + futlsq / 2 + 2.0)
            self.msp.add_text(f"P{i}", dxfattribs={
                'height': 1.5 * self.scale1,
                'insert': (label_x, label_y),
                'halign': 1  # Center alignment
            })

    def draw_abutment_foundation_plans(self):
        """Draw foundation plans for both abutments."""
        ccbr = float(self.variables.get('CCBR', 11.1))
        kerbw = float(self.variables.get('KERBW', 0.23))
        abtl = float(self.variables.get('ABTL', 0))
        nspan = int(self.variables.get('NSPAN', 3))
        span1 = float(self.variables.get('SPAN1', 12))

        abtlen = ccbr + 2 * kerbw
        yc = self.datum - 30.0

        # Left abutment foundation plan
        self.draw_single_abutment_foundation_plan(abtl, abtlen, yc, "A1")

        # Right abutment foundation plan
        right_abt_pos = abtl + nspan * span1
        self.draw_single_abutment_foundation_plan(right_abt_pos, abtlen, yc, "A2")

    def draw_single_abutment_foundation_plan(self, abt_x: float, abtlen: float, yc: float, label: str):
        """Draw foundation plan for a single abutment with dirt wall."""
        # Get dirt wall thickness
        dwth = float(self.variables.get('DWTH', 0.3))

        # Foundation dimensions with extensions
        foundation_ext = 1.5  # Extension beyond abutment

        y_top = yc + (abtlen + foundation_ext) / 2
        y_bottom = yc - (abtlen + foundation_ext) / 2

        # Foundation extends beyond abutment walls
        x_left = abt_x - foundation_ext
        x_right = abt_x + foundation_ext

        # Apply skew adjustments
        xx = (abtlen + foundation_ext) / 2
        x_adjust = xx * sin(radians(self.skew))
        y_adjust = xx * (1 - cos(radians(self.skew)))

        # Draw foundation plan with skew
        foundation_points = [
            self.pt(x_left - x_adjust, y_top - y_adjust),
            self.pt(x_right - x_adjust, y_top - y_adjust),
            self.pt(x_right + x_adjust, y_bottom + y_adjust),
            self.pt(x_left + x_adjust, y_bottom + y_adjust)
        ]

        self.msp.add_lwpolyline(foundation_points, close=True)

        # Draw dirt wall in plan view
        # Dirt wall is perpendicular to bridge axis
        _ = dwth / cos(radians(self.skew))

        # Determine dirt wall position based on abutment side
        if label == "A1":  # Left abutment - dirt wall on left side
            dw_x = abt_x - dwth
            dw_x_inner = abt_x
        else:  # Right abutment - dirt wall on right side
            dw_x = abt_x
            dw_x_inner = abt_x + dwth

        # Dirt wall extends full width of abutment
        xx_abt = abtlen / 2
        x_adjust_abt = xx_abt * sin(radians(self.skew))
        y_adjust_abt = xx_abt * (1 - cos(radians(self.skew)))

        y_top_abt = yc + abtlen / 2
        y_bottom_abt = yc - abtlen / 2

        # Draw dirt wall rectangle
        dw_points = [
            self.pt(dw_x - x_adjust_abt, y_top_abt - y_adjust_abt),
            self.pt(dw_x_inner - x_adjust_abt, y_top_abt - y_adjust_abt),
            self.pt(dw_x_inner + x_adjust_abt, y_bottom_abt + y_adjust_abt),
            self.pt(dw_x + x_adjust_abt, y_bottom_abt + y_adjust_abt)
        ]

        self.msp.add_lwpolyline(dw_points, close=True)

        # Add abutment label - position based on which abutment
        # Place label outside the foundation, with better spacing
        label_offset = 3.0  # Increased offset for better visibility

        if label == "A1":  # Left abutment
            # Place label to the left of the foundation
            label_x = self.hpos(x_left - label_offset)
            label_y = self.vpos(yc)  # Center vertically
        else:  # A2 - Right abutment
            # Place label to the right of the foundation
            label_x = self.hpos(x_right + label_offset)
            label_y = self.vpos(yc)  # Center vertically

        self.msp.add_text(label, dxfattribs={
            'height': 2.0 * self.scale1,  # Slightly larger for visibility
            'insert': (label_x, label_y),
            'halign': 1,  # Center alignment
            'valign': 2   # Middle vertical alignment
        })

    def add_dimensions_and_labels(self):
        """Add dimensions and text labels to the drawing."""
        try:
            # Add title block and labels
            self.add_title_block()

            # Add span dimensions
            self.add_span_dimensions()

            logger.info("Dimensions and labels added")

        except Exception as e:
            logger.error(f"Error adding dimensions: {e}")

    def draw_a4_border(self):
        """Draw A4 landscape border with professional frame."""
        try:
            right = float(self.variables.get('RIGHT', 50))
            _ = float(self.variables.get('LBRIDGE', 36))

            # A4 landscape dimensions in mm (1mm = 2.834645669 drawing units)
            # 297mm width × 210mm height = 841.89 × 595.27 units
            # Scale to drawing: make it visible and proportional
            border_margin = 50
            border_left = self.hpos(self.left) - border_margin
            border_right = self.hpos(right) + 100 * self.scale1
            border_top = self.vpos(float(self.variables.get('TOPRL', 115))) + 200
            border_bottom = self.datum - 120 * self.scale1

            # Draw A4 landscape border rectangle
            border_points = [
                (border_left, border_top),
                (border_right, border_top),
                (border_right, border_bottom),
                (border_left, border_bottom)
            ]
            self.msp.add_lwpolyline(border_points, close=True, dxfattribs={'lineweight': 35})

            # Inner frame
            inner_margin = 20
            inner_points = [
                (border_left + inner_margin, border_top - inner_margin),
                (border_right - inner_margin, border_top - inner_margin),
                (border_right - inner_margin, border_bottom + inner_margin),
                (border_left + inner_margin, border_bottom + inner_margin)
            ]
            self.msp.add_lwpolyline(inner_points, close=True)

            logger.info("A4 landscape border drawn")
        except Exception as e:
            logger.error(f"Error drawing A4 border: {e}")

    def add_title_block(self):
        """Add editable title block with modern GAD metadata fields."""
        try:
            right = float(self.variables.get('RIGHT', 50))

            # Metadata from Excel
            project_name = str(self.variables.get('PROJECT_NAME', 'Bridge General Arrangement Drawing'))
            company_name = str(self.variables.get('COMPANY_NAME', 'Bridge GAD Generator'))
            company_full = str(self.variables.get('COMPANY_FULL', 'Bridge Engineering Drawing Package'))
            address = str(self.variables.get('ADDRESS', '303 Vallabh Apartment, Udaipur'))
            import os as _os
            email = str(self.variables.get('EMAIL', _os.environ.get('CONTACT_EMAIL', 'contact@example.com')))
            mobile = str(self.variables.get('MOBILE', _os.environ.get('CONTACT_PHONE', '+91XXXXXXXXXX')))
            drawing_no = str(self.variables.get('DRAWING_NO', self.variables.get('PROJECT_CODE', 'GAD-001')))
            revision = str(self.variables.get('REVISION', 'R0'))
            sheet_no = str(self.variables.get('SHEET_NO', '1'))
            total_sheets = str(self.variables.get('TOTAL_SHEETS', '1'))
            drawing_standard = str(self.variables.get('DRAWING_STANDARD', 'IRC/MoRTH project criteria'))
            live_load = str(self.variables.get('DESIGN_LIVE_LOAD', 'To project basis'))
            drawn_by = str(self.variables.get('DRAWN_BY', 'Design Cell'))
            checked_by = str(self.variables.get('CHECKED_BY', 'Checker'))
            approved_by = str(self.variables.get('APPROVED_BY', 'Approver'))
            bearing_type = str(self.variables.get('BEARING_TYPE', 'As per design'))
            scale_text = f"Scale 1:{self.scale1} / Sec 1:{self.scale2}"

            # Position title block on right side of drawing
            title_block_x = self.hpos(right) + 50 * self.scale1
            title_block_y = self.vpos(float(self.variables.get('TOPRL', 115))) + 100

            block_width = 72 * self.scale1
            block_height = 34 * self.scale1
            row_height = block_height / 6
            x0 = title_block_x
            y0 = title_block_y
            x1 = x0 + block_width
            y1 = y0 - block_height

            self.msp.add_lwpolyline(
                [(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                close=True,
                dxfattribs={'lineweight': 35},
            )

            for row in range(1, 6):
                y_line = y0 - row * row_height
                self.msp.add_line((x0, y_line), (x1, y_line))

            self.msp.add_line((x0 + block_width * 0.62, y0 - 2 * row_height), (x0 + block_width * 0.62, y0 - 3 * row_height))
            self.msp.add_line((x0 + block_width * 0.80, y0 - 2 * row_height), (x0 + block_width * 0.80, y0 - 3 * row_height))
            self.msp.add_line((x0 + block_width / 3, y0 - 4 * row_height), (x0 + block_width / 3, y0 - 5 * row_height))
            self.msp.add_line((x0 + 2 * block_width / 3, y0 - 4 * row_height), (x0 + 2 * block_width / 3, y0 - 5 * row_height))

            text_x = x0 + 1.2 * self.scale1
            self.msp.add_text("GENERAL ARRANGEMENT DRAWING", dxfattribs={
                'height': 2.4 * self.scale1,
                'insert': (text_x, y0 - 1.6 * self.scale1),
                'style': 'Arial'
            })
            self.msp.add_text(project_name, dxfattribs={
                'height': 1.8 * self.scale1,
                'insert': (text_x, y0 - row_height - 1.5 * self.scale1),
                'style': 'Arial'
            })
            self.msp.add_text(f"DRG NO: {drawing_no}", dxfattribs={
                'height': 1.25 * self.scale1,
                'insert': (text_x, y0 - 2 * row_height - 1.3 * self.scale1)
            })
            self.msp.add_text(f"REV: {revision}", dxfattribs={
                'height': 1.25 * self.scale1,
                'insert': (x0 + block_width * 0.64, y0 - 2 * row_height - 1.3 * self.scale1)
            })
            self.msp.add_text(f"SHEET: {sheet_no}/{total_sheets}", dxfattribs={
                'height': 1.25 * self.scale1,
                'insert': (x0 + block_width * 0.81, y0 - 2 * row_height - 1.3 * self.scale1)
            })
            self.msp.add_text(f"STANDARD: {drawing_standard}", dxfattribs={
                'height': 1.1 * self.scale1,
                'insert': (text_x, y0 - 3 * row_height - 1.2 * self.scale1)
            })
            self.msp.add_text(f"LIVE LOAD: {live_load}", dxfattribs={
                'height': 1.1 * self.scale1,
                'insert': (text_x, y0 - 3 * row_height - 2.8 * self.scale1)
            })
            self.msp.add_text(f"BEARING: {bearing_type}", dxfattribs={
                'height': 1.1 * self.scale1,
                'insert': (text_x, y0 - 3 * row_height - 4.4 * self.scale1)
            })
            self.msp.add_text(f"DRAWN BY: {drawn_by}", dxfattribs={
                'height': 1.0 * self.scale1,
                'insert': (text_x, y0 - 4 * row_height - 1.2 * self.scale1)
            })
            self.msp.add_text(f"CHECKED BY: {checked_by}", dxfattribs={
                'height': 1.0 * self.scale1,
                'insert': (x0 + block_width / 3 + 0.8 * self.scale1, y0 - 4 * row_height - 1.2 * self.scale1)
            })
            self.msp.add_text(f"APPROVED BY: {approved_by}", dxfattribs={
                'height': 1.0 * self.scale1,
                'insert': (x0 + 2 * block_width / 3 + 0.8 * self.scale1, y0 - 4 * row_height - 1.2 * self.scale1)
            })
            self.msp.add_text(company_name, dxfattribs={
                'height': 1.1 * self.scale1,
                'insert': (text_x, y0 - 5 * row_height - 1.1 * self.scale1),
                'style': 'Arial'
            })
            self.msp.add_text(company_full, dxfattribs={
                'height': 0.95 * self.scale1,
                'insert': (text_x, y0 - 5 * row_height - 2.5 * self.scale1)
            })
            self.msp.add_text(scale_text, dxfattribs={
                'height': 0.95 * self.scale1,
                'insert': (text_x, y1 + 2.5 * self.scale1)
            })
            self.msp.add_text(address, dxfattribs={
                'height': 0.85 * self.scale1,
                'insert': (x0 + block_width * 0.42, y1 + 2.5 * self.scale1)
            })
            self.msp.add_text(f"{email} | {mobile}", dxfattribs={
                'height': 0.8 * self.scale1,
                'insert': (x0 + block_width * 0.42, y1 + 1.1 * self.scale1)
            })

            logger.info("Standards-aware title block added")
        except Exception as e:
            logger.error(f"Error adding title block: {e}")

    def add_project_name_footer(self):
        """Add full-width project name at bottom of drawing."""
        try:
            right = float(self.variables.get('RIGHT', 50))

            # Get project name from Excel
            project_name = str(self.variables.get('PROJECT_NAME', 'Bridge General Arrangement Drawing'))
            project_code = str(self.variables.get('PROJECT_CODE', ''))

            # Position at bottom, full width
            footer_x = self.hpos(self.left + (right - self.left) / 2)  # Center horizontally
            footer_y = self.datum - 130 * self.scale1  # Bottom of page

            # Draw footer text
            footer_text = f"{project_name}" + (f" | {project_code}" if project_code else "")
            self.msp.add_text(footer_text, dxfattribs={
                'height': 3.5 * self.scale1,
                'insert': (footer_x, footer_y),
                'halign': 1,  # Center alignment
                'style': 'Arial'
            })

            # Draw horizontal line above footer
            line_y = footer_y + 2.0 * self.scale1
            line_x1 = self.hpos(self.left)
            line_x2 = self.hpos(right)
            self.msp.add_line((line_x1, line_y), (line_x2, line_y))

            logger.info("Project name footer added")
        except Exception as e:
            logger.error(f"Error adding project footer: {e}")

    def draw_side_elevation(self):
        """Draw side elevation view showing cross-section of bridge components."""
        try:
            # Get bridge parameters
            nspan = int(self.variables.get('NSPAN', 3))
            _ = float(self.variables.get('SPAN1', 12))
            _ = float(self.variables.get('ABTL', 0))
            rtl = float(self.variables.get('RTL', 110.98))
            ccbr = float(self.variables.get('CCBR', 11.1))
            kerbw = float(self.variables.get('KERBW', 0.23))
            slbthe = float(self.variables.get('SLBTHE', 0.75))
            kerbd = float(self.variables.get('KERBD', 0.15))
            footpathw = float(self.variables.get('FOOTPATHW', 0.0))
            utilityd = float(self.variables.get('UTILITYD', 0.0))
            wcth = float(self.variables.get('WCTH', 0.08))
            crossfall = float(self.variables.get('CROSSFALL', 0.025))
            crashb = int(float(self.variables.get('CRASHB', 0)))
            barrierh = float(self.variables.get('BARRIERH', 1.10 if crashb else 0.0))
            capt = float(self.variables.get('CAPT', 110))
            capb = float(self.variables.get('CAPB', 109.4))
            piertw = float(self.variables.get('PIERTW', 1.2))
            pierst = float(self.variables.get('PIERST', 12))
            futrl = float(self.variables.get('FUTRL', 100))
            futd = float(self.variables.get('FUTD', 1.0))
            futw = float(self.variables.get('FUTW', 4.5))
            futl = float(self.variables.get('FUTL', 12))
            right = float(self.variables.get('RIGHT', 50))

            # Position side elevation to the right of main drawing with margin
            _ = float(self.variables.get('LBRIDGE', 36))
            side_x_offset = self.hpos(right) + 40 * self.scale1  # Fixed pixels offset from main drawing
            side_y_base = self.datum  # Start at datum level

            # Draw deck cross-section with calculated bounds
            deck_bounds = self.draw_deck_cross_section(
                side_x_offset,
                side_y_base,
                ccbr,
                kerbw,
                slbthe,
                kerbd,
                rtl,
                footpath_width=footpathw,
                barrier_height=barrierh if crashb else 0.0,
                utility_duct_width=utilityd,
                wearing_course_thickness=wcth,
                crossfall=crossfall,
            )

            # Draw typical pier cross-section below deck
            if nspan > 1 and deck_bounds:
                # Position pier section 5 units below deck bottom
                pier_y_offset = deck_bounds['y_bottom'] - 10 * self.scale1
                self.draw_pier_cross_section(side_x_offset, pier_y_offset,
                                             piertw, pierst, capt, capb, futrl, futd, futw, futl)

            logger.info("Side elevation drawing completed")

        except Exception as e:
            logger.error(f"Error drawing side elevation: {e}")

    def draw_deck_cross_section(
        self,
        x_offset: float,
        y_base: float,
        ccbr: float,
        kerbw: float,
        slbthe: float,
        kerbd: float,
        rtl: float,
        footpath_width: float = 0.0,
        barrier_height: float = 0.0,
        utility_duct_width: float = 0.0,
        wearing_course_thickness: float = 0.0,
        crossfall: float = 0.025,
    ):
        """Draw deck cross-section with roadway accessories. Returns bounds for label positioning."""
        # Calculate deck section dimensions with direct scaling
        total_width = ccbr + 2 * kerbw + 2 * footpath_width
        deck_thickness = slbthe

        # Direct coordinate calculations (no double scaling)
        section_scale = 0.5  # Scale down section for visibility
        x_start = x_offset
        width_scaled = total_width * self.hhs * section_scale
        x_center = x_start + width_scaled / 2
        x_end = x_start + width_scaled

        # Vertical positions - use datum offset
        height_offset = self.vvs * section_scale
        y_deck_top = y_base
        y_deck_bottom = y_base - deck_thickness * height_offset
        y_kerb_top = y_base + kerbd * height_offset
        y_wc_mid = y_deck_top + wearing_course_thickness * height_offset
        half_camber_drop = max(ccbr, 0.0) * crossfall * height_offset / 2.0

        # Draw main deck slab
        deck_points = [
            (x_start, y_deck_top),
            (x_end, y_deck_top),
            (x_end, y_deck_bottom),
            (x_start, y_deck_bottom)
        ]
        self.msp.add_lwpolyline(deck_points, close=True)

        footpath_width_scaled = footpath_width * self.hhs * section_scale
        # Draw left kerb
        kerb_width_scaled = kerbw * self.hhs * section_scale
        left_kerb_x = x_start + footpath_width_scaled + kerb_width_scaled
        left_kerb_points = [
            (x_start + footpath_width_scaled, y_deck_top),
            (left_kerb_x, y_deck_top),
            (left_kerb_x, y_kerb_top),
            (x_start + footpath_width_scaled, y_kerb_top)
        ]
        self.msp.add_lwpolyline(left_kerb_points, close=True)

        # Draw right kerb
        right_kerb_x = x_end - footpath_width_scaled - kerb_width_scaled
        right_kerb_points = [
            (right_kerb_x, y_deck_top),
            (x_end - footpath_width_scaled, y_deck_top),
            (x_end - footpath_width_scaled, y_kerb_top),
            (right_kerb_x, y_kerb_top)
        ]
        self.msp.add_lwpolyline(right_kerb_points, close=True)

        # Draw footpaths if specified
        if footpath_width_scaled > 0:
            self.msp.add_lwpolyline([
                (x_start, y_deck_top),
                (x_start + footpath_width_scaled, y_deck_top),
                (x_start + footpath_width_scaled, y_kerb_top),
                (x_start, y_kerb_top),
            ], close=True)
            self.msp.add_lwpolyline([
                (x_end - footpath_width_scaled, y_deck_top),
                (x_end, y_deck_top),
                (x_end, y_kerb_top),
                (x_end - footpath_width_scaled, y_kerb_top),
            ], close=True)

        # Draw wearing course / cross fall as a crown line
        carriageway_left = x_start + footpath_width_scaled + kerb_width_scaled
        carriageway_right = x_end - footpath_width_scaled - kerb_width_scaled
        self.msp.add_lwpolyline([
            (carriageway_left, y_wc_mid - half_camber_drop),
            (x_center, y_wc_mid),
            (carriageway_right, y_wc_mid - half_camber_drop),
        ])

        # Draw crash barriers or parapets if specified
        feature_top = max(y_kerb_top, y_wc_mid)
        if barrier_height > 0:
            barrier_width_scaled = max(0.25 * self.hhs * section_scale, kerb_width_scaled * 0.65)
            left_barrier_top = y_kerb_top + barrier_height * height_offset
            right_barrier_top = left_barrier_top
            self.msp.add_lwpolyline([
                (x_start, y_kerb_top),
                (x_start + barrier_width_scaled, y_kerb_top),
                (x_start + barrier_width_scaled, left_barrier_top),
                (x_start, left_barrier_top),
            ], close=True)
            self.msp.add_lwpolyline([
                (x_end - barrier_width_scaled, y_kerb_top),
                (x_end, y_kerb_top),
                (x_end, right_barrier_top),
                (x_end - barrier_width_scaled, right_barrier_top),
            ], close=True)
            feature_top = max(feature_top, left_barrier_top)

        # Draw indicative utility duct beneath left footpath/kerb zone
        if utility_duct_width > 0:
            duct_width_scaled = utility_duct_width * self.hhs * section_scale
            duct_height = max(0.25 * height_offset, deck_thickness * height_offset * 0.35)
            duct_x1 = x_start + footpath_width_scaled * 0.2
            duct_x2 = min(duct_x1 + duct_width_scaled, x_center - kerb_width_scaled * 0.4)
            duct_y1 = y_deck_bottom + 0.18 * deck_thickness * height_offset
            duct_y2 = duct_y1 + duct_height
            self.msp.add_lwpolyline([
                (duct_x1, duct_y1),
                (duct_x2, duct_y1),
                (duct_x2, duct_y2),
                (duct_x1, duct_y2),
            ], close=True)
            self.msp.add_text("UTILITY DUCT", dxfattribs={
                'height': 0.9 * self.scale1,
                'insert': (duct_x1, duct_y2 + 0.7 * self.scale1),
            })

        # Add concise labels for current practice components
        if footpath_width_scaled > 0:
            self.msp.add_text("FOOTPATH", dxfattribs={
                'height': 0.85 * self.scale1,
                'insert': (x_start + 0.25 * footpath_width_scaled, y_kerb_top + 0.8 * self.scale1),
            })
        if barrier_height > 0:
            self.msp.add_text("BARRIER", dxfattribs={
                'height': 0.85 * self.scale1,
                'insert': (x_end - max(0.25 * self.hhs * section_scale, kerb_width_scaled * 0.65), feature_top + 0.8 * self.scale1),
            })
        self.msp.add_text(f"CROSSFALL {crossfall * 100:.1f}%", dxfattribs={
            'height': 0.85 * self.scale1,
            'insert': (x_center - 5.0 * self.scale1, y_wc_mid + 1.0 * self.scale1),
        })
        self.msp.add_text(f"WC {wearing_course_thickness * 1000:.0f} mm", dxfattribs={
            'height': 0.85 * self.scale1,
            'insert': (x_center - 4.0 * self.scale1, y_wc_mid + 2.3 * self.scale1),
        })

        # Add section label - dynamically positioned above section with proper spacing
        label_x = x_center
        label_spacing = max(3.0 * self.scale1, 50)  # Dynamic spacing based on scale
        label_y = feature_top + label_spacing
        self.msp.add_text("SECTION A-A", dxfattribs={
            'height': 2.0 * self.scale1,
            'insert': (label_x, label_y),
            'halign': 1,  # Center alignment
            'valign': 0   # Bottom alignment
        })

        # Store bounds for next section positioning
        return {
            'x_start': x_start,
            'x_end': x_end,
            'x_center': x_center,
            'y_top': feature_top,
            'y_bottom': y_deck_bottom,
            'y_kerb': y_kerb_top,
            'label_y': label_y
        }

    def draw_pier_cross_section(self, x_offset: float, y_base: float, piertw: float,
                                pierst: float, capt: float, capb: float, futrl: float,
                                futd: float, futw: float, futl: float):
        """Draw typical pier cross-section."""
        # Direct coordinate calculations (no double scaling)
        section_scale = 0.5
        height_offset = self.vvs * section_scale

        # Pier center position
        pier_width_scaled = pierst * self.hhs * section_scale
        pier_center_x = x_offset + pier_width_scaled / 2

        # Draw pier cap in section
        cap_width_scaled = piertw * self.hhs * section_scale
        cap_x_start = pier_center_x - cap_width_scaled / 2
        cap_x_end = pier_center_x + cap_width_scaled / 2

        cap_height = (capt - capb) * height_offset
        cap_y_top = y_base
        cap_y_bottom = y_base - cap_height

        cap_points = [
            (cap_x_start, cap_y_top),
            (cap_x_end, cap_y_top),
            (cap_x_end, cap_y_bottom),
            (cap_x_start, cap_y_bottom)
        ]
        self.msp.add_lwpolyline(cap_points, close=True)

        # Draw pier shaft in section
        shaft_height = (capb - futrl) * height_offset
        shaft_y_top = cap_y_bottom
        shaft_y_bottom = cap_y_bottom - shaft_height

        shaft_points = [
            (cap_x_start, shaft_y_top),
            (cap_x_end, shaft_y_top),
            (cap_x_end, shaft_y_bottom),
            (cap_x_start, shaft_y_bottom)
        ]
        self.msp.add_lwpolyline(shaft_points, close=True)

        # Draw footing in section
        footing_width_scaled = futw * self.hhs * section_scale
        footing_x_start = pier_center_x - footing_width_scaled / 2
        footing_x_end = pier_center_x + footing_width_scaled / 2

        footing_height = futd * height_offset
        footing_y_top = shaft_y_bottom
        footing_y_bottom = footing_y_top - footing_height

        footing_points = [
            (footing_x_start, footing_y_top),
            (footing_x_end, footing_y_top),
            (footing_x_end, footing_y_bottom),
            (footing_x_start, footing_y_bottom)
        ]
        self.msp.add_lwpolyline(footing_points, close=True)

        # Add section label - dynamically positioned above pier cap with proper spacing
        label_x = pier_center_x
        label_spacing = max(3.0 * self.scale1, 50)  # Dynamic spacing based on scale
        label_y = cap_y_top + label_spacing
        self.msp.add_text("SECTION B-B (TYPICAL PIER)", dxfattribs={
            'height': 2.0 * self.scale1,
            'insert': (label_x, label_y),
            'halign': 1,  # Center alignment
            'valign': 0   # Bottom alignment
        })

    def add_span_dimensions(self):
        """Add span length dimensions."""
        nspan = int(self.variables.get('NSPAN', 3))
        span1 = float(self.variables.get('SPAN1', 12))
        abtl = float(self.variables.get('ABTL', 0))
        rtl = float(self.variables.get('RTL', 110.98))

        for i in range(nspan):
            x1 = abtl + i * span1
            x2 = x1 + span1
            y_dim = self.vpos(rtl) + 200

            # Add linear dimension
            dim = self.msp.add_linear_dim(
                base=(self.hpos(x1 + span1 / 2), y_dim),
                p1=(self.hpos(x1), self.vpos(rtl)),
                p2=(self.hpos(x2), self.vpos(rtl)),
                angle=0,
                dimstyle="PMB100"
            )
            dim.render()

    # =================================================================
    # PMGSY 2-Sheet Minor Bridge — drawing helpers (T4)
    # Draws: Soil Profile legend, Bridge Schedule Table,
    #        weep-hole circles at specified c/c, 13-item Notes panel.
    # All functions are OPT-IN: only draw when the corresponding keys
    # are present in self.variables.  Silent no-op otherwise so the
    # non-PMGSY templates continue to render exactly as before.
    # =================================================================

    def draw_soil_profile_legend(self, x0: float, y0: float) -> bool:
        """Draw 3-layer soil legend (Sheet 02 inset) with 3 hatches + Avg GL marker.

        Parameters
        ----------
        x0, y0:
            Top-left insertion point (model coords, metres via vpos/hpos).

        Returns True if anything was drawn (soil vars present), else False.
        """

        v = self.variables
        names = [v.get(f"SOIL{i}_NAME", "") for i in range(1, 4)]
        thicks = [float(v.get(f"SOIL{i}_THICK", 0) or 0) for i in range(1, 4)]
        hatchs = [v.get(f"SOIL{i}_HATCH", "") or "" for i in range(1, 4)]
        cols = [int(v.get(f"SOIL{i}_COLOR", 7) or 7) for i in range(1, 4)]
        avg_gl = v.get("AVG_GL_RL", None)

        if not any(names) and not any(thicks):
            return False

        box_w = max(3.0, float(self.variables.get("CCBR", 7.5)) * 0.35)  # m
        total_h = sum(max(0.25, t) for t in thicks)
        if total_h <= 0:
            return False

        # Drawing-unit conversions (metres → scaled units via hhs/vvs / SCALE1)
        s1 = float(self.variables.get("SCALE1", 186) or 186)

        def to_units_m(m_val: float) -> float:
            return m_val * 1000.0  # metres → drawing mm when scales are 1:100 style

        # Render relative to x0, y0 in model space.  Use a small section-style scale.
        inset_scale = 0.5
        box_w_u = box_w * 1000.0 * inset_scale
        row_h_u = [max(0.25, thicks[i]) * 1000.0 * inset_scale for i in range(3)]

        # --- Column 1: stacked soil hatches ---
        y_cursor = y0
        for i in range(3):
            if row_h_u[i] <= 0:
                continue
            x_left = x0
            x_right = x0 + box_w_u
            y_bot = y_cursor - row_h_u[i]
            y_top = y_cursor
            rect_pts = [(x_left, y_top), (x_right, y_top),
                        (x_right, y_bot), (x_left, y_bot)]
            self.msp.add_lwpolyline(rect_pts, close=True,
                                    dxfattribs={"color": cols[i]})
            hatch_name = hatchs[i] or ("ANSI31" if i == 0 else
                                       "ANSI37" if i == 1 else "AR-SAND")
            try:
                h = self.msp.add_hatch(
                    color=cols[i],
                    dxfattribs={"layer": "HATCHING", "color": cols[i]},
                )
                h.paths.add_polyline_path(rect_pts, is_closed=1)
                h.set_pattern_fill(hatch_name, scale=max(0.5, s1 / 200.0))
            except Exception as exc:
                logger.info("draw_soil_profile_legend: hatch skipped i=%d: %s", i, exc)
            # Label (SOILi_NAME + thickness) to the right of the box
            label_x = x_right + (40.0 * inset_scale)
            label_y = (y_top + y_bot) / 2.0
            name = names[i] or f"Layer {i+1}"
            th_metre = max(0.25, thicks[i])
            self.msp.add_text(f"{name}  {th_metre:.2f} m",
                              dxfattribs={
                                  "height": max(80.0, s1 * 0.5) * inset_scale,
                                  "insert": (label_x, label_y),
                                  "color": cols[i],
                              })
            y_cursor = y_bot

        # --- Average Ground Level arrow on left margin ---
        if avg_gl is not None:
            try:
                gl_rl = float(avg_gl)
            except Exception:
                gl_rl = None
            if gl_rl is not None:
                arrow_x = x0 - (80.0 * inset_scale)
                arrow_y = y0 - (sum(row_h_u) * 0.3)
                self.msp.add_line((arrow_x, arrow_y),
                                  (x0, arrow_y),
                                  dxfattribs={"color": 3})
                try:
                    # Triangle arrow head (simple 3-point lwpolyline)
                    tip = (x0, arrow_y)
                    back_1 = (x0 - (20.0 * inset_scale), arrow_y - (10.0 * inset_scale))
                    back_2 = (x0 - (20.0 * inset_scale), arrow_y + (10.0 * inset_scale))
                    self.msp.add_lwpolyline([tip, back_1, back_2], close=True,
                                            dxfattribs={"color": 3, "fill": True})
                except Exception:
                    pass
                self.msp.add_text(f"Avg GL  RL {gl_rl:.3f}",
                                  dxfattribs={
                                      "height": max(70.0, s1 * 0.45) * inset_scale,
                                      "insert": (arrow_x - (10.0 * inset_scale),
                                                 arrow_y + (20.0 * inset_scale)),
                                      "color": 3,
                                  })

        # --- Header label ---
        self.msp.add_text("SOIL PROFILE",
                          dxfattribs={
                              "height": max(100.0, s1 * 0.6) * inset_scale,
                              "insert": (x0, y0 + (80.0 * inset_scale)),
                              "color": 5,
                          })
        return True

    def draw_schedule_table(self, x0: float, y0: float) -> bool:
        """Draw the PMGSY bridge schedule table (Sheet 02, ~12 columns wide).

        Headers:
          S.No | Chainage | Type | FRL | BL | Proposed | Span | Height
               | B1 | B2 | B3 | B4
        Returns True if at least one SCHED_* key present.
        """
        v = self.variables
        sched_keys = [k for k in v.keys() if str(k).startswith("SCHED_")]
        if not sched_keys:
            return False

        s1 = float(self.variables.get("SCALE1", 186) or 186)
        row_h = max(160.0, s1 * 0.9)
        cell_pad_x = 30.0
        text_h = max(100.0, s1 * 0.55)
        head_h = row_h * 1.2

        # --- Build header + 1 data row (single bridge per schedule) ---
        headers = [
            "S.No", "Chainage", "Type", "FRL (m)", "BL (m)",
            "Proposed", "Span", "Height (m)",
            "B1 (m)", "B2 (m)", "B3 (m)", "B4 (m)",
        ]
        fmt_vals = [
            str(v.get("SCHED_SNO", "")),
            str(v.get("SCHED_CHAINAGE", "")),
            str(v.get("SCHED_TYPE", "")),
            _fmt_num(v.get("SCHED_FRL")),
            _fmt_num(v.get("SCHED_BL")),
            str(v.get("SCHED_PROPOSED", "")),
            str(v.get("SCHED_SPAN_TEXT", v.get("SCHED_PROPOSED", ""))),
            _fmt_num(v.get("SCHED_HEIGHT")),
            _fmt_num(v.get("SCHED_B1")),
            _fmt_num(v.get("SCHED_B2")),
            _fmt_num(v.get("SCHED_B3")),
            _fmt_num(v.get("SCHED_B4")),
        ]

        # Column widths: label-based auto-fit with minimums
        min_cw = [100, 200, 120, 140, 140, 200, 260, 160, 120, 120, 120, 120]
        col_w = []
        for i, h in enumerate(headers):
            content_len = max(len(h), len(str(fmt_vals[i]) if i < len(fmt_vals) else ""))
            auto = max(min_cw[i], content_len * text_h * 0.55 + cell_pad_x * 2.0)
            col_w.append(auto)

        total_w = sum(col_w)
        x_positions = []
        acc = 0.0
        for w in col_w:
            x_positions.append(acc)
            acc += w

        # Draw outer border + header separator + row separator
        y_top = y0
        y_head_bottom = y_top - head_h
        y_row_bottom = y_head_bottom - row_h

        outer = [(x0, y_top), (x0 + total_w, y_top),
                 (x0 + total_w, y_row_bottom), (x0, y_row_bottom)]
        self.msp.add_lwpolyline(outer, close=True, dxfattribs={"color": 5, "lineweight": 50})
        # Header row underline
        self.msp.add_line((x0, y_head_bottom),
                          (x0 + total_w, y_head_bottom),
                          dxfattribs={"color": 5, "lineweight": 50})
        # Vertical separators
        cx = x0
        for w in col_w[:-1]:
            cx += w
            self.msp.add_line((cx, y_top), (cx, y_row_bottom),
                              dxfattribs={"color": 7, "lineweight": 25})

        # Populate text cells
        for i, h in enumerate(headers):
            cx = x0 + x_positions[i] + cell_pad_x
            cy = y_top - (head_h * 0.65)
            self.msp.add_text(h, dxfattribs={
                "height": text_h * 0.95, "insert": (cx, cy),
                "color": 7,
            })
        for i, val in enumerate(fmt_vals):
            cx = x0 + x_positions[i] + cell_pad_x
            cy = y_head_bottom - (row_h * 0.65)
            self.msp.add_text(str(val), dxfattribs={
                "height": text_h, "insert": (cx, cy),
                "color": 1 if i in (7, 8, 9, 10, 11) else 7,  # red dim colors for heights/Bs
            })

        # Title above the table
        self.msp.add_text("BRIDGE SCHEDULE",
                          dxfattribs={
                              "height": text_h * 1.4,
                              "insert": (x0, y_top + (row_h * 0.7)),
                              "color": 5,
                          })
        return True

    def draw_weep_holes(self, x_start: float, y_start: float,
                        width: float, height: float) -> int:
        """Draw weep-hole circles at specified c/c in abutment/return-wall box.

        Wraps in meters → drawing units.  Returns number of circles drawn.
        """
        v = self.variables
        diam_mm = float(v.get("WEEP_DIAM", 0) or 0)
        c2c_mm = float(v.get("WEEP_C_TO_C", 0) or 0)
        rows_n = int(float(v.get("WEEP_ROWS", 0) or 0))
        staggered = bool(int(float(v.get("WEEP_STAGGER", 0) or 0)))
        if diam_mm <= 0 or c2c_mm <= 0 or rows_n <= 0 or width <= 0 or height <= 0:
            return 0

        # metres → drawing scale units (assume SCALE1-based)
        s1 = float(self.variables.get("SCALE1", 186) or 186)
        diam_u = diam_mm * (s1 / 186.0)
        c2c_u = c2c_mm * (s1 / 186.0)

        # Draw inside [x_start, y_start + height] * [x_start + width, y_start]
        margin_x = c2c_u * 0.5
        margin_y = c2c_u * 0.5
        count = 0
        for r in range(rows_n):
            cy = y_start + height - margin_y - r * c2c_u
            if cy - diam_u / 2 < y_start + margin_y:
                break
            x_off = (c2c_u / 2.0) if (staggered and r % 2 == 1) else 0.0
            cx = x_start + margin_x + x_off
            while cx + diam_u / 2 <= x_start + width - margin_x:
                self.msp.add_circle(center=(cx, cy), radius=diam_u / 2.0,
                                    dxfattribs={"color": 1})
                count += 1
                cx += c2c_u

        # Label
        if count:
            self.msp.add_text(
                f"Weep holes {diam_mm:.0f} dia @ {c2c_mm:.0f} c/c "
                f"({rows_n} row{'s' if rows_n > 1 else ''}"
                f"{', staggered' if staggered else ''})",
                dxfattribs={
                    "height": max(80.0, s1 * 0.45),
                    "insert": (x_start, y_start - diam_u),
                    "color": 1,
                })
        return count

    def draw_pmgsy_notes_panel(self, x0: float, y0: float,
                               width: float) -> bool:
        """Draw the 13-item PMGSY notes panel, plus structured note-blocks.

        Draws NOTE1_TEXT ... NOTE13_TEXT and, when present, the
        structured concrete-grades, reinforcement, live-load, backfill,
        scour-code, dist-to-weir summary blocks.

        Returns True if any note text was drawn.
        """
        v = self.variables
        s1 = float(self.variables.get("SCALE1", 186) or 186)
        line_h = max(140.0, s1 * 0.75)
        text_h = max(95.0, s1 * 0.52)
        margin_left = 40.0

        # Collect numbered items NOTE1_TEXT ... NOTE13_TEXT
        items: List[str] = []
        for i in range(1, 14):
            val = v.get(f"NOTE{i}_TEXT")
            if val:
                items.append(str(val))

        # Add structured summary blocks when keys populated
        structured_titles = [
            ("CONCRETE GRADES", "NOTE_CONCRETE_GRADES"),
            ("REINFORCEMENT", "NOTE_REINF_STANDARD"),
            ("LIVE LOAD BASIS", "NOTE_LIVE_LOAD_COMBO"),
            ("BACKFILL PARAMETERS", "NOTE_BACKFILL_PARAMS"),
            ("SCOUR PROVISION", "NOTE_SCOUR_CODE"),
            ("DISTANCE TO WEIR", "NOTE_DIST_TO_WEIR"),
            ("BEARING (MINOR BRIDGE)", "NOTE_BEARING_OVERRIDE"),
        ]
        for title, key in structured_titles:
            val = v.get(key)
            if val in (None, ""):
                continue
            items.append(f"{title}  —  {val}")

        if not items:
            return False

        # --- Panel border ---
        total_h = line_h + len(items) * line_h  # 1 header + N items
        total_h = max(total_h, line_h * 2.0)
        border = [(x0, y0), (x0 + width, y0),
                  (x0 + width, y0 - total_h), (x0, y0 - total_h)]
        self.msp.add_lwpolyline(border, close=True,
                                dxfattribs={"color": 5, "lineweight": 50})

        # Panel title
        self.msp.add_text("NOTES", dxfattribs={
            "height": text_h * 1.4,
            "insert": (x0 + margin_left, y0 - line_h * 0.70),
            "color": 5,
        })

        # Items — word-wrap is intentionally skipped because NOTEi_TEXT
        # is kept to single line-length by the parameter spec (<=120 chars).
        for i, line in enumerate(items):
            self.msp.add_text(line, dxfattribs={
                "height": text_h,
                "insert": (x0 + margin_left,
                           y0 - line_h * (2 + i) + (text_h * 0.1)),
                "color": 7,
            })
        return True

    def generate_complete_drawing(self, excel_file: Path, output_file: Path) -> bool:
        """Generate complete bridge GAD drawing."""
        try:
            # Setup
            self.setup_document()
            self._excel_path = Path(excel_file)

            # Read parameters
            if not self.read_variables_from_excel(excel_file):
                return False

            # Draw all components
            logger.info("Starting bridge drawing generation...")

            # Draw border and title block first (underneath)
            self.draw_a4_border()

            # Main drawing elements
            self.draw_layout_and_axes()
            self.draw_cross_section_profile()
            self.draw_bridge_superstructure()
            self.draw_piers_elevation()
            self.draw_abutments()
            self.draw_plan_view()
            self.draw_side_elevation()
            self.add_dimensions_and_labels()

            # ----- PMGSY optional panels (OPT-IN, silent skip otherwise) -----
            try:
                # Find a quiet corner of the sheet (bottom-right free area) to
                # place soil legend + notes.  When templates do not set the
                # SOIL/NOTES/SCHED variables, these calls are no-ops.
                page_w = float(self.doc.header.get("$EXTMAX", (0,))[0]
                               if getattr(self.doc, "header", None) else 29700.0)
                if page_w < 1000:
                    page_w = 29700.0  # A4 width at 1:1 scale in mm
                s1 = float(self.variables.get("SCALE1", 186) or 186)
                # Bottom of sheet + some margin upwards
                y_inset = 2200.0 + s1 * 5.0
                x_right = page_w - (300.0 + s1 * 10.0)

                # Sheet 2 style: Soil legend, schedule, notes sit below the
                # existing views.  For the single-sheet generate_complete_
                # drawing() pipeline they stack to the right of plan view so
                # no overlap occurs.
                try:
                    # Left column: SOIL profile legend
                    y_soil = y_inset + 5500.0
                    self.draw_soil_profile_legend(2500.0, y_soil)
                except Exception as exc:
                    logger.info("soil_profile_legend opt-in skip: %s", exc)
                try:
                    # Schedule table spans the mid-width at the bottom
                    y_sched = y_inset + 2600.0
                    self.draw_schedule_table(2500.0, y_sched)
                except Exception as exc:
                    logger.info("schedule_table opt-in skip: %s", exc)
                try:
                    # Notes panel bottom-right
                    y_notes = y_inset + 2200.0
                    self.draw_pmgsy_notes_panel(2500.0, y_notes, width=x_right - 2500.0)
                except Exception as exc:
                    logger.info("pmgsy_notes_panel opt-in skip: %s", exc)
            except Exception as exc:
                logger.info("PMGSY optional panels skipped (%s)", exc)

            # Add title block and footer
            self.add_title_block()
            self.add_project_name_footer()

            # Last-write structural pass: sanitize any TEXT entities that
            # have insert=None (which would otherwise poison ezdxf Frontend
            # rendering and produce blank-PDF output). Also drops unreadable
            # orphan entities. Logging only; never raises.
            self._sanitize_entities_before_save()

            # Save the drawing
            self.doc.saveas(output_file)
            logger.info(f"Bridge GAD drawing saved to: {output_file}")

            return True

        except Exception as e:
            logger.error(f"Error generating complete drawing: {e}")
            return False


def _fmt_num(val: Any) -> str:
    """Format a numeric parameter to 3 decimal places for schedule display."""
    if val is None:
        return ""
    try:
        return f"{float(val):.3f}"
    except (TypeError, ValueError):
        s = str(val).strip()
        return s if s else ""


def generate_bridge_gad(excel_file: Path, output_file: Path = None) -> Path:
    """Main function to generate bridge GAD from Excel input."""
    if output_file is None:
        output_file = excel_file.parent / "bridge_gad_output.dxf"

    generator = BridgeGADGenerator()

    if generator.generate_complete_drawing(excel_file, output_file):
        return output_file
    else:
        raise RuntimeError("Failed to generate bridge GAD drawing")
