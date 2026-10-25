"""Sheet coordinate contract — the single statement of where things live.

WHY THIS FILE EXISTS
    Historically each sheet picked its own origin. Extents came out plausible
    per sheet and meaningless as a set, so a pier on sheet 2 and the same pier
    on sheet 5 sat at different coordinates with no way to correlate them.

THE CONTRACT — every clause is asserted in tests/draw/test_coordinates.py

 1. MODEL SPACE IS MILLIMETRES, 1:1. No metres, ever. Conversion happens once,
    in `m()`.
 2. Y IS UP. X increases along increasing chainage. Right-handed.
 3. THE DATUM IS DECLARED, NOT IMPLIED. Every sheet has an ORIGIN entry. A
    sheet with no entry is a bug, not a default.
 4. ORIGINS ARE IN CHAINAGE/LEVEL SPACE, converted through `origin_xy()`. Two
    sheets showing the same station resolve to the same model point.
 5. PLOT SCALE IS DECLARED PER SHEET and applied at plot time only. Model space
    never carries a scale factor.
 6. THE SHEET FRAME IS A-SERIES LANDSCAPE. Title block occupies a declared
    corner region; the drawing region is the frame minus that region.
 7. NOTHING DRAWS AT (0, 0) BY ACCIDENT. Geometry outside the declared frame
    fails the test, which is how a mis-signed offset gets caught.
"""

from __future__ import annotations

from dataclasses import dataclass

MM_PER_M = 1000.0

# A-series landscape, millimetres.
FRAME = {
    "A0": (1189.0, 841.0),
    "A1": (841.0, 594.0),
    "A2": (594.0, 420.0),
    "A3": (420.0, 297.0),
    "A4": (297.0, 210.0),
}

# Declared plot scales. Non-standard scales are a bug, not a preference.
# 1:1 is standard for a schedule — a bill of quantities is a table, not a
# scaled view, and drawing it full size is the engineering-correct choice.
PLOT_SCALES = (1, 20, 25, 50, 100, 200, 250, 500, 1000)

TITLE_BLOCK = {"width_mm": 180.0, "height_mm": 60.0, "corner": "bottom_right"}


@dataclass(frozen=True)
class SheetFrame:
    """Where a sheet's geometry is allowed to live."""

    size: str
    origin_chainage_m: float
    origin_level_m: float
    plot_scale: int

    @property
    def width_mm(self) -> float:
        return FRAME[self.size][0]

    @property
    def height_mm(self) -> float:
        return FRAME[self.size][1]

    @property
    def drawing_region_mm(self) -> tuple[float, float, float, float]:
        """(x0, y0, x1, y1) excluding the title block corner."""
        tb_w, tb_h = TITLE_BLOCK["width_mm"], TITLE_BLOCK["height_mm"]
        return (
            (0.0, tb_h, self.width_mm, self.height_mm)
            if TITLE_BLOCK["corner"] == "bottom_right"
            else (0.0, 0.0, self.width_mm - tb_w, self.height_mm)
        )


# Every sheet must appear. Sheet 1's datum is the reference all others share.
FRAMES: dict[str, SheetFrame] = {
    "sheet1_plan": SheetFrame("A1", 0.0, 0.0, 200),
    "sheet2_long_section": SheetFrame("A1", 0.0, 90.0, 100),
    "sheet3_cross_section": SheetFrame("A1", 0.0, 0.0, 50),
    "sheet4_foundation": SheetFrame("A1", 0.0, 0.0, 100),
    "sheet5_pier_abutment_details": SheetFrame("A1", 0.0, 0.0, 50),
    "sheet6_bearings_joints": SheetFrame("A1", 0.0, 0.0, 20),
    "sheet7_bill_of_quantities": SheetFrame("A1", 0.0, 0.0, 1),
}


def m(metres: float) -> float:
    """Metres -> model millimetres. The only conversion in the codebase."""
    return metres * MM_PER_M


def origin_xy(sheet: str) -> tuple[float, float]:
    """Model-space translation for a sheet's declared datum, in millimetres.

    Model space is sheet-relative: the declared origin is (0, 0) on the drawing
    and this is the offset that maps project chainage/level into it. Sheet 1
    declares a zero datum, so it is the reference every other sheet is measured
    against — moving a shared clause there moves it everywhere.
    """
    frame = FRAMES[sheet]
    return (-m(frame.origin_chainage_m), -m(frame.origin_level_m))


def to_model_space(sheet: str, chainage_m: float, level_m: float) -> tuple[float, float]:
    """Chainage/level (metres, project space) -> model space (mm, sheet space)."""
    ox, oy = origin_xy(sheet)
    return (ox + m(chainage_m), oy + m(level_m))


def model_text_height_mm(sheet: str, paper_mm: float) -> float:
    """Text height on paper -> the model height that plots at that size.

    A 1:100 sheet draws 100 mm of model per paper millimetre, so 2.5 mm of
    paper text is 250 mm of model text. Getting this backwards is invisible on
    screen and unreadable in print.
    """
    return paper_mm * check_declared(sheet).plot_scale


def paper_size_mm(sheet: str, size_mm: tuple[float, float]) -> tuple[float, float]:
    """Model-space extent -> the millimetres it occupies on the printed sheet."""
    scale = check_declared(sheet).plot_scale
    return (size_mm[0] / scale, size_mm[1] / scale)


def check_declared(sheet: str) -> SheetFrame:
    """Raise rather than silently defaulting to a (0,0) origin."""
    if sheet not in FRAMES:
        raise KeyError(f"sheet {sheet!r} has no declared frame — add it to coordinates.FRAMES")
    frame = FRAMES[sheet]
    if frame.plot_scale not in PLOT_SCALES:
        raise ValueError(f"{sheet}: non-standard plot scale 1:{frame.plot_scale}")
    if frame.size not in FRAME:
        raise ValueError(f"{sheet}: unknown sheet size {frame.size!r}")
    return frame
