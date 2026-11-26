"""
Enhanced LISP Function Implementations for Bridge GAD Generator
This module implements the missing LISP logic as identified in the bug removal prompt.
"""

import math
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)


class EnhancedLispFunctions:
    """Enhanced LISP function implementations for bridge drawing."""

    def __init__(self, doc, msp):
        self.doc = doc
        self.msp = msp
        self.current_layer = "0"

    def set_layer(self, layer_name: str) -> None:
        """Set the current layer for drawing."""
        if layer_name not in self.doc.layers:
            self.doc.layers.add(name=layer_name, color=7)
        self.current_layer = layer_name

    def st(self, text_height: float = 400, arrow_size: float = 150) -> None:
        """Advanced Text Styling - equivalent to LISP st() function.

        Args:
            text_height: Height of text in drawing units
            arrow_size: Size of dimension arrows
        """
        # Set up text style
        if "Arial" not in self.doc.styles:
            self.doc.styles.add("Arial")

        # Set up dimension style
        dimstyle_name = "pmb100"
        if dimstyle_name not in self.doc.dimstyles:
            dimstyle = self.doc.dimstyles.add(dimstyle_name)
            dimstyle.dxf.dimtxt = text_height
            dimstyle.dxf.dimasz = arrow_size
            dimstyle.dxf.dimexe = 400
            dimstyle.dxf.dimexo = 400
            dimstyle.dxf.dimlfac = 1.0
            dimstyle.dxf.dimtxsty = "Arial"
            dimstyle.dxf.dimtad = 0
            dimstyle.dxf.dimtih = 1
            dimstyle.dxf.dimdec = 0

        logger.info(f"Text style '{dimstyle_name}' configured with height {text_height}")

    def enhanced_layout(self,
                        left: float, right: float, datum: float, toprl: float,
                        scale1: float, xincr: float, yincr: float) -> None:
        """Enhanced Layout Grid System - equivalent to LISP layout() function.

        Args:
            left: Left chainage
            right: Right chainage
            datum: Datum level
            toprl: Top reduced level
            scale1: Scale factor
            xincr: X increment for chainage
            yincr: Y increment for levels
        """
        self.set_layer("GRID")

        # Main grid lines
        d1 = 20
        pta1 = (left, datum)
        ptb1 = (left, datum - d1 * scale1)
        pta2 = (right, datum)
        ptb2 = (right, datum - d1 * scale1)
        ptc1 = (left, datum - 2 * d1 * scale1)
        ptc2 = (right, datum - 2 * d1 * scale1)
        ptd1 = (left, toprl)

        # Draw main grid lines
        self.msp.add_line(pta1, pta2, dxfattribs={"layer": self.current_layer})
        self.msp.add_line(ptb1, ptb2, dxfattribs={"layer": self.current_layer})
        self.msp.add_line(ptc1, ptc2, dxfattribs={"layer": self.current_layer})
        self.msp.add_line(ptc1, ptd1, dxfattribs={"layer": self.current_layer})

        # Add labels
        self.set_layer("TEXT")
        ptb3 = (left - 25 * scale1, datum - 0.5 * d1 * scale1)
        self.msp.add_text("BED LEVEL", dxfattribs={
            "height": 2.5 * scale1,
            "layer": self.current_layer
        }).set_placement(ptb3)

        ptb3 = (left - 25 * scale1, datum - 1.5 * d1 * scale1)
        self.msp.add_text("CHAINAGE", dxfattribs={
            "height": 2.5 * scale1,
            "layer": self.current_layer
        }).set_placement(ptb3)

        # Vertical grid lines with level annotations
        nov = int(toprl - datum)
        for i in range(nov + 1):
            lvl = datum + i * yincr
            pta1 = (left - 13 * scale1, lvl)
            self.msp.add_text(f"{lvl:.3f}", dxfattribs={
                "height": 2.0 * scale1,
                "layer": self.current_layer
            }).set_placement((pta1[0] - 40, pta1[1] - 2.5))

            # Grid line
            if i > 0:
                pta1 = (left - 2.5 * scale1, lvl)
                pta2 = (left + 2.5 * scale1, lvl)
                self.msp.add_line(pta1, pta2, dxfattribs={
                    "layer": "GRID",
                    "color": 7  # Gray
                })

        # Horizontal grid lines with chainage annotations
        noh = right - left
        n = int(noh / xincr)
        d4 = 2 * d1
        d5 = d4 - 2.0
        d8 = d4 - 4.0

        for a in range(1, n + 1):
            ch = left + a * xincr
            b1 = f"{ch:.3f}"
            pta1 = (ch, datum - d8 * scale1)

            # Chainage text
            self.msp.add_text(b1, dxfattribs={
                "height": 2.0 * scale1,
                "rotation": 90,
                "layer": self.current_layer
            }).set_placement((pta1[0], pta1[1] - 5))

            # Grid line
            pta1 = (ch, datum - d4 * scale1)
            pta2 = (ch, datum - d5 * scale1)
            self.msp.add_line(pta1, pta2, dxfattribs={
                "layer": "GRID",
                "color": 7  # Gray
            })

        logger.info("Enhanced layout grid system completed")

    def enhanced_cs(self,
                    cs_data: List[Tuple[float, float]],
                    left: float, datum: float, scale1: float, xincr: float) -> None:
        """Enhanced Cross-Section Plotting - equivalent to LISP cs() function.

        Args:
            cs_data: List of (x, y) coordinate pairs for cross-section
            left: Left chainage
            datum: Datum level
            scale1: Scale factor
            xincr: X increment for chainage
        """
        self.set_layer("CROSS_SECTION")

        ptb3 = None
        for a, (x, y) in enumerate(cs_data, 1):
            b1 = f"{x:.3f}"
            b2 = f"{y:.3f}"
            xx = x  # Horizontal position

            d4 = 40.0
            d5 = d4 - 2.0
            d8 = d4 - 4.0
            d9 = 20.0 - 4.0

            # River level annotation
            pta2 = (xx + 0.9 * scale1, datum - d9 * scale1)
            self.msp.add_text(b2, dxfattribs={
                "height": 2.0 * scale1,
                "rotation": 90,
                "layer": self.current_layer
            }).set_placement((pta2[0], pta2[1] - 5))

            # Chainage annotation (if not on grid)
            b = (x - left) % xincr
            if b != 0.0:
                pta1 = (xx + 0.9 * scale1, datum - d8 * scale1)
                self.msp.add_text(b1, dxfattribs={
                    "height": 1.8 * scale1,
                    "rotation": 90,
                    "layer": self.current_layer
                }).set_placement((pta1[0], pta1[1] - 5))

                # Grid line markers
                pta1 = (xx, datum - d4 * scale1)
                pta2 = (xx, datum - d5 * scale1)
                self.msp.add_line(pta1, pta2, dxfattribs={
                    "layer": self.current_layer
                })

            # Vertical line to datum
            pta5 = (xx, datum - 2 * scale1)
            pta6 = (xx, datum)
            self.msp.add_line(pta5, pta6, dxfattribs={
                "layer": self.current_layer
            })

            # Cross-section line
            ptb4 = (x, y)
            if a > 1 and ptb3 is not None:
                self.msp.add_line(ptb3, ptb4, dxfattribs={
                    "layer": self.current_layer,
                    "lineweight": 2
                })
            ptb3 = ptb4

        logger.info(f"Enhanced cross-section plotting completed with {len(cs_data)} points")

    def enhanced_pier(self,
                      spane: float, RTL: float, Sofl: float, capt: float, capb: float,
                      capw: float, piertw: float, battr: float, pierst: float,
                      futrl: float, futd: float, futw: float, futl: float,
                      skew: float, c: float, s: float, tn: float) -> None:
        """Enhanced Pier Geometry - equivalent to LISP pier() function.

        Args:
            spane: Span end position
            RTL: Top level of right abutment
            Sofl: Soffit level
            capt: Pier cap top level
            capb: Pier cap bottom level
            capw: Width of pier cap
            piertw: Width of pier top
            battr: Pier batter ratio
            pierst: Straight length of pier
            futrl: Founding level of pier foundation
            futd: Depth of pier foundation
            futw: Width of pier foundation
            futl: Length of pier foundation
            skew: Skew angle
            c: Cosine of skew angle
            s: Sine of skew angle
            tn: Tangent of skew angle
        """
        self.set_layer("PIER")
        yc = 0  # Center Y coordinate

        # Elevation: Superstructure
        x1 = spane
        y1 = RTL
        x2 = spane
        y2 = Sofl
        pta1 = (x1 + 25.0, y1)
        pta2 = (x2 - 25.0, y2)

        # Draw superstructure rectangle
        points = [pta1, (pta2[0], pta1[1]), pta2, (pta1[0], pta2[1]), pta1]
        self.msp.add_lwpolyline(points, close=True, dxfattribs={
            "layer": self.current_layer
        })

        # Elevation: Pier cap
        capwsq = capw / c if c != 0 else capw
        x1 = spane - capwsq / 2
        x2 = x1 + capwsq
        y1 = capt
        y2 = capb
        pta1 = (x1, y1)
        pta2 = (x2, y2)

        # Draw pier cap
        points = [pta1, (pta2[0], pta1[1]), pta2, (pta1[0], pta2[1]), pta1]
        self.msp.add_lwpolyline(points, close=True, dxfattribs={
            "layer": self.current_layer
        })

        # Elevation: Pier with batter
        piertwsq = piertw / c if c != 0 else piertw
        x1 = spane - piertwsq / 2
        x3 = x1 + piertwsq
        y2 = futrl + futd
        ofset = (capb - y2) / battr
        ofsetsq = ofset / c if c != 0 else ofset
        x2 = x1 - ofsetsq
        x4 = x3 + ofsetsq
        y4 = y2

        pta1 = (x1, capb)
        pta2 = (x2, y2)
        pta3 = (x3, capb)
        pta4 = (x4, y4)

        # Draw pier sides with batter
        self.msp.add_line(pta1, pta2, dxfattribs={
            "layer": self.current_layer,
            "lineweight": 2
        })
        self.msp.add_line(pta3, pta4, dxfattribs={
            "layer": self.current_layer,
            "lineweight": 2
        })

        # Elevation: Foundation footing
        futwsq = futw / c if c != 0 else futw
        x5 = spane - futwsq / 2
        x6 = x5 + futwsq
        y6 = futrl
        y5 = y4

        pta5 = (x5, y5)
        pta6 = (x6, y6)

        # Draw foundation footing
        points = [pta5, (pta6[0], pta5[1]), pta6, (pta5[0], pta6[1]), pta5]
        self.msp.add_lwpolyline(points, close=True, dxfattribs={
            "layer": self.current_layer
        })

        # Plan: Foundation footing (rotated for skew)
        x7 = spane - futw / 2
        x8 = x7 + futw
        y7 = yc + futl / 2
        y8 = y7 - futl

        pta7 = (x7, y7)
        pta8 = (x8, y8)

        # Rotate for skew
        center = (spane, yc)
        rect_points = [pta7, (pta7[0], pta8[1]), pta8, (pta8[0], pta7[1])]
        rotated_points = [self._rotate_point(p, center, skew) for p in rect_points]

        # Offset for plan view
        plan_offset = 400
        plan_points = [(p[0], p[1] + plan_offset) for p in rotated_points]
        self.msp.add_lwpolyline(plan_points, close=True, dxfattribs={
            "layer": self.current_layer
        })

        # Plan: Pier (rotated for skew)
        pierstsq = pierst / c + abs(piertw * tn) if c != 0 else pierst
        x1 = spane - piertw / 2
        x3 = x1 + piertw
        x2 = x1 - ofset
        x4 = x3 + ofset
        y9 = yc + pierstsq / 2
        y10 = y9 - pierstsq

        # Draw pier plan lines
        lines = [
            ((x2, y9), (x2, y10)),
            ((x1, y9), (x1, y10)),
            ((x3, y9), (x3, y10)),
            ((x4, y9), (x4, y10))
        ]

        for start, end in lines:
            start_rot = self._rotate_point(start, center, skew)
            end_rot = self._rotate_point(end, center, skew)
            plan_start = (start_rot[0], start_rot[1] + plan_offset)
            plan_end = (end_rot[0], end_rot[1] + plan_offset)
            self.msp.add_line(plan_start, plan_end, dxfattribs={
                "layer": self.current_layer
            })

        logger.info("Enhanced pier geometry completed")

    def enhanced_abt1(self,
                      abtl: float, RTL: float, capt: float, ccbr: float, kerbw: float,
                      dwth: float, alcw: float, alcd: float, alfb: float, alfbl: float,
                      altb: float, altbl: float, alfo: float, alfd: float,
                      albb: float, albbl: float, skew: float, c: float, s: float) -> None:
        """Enhanced Abutment Geometry - equivalent to LISP abt1() function.

        Args:
            abtl: Chainage of left abutment
            RTL: Top level of right abutment
            capt: Pier cap top level
            ccbr: Clear carriageway width
            kerbw: Width of kerb
            dwth: Thickness of dirt wall
            alcw: Width of abutment left cap
            alcd: Depth of abutment left cap
            alfb: Batter of abutment left face
            alfbl: Level of abutment left face bottom
            altb: Toe batter of abutment left
            altbl: Level of abutment left toe bottom
            alfo: Offset of abutment left face
            alfd: Depth of abutment left face
            albb: Batter of abutment left back
            albbl: Level of abutment left back bottom
            skew: Skew angle
            c: Cosine of skew angle
            s: Sine of skew angle
        """
        self.set_layer("ABUTMENT")

        # Calculate abutment dimensions
        ccbrsq = ccbr / c if c != 0 else ccbr
        kerbwsq = kerbw / c if c != 0 else kerbw
        abtlen = ccbrsq + 2 * kerbwsq

        # Elevation calculations
        x1 = abtl
        alcwsq = alcw
        x3 = x1 + alcwsq
        capb = capt - alcd
        p1 = (capb - alfbl) / alfb
        p1sq = p1
        x5 = x3 + p1sq
        p2 = (alfbl - altbl) / altb
        p2sq = p2
        x6 = x5 + p2sq
        alfosq = alfo
        x7 = x6 + alfosq
        y8 = altbl - alfd
        dwthsq = dwth
        x14 = x1 - dwthsq
        p3 = (capb - albbl) / albb
        p3sq = p3
        x12 = x14 - p3sq
        x10 = x12 - alfosq

        # Create elevation points
        points = [
            (x1, RTL), (x1, capt), (x3, capt), (x3, capb),
            (x5, alfbl), (x6, altbl), (x7, altbl), (x7, y8),
            (x10, y8), (x10, altbl), (x12, altbl), (x12, albbl),
            (x14, capb), (x14, RTL), (x1, RTL)
        ]

        # Draw elevation outline
        self.msp.add_lwpolyline(points, close=True, dxfattribs={
            "layer": self.current_layer
        })

        # Draw internal lines
        self.msp.add_line((x14, capb), (x3, capb), dxfattribs={
            "layer": self.current_layer
        })
        self.msp.add_line((x10, altbl), (x7, altbl), dxfattribs={
            "layer": self.current_layer
        })
        self.msp.add_line((x12, albbl), (x12, RTL), dxfattribs={
            "layer": self.current_layer
        })
        self.msp.add_line((x12, RTL), (x14, RTL), dxfattribs={
            "layer": self.current_layer
        })

        # Plan view calculations
        yc = 0  # Center Y coordinate
        y20 = yc + abtlen / 2
        y21 = y20 - abtlen
        y16 = y20 + 0.15
        y17 = y21 - 0.15
        footl = (y16 - y17) / 2
        x = footl * s
        y = footl * (1 - c)

        # Create plan view points
        pt16 = (x10 - x, y16 - y)
        pt17 = (x10 + x, y17 + y)
        pt18 = (x7 - x, y16 - y)
        pt19 = (x7 + x, y17 + y)

        # Draw plan view outline
        plan_points = [pt16, pt17, pt19, pt18, pt16]
        self.msp.add_lwpolyline(plan_points, close=True, dxfattribs={
            "layer": self.current_layer
        })

        # Additional plan view lines
        xx = abtlen / 2
        x = xx * s
        y = xx * (1 - c)
        y20 -= y
        y21 += y

        # Create additional plan view points
        plan_lines = [
            ((x12 - x, y20), (x12 + x, y21)),
            ((x14 - x, y20), (x14 + x, y21)),
            ((x1 - x, y20), (x1 + x, y21)),
            ((x3 - x, y20), (x3 + x, y21)),
            ((x5 - x, y20), (x5 + x, y21)),
            ((x6 - x, y20), (x6 + x, y21)),
            ((x12 + x, y21), (x6 + x, y21)),
            ((x12 - x, y20), (x6 - x, y20))
        ]

        # Draw additional plan view lines
        for start, end in plan_lines:
            self.msp.add_line(start, end, dxfattribs={
                "layer": self.current_layer
            })

        logger.info("Enhanced abutment geometry completed")

    def _rotate_point(self, point: Tuple[float, float],
                      center: Tuple[float, float], angle: float) -> Tuple[float, float]:
        """Rotate a point around a center by given angle in degrees."""
        angle_rad = math.radians(angle)
        x, y = point[0] - center[0], point[1] - center[1]
        new_x = x * math.cos(angle_rad) - y * math.sin(angle_rad)
        new_y = x * math.sin(angle_rad) + y * math.cos(angle_rad)
        return (new_x + center[0], new_y + center[1])

    def create_professional_layout(self,
                                   width: float, height: float,
                                   title: str = "Bridge General Arrangement Drawing",
                                   scale: str = "1:100",
                                   drawing_number: str = "BGD-001") -> None:
        """Create professional plotting layout with title block.

        Args:
            width: Drawing width
            height: Drawing height
            title: Drawing title
            scale: Drawing scale
            drawing_number: Drawing number
        """
        self.set_layer("TITLE_BLOCK")

        # Title block dimensions
        title_height = 40
        title_width = width

        # Draw title block border
        title_points = [
            (0, 0), (title_width, 0), (title_width, title_height), (0, title_height), (0, 0)
        ]
        self.msp.add_lwpolyline(title_points, close=True, dxfattribs={
            "layer": self.current_layer,
            "lineweight": 3
        })

        # Add title
        self.msp.add_text(title, dxfattribs={
            "height": 8,
            "layer": self.current_layer
        }).set_placement((title_width / 2, title_height - 10), align="MIDDLE_CENTER")

        # Add scale
        self.msp.add_text(f"Scale: {scale}", dxfattribs={
            "height": 4,
            "layer": self.current_layer
        }).set_placement((title_width - 20, title_height - 20), align="TOP_RIGHT")

        # Add drawing number
        self.msp.add_text(f"Drawing No: {drawing_number}", dxfattribs={
            "height": 4,
            "layer": self.current_layer
        }).set_placement((20, title_height - 20), align="TOP_LEFT")

        # Add date
        from datetime import datetime
        date_str = datetime.now().strftime("%Y-%m-%d")
        self.msp.add_text(f"Date: {date_str}", dxfattribs={
            "height": 4,
            "layer": self.current_layer
        }).set_placement((20, title_height - 30), align="TOP_LEFT")

        logger.info("Professional layout with title block created")
