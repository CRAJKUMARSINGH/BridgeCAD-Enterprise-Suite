"""bridgecad_draw.sheets.sheet7_bill_of_quantities — the abstract bill of quantities.

A schedule sheet, not a geometry sheet: one ruled table, every line's quantity
read from the model, and an explicit "NOT CALCULATED" wherever the input does
not carry the number. Unit rates are deliberately left as TBC — pricing is the
priced BOQ's job (``bridgecad-bill``), and an abstract that invents a rate is
worse than an abstract that says it has none.

Quantities come from ``project.calculations``. A handful — formwork area,
wearing coat, approach slab, railing — are ratios of measured quantities, so
they are marked with the multiplier that produced them in the notes.
"""

from __future__ import annotations

from bridgecad_draw.sheets._common import Canvas, field

SHEET = "sheet7_bill_of_quantities"
TITLE = "S7 Bill of Quantities"
INDEX = 7

#: (item_no, description, unit, quantity key, decimal places, MORTH reference).
_ITEMS = (
    ("1", "EARTHWORK — EMBANKMENT (IMPORTED MOORUM)", "CUM", "earthwork", 1, "MORTH 300"),
    ("2", "GRANULAR SUB-BASE (GSB) — APPROACH ROAD", "CUM", "gsb", 1, "MORTH 401"),
    ("3", "CONCRETE M25 — PILE FOUNDATION", "CUM", "conc_fnd", 2, "MORTH 1700"),
    ("4", "CONCRETE M30 — SUBSTRUCTURE (PIER & ABUTMENT)", "CUM", "conc_sub", 2, "MORTH 1700"),
    ("5", "CONCRETE M40 — SUPERSTRUCTURE DECK & GIRDERS", "CUM", "conc_sup", 2, "MORTH 1700"),
    ("6", "REINFORCEMENT STEEL Fe500D — ALL ITEMS", "MT", "rebar", 2, "MORTH 1600"),
    ("7", "PRESTRESSING STEEL (STRANDS G1860)", "MT", "prestress", 2, "MORTH 1600"),
    ("8", "FORMWORK — SUPERSTRUCTURE", "SQM", "formwork", 1, "MORTH 1700"),
    ("9", "BITUMINOUS CONCRETE (BC) WEARING COAT", "SQM", "wc", 1, "MORTH 510"),
    ("10", "ELASTOMERIC / POT BEARINGS (SUPPLY & INSTALL)", "EACH", "bearings", 0, "MORTH 2800"),
    ("11", "EXPANSION JOINTS (STRIP SEAL / MODULAR)", "RM", "joints", 1, "MORTH 2800"),
    ("12", "APPROACH SLAB M30 (BOTH ENDS)", "CUM", "app_slab", 2, "MORTH 1700"),
    ("13", "RIVER TRAINING WORKS (LUMP SUM ESTIMATE)", "LS", "river", 0, "MORTH 2500"),
    ("14", "RAILING / CRASH BARRIER (M.S. W-BEAM, HDG)", "RM", "railing", 1, "MORTH 800"),
    ("15", "WATERPROOFING MEMBRANE — DECK", "SQM", "waterproof", 1, "MORTH 2600"),
)

_COLUMNS = (
    ("ITEM", 16.0),
    ("DESCRIPTION", 210.0),
    ("UNIT", 24.0),
    ("QUANTITY", 48.0),
    ("RATE (INR)", 52.0),
    ("AMOUNT (INR)", 62.0),
    ("MORTH REF.", 34.0),
)


def _value(obj, name: str):
    """The model's number for *name*, or ``None`` when the model is silent.

    ``None`` and ``0`` are different answers: a zero is a measured zero, a ``None``
    is an input the workbook never carried. Collapsing them is the failure the
    "NOT CALCULATED" column exists to make visible.
    """
    raw = field(obj, name, None)
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _num(obj, name: str, default: float) -> float:
    value = _value(obj, name)
    return default if value is None else value


def _fmt(value, digits: int) -> str:
    """A quantity cell: the number, or the honest absence of one."""
    if value is None:
        return "NOT CALCULATED"
    return f"{value:,.{digits}f}"


def _quantities(project) -> tuple[dict, dict]:
    """(quantity by key, the model facts the notes quote)."""
    calc = project.calculations
    gi = project.geometry_input
    sub = project.substructure

    total_len = _num(gi, "total_length_m", 0.0)
    overall_w = _num(gi, "overall_width_m", 0.0)
    carriageway = _num(gi, "carriageway_width_m", 7.5) or 7.5

    conc_sup = _value(calc, "concrete_volume_superstructure_cum")
    conc_sub = _value(calc, "concrete_volume_substructure_cum")
    conc_fnd = _value(calc, "concrete_volume_foundation_cum")
    bearings = _value(calc, "bearing_count")
    joints = _value(calc, "expansion_joint_count")

    app_l = _num(sub, "approach_slab_length_m", 3.5) or 3.5
    app_t = (_num(sub, "approach_slab_thickness_mm", 200.0) or 200.0) / 1000.0

    def area(value, factor: float):
        return None if value is None else value * factor

    plan_area = total_len * overall_w if total_len and overall_w else None
    qty = {
        "earthwork": None if plan_area is None else plan_area * 2.5,
        "gsb": None if not total_len else total_len * carriageway * 0.25,
        "conc_fnd": conc_fnd,
        "conc_sub": conc_sub,
        "conc_sup": conc_sup,
        "rebar": _value(calc, "rebar_weight_tonnes_approx"),
        "prestress": _value(calc, "prestress_tonnes_approx"),
        "formwork": area(conc_sup, 4.5),
        "wc": None if not total_len else total_len * carriageway,
        "bearings": bearings,
        "joints": None if joints is None or not overall_w else overall_w * joints,
        "app_slab": None if not overall_w else app_l * overall_w * app_t * 2.0,
        "river": 1.0,
        "railing": None if not total_len else total_len * 2.0 + app_l * 4.0,
        "waterproof": plan_area,
    }
    facts = {
        "total_len": total_len,
        "overall_w": overall_w,
        "carriageway": carriageway,
        "total_cost": _value(calc, "total_estimated_quantity_cost_inr"),
    }
    return qty, facts


def build(project):
    """Build the abstract bill of quantities for *project*."""
    cv = Canvas(SHEET, TITLE, INDEX)
    pm = project.project_master
    qty, facts = _quantities(project)

    x0 = 20.0
    y_top = 505.0
    row_h = cv.height * 2.4

    rows = [[label for label, _ in _COLUMNS]]
    for no, desc, unit, key, digits, ref in _ITEMS:
        rows.append([no, desc, unit, _fmt(qty.get(key), digits), "TBC", "", ref])

    total_cost = facts["total_cost"]
    rows.append(
        [
            "",
            "TOTAL ESTIMATED COST (CIVIL WORKS)",
            "",
            "",
            "",
            "NOT PRICED" if total_cost is None else f"INR {total_cost:,.0f}",
            "",
        ]
    )

    # ── title band ─────────────────────────────────────────────────────────
    with cv.on("TEXT-HEADER"):
        cv.text(
            "BILL OF QUANTITIES — ABSTRACT OF ESTIMATED COST", x0, 522.0, height=cv.height * 1.4
        )
    with cv.on("TEXT-GENERAL"):
        bridge = str(field(pm, "bridge_name", "") or "BRIDGE")
        chainage = _num(pm, "chainage_km", 0.0)
        cv.text(
            f"{bridge}  |  CHAINAGE {chainage:.3f} km  |  "
            f"TOTAL LENGTH {facts['total_len']:.3f} m  |  "
            f"OVERALL WIDTH {facts['overall_w']:.3f} m  |  "
            f"CARRIAGEWAY {facts['carriageway']:.3f} m",
            x0,
            514.0,
        )

    # ── the schedule ───────────────────────────────────────────────────────
    bottom = cv.table(x0, y_top, [w for _, w in _COLUMNS], rows, row_h=row_h)
    width = sum(w for _, w in _COLUMNS)

    # ── column grid, dimensioned (a schedule whose widths are a standard) ──
    with cv.on("DIM"):
        cv.dimension(
            (x0, bottom),
            (x0 + width, bottom),
            base=(x0 + width / 2.0, bottom - cv.height * 2.0),
            text=f"SCHEDULE WIDTH {width:.0f}",
        )
        cv.dimension(
            (x0, bottom),
            (x0 + _COLUMNS[0][1] + _COLUMNS[1][1], bottom),
            base=(x0 + (_COLUMNS[0][1] + _COLUMNS[1][1]) / 2.0, bottom - cv.height * 4.0),
            text="DESCRIPTION",
        )
        cv.dimension(
            (x0 + sum(w for _, w in _COLUMNS[:3]), bottom),
            (x0 + sum(w for _, w in _COLUMNS[:5]), bottom),
            base=(x0 + sum(w for _, w in _COLUMNS[:4]), bottom - cv.height * 4.0),
            text="QUANTITY + RATE",
        )
        cv.dimension(
            (x0 + width, bottom),
            (x0 + width, y_top),
            base=(x0 + width + cv.height * 10.0, bottom),
            angle=90.0,
            text=f"{len(rows)} ROWS",
        )

    cv.note(
        [
            "NOTES:",
            "1. Quantities are preliminary estimates for budget purposes only.",
            "2. Final quantities to be measured as per IS:1200 / MORTH specifications.",
            "3. Rate column reads TBC: pricing belongs to the priced BOQ, not this abstract.",
            "4. Estimated lines carry their multiplier: formwork = concrete x 4.5,",
            "   earthwork = plan area x 2.5, railing = deck edges + approach slab runs.",
            "5. NOT CALCULATED marks a quantity the input model does not carry — not a zero.",
            "6. 15% contingency to be added for unforeseen items.",
        ],
        x0,
        bottom - cv.height * 6.0,
    )

    return cv.doc
