"""bridgecad_draw.sheets.sheet6_bearings_joints — bearing and expansion-joint sheet.

Wing-16. Two schedules rule the sheet — bearings and expansion joints, straight
off ``project.bearings_joints`` — with a detail of each above. A schedule with no
rows is a blank where an auditor expects a quantity, so an unpopulated schedule
still emits one row saying the design is not yet fixed.
"""

from __future__ import annotations

from bridgecad_draw.sheets._common import Canvas, field

SHEET = "sheet6_bearings_joints"
TITLE = "S6 Bearings and Expansion Joints"
INDEX = 6

#: Detail views are enlarged so a 350 mm bearing is legible on a 1:20 sheet.
ENLARGE = 4.0


def _bearing_rows(bj) -> list[list[str]]:
    rows = []
    for item in list(field(bj, "bearing_schedule", []) or []):
        rows.append(
            [
                str(field(item, "location", "-")),
                str(field(item, "bearing_type", "-")).replace("_", " "),
                f"{float(field(item, 'size_x_mm', 0) or 0):.0f}x"
                f"{float(field(item, 'size_y_mm', 0) or 0):.0f}",
                f"{float(field(item, 'design_load_kn', 0) or 0):.0f}",
                str(field(item, "fixed_or_guide_or_free", "-")).upper(),
                f"{int(field(item, 'quantity', 0) or 0)}",
            ]
        )
    return rows or [["-", "NOT FIXED", "-", "-", "-", "-"]]


def _joint_rows(bj) -> list[list[str]]:
    rows = []
    for item in list(field(bj, "expansion_joint_schedule", []) or []):
        rows.append(
            [
                str(field(item, "location", "-")),
                str(field(item, "joint_type", "-")).replace("_", " "),
                f"{float(field(item, 'width_mm', 0) or 0):.0f}",
                f"{float(field(item, 'movement_range_mm', 0) or 0):.0f}",
                f"{float(field(item, 'gap_mm', 0) or 0):.0f}",
                f"{int(field(item, 'quantity', 0) or 0)}",
            ]
        )
    return rows or [["-", "NOT FIXED", "-", "-", "-", "-"]]


def build(project):
    """Build the bearings and expansion-joints sheet for *project*."""
    cv = Canvas(SHEET, TITLE, INDEX)
    bj = project.bearings_joints
    calc = project.calculations

    bearing_rows = _bearing_rows(bj)
    joint_rows = _joint_rows(bj)

    # ── bearing detail — pad on a masonry plate, enlarged ──────────────────
    first = list(field(bj, "bearing_schedule", []) or [])
    sx = float(field(first[0], "size_x_mm", 350) or 350) if first else 350.0
    load_kn = float(field(first[0], "design_load_kn", 0) or 0) if first else 0.0
    pad_w = cv.mm(sx / 1000.0) * ENLARGE
    pad_t = cv.height * 3.0
    plate_t = cv.height * 1.8
    x_d = cv.mm(2.0)
    y_d = cv.height * 120.0

    with cv.on("SUB-BEARING"):
        cv.rect(x_d, y_d, pad_w, pad_t)
        cv.rect(x_d - cv.height, y_d - plate_t, pad_w + cv.height * 2.0, plate_t)
    with cv.on("HTCH"):
        cv.hatch(x_d, y_d, pad_w, pad_t, pattern="ANSI31", scale=cv.height * 0.3)
    with cv.on("TEXT"):
        cv.text(f"BEARING {sx:.0f} mm", x_d + pad_w + cv.height * 1.5, y_d + pad_t * 0.4)
    with cv.on("TEXT-HEADER"):
        cv.text("BEARING DETAIL — ENLARGED 4X", x_d, y_d + pad_t + cv.height * 3.0)

    # ── expansion joint detail — two slab edges and the seal ──────────────
    joints = list(field(bj, "expansion_joint_schedule", []) or [])
    gap_mm = float(field(joints[0], "gap_mm", 12) or 12) if joints else 12.0
    gap = cv.mm(gap_mm / 1000.0) * ENLARGE
    slab_t = cv.height * 4.0
    x_j = cv.mm(10.0)
    y_j = y_d
    with cv.on("SUB-EXPJOINT"):
        cv.rect(x_j, y_j, pad_w, slab_t)
        cv.rect(x_j + pad_w + gap, y_j, pad_w, slab_t)
        cv.rect(x_j + pad_w, y_j, gap, slab_t * 0.6)
    with cv.on("HTCH"):
        cv.hatch(
            x_j + pad_w,
            y_j + slab_t * 0.6,
            gap,
            slab_t * 0.4,
            pattern="ANSI31",
            scale=cv.height * 0.3,
        )
    with cv.on("TEXT"):
        cv.text(f"EXPANSION JOINT GAP {gap_mm:.0f} mm", x_j, y_j - slab_t * 0.3 - cv.height * 3.0)
    with cv.on("TEXT-HEADER"):
        cv.text("EXPANSION JOINT DETAIL — ENLARGED 4X", x_j, y_j + slab_t + cv.height * 3.0)

    # ── schedule 1 — bearings ──────────────────────────────────────────────
    y_t1 = cv.height * 70.0
    with cv.on("TEXT-HEADER"):
        cv.text("BEARING SCHEDULE", cv.mm(1.5), y_t1 + cv.height * 2.0)
    cv.table(
        cv.mm(1.5),
        y_t1,
        [cv.mm(1.8), cv.mm(3.2), cv.mm(2.2), cv.mm(1.9), cv.mm(1.6), cv.mm(1.2)],
        [["LOCATION", "TYPE", "SIZE (mm)", "LOAD (kN)", "FIXITY", "QTY"], *bearing_rows],
        row_h=cv.height * 2.2,
    )

    # ── schedule 2 — expansion joints ──────────────────────────────────────
    y_t2 = cv.height * 40.0
    with cv.on("TEXT-HEADER"):
        cv.text("EXPANSION JOINT SCHEDULE", cv.mm(1.5), y_t2 + cv.height * 2.0)
    cv.table(
        cv.mm(1.5),
        y_t2,
        [cv.mm(1.8), cv.mm(3.2), cv.mm(2.2), cv.mm(2.4), cv.mm(1.8), cv.mm(1.2)],
        [["LOCATION", "TYPE", "WIDTH (mm)", "MOVEMENT (mm)", "GAP (mm)", "QTY"], *joint_rows],
        row_h=cv.height * 2.2,
    )

    # ── dimensions on the details ──────────────────────────────────────────
    with cv.on("DIM"):
        cv.dimension(
            (x_d, y_d),
            (x_d + pad_w, y_d),
            base=(x_d + pad_w / 2.0, y_d - plate_t - cv.height * 3.0),
            text=f"{sx:.0f} mm",
        )
        cv.dimension(
            (x_d - cv.height * 2, y_d),
            (x_d - cv.height * 2, y_d + pad_t),
            base=(x_d - cv.height * 9.0, y_d),
            angle=90.0,
            text=f"{pad_t / ENLARGE:.0f} mm",
        )
        cv.dimension(
            (x_j + pad_w, y_j + slab_t * 0.8),
            (x_j + pad_w + gap, y_j + slab_t * 0.8),
            base=(x_j + pad_w + gap / 2.0, y_j + slab_t * 1.6),
            text=f"GAP {gap_mm:.0f} mm",
        )
        cv.dimension(
            (x_j, y_j + slab_t),
            (x_j + 2 * pad_w + gap, y_j + slab_t),
            base=(x_j + pad_w, y_j + slab_t + cv.height * 6.0),
            text=f"TRANSVERSE {2 * pad_w / ENLARGE / 1000.0:.2f} m",
        )
        # masonry plate width under the bearing pad
        cv.dimension(
            (x_d - cv.height, y_d - plate_t),
            (x_d + pad_w + cv.height, y_d - plate_t),
            base=(x_d + pad_w / 2.0, y_d - plate_t - cv.height * 7.0),
            text=f"PLATE {pad_w / ENLARGE + 200:.0f} mm",
        )
        # bearing pad thickness
        cv.dimension(
            (x_d + pad_w + cv.height * 3.0, y_d),
            (x_d + pad_w + cv.height * 3.0, y_d + pad_t),
            base=(x_d + pad_w + cv.height * 10.0, y_d),
            angle=90.0,
            text=f"PAD {pad_t / ENLARGE:.0f} mm",
        )
        # joint slab thickness
        cv.dimension(
            (x_j + pad_w * 1.5, y_j),
            (x_j + pad_w * 1.5, y_j + slab_t),
            base=(x_j + pad_w * 1.5 - cv.height * 7.0, y_j),
            angle=90.0,
            text=f"SLAB {slab_t / ENLARGE:.0f} mm",
        )
        # joint slab width
        cv.dimension(
            (x_j, y_j - slab_t * 0.5),
            (x_j + pad_w, y_j - slab_t * 0.5),
            base=(x_j + pad_w / 2.0, y_j - slab_t * 0.5 - cv.height * 3.0),
            text=f"{pad_w / ENLARGE:.0f} mm",
        )

    cv.note(
        [
            "1. All dimensions in millimetres unless stated otherwise.",
            f"2. Bearings: {int(field(calc, 'bearing_count', 0) or 0)} Nos. total.",
            f"3. Expansion joints: {int(field(calc, 'expansion_joint_count', 0) or 0)} Nos. total.",
            f"4. Maximum bearing reaction {load_kn:.0f} kN (service).",
            "5. Bearing and joint types to be confirmed against the approved design.",
        ],
        cv.mm(9.0),
        cv.height * 24.0,
    )

    return cv.doc
