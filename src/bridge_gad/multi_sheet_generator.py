"""
Multi-sheet detailed drawing generator.

Generates detailed A4 landscape sheets and a phase two package that is closer to
an actual submission bundle.
"""

import ezdxf
from ezdxf.document import Drawing
from pathlib import Path
from typing import Dict

from .standards import get_owner_profile, phase_two_sheet_rows, phase_three_sheet_rows


class DetailedSheetGenerator:
    """Generates detailed A4 landscape sheets with professional formatting"""

    # A4 Landscape dimensions (mm to DXF units)
    A4_WIDTH = 297
    A4_HEIGHT = 210
    MARGIN = 10
    TITLE_HEIGHT = 30

    def __init__(self, acad_version: str = "R2010"):
        """Initialize for multi-sheet generation"""
        self.acad_version = acad_version
        self.sheets = []

    def _create_sheet(self, sheet_title: str):
        """Create new sheet document"""
        doc = ezdxf.new(self.acad_version)
        msp = doc.modelspace()
        return doc, msp

    def _draw_border(self, msp, sheet_num: int):
        """Draw A4 landscape border with professional frame"""
        # Outer border
        points_outer = [
            (self.MARGIN, self.MARGIN),
            (self.A4_WIDTH - self.MARGIN, self.MARGIN),
            (self.A4_WIDTH - self.MARGIN, self.A4_HEIGHT - self.MARGIN),
            (self.MARGIN, self.A4_HEIGHT - self.MARGIN),
            (self.MARGIN, self.MARGIN)
        ]
        msp.add_lwpolyline(points_outer, dxfattribs={'lineweight': 50})

        # Inner border
        inner_margin = self.MARGIN + 2
        points_inner = [
            (inner_margin, inner_margin),
            (self.A4_WIDTH - inner_margin, inner_margin),
            (self.A4_WIDTH - inner_margin, self.A4_HEIGHT - inner_margin),
            (inner_margin, self.A4_HEIGHT - inner_margin),
            (inner_margin, inner_margin)
        ]
        msp.add_lwpolyline(points_inner, dxfattribs={'lineweight': 25})

    def _draw_title_block(self, msp, sheet_title: str, sheet_num: int, total_sheets: int, variables: Dict):
        """Draw standards-aware title block."""
        _ = self.MARGIN + 2

        # Title block background rectangle
        title_y_start = self.A4_HEIGHT - self.MARGIN - 25
        title_y_end = self.A4_HEIGHT - self.MARGIN - 5

        rect_points = [
            (self.MARGIN + 3, title_y_start),
            (self.A4_WIDTH - self.MARGIN - 3, title_y_start),
            (self.A4_WIDTH - self.MARGIN - 3, title_y_end),
            (self.MARGIN + 3, title_y_end),
            (self.MARGIN + 3, title_y_start)
        ]
        msp.add_lwpolyline(rect_points, dxfattribs={'lineweight': 35})

        # Title text
        title_text = sheet_title
        msp.add_text(title_text, dxfattribs={
            'height': 3.5,
            'style': 'STANDARD'
        }).set_placement((self.MARGIN + 5, title_y_end - 5))

        # Company info
        company = str(variables.get('COMPANY_NAME', 'Bridge GAD Generator'))
        msp.add_text(f"By: {company}", dxfattribs={
            'height': 2,
            'style': 'STANDARD'
        }).set_placement((self.MARGIN + 5, title_y_end - 10))

        # Project info
        project = str(variables.get('PROJECT_NAME', 'Bridge Project'))
        msp.add_text(f"Project: {project}", dxfattribs={
            'height': 2,
            'style': 'STANDARD'
        }).set_placement((self.A4_WIDTH - 80, title_y_end - 5))

        # Sheet number
        sheet_text = f"Sheet {sheet_num} of {total_sheets}"
        msp.add_text(sheet_text, dxfattribs={
            'height': 2,
            'style': 'STANDARD'
        }).set_placement((self.A4_WIDTH - 80, title_y_end - 10))

        drawing_no = str(variables.get("DRAWING_NO", "GAD-001"))
        revision = str(variables.get("REVISION", "R0"))
        owner_profile = get_owner_profile(variables.get("OWNER_PROFILE"))
        msp.add_text(f"Drg: {drawing_no}  Rev: {revision}", dxfattribs={'height': 1.8}).set_placement(
            (self.A4_WIDTH - 80, title_y_end - 15)
        )
        msp.add_text(f"Basis: {owner_profile.owner}", dxfattribs={'height': 1.8}).set_placement(
            (self.MARGIN + 70, title_y_end - 10)
        )

        # Contact info footer. PII defaults come from env vars.
        import os as _os
        address = str(variables.get('ADDRESS', '303 Vallabh Apartment, Udaipur'))
        email = str(variables.get('EMAIL', _os.environ.get('CONTACT_EMAIL', 'contact@example.com')))
        phone = str(variables.get('MOBILE', _os.environ.get('CONTACT_PHONE', '+91XXXXXXXXXX')))

        footer_y = self.MARGIN + 3
        msp.add_text(f"Addr: {address[:40]}", dxfattribs={'height': 1.5}).set_placement((self.MARGIN + 5, footer_y))
        msp.add_text(f"Email: {email}", dxfattribs={'height': 1.5}).set_placement((self.MARGIN + 5, footer_y - 3))
        msp.add_text(f"Phone: {phone}", dxfattribs={'height': 1.5}).set_placement((self.MARGIN + 5, footer_y - 6))

    def _save_sheet_set(self, sheets, output_path: Path):
        """Save a sheet list to numbered DXF files."""

        output_dir = output_path.parent
        output_stem = output_path.stem
        filenames = []
        for i, sheet in enumerate(sheets, 1):
            filename = output_dir / f"{output_stem}_Sheet{i}.dxf"
            sheet.saveas(filename)
            filenames.append(filename)
        return filenames

    def generate_index_sheet(self, variables: Dict) -> Drawing:
        """Generate the phase two or three drawing index sheet.

        The index uses phase_three_sheet_rows (11 rows) when either the
        TOTAL_SHEETS variable or the include_phase_three flag is set to
        request the phase three appendix.  Otherwise the classic 7-row
        phase two schedule is used.
        """
        total_hint = int(str(variables.get("TOTAL_SHEETS") or 0) or 0)
        include_p3 = bool(variables.get("INCLUDE_PHASE_THREE")) or total_hint >= 11
        rows_source = phase_three_sheet_rows() if include_p3 else phase_two_sheet_rows()
        title_base = (
            "DRAWING INDEX AND BASIS (PHASE 3 — 11 SHEETS)" if include_p3
            else "DRAWING INDEX AND BASIS"
        )

        doc, msp = self._create_sheet("DRAWING INDEX")
        self._draw_border(msp, 1)
        self._draw_title_block(msp, title_base, 1, len(rows_source), variables)

        start_x = 25
        start_y = 150
        row_h = 12
        col_x = [start_x, start_x + 22, start_x + 52, start_x + 150]

        msp.add_text("Sheet", dxfattribs={'height': 2.5}).set_placement((col_x[0], start_y))
        msp.add_text("Code", dxfattribs={'height': 2.5}).set_placement((col_x[1], start_y))
        msp.add_text("Title", dxfattribs={'height': 2.5}).set_placement((col_x[2], start_y))
        msp.add_text("Purpose", dxfattribs={'height': 2.5}).set_placement((col_x[3], start_y))

        y = start_y - 8
        for row in rows_source:
            msp.add_line((start_x, y + 3), (self.A4_WIDTH - 25, y + 3))
            msp.add_text(row["Sheet No"], dxfattribs={'height': 2.0}).set_placement((col_x[0], y))
            msp.add_text(row["Code"], dxfattribs={'height': 2.0}).set_placement((col_x[1], y))
            msp.add_text(row["Title"], dxfattribs={'height': 2.0}).set_placement((col_x[2], y))
            msp.add_text(row["Purpose"], dxfattribs={'height': 1.8}).set_placement((col_x[3], y))
            y -= row_h

        profile = get_owner_profile(variables.get("OWNER_PROFILE"))
        msp.add_text(f"Owner Profile: {profile.owner}", dxfattribs={'height': 2.2}).set_placement((25, 55))
        msp.add_text(f"Drawing Standard: {profile.drawing_standard[:70]}", dxfattribs={'height': 2.0}).set_placement((25, 47))
        msp.add_text(f"Live Load Basis: {profile.design_live_load[:72]}", dxfattribs={'height': 2.0}).set_placement((25, 39))
        if include_p3:
            msp.add_text(
                "Phase 3 detail sheets: ALL placeholders marked TBC_BY_ENGINEER on drawing (no invented data).",
                dxfattribs={'height': 1.7, 'color': 1},
            ).set_placement((25, 31))
        else:
            msp.add_text(profile.review_note[:90], dxfattribs={'height': 1.8}).set_placement((25, 31))
        return doc

    def generate_bearing_joint_sheet(self, variables: Dict) -> Drawing:
        """Generate a notes-driven bearing and expansion joint sheet."""

        doc, msp = self._create_sheet("BEARING AND JOINT NOTES")
        total = len(phase_two_sheet_rows())
        self._draw_border(msp, 6)
        self._draw_title_block(msp, "BEARING AND EXPANSION JOINT NOTES", 6, total, variables)

        bearing_type = str(variables.get("BEARING_TYPE", "As per design"))
        bearing_w = float(variables.get("BEARING_W", 0.0))
        expjt = float(variables.get("EXPJT", 0.025))
        span1 = float(variables.get("SPAN1", 12))

        box = [(30, 60), (267, 60), (267, 145), (30, 145), (30, 60)]
        msp.add_lwpolyline(box, dxfattribs={'lineweight': 35})
        msp.add_text("Typical note set", dxfattribs={'height': 3.0}).set_placement((35, 138))
        notes = [
            f"1. Bearing system: {bearing_type}",
            f"2. Indicative bearing seat width: {bearing_w:.2f} m",
            f"3. Expansion joint movement gap shown in GAD: {expjt:.3f} m",
            f"4. Review expansion provisions against final span arrangement of {span1:.2f} m typical span.",
            "5. Final bearing schedule, load table, and manufacturer data to be issued in detail drawings.",
        ]
        y = 126
        for note in notes:
            msp.add_text(note, dxfattribs={'height': 2.2}).set_placement((38, y))
            y -= 14
        return doc

    def generate_drainage_utility_sheet(self, variables: Dict) -> Drawing:
        """Generate a drainage, safety, and utility notes sheet."""

        doc, msp = self._create_sheet("DRAINAGE SAFETY UTILITY")
        total = len(phase_two_sheet_rows())
        self._draw_border(msp, 7)
        self._draw_title_block(msp, "DRAINAGE, SAFETY AND UTILITY NOTES", 7, total, variables)

        drainsp = float(variables.get("DRAINSP", 0.0))
        barrierh = float(variables.get("BARRIERH", 0.0))
        barrier_type = str(variables.get("BARRIERT", "Barrier / parapet"))
        utilityd = float(variables.get("UTILITYD", 0.0))

        box = [(30, 60), (267, 60), (267, 145), (30, 145), (30, 60)]
        msp.add_lwpolyline(box, dxfattribs={'lineweight': 35})
        notes = [
            f"1. Drainage spout spacing shown/assumed: {drainsp:.2f} m",
            f"2. Safety edge treatment: {barrier_type}, height {barrierh:.2f} m",
            f"3. Utility duct width reserved in typical section: {utilityd:.2f} m",
            "4. Confirm outlet locations, down-take routing, and maintenance access in detail design.",
            "5. Barrier, kerb, and utility details to be coordinated with owner-specific standard drawings.",
        ]
        y = 132
        for note in notes:
            msp.add_text(note, dxfattribs={'height': 2.2}).set_placement((38, y))
            y -= 14
        return doc

    def _draw_dimensions(self, msp, positions: list, labels: list):
        """Add dimension lines and labels"""
        for pos, label in zip(positions, labels):
            x, y = pos
            # Dimension line
            msp.add_line((x - 5, y), (x + 5, y), dxfattribs={'lineweight': 15})
            # Label text
            msp.add_text(label, dxfattribs={'height': 2}).set_placement((x - 3, y + 2))

    def generate_pier_elevation(self, variables: Dict, sheet_num: int = 1, total_sheets: int = 4) -> Drawing:
        """Generate detailed pier elevation sheet"""
        doc, msp = self._create_sheet("PIER ELEVATION")
        self._draw_border(msp, sheet_num)
        self._draw_title_block(msp, "PIER ELEVATION - ENLARGED", sheet_num, total_sheets, variables)

        # Get dimensions
        piertw = float(variables.get('PIERTW', 1.2))
        _ = float(variables.get('SPAN1', 12))
        rtl = float(variables.get('RTL', 110.98))
        datum = float(variables.get('DATUM', 100))
        futd = float(variables.get('FUTD', 1.0))
        futw = float(variables.get('FUTW', 4.5))

        # Draw pier (scaled for A4)
        scale = 3  # Scale factor for detail sheet
        pier_base_x = 100
        pier_base_y = 80

        # Pier shaft
        pier_top_y = pier_base_y + (rtl - datum) * scale
        pier_points = [
            (pier_base_x, pier_base_y),
            (pier_base_x + piertw * scale, pier_base_y),
            (pier_base_x + piertw * scale, pier_top_y),
            (pier_base_x, pier_top_y),
            (pier_base_x, pier_base_y)
        ]
        msp.add_lwpolyline(pier_points, dxfattribs={'lineweight': 50, 'color': 2})

        # Footing
        foot_y = pier_base_y - futd * scale
        foot_points = [
            (pier_base_x - (futw - piertw) / 2 * scale, pier_base_y),
            (pier_base_x + piertw * scale + (futw - piertw) / 2 * scale, pier_base_y),
            (pier_base_x + piertw * scale + (futw - piertw) / 2 * scale, foot_y),
            (pier_base_x - (futw - piertw) / 2 * scale, foot_y),
            (pier_base_x - (futw - piertw) / 2 * scale, pier_base_y)
        ]
        msp.add_lwpolyline(foot_points, dxfattribs={'lineweight': 35, 'color': 3})

        # Dimensions - Pier width
        dim_y = pier_base_y - 10
        msp.add_line((pier_base_x, dim_y), (pier_base_x + piertw * scale, dim_y),
                     dxfattribs={'lineweight': 15})
        msp.add_text(f"Pier Width: {piertw}m", dxfattribs={'height': 2.5}).set_placement(
            (pier_base_x + piertw * scale / 2 - 8, dim_y - 3))

        # Dimensions - Pier height
        dim_x = pier_base_x - 15
        msp.add_line((dim_x, pier_base_y), (dim_x, pier_top_y),
                     dxfattribs={'lineweight': 15})
        height_label = f"Height: {rtl - datum:.2f}m"
        msp.add_text(height_label, dxfattribs={'height': 2.5}).set_placement(
            (dim_x - 12, pier_base_y + (pier_top_y - pier_base_y) / 2))

        # Dimensions - Footing width
        foot_dim_y = foot_y - 8
        msp.add_line((pier_base_x - (futw - piertw) / 2 * scale, foot_dim_y),
                     (pier_base_x + piertw * scale + (futw - piertw) / 2 * scale, foot_dim_y),
                     dxfattribs={'lineweight': 15})
        msp.add_text(f"Footing Width: {futw}m", dxfattribs={'height': 2.5}).set_placement(
            (pier_base_x + piertw * scale / 2 - 10, foot_dim_y - 3))

        # Ground line
        msp.add_line((pier_base_x - 15, pier_base_y), (pier_base_x + piertw * scale + 15, pier_base_y),
                     dxfattribs={'lineweight': 25, 'linetype': 'DASHED'})
        msp.add_text("GROUND LEVEL", dxfattribs={'height': 2}).set_placement(
            (pier_base_x - 10, pier_base_y + 2))

        return doc

    def generate_abutment_elevation(self, variables: Dict, sheet_num: int = 2, total_sheets: int = 4) -> Drawing:
        """Generate detailed abutment elevation sheet"""
        doc, msp = self._create_sheet("ABUTMENT ELEVATION")
        self._draw_border(msp, sheet_num)
        self._draw_title_block(msp, "ABUTMENT ELEVATION - ENLARGED", sheet_num, total_sheets, variables)

        # Get dimensions
        # Bug 4 (CRITICAL): ABTL defaults to 0.0 in many templates (simple_12m
        # verified) → zero-length wall.  When ABTL is degenerate (< 1.0 m)
        # fall back through PMGSY-standard parameters that are reliably set:
        #   FUTL  (abutment footing length — default 13.0 in specs)
        #   ALCL  (abutment-left clear length)
        #   ALCW  (abutment-left clear width)
        # Never invent engineering numbers; just take best available length
        # from existing real PMGSY params already in the template workbook.
        raw_abtl = float(variables.get('ABTL', 0.0))
        futl = float(variables.get('FUTL', variables.get('FOOTL', variables.get('FUTRL', 13.0))))
        alcl = float(variables.get('ALCL', 0.0))
        alcw = float(variables.get('ALCW', 0.0))
        if raw_abtl >= 1.0:
            abtl = raw_abtl
        elif futl >= 1.0:
            abtl = futl
        elif alcl >= 1.0:
            abtl = alcl
        elif alcw >= 1.0:
            abtl = alcw
        else:
            abtl = 13.0  # spec default; only reached if ALL are missing
        abtl_source = "ABTL" if raw_abtl >= 1.0 else (
            "FUTL" if futl >= 1.0 else (
                "ALCL" if alcl >= 1.0 else (
                    "ALCW" if alcw >= 1.0 else "SPEC-DEFAULT")))
        rtl = float(variables.get('RTL', 110.98))
        datum = float(variables.get('DATUM', 100))
        _ = float(variables.get('CCBR', 11.1))
        _ = float(variables.get('FUTW', 4.5))
        futd = float(variables.get('FUTD', 1.0))

        scale = 2.5
        abt_base_x = 100
        abt_base_y = 80

        # Abutment wall
        abt_top_y = abt_base_y + (rtl - datum) * scale
        abt_points = [
            (abt_base_x, abt_base_y),
            (abt_base_x + abtl * scale, abt_base_y),
            (abt_base_x + abtl * scale, abt_top_y),
            (abt_base_x, abt_top_y),
            (abt_base_x, abt_base_y)
        ]
        msp.add_lwpolyline(abt_points, dxfattribs={'lineweight': 50, 'color': 4})

        # Footing (protrude 2.0m each side, or 5 scaled-units whichever larger)
        foot_protrude = max(5, 2.0 * scale)
        foot_y = abt_base_y - futd * scale
        foot_points = [
            (abt_base_x - foot_protrude, abt_base_y),
            (abt_base_x + abtl * scale + foot_protrude, abt_base_y),
            (abt_base_x + abtl * scale + foot_protrude, foot_y),
            (abt_base_x - foot_protrude, foot_y),
            (abt_base_x - foot_protrude, abt_base_y)
        ]
        msp.add_lwpolyline(foot_points, dxfattribs={'lineweight': 35, 'color': 5})

        # Dimensions
        dim_y = abt_base_y - 10
        msp.add_line((abt_base_x, dim_y), (abt_base_x + abtl * scale, dim_y),
                     dxfattribs={'lineweight': 15})
        msp.add_text(f"Length: {abtl:.1f}m (from {abtl_source})",
                     dxfattribs={'height': 2.5}).set_placement(
            (abt_base_x + abtl * scale / 2 - 14, dim_y - 3))

        dim_x = abt_base_x - 15
        msp.add_line((dim_x, abt_base_y), (dim_x, abt_top_y),
                     dxfattribs={'lineweight': 15})
        height_label = f"Height: {rtl - datum:.2f}m"
        msp.add_text(height_label, dxfattribs={'height': 2.5}).set_placement(
            (dim_x - 12, abt_base_y + (abt_top_y - abt_base_y) / 2))

        # Ground line
        msp.add_line((abt_base_x - 10, abt_base_y), (abt_base_x + abtl * scale + 10, abt_base_y),
                     dxfattribs={'lineweight': 25, 'linetype': 'DASHED'})
        msp.add_text("GROUND LEVEL", dxfattribs={'height': 2}).set_placement(
            (abt_base_x, abt_base_y + 2))

        return doc

    def generate_plan_view(self, variables: Dict, sheet_num: int = 3, total_sheets: int = 4) -> Drawing:
        """Generate plan view (top view) sheet"""
        doc, msp = self._create_sheet("PLAN VIEW")
        self._draw_border(msp, sheet_num)
        self._draw_title_block(msp, "PLAN VIEW - TOP", sheet_num, total_sheets, variables)

        nspan = int(variables.get('NSPAN', 3))
        span1 = float(variables.get('SPAN1', 12))
        ccbr = float(variables.get('CCBR', 11.1))
        piertw = float(variables.get('PIERTW', 1.2))

        scale = 2.0
        start_x = 80
        start_y = 100

        # Draw spans (rectangles)
        for i in range(nspan):
            x_pos = start_x + i * span1 * scale
            rect_points = [
                (x_pos, start_y),
                (x_pos + span1 * scale, start_y),
                (x_pos + span1 * scale, start_y + ccbr * scale),
                (x_pos, start_y + ccbr * scale),
                (x_pos, start_y)
            ]
            msp.add_lwpolyline(rect_points, dxfattribs={'lineweight': 40, 'color': 1})

            # Span label
            span_label = f"Span {i+1}: {span1}m"
            msp.add_text(span_label, dxfattribs={'height': 2}).set_placement(
                (x_pos + span1 * scale / 2 - 5, start_y + ccbr * scale + 3))

        # Draw piers (between spans)
        for i in range(nspan - 1):
            pier_x = start_x + (i + 1) * span1 * scale
            pier_points = [
                (pier_x - piertw * scale / 2, start_y - 5),
                (pier_x + piertw * scale / 2, start_y - 5),
                (pier_x + piertw * scale / 2, start_y + ccbr * scale + 5),
                (pier_x - piertw * scale / 2, start_y + ccbr * scale + 5),
                (pier_x - piertw * scale / 2, start_y - 5)
            ]
            msp.add_lwpolyline(pier_points, dxfattribs={'lineweight': 50, 'color': 2})

        # Dimensions - Span lengths
        dim_y = start_y - 15
        for i in range(nspan):
            x_pos = start_x + i * span1 * scale
            msp.add_line((x_pos, dim_y), (x_pos + span1 * scale, dim_y),
                         dxfattribs={'lineweight': 15})

        # Dimension - Width
        dim_x = start_x - 15
        msp.add_line((dim_x, start_y), (dim_x, start_y + ccbr * scale),
                     dxfattribs={'lineweight': 15})
        msp.add_text(f"Width: {ccbr}m", dxfattribs={'height': 2.5}).set_placement(
            (dim_x - 8, start_y + ccbr * scale / 2))

        # Total length dimension
        total_length = nspan * span1
        total_dim_y = start_y + ccbr * scale + 15
        msp.add_line((start_x, total_dim_y), (start_x + total_length * scale, total_dim_y),
                     dxfattribs={'lineweight': 20})
        msp.add_text(f"Total Length: {total_length}m", dxfattribs={'height': 2.5}).set_placement(
            (start_x + total_length * scale / 2 - 12, total_dim_y + 3))

        return doc

    def generate_section_view(self, variables: Dict, sheet_num: int = 4, total_sheets: int = 4) -> Drawing:
        """Generate section/profile view sheet"""
        doc, msp = self._create_sheet("SECTION VIEW")
        self._draw_border(msp, sheet_num)
        self._draw_title_block(msp, "SECTION VIEW - PROFILE", sheet_num, total_sheets, variables)

        # Get dimensions
        span1 = float(variables.get('SPAN1', 12))
        _ = float(variables.get('CCBR', 11.1))
        slbthe = float(variables.get('SLBTHE', 0.75))
        rtl = float(variables.get('RTL', 110.98))
        datum = float(variables.get('DATUM', 100))
        futd = float(variables.get('FUTD', 1.0))
        piertw = float(variables.get('PIERTW', 1.2))

        scale_h = 3.0  # Horizontal scale
        scale_v = 4.0  # Vertical scale (exaggerated for clarity)

        start_x = 60
        start_y = 80

        # Draw ground/datum line
        ground_y = start_y
        msp.add_line((start_x, ground_y), (start_x + span1 * scale_h + piertw * scale_h * 2, ground_y),
                     dxfattribs={'lineweight': 25, 'linetype': 'DASHED'})
        msp.add_text("DATUM", dxfattribs={'height': 2}).set_placement((start_x, ground_y - 3))

        # Draw deck slab
        deck_y_top = ground_y + (rtl - datum) * scale_v
        slab_points = [
            (start_x + piertw * scale_h, deck_y_top - slbthe * scale_v),
            (start_x + span1 * scale_h + piertw * scale_h, deck_y_top - slbthe * scale_v),
            (start_x + span1 * scale_h + piertw * scale_h, deck_y_top),
            (start_x + piertw * scale_h, deck_y_top),
            (start_x + piertw * scale_h, deck_y_top - slbthe * scale_v)
        ]
        msp.add_lwpolyline(slab_points, dxfattribs={'lineweight': 50, 'color': 6})

        # Draw pier
        pier_top_y = deck_y_top - slbthe * scale_v
        pier_points = [
            (start_x + span1 * scale_h, ground_y - futd * scale_v),
            (start_x + span1 * scale_h + piertw * scale_h, ground_y - futd * scale_v),
            (start_x + span1 * scale_h + piertw * scale_h, pier_top_y),
            (start_x + span1 * scale_h, pier_top_y),
            (start_x + span1 * scale_h, ground_y - futd * scale_v)
        ]
        msp.add_lwpolyline(pier_points, dxfattribs={'lineweight': 45, 'color': 2})

        # Dimensions - Slab thickness
        slab_dim_x = start_x + piertw * scale_h - 8
        msp.add_line((slab_dim_x, deck_y_top - slbthe * scale_v),
                     (slab_dim_x, deck_y_top),
                     dxfattribs={'lineweight': 15})
        msp.add_text(f"{slbthe}m", dxfattribs={'height': 2}).set_placement(
            (slab_dim_x - 5, deck_y_top - slbthe * scale_v / 2))

        # Dimensions - Span
        span_dim_y = deck_y_top + 8
        msp.add_line((start_x + piertw * scale_h, span_dim_y),
                     (start_x + span1 * scale_h + piertw * scale_h, span_dim_y),
                     dxfattribs={'lineweight': 15})
        msp.add_text(f"Span: {span1}m", dxfattribs={'height': 2.5}).set_placement(
            (start_x + span1 * scale_h / 2 - 4, span_dim_y + 2))

        # Dimensions - Height
        height_dim_x = start_x + span1 * scale_h + piertw * scale_h + 8
        msp.add_line((height_dim_x, ground_y - futd * scale_v),
                     (height_dim_x, deck_y_top),
                     dxfattribs={'lineweight': 15})
        height_val = (rtl - datum) + futd
        msp.add_text(f"Height: {height_val:.2f}m", dxfattribs={'height': 2.5}).set_placement(
            (height_dim_x + 2, ground_y - futd * scale_v + height_val * scale_v / 2))

        return doc

    def _draw_tbc_stamp(self, msp, corner_ll, corner_ur):
        """Draw a non-erasable TBC_BY_ENGINEER frame over technical placeholders.

        The frame warns the reviewer that dimensions inside are NOT real
        engineering values but placeholders derived from proportions or
        defaulted to TBC.  Compliance with the no-invented-data rule.
        """
        x1, y1 = corner_ll
        x2, y2 = corner_ur
        msp.add_lwpolyline(
            [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)],
            dxfattribs={'lineweight': 60, 'linetype': 'DASHED', 'color': 1},
        )
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        msp.add_text(
            "TBC_BY_ENGINEER",
            dxfattribs={'height': 2.8, 'style': 'STANDARD', 'color': 1},
        ).set_placement((cx - 18, cy - 1.2))

    # =================================================================
    # PHASE 3 — parametric detail sheets
    # All values not derived from existing PARAMETER_SPECS are explicitly
    # ring-fenced with the TBC_BY_ENGINEER stamp above.
    # =================================================================

    def generate_bearing_detail_sheet(self, variables: Dict) -> Drawing:
        """Generate Bearing Detail sheet (BRG-DET) — plan + section through bearing seat."""

        title = "BEARING DETAILS — PLAN AND SECTION"
        doc, msp = self._create_sheet(title)
        total = len(phase_three_sheet_rows())
        self._draw_border(msp, 8)
        self._draw_title_block(msp, title, 8, total, variables)

        # --- Parameters (derived from existing PARAMETER_SPECS when possible)
        bw = float(variables.get("BEARING_W", 0.3) or 0.3)
        bl = float(variables.get("BEARING_L", 0.0) or 0.0)
        if bl <= 0:
            bl = 1.2 * bw  # indicative proportion only (TBC stamped)
        bt = float(variables.get("BEARING_T", 0.05) or 0.05)
        pier_top_w = float(variables.get("PIERTW", 1.2) or 1.2)
        pier_st = float(variables.get("PIERST", pier_top_w) or pier_top_w)
        dowel_d_mm = float(variables.get("BEARING_DOWEL_D", 0.0) or 0.0)
        dowel_n = int(variables.get("BEARING_DOWEL_N", 4) or 4)
        pad_type = str(variables.get("BEARING_PAD_TYPE") or variables.get("BEARING_TYPE") or "Elastomeric pad")

        # --- Scale: bridge metres -> DXF mm on A4 (detail scale)
        scale_plan = 30.0  # 1 m = 30 mm => ~1:33 for 3 m bearing width
        scale_sec = scale_plan

        # --- BEARING PLAN VIEW (top-left area)
        plan_cx, plan_cy = 95, 150
        bw_dx = bw * scale_plan
        bl_dx = bl * scale_plan
        plan_x0 = plan_cx - bw_dx / 2
        plan_y0 = plan_cy - bl_dx / 2
        plan_poly = [
            (plan_x0, plan_y0),
            (plan_x0 + bw_dx, plan_y0),
            (plan_x0 + bw_dx, plan_y0 + bl_dx),
            (plan_x0, plan_y0 + bl_dx),
            (plan_x0, plan_y0),
        ]
        msp.add_lwpolyline(plan_poly, dxfattribs={'lineweight': 50, 'color': 5})
        # Pier cap hatched rectangle (larger, around pad)
        cap_w = max(pier_top_w * 1.15, bw + 0.4)
        cap_l = max(pier_st * 1.15, bl + 0.4)
        cap_x0 = plan_cx - cap_w * scale_plan / 2
        cap_y0 = plan_cy - cap_l * scale_plan / 2
        msp.add_lwpolyline(
            [
                (cap_x0, cap_y0),
                (cap_x0 + cap_w * scale_plan, cap_y0),
                (cap_x0 + cap_w * scale_plan, cap_y0 + cap_l * scale_plan),
                (cap_x0, cap_y0 + cap_l * scale_plan),
                (cap_x0, cap_y0),
            ],
            dxfattribs={'lineweight': 35, 'color': 2},
        )
        # Dowel markers (schematic)
        for i in range(max(2, dowel_n)):
            frac = (i + 1) / (dowel_n + 1) if dowel_n > 0 else 0.5
            dx = plan_x0 + frac * bw_dx
            dy = plan_y0 + frac * bl_dx
            r = (dowel_d_mm / 2000.0) * scale_plan if dowel_d_mm > 0 else 0.8
            msp.add_circle((dx, dy), max(r, 0.8), dxfattribs={'lineweight': 30, 'color': 1})

        msp.add_text("PLAN", dxfattribs={'height': 2.8}).set_placement((plan_cx - 10, cap_y0 - 6))
        msp.add_text(
            f"Bearing pad: {bw:.2f} x {bl:.2f} m  (type: {pad_type})",
            dxfattribs={'height': 2.0},
        ).set_placement((cap_x0, cap_y0 + cap_l * scale_plan + 4))
        msp.add_text(
            f"Dowels: {dowel_n} no.  D = {dowel_d_mm if dowel_d_mm else 'TBC'} mm",
            dxfattribs={'height': 2.0},
        ).set_placement((cap_x0, cap_y0 + cap_l * scale_plan + 1))

        # TBC stamp for dowel/seat proportions (unless user gave exact values)
        if dowel_d_mm <= 0 or bl == 1.2 * bw:
            self._draw_tbc_stamp(msp, (cap_x0 - 2, cap_y0 - 2),
                                 (cap_x0 + cap_w * scale_plan + 2, cap_y0 + cap_l * scale_plan + 2))

        # --- BEARING SECTION A-A (right side)
        sec_cx = 215
        sec_y_base = 110
        seat_h = (bt * 1.5) * scale_sec  # seat concrete depth = 1.5*pad_t indicative
        pad_h = bt * scale_sec
        _ = 25  # fixed on-sheet visual only
        deck_h = 12
        # Pier / seat block (concrete)
        msp.add_lwpolyline(
            [
                (sec_cx - cap_w * scale_sec / 2, sec_y_base),
                (sec_cx + cap_w * scale_sec / 2, sec_y_base),
                (sec_cx + cap_w * scale_sec / 2, sec_y_base + seat_h),
                (sec_cx - cap_w * scale_sec / 2, sec_y_base + seat_h),
                (sec_cx - cap_w * scale_sec / 2, sec_y_base),
            ],
            dxfattribs={'lineweight': 35, 'color': 2},
        )
        # Pad on seat
        msp.add_lwpolyline(
            [
                (sec_cx - bw_dx / 2, sec_y_base + seat_h),
                (sec_cx + bw_dx / 2, sec_y_base + seat_h),
                (sec_cx + bw_dx / 2, sec_y_base + seat_h + pad_h),
                (sec_cx - bw_dx / 2, sec_y_base + seat_h + pad_h),
                (sec_cx - bw_dx / 2, sec_y_base + seat_h),
            ],
            dxfattribs={'lineweight': 50, 'color': 5},
        )
        # Deck slab above (indicative)
        msp.add_lwpolyline(
            [
                (sec_cx - cap_w * scale_sec / 2 - 10, sec_y_base + seat_h + pad_h),
                (sec_cx + cap_w * scale_sec / 2 + 10, sec_y_base + seat_h + pad_h),
                (sec_cx + cap_w * scale_sec / 2 + 10, sec_y_base + seat_h + pad_h + deck_h),
                (sec_cx - cap_w * scale_sec / 2 - 10, sec_y_base + seat_h + pad_h + deck_h),
                (sec_cx - cap_w * scale_sec / 2 - 10, sec_y_base + seat_h + pad_h),
            ],
            dxfattribs={'lineweight': 40, 'color': 6},
        )
        # Section label + dim
        msp.add_text("SECTION A-A", dxfattribs={'height': 2.8}).set_placement((sec_cx - 16, sec_y_base - 6))
        msp.add_text(
            f"Pad thickness: {bt*1000:.0f} mm  Seat concrete: {bt*1.5*1000:.0f} mm (TBC)",
            dxfattribs={'height': 2.0},
        ).set_placement((sec_cx - cap_w * scale_sec / 2 - 10, sec_y_base + seat_h + pad_h + deck_h + 3))
        # TBC stamp over section (seat thickness is indicative)
        self._draw_tbc_stamp(
            msp,
            (sec_cx - cap_w * scale_sec / 2 - 12, sec_y_base - 8),
            (sec_cx + cap_w * scale_sec / 2 + 12, sec_y_base + seat_h + pad_h + deck_h + 9),
        )

        # --- Notes panel (bottom)
        notes = [
            f"1. Bearing system: {pad_type}",
            f"2. Pad plan: W {bw:.2f} m  x  L {bl:.2f} m  x  T {bt*1000:.0f} mm",
            f"3. Fixing: {dowel_n} dowels/anchors per bearing —  dia {dowel_d_mm if dowel_d_mm else 'TBC'} mm",
            "4. All seat levels, pad grade, SHC and manufacturer data — TBC_BY_ENGINEER.",
            "5. Coordinate bearing schedule with substructure drawings prior to issue.",
        ]
        ny = 65
        for n in notes:
            msp.add_text(n, dxfattribs={'height': 2.0}).set_placement((25, ny))
            ny -= 4
        return doc

    def generate_expansion_joint_detail_sheet(self, variables: Dict) -> Drawing:
        """Generate Expansion Joint Detail sheet (EXPJ-DET)."""

        title = "EXPANSION JOINT DETAILS"
        doc, msp = self._create_sheet(title)
        total = len(phase_three_sheet_rows())
        self._draw_border(msp, 9)
        self._draw_title_block(msp, title, 9, total, variables)

        gap = float(variables.get("EXPJT", 0.025) or 0.025)  # from existing PARAMETER_SPECS
        slot_w = float(variables.get("EJ_SLOT_W", 0.0) or 0.0)
        if slot_w <= 0:
            slot_w = max(0.08, gap + 0.05)  # indicative; TBC stamped
        ej_type = str(variables.get("EJ_TYPE") or "SWSF strip-seal (typical)")
        sealant = str(variables.get("EJ_SEALANT") or "TBC_BY_ENGINEER")
        wc = float(variables.get("WCTH", 0.05) or 0.05)
        slb = float(variables.get("SLBTHE", 0.75) or 0.75)

        scale = 40.0  # 1 m -> 40 mm on sheet (detail scale)
        cx, cy = 148, 140

        deck_dx = 120  # on-sheet total slab visual width (mm)
        slab_h = slb * scale
        wc_h = wc * scale
        half_gap_dx = (gap * scale) / 2
        slot_dx = slot_w * scale

        # --- LEFT SLAB (deck + wearing course)
        msp.add_lwpolyline(
            [
                (cx - deck_dx / 2 - half_gap_dx, cy),
                (cx - half_gap_dx, cy),
                (cx - half_gap_dx, cy + slab_h),
                (cx - deck_dx / 2 - half_gap_dx, cy + slab_h),
                (cx - deck_dx / 2 - half_gap_dx, cy),
            ],
            dxfattribs={'lineweight': 45, 'color': 6},
        )
        # Wearing course on top of left slab
        msp.add_lwpolyline(
            [
                (cx - deck_dx / 2 - half_gap_dx, cy + slab_h),
                (cx - half_gap_dx, cy + slab_h),
                (cx - half_gap_dx, cy + slab_h + wc_h),
                (cx - deck_dx / 2 - half_gap_dx, cy + slab_h + wc_h),
                (cx - deck_dx / 2 - half_gap_dx, cy + slab_h),
            ],
            dxfattribs={'lineweight': 30, 'color': 7},
        )
        # --- RIGHT SLAB (mirror)
        msp.add_lwpolyline(
            [
                (cx + half_gap_dx, cy),
                (cx + deck_dx / 2 + half_gap_dx, cy),
                (cx + deck_dx / 2 + half_gap_dx, cy + slab_h),
                (cx + half_gap_dx, cy + slab_h),
                (cx + half_gap_dx, cy),
            ],
            dxfattribs={'lineweight': 45, 'color': 6},
        )
        msp.add_lwpolyline(
            [
                (cx + half_gap_dx, cy + slab_h),
                (cx + deck_dx / 2 + half_gap_dx, cy + slab_h),
                (cx + deck_dx / 2 + half_gap_dx, cy + slab_h + wc_h),
                (cx + half_gap_dx, cy + slab_h + wc_h),
                (cx + half_gap_dx, cy + slab_h),
            ],
            dxfattribs={'lineweight': 30, 'color': 7},
        )
        # Slot recess (saw-cut or formed)
        msp.add_lwpolyline(
            [
                (cx - slot_dx / 2, cy + slab_h - 0.10 * scale),
                (cx + slot_dx / 2, cy + slab_h - 0.10 * scale),
                (cx + slot_dx / 2, cy + slab_h + wc_h + 0.02 * scale),
                (cx - slot_dx / 2, cy + slab_h + wc_h + 0.02 * scale),
                (cx - slot_dx / 2, cy + slab_h - 0.10 * scale),
            ],
            dxfattribs={'lineweight': 35, 'color': 1},
        )
        # Seal strip across gap
        msp.add_line(
            (cx - half_gap_dx, cy + slab_h - 0.05 * scale),
            (cx + half_gap_dx, cy + slab_h - 0.05 * scale),
            dxfattribs={'lineweight': 50, 'color': 5},
        )
        # Joint label lines (gap)
        msp.add_line((cx - half_gap_dx, cy - 4), (cx - half_gap_dx, cy),
                     dxfattribs={'lineweight': 20, 'linetype': 'DASHED'})
        msp.add_line((cx + half_gap_dx, cy - 4), (cx + half_gap_dx, cy),
                     dxfattribs={'lineweight': 20, 'linetype': 'DASHED'})
        msp.add_line((cx - half_gap_dx, cy - 6), (cx + half_gap_dx, cy - 6),
                     dxfattribs={'lineweight': 15})
        msp.add_text(f"Expansion gap = {gap*1000:.0f} mm",
                     dxfattribs={'height': 2.0}).set_placement((cx - 22, cy - 11))
        # Slot dimension
        msp.add_line((cx - slot_dx / 2, cy + slab_h + wc_h + 6),
                     (cx + slot_dx / 2, cy + slab_h + wc_h + 6), dxfattribs={'lineweight': 15})
        msp.add_text(f"Slot / throat W = {slot_w*1000:.0f} mm",
                     dxfattribs={'height': 2.0}).set_placement((cx - 28, cy + slab_h + wc_h + 9))
        msp.add_text(f"System: {ej_type}     Sealant: {sealant}",
                     dxfattribs={'height': 2.0}).set_placement((cx - deck_dx / 2 - 10, cy - 20))
        msp.add_text("SECTION THROUGH EXPANSION JOINT",
                     dxfattribs={'height': 2.6}).set_placement((cx - 75, cy + slab_h + wc_h + 16))

        # TBC stamp over whole joint (slot width proportions & sealant are indicative)
        self._draw_tbc_stamp(
            msp,
            (cx - deck_dx / 2 - 14, cy - 24),
            (cx + deck_dx / 2 + 14, cy + slab_h + wc_h + 22),
        )

        # Notes
        notes = [
            f"1. Expansion joint system: {ej_type}",
            f"2. Nominal movement gap: {gap*1000:.0f} mm  (slot throat width {slot_w*1000:.0f} mm)",
            f"3. Sealant / strip-seal membrane: {sealant}",
            "4. Backer rod, nosing concrete, edge reinforcement — TBC_BY_ENGINEER.",
            "5. Verify total joint movement against deck temperature + seismic + creep package.",
        ]
        ny = 65
        for n in notes:
            msp.add_text(n, dxfattribs={'height': 2.0}).set_placement((25, ny))
            ny -= 4
        return doc

    def generate_wing_wall_detail_sheet(self, variables: Dict) -> Drawing:
        """Generate Wing / Return Wall detail sheet (WING-DET) with section + rebar."""

        title = "WING AND RETURN WALL DETAILS"
        doc, msp = self._create_sheet(title)
        total = len(phase_three_sheet_rows())
        self._draw_border(msp, 10)
        self._draw_title_block(msp, title, 10, total, variables)

        abtl = float(variables.get("ABTLEN", 0.0) or variables.get("ABTL", 13.0) or 13.0)
        rtl = float(variables.get("RTL", 110.98) or 110.98)
        datum = float(variables.get("DATUM", 100.0) or 100.0)
        futd = float(variables.get("FUTD", 1.0) or 1.0)
        # Wing dims — derived when possible, else TBC stamped
        w_stem = float(variables.get("WING_W", 0.4) or 0.4)
        w_len = float(variables.get("WING_L", 0.0) or 0.0)
        if w_len <= 0:
            w_len = max(2.0, abtl * 0.25)  # indicative; TBC stamped
        w_height = float(variables.get("WING_H", 0.0) or 0.0)
        if w_height <= 0:
            w_height = max(1.5, (rtl - datum) - futd * 0.5)
        main_d = float(variables.get("REBAR_MAIN_D", 0.0) or 0.0)
        tie_d = float(variables.get("REBAR_TIE_D", 0.0) or 0.0)
        tie_s = float(variables.get("REBAR_SPACING", 0.0) or 0.0)
        scale = 12.0  # 1 m = 12 mm

        base_y = 70
        stem_x0 = 100
        footing_w = max(w_len + 0.6, w_stem + 1.0)
        footing_d = max(futd, w_stem * 1.2)

        # --- WING WALL SECTION (left)
        # Base footing
        msp.add_lwpolyline(
            [
                (stem_x0, base_y),
                (stem_x0 + footing_w * scale, base_y),
                (stem_x0 + footing_w * scale, base_y - footing_d * scale),
                (stem_x0, base_y - footing_d * scale),
                (stem_x0, base_y),
            ],
            dxfattribs={'lineweight': 40, 'color': 2},
        )
        # Stem (slight batter visual)
        stem_top_x = stem_x0 + (footing_w - w_stem) / 2 * scale
        stem_top_y = base_y + w_height * scale
        msp.add_lwpolyline(
            [
                (stem_x0 + (footing_w - w_stem) / 2 * scale, base_y),
                (stem_x0 + (footing_w + w_stem) / 2 * scale, base_y),
                (stem_x0 + (footing_w + w_stem) / 2 * scale + 2, stem_top_y),
                (stem_top_x - 2, stem_top_y),
                (stem_x0 + (footing_w - w_stem) / 2 * scale, base_y),
            ],
            dxfattribs={'lineweight': 50, 'color': 4},
        )
        # Parapet cap at top
        msp.add_lwpolyline(
            [
                (stem_top_x - 4, stem_top_y),
                (stem_top_x + w_stem * scale + 4, stem_top_y),
                (stem_top_x + w_stem * scale + 4, stem_top_y + 0.3 * scale),
                (stem_top_x - 4, stem_top_y + 0.3 * scale),
                (stem_top_x - 4, stem_top_y),
            ],
            dxfattribs={'lineweight': 35, 'color': 3},
        )
        msp.add_text("SECTION — WING WALL",
                     dxfattribs={'height': 2.6}).set_placement((stem_x0, base_y - footing_d * scale - 10))
        # Dim: height
        msp.add_line((stem_x0 - 10, base_y), (stem_x0 - 10, stem_top_y),
                     dxfattribs={'lineweight': 15})
        msp.add_text(f"H = {w_height:.2f} m",
                     dxfattribs={'height': 2.0}).set_placement((stem_x0 - 25, base_y + w_height * scale / 2))
        # Dim: stem t
        msp.add_line((stem_top_x - 2, stem_top_y - 6),
                     (stem_top_x + w_stem * scale + 2, stem_top_y - 6),
                     dxfattribs={'lineweight': 15})
        msp.add_text(f"t = {w_stem:.2f} m",
                     dxfattribs={'height': 2.0}).set_placement((stem_top_x - 14, stem_top_y - 11))
        # Dim: base length
        msp.add_line((stem_x0, base_y - footing_d * scale - 4),
                     (stem_x0 + footing_w * scale, base_y - footing_d * scale - 4),
                     dxfattribs={'lineweight': 15})
        msp.add_text(f"Base L = {footing_w:.2f} m,  d = {footing_d:.2f} m",
                     dxfattribs={'height': 2.0}).set_placement((stem_x0, base_y - footing_d * scale - 10))

        # --- REINFORCEMENT SCHEDULE (right)
        sched_x = 205
        sched_y = 165
        msp.add_text("REINFORCEMENT (INDICATIVE — TBC)",
                     dxfattribs={'height': 2.6}).set_placement((sched_x - 55, sched_y))
        rows = [
            ("Main vertical bars", f"{main_d if main_d else 'TBC'} mm", "TBC" if main_d else "TBC_BY_ENGINEER"),
            ("Horizontal ties", f"{tie_d if tie_d else 'TBC'} mm", f"{tie_s if tie_s else 'TBC'} mm c/c"),
            ("Footing bars", "TBC mm", "TBC c/c"),
            ("Distribution mesh", "TBC mm", "TBC c/c"),
        ]
        ly = sched_y - 8
        header = ["Bar", "Dia", "Spacing"]
        cx_cols = [sched_x - 55, sched_x - 10, sched_x + 25]
        for h, xx in zip(header, cx_cols):
            msp.add_text(h, dxfattribs={'height': 2.2}).set_placement((xx, ly))
        ly -= 6
        for a, b, c in rows:
            msp.add_text(a, dxfattribs={'height': 1.9}).set_placement((cx_cols[0] - 30, ly))
            msp.add_text(b, dxfattribs={'height': 1.9}).set_placement((cx_cols[1], ly))
            msp.add_text(c, dxfattribs={'height': 1.9}).set_placement((cx_cols[2], ly))
            ly -= 6
        # Rebar visuals on stem (schematic)
        stem_cent = stem_top_x + w_stem * scale / 2
        n_bars = 4
        for i in range(n_bars):
            frac_y = (i + 0.5) / n_bars
            by = base_y + w_height * scale * frac_y
            msp.add_circle((stem_cent - w_stem * scale * 0.25, by), 0.9,
                           dxfattribs={'lineweight': 25, 'color': 1})
            msp.add_circle((stem_cent + w_stem * scale * 0.25, by), 0.9,
                           dxfattribs={'lineweight': 25, 'color': 1})
        # Tie (stirrup) lines
        for i in range(n_bars + 1):
            ty = base_y + w_height * scale * i / n_bars
            msp.add_lwpolyline(
                [
                    (stem_cent - w_stem * scale * 0.4, ty),
                    (stem_cent + w_stem * scale * 0.4, ty),
                ],
                dxfattribs={'lineweight': 18, 'linetype': 'DASHED', 'color': 1},
            )

        # TBC stamps
        self._draw_tbc_stamp(msp, (stem_x0 - 12, base_y - footing_d * scale - 12),
                             (stem_x0 + footing_w * scale + 12, stem_top_y + 8))
        self._draw_tbc_stamp(msp, (sched_x - 65, sched_y - 62), (sched_x + 65, sched_y + 8))

        notes = [
            f"1. Wing wall: Height {w_height:.2f} m,  stem t {w_stem:.2f} m,  base L {w_len:.2f} m (indicative)",
            f"2. Main bars: {main_d if main_d else 'TBC'} mm,  ties: {tie_d if tie_d else 'TBC'} mm @ {tie_s if tie_s else 'TBC'} mm c/c",
            "3. Splice lengths, development length, bar schedule — TBC_BY_ENGINEER.",
            "4. Drainage weep holes through wing stem: owner-typical detail required.",
            "5. Backfill gradation and compaction behind wall — to project spec.",
        ]
        ny = 65
        for n in notes:
            msp.add_text(n, dxfattribs={'height': 2.0}).set_placement((25, ny))
            ny -= 4
        return doc

    def generate_drainage_downtake_detail_sheet(self, variables: Dict) -> Drawing:
        """Generate Drainage Scupper and Downtake Detail sheet (DRN-DET)."""

        title = "DRAINAGE SCUPPER AND DOWNTAKE DETAILS"
        doc, msp = self._create_sheet(title)
        total = len(phase_three_sheet_rows())
        self._draw_border(msp, 11)
        self._draw_title_block(msp, title, 11, total, variables)

        drain_sp = float(variables.get("DRAINSP", 4.0) or 4.0)
        scupper_w = float(variables.get("SCUPPER_W", 0.0) or 0.0)
        if scupper_w <= 0:
            scupper_w = 0.30  # typical 300mm wide inlet; TBC
        dp_mm = float(variables.get("DOWNPIPE_D", 0.0) or 0.0)
        outlet_t = str(variables.get("OUTLET_TYPE") or "Hopper + downpipe to splash plate")
        kerbw = float(variables.get("KERBW", 0.35) or 0.35)
        kerbd = float(variables.get("KERBD", 0.25) or 0.25)
        _ = float(variables.get("FOOTPATHW", 0.0) or 0.0)
        wc = float(variables.get("WCTH", 0.05) or 0.05)

        scale = 25.0

        # --- TOP LEFT: SCUPPER PLAN (kerb inlet in plan)
        plan_cx, plan_cy = 90, 160
        # Kerb strip in plan
        kerb_l = 3.0  # m, visual on sheet
        msp.add_lwpolyline(
            [
                (plan_cx - kerb_l * scale / 2, plan_cy - kerbw * scale / 2),
                (plan_cx + kerb_l * scale / 2, plan_cy - kerbw * scale / 2),
                (plan_cx + kerb_l * scale / 2, plan_cy + kerbw * scale / 2),
                (plan_cx - kerb_l * scale / 2, plan_cy + kerbw * scale / 2),
                (plan_cx - kerb_l * scale / 2, plan_cy - kerbw * scale / 2),
            ],
            dxfattribs={'lineweight': 35, 'color': 3},
        )
        # Scupper opening cut in kerb
        msp.add_lwpolyline(
            [
                (plan_cx - scupper_w * scale / 2, plan_cy - kerbw * scale / 2 - 4),
                (plan_cx + scupper_w * scale / 2, plan_cy - kerbw * scale / 2 - 4),
                (plan_cx + scupper_w * scale / 2, plan_cy + kerbw * scale / 2 + 4),
                (plan_cx - scupper_w * scale / 2, plan_cy + kerbw * scale / 2 + 4),
                (plan_cx - scupper_w * scale / 2, plan_cy - kerbw * scale / 2 - 4),
            ],
            dxfattribs={'lineweight': 50, 'color': 1},
        )
        # Grate cross pattern
        msp.add_line((plan_cx - scupper_w * scale / 2, plan_cy),
                     (plan_cx + scupper_w * scale / 2, plan_cy),
                     dxfattribs={'lineweight': 20})
        msp.add_line((plan_cx, plan_cy - kerbw * scale / 2 - 3),
                     (plan_cx, plan_cy + kerbw * scale / 2 + 3),
                     dxfattribs={'lineweight': 20})
        msp.add_text("SCUPPER PLAN",
                     dxfattribs={'height': 2.6}).set_placement((plan_cx - 25, plan_cy + kerbw * scale / 2 + 10))
        msp.add_text(f"Opening W = {scupper_w*1000:.0f} mm,  spacing ~ {drain_sp:.1f} m c/c",
                     dxfattribs={'height': 2.0}).set_placement((plan_cx - 70, plan_cy + kerbw * scale / 2 + 5))
        self._draw_tbc_stamp(
            msp,
            (plan_cx - kerb_l * scale / 2 - 6, plan_cy - kerbw * scale / 2 - 10),
            (plan_cx + kerb_l * scale / 2 + 6, plan_cy + kerbw * scale / 2 + 10),
        )

        # --- TOP RIGHT: SECTION B-B THROUGH SCUPPER + DOWNTAKE
        sec_cx = 215
        sec_y = 120
        # Deck slab (RHS: deck, LHS: footpath)
        deck_w = 3.0  # m visual
        slab_h_m = 0.50 + kerbd  # indicative; TBC
        deck_wd = deck_w * scale
        msp.add_lwpolyline(
            [
                (sec_cx - deck_wd / 2, sec_y),
                (sec_cx + deck_wd / 2, sec_y),
                (sec_cx + deck_wd / 2, sec_y + slab_h_m * scale),
                (sec_cx - deck_wd / 2, sec_y + slab_h_m * scale),
                (sec_cx - deck_wd / 2, sec_y),
            ],
            dxfattribs={'lineweight': 45, 'color': 6},
        )
        # Wearing course on deck half (right)
        msp.add_lwpolyline(
            [
                (sec_cx, sec_y + slab_h_m * scale),
                (sec_cx + deck_wd / 2, sec_y + slab_h_m * scale),
                (sec_cx + deck_wd / 2, sec_y + (slab_h_m + wc) * scale),
                (sec_cx, sec_y + (slab_h_m + wc) * scale),
                (sec_cx, sec_y + slab_h_m * scale),
            ],
            dxfattribs={'lineweight': 25, 'color': 7},
        )
        # Footpath slab (left, higher)
        fp_h_m = slab_h_m + 0.02
        msp.add_lwpolyline(
            [
                (sec_cx - deck_wd / 2, sec_y + slab_h_m * scale),
                (sec_cx, sec_y + slab_h_m * scale),
                (sec_cx, sec_y + fp_h_m * scale),
                (sec_cx - deck_wd / 2, sec_y + fp_h_m * scale),
                (sec_cx - deck_wd / 2, sec_y + slab_h_m * scale),
            ],
            dxfattribs={'lineweight': 30, 'color': 3},
        )
        # Kerb at deck-footpath junction
        msp.add_lwpolyline(
            [
                (sec_cx - kerbw * scale / 2, sec_y + fp_h_m * scale),
                (sec_cx + kerbw * scale / 2, sec_y + fp_h_m * scale),
                (sec_cx + kerbw * scale / 2, sec_y + (fp_h_m + kerbd) * scale),
                (sec_cx - kerbw * scale / 2, sec_y + (fp_h_m + kerbd) * scale),
                (sec_cx - kerbw * scale / 2, sec_y + fp_h_m * scale),
            ],
            dxfattribs={'lineweight': 40, 'color': 4},
        )
        # Scupper opening through kerb
        scupp_h_m = kerbd * 0.7
        msp.add_lwpolyline(
            [
                (sec_cx - scupper_w * scale / 2, sec_y + fp_h_m * scale + (kerbd - scupp_h_m) * scale / 2),
                (sec_cx + scupper_w * scale / 2, sec_y + fp_h_m * scale + (kerbd - scupp_h_m) * scale / 2),
                (sec_cx + scupper_w * scale / 2, sec_y + fp_h_m * scale + (kerbd - scupp_h_m) * scale / 2 + scupp_h_m * scale),
                (sec_cx - scupper_w * scale / 2, sec_y + fp_h_m * scale + (kerbd - scupp_h_m) * scale / 2 + scupp_h_m * scale),
                (sec_cx - scupper_w * scale / 2, sec_y + fp_h_m * scale + (kerbd - scupp_h_m) * scale / 2),
            ],
            dxfattribs={'lineweight': 40, 'color': 1},
        )
        # Hopper head + downtake pipe (underside of slab)
        hopper_btm_y = sec_y - 35
        msp.add_lwpolyline(
            [
                (sec_cx - scupper_w * scale / 2, sec_y),
                (sec_cx - 3.5, hopper_btm_y),
                (sec_cx + 3.5, hopper_btm_y),
                (sec_cx + scupper_w * scale / 2, sec_y),
                (sec_cx - scupper_w * scale / 2, sec_y),
            ],
            dxfattribs={'lineweight': 30, 'color': 5},
        )
        dp_r = max(1.5, (dp_mm / 2000.0) * scale) if dp_mm > 0 else 2.0
        pipe_y_end = hopper_btm_y - 25
        msp.add_lwpolyline(
            [
                (sec_cx - dp_r, hopper_btm_y),
                (sec_cx + dp_r, hopper_btm_y),
                (sec_cx + dp_r, pipe_y_end),
                (sec_cx - dp_r, pipe_y_end),
                (sec_cx - dp_r, hopper_btm_y),
            ],
            dxfattribs={'lineweight': 35, 'color': 1},
        )
        # Splash plate
        msp.add_lwpolyline(
            [
                (sec_cx - dp_r - 5, pipe_y_end - 2),
                (sec_cx + dp_r + 5, pipe_y_end - 2),
                (sec_cx + dp_r + 5, pipe_y_end - 4),
                (sec_cx - dp_r - 5, pipe_y_end - 4),
                (sec_cx - dp_r - 5, pipe_y_end - 2),
            ],
            dxfattribs={'lineweight': 25, 'color': 2},
        )
        msp.add_text("SECTION B-B — SCUPPER + DOWNTAKE",
                     dxfattribs={'height': 2.6}).set_placement((sec_cx - 90, sec_y - 45))
        msp.add_text(f"Downpipe dia = {dp_mm if dp_mm else 'TBC'} mm,  outfall: {outlet_t}",
                     dxfattribs={'height': 2.0}).set_placement((sec_cx - deck_wd / 2 - 10, pipe_y_end - 12))
        self._draw_tbc_stamp(
            msp,
            (sec_cx - deck_wd / 2 - 10, sec_y - 50),
            (sec_cx + deck_wd / 2 + 10, sec_y + (fp_h_m + kerbd) * scale + 10),
        )

        notes = [
            f"1. Scuppers @ ~ {drain_sp:.1f} m c/c in kerb line  (opening W={scupper_w*1000:.0f} mm)",
            f"2. Downtake pipe: {dp_mm if dp_mm else 'TBC'} mm  — outfall: {outlet_t}",
            "3. Grate / inlet grating material, clear opening — TBC_BY_ENGINEER.",
            "4. Anti-freeze / anti-clog measures (for cold climates) — as applicable, TBC.",
            "5. All pipe routing, supports, access for maintenance — coordinate with utility drawings.",
        ]
        ny = 65
        for n in notes:
            msp.add_text(n, dxfattribs={'height': 2.0}).set_placement((25, ny))
            ny -= 4
        return doc

    def generate_all_sheets(self, variables: Dict, output_path: Path) -> bool:
        """Generate all 4 sheets and combine into single PDF/DXF"""
        try:
            # Generate all sheets
            sheets = [
                self.generate_pier_elevation(variables, 1, 4),
                self.generate_abutment_elevation(variables, 2, 4),
                self.generate_plan_view(variables, 3, 4),
                self.generate_section_view(variables, 4, 4),
            ]

            self._save_sheet_set(sheets, output_path)
            return True
        except Exception as e:
            print(f"Error generating sheets: {e}")
            return False

    def generate_phase_two_package(self, variables: Dict, output_path: Path) -> bool:
        """Generate the seven-sheet phase two package."""

        try:
            total = len(phase_two_sheet_rows())
            variables = dict(variables)
            variables["INCLUDE_PHASE_THREE"] = False
            variables.setdefault("TOTAL_SHEETS", str(total))
            sheets = [
                self.generate_index_sheet(variables),
                self.generate_plan_view(variables, 2, total),
                self.generate_section_view(variables, 3, total),
                self.generate_abutment_elevation(variables, 4, total),
                self.generate_pier_elevation(variables, 5, total),
                self.generate_bearing_joint_sheet(variables),
                self.generate_drainage_utility_sheet(variables),
            ]
            self._save_sheet_set(sheets, output_path)
            return True
        except Exception as e:
            print(f"Error generating phase two package: {e}")
            return False

    def generate_phase_three_package(self, variables: Dict, output_path: Path) -> bool:
        """Generate the eleven-sheet phase three package.

        The 11-sheet submission bundle contains the phase two GAD set (sheets 1-7)
        followed by four consultant-grade detail sheets added in phase three:
          8  BRG-DET  Bearing Details — Plan and Section
          9  EXPJ-DET Expansion Joint Details
         10  WING-DET Wing and Return Wall Details
         11  DRN-DET  Drainage Scupper and Downtake Details
        """
        try:
            total = len(phase_three_sheet_rows())
            variables = dict(variables)
            variables["INCLUDE_PHASE_THREE"] = True
            variables.setdefault("TOTAL_SHEETS", str(total))
            # 1..7: phase two geometry and notes
            sheets = [
                self.generate_index_sheet(variables),
                self.generate_plan_view(variables, 2, total),
                self.generate_section_view(variables, 3, total),
                self.generate_abutment_elevation(variables, 4, total),
                self.generate_pier_elevation(variables, 5, total),
                self.generate_bearing_joint_sheet(variables),
                self.generate_drainage_utility_sheet(variables),
                # 8..11: phase three detail sheets
                self.generate_bearing_detail_sheet(variables),
                self.generate_expansion_joint_detail_sheet(variables),
                self.generate_wing_wall_detail_sheet(variables),
                self.generate_drainage_downtake_detail_sheet(variables),
            ]
            self._save_sheet_set(sheets, output_path)
            return True
        except Exception as e:
            print(f"Error generating phase three package: {e}")
            return False
