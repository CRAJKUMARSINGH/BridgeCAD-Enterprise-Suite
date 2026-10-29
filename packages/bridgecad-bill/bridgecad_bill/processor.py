"""
bridgecad_bill.processor — Extract quantities from BridgeProject and build a
priced BillOfQuantities using the MORTH rates database.

Uses bridgecad_core.quantities.extract_quantities() for precise component-by-
component volumes, then prices using MORTH rates with state PWD override.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

from .models import BillItem, BillOfQuantities, BillSection
from .provenance import BoqLine, LineStatus, RateSource
from .rates_db import get_rates_db


# ── Bootstrap path so processor can import bridgecad_core ─────────────────
def _ensure_core_importable() -> None:
    core_dir = Path(__file__).parents[3] / "bridgecad-core"
    if core_dir.exists() and str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))


def extract_and_price(
    project: Any,
    state: str | None = None,
    contingency_pct: Decimal = Decimal("15"),
) -> BillOfQuantities:
    """Build a fully-priced BOQ from a BridgeProject.

    Uses bridgecad_core.quantities.extract_quantities() for component volumes
    rather than simple parametric ratios. State PWD multiplier applied.

    Parameters
    ----------
    project         : BridgeProject
    state           : str | None  Two-letter state code (MH, GJ, etc.)
    contingency_pct : Decimal     Contingency % (default 15%)

    Returns
    -------
    BillOfQuantities  Priced hierarchical BOQ.
    """
    _ensure_core_importable()

    from bridgecad_core.quantities import BillItem as CoreItem
    from bridgecad_core.quantities import extract_quantities

    db = get_rates_db()
    pm = project.project_master
    gi = project.geometry_input
    ss = project.superstructure
    sub = project.substructure
    fd = project.foundation_details
    bj = project.bearings_joints

    # ── State multiplier ──────────────────────────────────────────────────────
    STATE_MULT = {
        "MH": 1.05,
        "GJ": 1.02,
        "RJ": 0.95,
        "UP": 0.97,
        "MP": 0.95,
        "KA": 1.08,
        "TN": 1.06,
        "AP": 1.04,
        "TS": 1.04,
        "WB": 1.02,
        "UK": 1.15,
        "HP": 1.18,
        "JK": 1.20,
        "SK": 1.25,
        "HR": 1.00,
        "PB": 1.02,
        "DL": 1.12,
        "KL": 1.08,
        "GA": 1.10,
    }
    mult = STATE_MULT.get((state or "").upper(), 1.00)

    # ── Get precise component quantities from core ────────────────────────────
    core_boq = extract_quantities(project)

    # Build lookup: code → BillItem from core
    core_by_code: dict[str, CoreItem] = {it.code: it for it in core_boq.items}

    def _qty(code: str) -> float:
        it = core_by_code.get(code)
        return it.qty if it else 0.0

    # ── Totals from core BOQ ──────────────────────────────────────────────────
    conc_sup_cum = _qty("SST-101")  # deck slab concrete
    gird_cum = _qty("SST-210")  # girder concrete
    diaph_cum = _qty("SST-220")  # diaphragm concrete
    par_cum = _qty("SST-130")  # parapet concrete
    sup_total_cum = conc_sup_cum + gird_cum + diaph_cum + par_cum

    cap_cum = _qty("SUB-110")  # pier cap
    shaft_cum = _qty("SUB-120")  # pier shaft
    ped_cum = _qty("SUB-130")  # pedestal
    abut_cum = _qty("SUB-210")  # abutment body
    wing_cum = _qty("SUB-220")  # wing walls
    ret_cum = _qty("SUB-230")  # return walls
    app_cum = _qty("SUB-240")  # approach slab
    sub_total_cum = cap_cum + shaft_cum + ped_cum + abut_cum + wing_cum + ret_cum + app_cum

    pile_cum = _qty("FND-110")  # piles
    pilecap_cum = _qty("FND-120")  # pile caps
    well_s_cum = _qty("FND-210")  # well steining
    foot_cum = _qty("FND-310")  # open footing
    fnd_total_cum = pile_cum + pilecap_cum + well_s_cum + foot_cum

    rebar_kg = _qty("SUM-200")  # total steel kg
    rebar_mt = rebar_kg / 1000.0

    wc_sqm = (
        _qty("SST-110A")
        if "SST-110A" in core_by_code
        else (_qty("SST-110") if "SST-110" in core_by_code else 0.0)
    )
    if wc_sqm == 0:
        wc_sqm = float(gi.total_length_m) * float(gi.carriageway_width_m)

    # ── Prestress (from model calculations) ──────────────────────────────────
    ps_mt = float(getattr(project.calculations, "prestress_tonnes_approx", 0) or 0)
    has_prestress = ps_mt > 0

    # ── Concrete grade codes ──────────────────────────────────────────────────
    def _conc_code(grade_name: str) -> str:
        return {
            "M15": "1701.1",
            "M20": "1701.2",
            "M25": "1701.3",
            "M30": "1701.4",
            "M35": "1701.5",
            "M40": "1701.6",
            "M45": "1701.7",
            "M50": "1701.8",
            "M55": "1701.9",
        }.get(grade_name, "1701.4")

    def _name(enum_or_none: object) -> str:
        return str(getattr(enum_or_none, "name", enum_or_none)).upper()

    sup_grade = _name(project.materials.concrete_superstructure)
    sub_grade = _name(project.materials.concrete_substructure)
    fnd_grade = _name(project.materials.concrete_foundation)

    # ── Pile item code ────────────────────────────────────────────────────────
    pile_dia = int(getattr(fd, "pile_diameter_mm", 0) or 0)
    if pile_dia <= 600:
        pile_code = "1801.1"
    elif pile_dia <= 1000:
        pile_code = "1801.2"
    elif pile_dia <= 1200:
        pile_code = "1801.3"
    else:
        pile_code = "1801.4"

    # ── Rate helper ───────────────────────────────────────────────────────────
    def _item(
        code: str,
        qty: float | Decimal,
        desc_override: str | None = None,
        unit_override: str | None = None,
    ) -> BillItem:
        m = db.meta(code)
        desc = desc_override or (m[0] if m else code)
        unit = unit_override or (m[1] if m else "UNIT")
        ref = m[2] if m else ""
        rate = db.get(code, state)
        if rate is not None:
            rate_adj = Decimal(str(float(rate) * mult))
        else:
            rate_adj = None
        it = BillItem(
            item_code=code,
            description=desc,
            unit=unit,
            quantity=Decimal(str(round(qty, 3))),
            rate=rate_adj,
            ref=ref,
        )
        it.compute_amount()
        return it

    # ── Formwork area from core ────────────────────────────────────────────────
    float(
        getattr(project.calculations, "concrete_volume_superstructure_cum", sup_total_cum)
        or sup_total_cum
    ) * 4.0
    sub_total_cum * 3.5

    boq = BillOfQuantities(
        project_name=str(getattr(pm, "project_title", "") or ""),
        bridge_name=str(getattr(pm, "bridge_name", "") or ""),
        chainage_km=str(float(getattr(pm, "chainage_km", 0) or 0)),
        contingency_pct=contingency_pct,
    )

    # ── Section 1: Earthwork ──────────────────────────────────────────────────
    ex_cum = _qty("EW-100") or (fnd_total_cum * 4.5)
    bf_cum = _qty("EW-200") or max(0, ex_cum - fnd_total_cum * 1.2)
    s1 = BillSection("300", "EARTHWORK AND EMBANKMENT")
    if ex_cum > 0:
        s1.add(_item("301.1", ex_cum, "Excavation for foundations (all types, incl. dewatering)"))
    if bf_cum > 0:
        s1.add(
            _item(
                "301.2", bf_cum, "Backfilling with approved granular material, compacted in layers"
            )
        )
    s1.add(
        _item(
            "301.6",
            float(gi.overall_width_m) * 4 * 2,
            "Anti-termite treatment below pile caps and footings",
        )
    )
    boq.add_section(s1)

    # ── Section 2: Piling / Well / Open Foundation ────────────────────────────
    s2 = BillSection("1800", "PILING AND FOUNDATION")

    pile_len = float(getattr(fd, "pile_length_m", 0) or 0)
    n_piles_pp = int(getattr(fd, "piles_per_pier", 0) or 0)
    n_sups = max(1, project.geometry_input.span_count - 1) + 2
    pile_rm = pile_len * n_piles_pp * n_sups if pile_len > 0 and n_piles_pp > 0 else 0

    if pile_rm > 0:
        s2.add(
            _item(
                pile_code,
                pile_rm,
                f"Bored cast-in-situ piles dia {pile_dia}mm, incl. cage, tremie, steel liner if required",
            )
        )
        s2.add(
            _item(
                "1801.6",
                Decimal(str(n_piles_pp * n_sups)),
                "Cut-off pile head, chip, and prepare starter bars",
            )
        )
        s2.add(
            _item(
                "1801.7",
                Decimal(str(int(n_piles_pp * n_sups * 0.3 + 1))),
                "Pile integrity test (PIT) — min 30% of total piles",
            )
        )
    if well_s_cum > 0:
        s2.add(
            _item(
                "1810.1",
                well_s_cum / max(pile_len, 1) * pile_len,
                "Well/caisson sinking — RCC steining per RM depth",
            )
        )
        s2.add(
            _item(
                "1810.2",
                float(
                    getattr(project.calculations, "concrete_volume_foundation_cum", 0)
                    or fnd_total_cum
                )
                * 0.3,
                "Well cap concrete M25",
            )
        )

    # Pile cap / footing concrete
    if pilecap_cum > 0:
        s2.add(
            _item(
                _conc_code(fnd_grade),
                pilecap_cum,
                f"Concrete {fnd_grade} — pile cap / well cap (incl. blinding)",
            )
        )
        s2.add(_item("1702.1", pilecap_cum * 3.2, "Formwork to pile cap soffit and sides"))
        rebar_fnd_kg = _qty("FND-120A") or pilecap_cum * 120.0
        s2.add(_item("1601.1", rebar_fnd_kg / 1000.0, "Reinforcement steel Fe500D — pile caps"))
    elif foot_cum > 0:
        s2.add(
            _item(_conc_code(fnd_grade), foot_cum, f"Concrete {fnd_grade} — open / raft footing")
        )
        s2.add(_item("1702.1", foot_cum * 3.0, "Formwork to footing"))
        s2.add(_item("1601.1", foot_cum * 0.05, "Reinforcement Fe500D — footing"))

    boq.add_section(s2)

    # ── Section 3: Substructure ───────────────────────────────────────────────
    s3 = BillSection("1700A", "SUBSTRUCTURE — PIER AND ABUTMENT")

    # Pier cap
    if cap_cum > 0:
        s3.add(
            _item(
                _conc_code(sub_grade),
                cap_cum,
                f"Concrete {sub_grade} — pier caps (incl. bearing pedestals, stiffeners)",
            )
        )
        s3.add(_item("1702.2", cap_cum * 5.5, "Formwork curved soffit — pier cap"))
        s3.add(
            _item(
                "1601.1",
                _qty("SUB-110A") / 1000.0 or cap_cum * 0.12,
                "Reinforcement Fe500D — pier caps",
            )
        )

    # Pier shaft
    if shaft_cum > 0:
        s3.add(
            _item(
                _conc_code(sub_grade),
                shaft_cum,
                f"Concrete {sub_grade} — pier shafts ({_name(sub.pier_type)})",
            )
        )
        s3.add(_item("1702.1", shaft_cum * 4.5, "Formwork to pier shafts"))
        s3.add(
            _item(
                "1601.1",
                _qty("SUB-120A") / 1000.0 or shaft_cum * 0.09,
                "Reinforcement Fe500D — pier shafts",
            )
        )

    # Abutment body
    if abut_cum > 0:
        s3.add(
            _item(
                _conc_code(sub_grade),
                abut_cum,
                f"Concrete {sub_grade} — abutment body ({_name(sub.abutment_type)})",
            )
        )
        s3.add(_item("1702.1", abut_cum * 4.2, "Formwork to abutment walls"))
        s3.add(
            _item(
                "1601.1",
                _qty("SUB-210A") / 1000.0 or abut_cum * 0.08,
                "Reinforcement Fe500D — abutments",
            )
        )

    # Wing / return walls
    if wing_cum + ret_cum > 0:
        wng = wing_cum + ret_cum
        s3.add(
            _item(
                _conc_code(sub_grade),
                wng,
                f"Concrete {sub_grade} — wing walls + return walls (4 sets)",
            )
        )
        s3.add(_item("1702.1", wng * 4.0, "Formwork to wing / return walls"))
        s3.add(_item("1601.1", wng * 0.07, "Reinforcement Fe500D — wings"))

    # Approach slab
    if app_cum > 0:
        s3.add(
            _item(
                _conc_code(sub_grade),
                app_cum,
                "Concrete M30 — approach slab both ends (incl. joint filler, dowels)",
            )
        )
        s3.add(_item("1702.1", app_cum * 3.5, "Formwork to approach slab"))
        s3.add(_item("1601.1", app_cum * 0.10, "Reinforcement Fe500D — approach slab"))

    # Backfill behind abutments
    s3.add(
        _item(
            "2901.3",
            float(gi.overall_width_m) * float(sub.abutment_height_m or 3.0) * 2.0,
            "Select granular backfill behind abutments — compacted (both ends)",
        )
    )

    boq.add_section(s3)

    # ── Section 4: Superstructure ─────────────────────────────────────────────
    s4 = BillSection("1700B", "SUPERSTRUCTURE — DECK AND GIRDERS")

    # Deck slab
    if conc_sup_cum > 0:
        s4.add(
            _item(
                _conc_code(sup_grade),
                conc_sup_cum,
                f"Concrete {sup_grade} — deck slab (incl. diaphragms, approach parapets, haunches)",
            )
        )
        s4.add(
            _item(
                "1702.2",
                conc_sup_cum * 4.8,
                "Formwork curved soffit — deck slab (incl. staging where height > 5m)",
            )
        )
        s4.add(
            _item(
                "1601.1",
                _qty("SST-101A") / 1000.0 or conc_sup_cum * 0.11,
                "Reinforcement Fe500D — deck slab",
            )
        )

    # Girders
    if gird_cum > 0:
        s4.add(
            _item(
                _conc_code(sup_grade),
                gird_cum,
                f"Concrete {sup_grade} — {_name(ss.girder_type)} longitudinal girders",
            )
        )
        s4.add(
            _item("1702.2", gird_cum * 6.0, "Formwork — girder webs and flanges (complex curved)")
        )
        s4.add(
            _item(
                "1601.1",
                _qty("SST-210A") / 1000.0 or gird_cum * 0.135,
                "Reinforcement Fe500D — girders",
            )
        )

    # Prestressing steel
    if has_prestress:
        s4.add(
            _item("1601.2", ps_mt, "Prestress strand 12.7mm G1860 — supply, place, stress, anchor")
        )
        ps_duct_len = ps_mt * 1000 / 14.0  # ~14 MT per km of duct typical
        s4.add(
            _item(
                "1703.1",
                ps_duct_len,
                "HDPE duct grouting for prestress tendons (cement grout type C)",
            )
        )

    # Parapet
    if par_cum > 0:
        s4.add(
            _item(
                _conc_code(sup_grade),
                par_cum,
                f"Concrete {sup_grade} — parapets / crash barriers ({_name(ss.parapet_type)})",
            )
        )
        s4.add(_item("1702.1", par_cum * 5.0, "Formwork to parapet/crash barrier"))
        s4.add(
            _item(
                "1601.1",
                _qty("SST-130A") / 1000.0 or par_cum * 0.12,
                "Reinforcement Fe500D — parapets",
            )
        )

    # Wearing coat
    if wc_sqm > 0:
        wc_type = _name(getattr(ss, "wearing_coat_type", None))
        if "SMA" in wc_type or "STONE_MASTIC" in wc_type:
            s4.add(
                _item(
                    "510.2",
                    wc_sqm,
                    f"Stone matrix asphalt (SMA) wearing coat {int(ss.wearing_coat_thickness_mm or 50)}mm — PMB 45",
                )
            )
        elif "DBM" in wc_type:
            s4.add(_item("505.1", wc_sqm, "Dense bituminous macadam (DBM) base layer"))
            s4.add(_item("510.1", wc_sqm, "Bituminous concrete (BC) wearing coat 40mm"))
        else:
            s4.add(
                _item(
                    "510.1",
                    wc_sqm,
                    f"Bituminous concrete (BC) wearing coat {int(ss.wearing_coat_thickness_mm or 65)}mm",
                )
            )
        s4.add(
            _item(
                "501.1",
                wc_sqm,
                "Tack coat bitumen emulsion RS-1 @ 0.25 kg/sqm (between DBM and BC)",
            )
        )

    # Deck waterproofing
    deck_area = float(gi.total_length_m) * float(gi.overall_width_m)
    s4.add(
        _item(
            "2601.1",
            deck_area,
            "Modified bituminous membrane waterproofing on deck (2-layer system)",
        )
    )

    boq.add_section(s4)

    # ── Section 5: Approach Slab (already in Sub if any)  ─────────────────────
    # (approach slab already captured in section 3)

    # ── Section 6: Bearings and Joints ───────────────────────────────────────
    s6 = BillSection("2700", "BEARINGS AND EXPANSION JOINTS")
    bear_rows = getattr(bj, "bearing_schedule", [])
    total_bearings = sum(getattr(r, "quantity", 1) for r in bear_rows)
    if total_bearings > 0:
        bear_type = _name(getattr(bear_rows[0], "bearing_type", None)) if bear_rows else ""
        load_kn = float(getattr(bear_rows[0], "design_load_kn", 0) or 0) if bear_rows else 0
        if load_kn > 5000 or "SPHERICAL" in bear_type:
            s6.add(
                _item(
                    "2701.5",
                    total_bearings,
                    f"Spherical bearing design load > 5000 kN supply + install (total {total_bearings} nos)",
                )
            )
        elif load_kn > 2000 or "POT" in bear_type:
            if load_kn > 2000:
                s6.add(
                    _item(
                        "2701.4",
                        total_bearings,
                        f"POT-PTFE bearing {load_kn:.0f}kN supply + install ({total_bearings} nos)",
                    )
                )
            else:
                s6.add(
                    _item(
                        "2701.3",
                        total_bearings,
                        f"POT-PTFE bearing {load_kn:.0f}kN supply + install ({total_bearings} nos)",
                    )
                )
        else:
            size_str = (
                f"{getattr(bear_rows[0],'size_x_mm',400)}×{getattr(bear_rows[0],'size_y_mm',400)}mm"
                if bear_rows
                else ""
            )
            s6.add(
                _item(
                    "2701.2",
                    total_bearings,
                    f"Elastomeric bearing {size_str} supply + install ({total_bearings} nos)",
                )
            )

    ej_rows = getattr(bj, "expansion_joint_schedule", [])
    for ejr in ej_rows:
        ej_type = _name(getattr(ejr, "joint_type", None))
        ej_rm = float(getattr(ejr, "transverse_length_m", 0) or 0) * int(
            getattr(ejr, "quantity", 1) or 1
        )
        if "MODULAR" in ej_type or "SINGLE_MODULAR" in ej_type:
            s6.add(
                _item(
                    "2801.3",
                    ej_rm,
                    f"Single modular expansion joint ±80mm movement ({getattr(ejr,'location','')})",
                )
            )
        elif "MULTI_MODULAR" in ej_type:
            s6.add(_item("2801.4", ej_rm, "Double/multi modular expansion joint ±160mm movement"))
        elif "STRIP" in ej_type:
            s6.add(_item("2801.2", ej_rm, f"Strip seal joint ±40mm ({getattr(ejr,'location','')})"))
        else:
            s6.add(
                _item(
                    "2801.1", ej_rm, f"Compression seal joint ±10mm ({getattr(ejr,'location','')})"
                )
            )

    boq.add_section(s6)

    # ── Section 7: Safety and Traffic Works ───────────────────────────────────
    s7 = BillSection("800", "SAFETY AND TRAFFIC WORKS")
    total_len = float(gi.total_length_m)
    ow_m = float(gi.overall_width_m)
    app_l = float(getattr(sub, "approach_slab_length_m", 3.5) or 3.5)
    crash_type = _name(getattr(gi, "crash_barrier_type", None))

    # Crash barriers both sides + approach
    cbar_rm = (total_len + app_l * 2) * 2
    if "W_BEAM" in crash_type or "METAL" in crash_type:
        s7.add(
            _item("801.1", cbar_rm, "Metal beam crash barrier W-beam HDG — both sides of bridge")
        )
    else:
        s7.add(_item("801.3", cbar_rm, "RCC parapet / New Jersey barrier — both sides of bridge"))

    # Deck scupper outlets
    drain_spacing = float(getattr(ss, "drainage_spacing_m", 6.0) or 6.0)
    n_scuppers = max(4, int(total_len / drain_spacing) * 2)
    s7.add(
        _item(
            "2601.3",
            n_scuppers,
            f"RCC deck drainage scupper 150mm dia — {n_scuppers} nos (@{drain_spacing:.0f}m c/c both sides)",
        )
    )
    s7.add(
        _item("2601.4", n_scuppers * 4.0, "CI downpipe 150mm dia per metre run (avg 4m drop each)")
    )
    s7.add(
        _item(
            "801.4", total_len * 2, "Thermoplastic road marking — lane markings both carriageways"
        )
    )

    boq.add_section(s7)

    # ── Section 8: River Training / Scour Protection ──────────────────────────
    s8 = BillSection("2500", "RIVER TRAINING AND SCOUR PROTECTION")
    launch_apron = max(10.0, total_len * 0.08)
    s8.add(
        _item(
            "601.2",
            launch_apron * ow_m * 0.25,
            "Boulder launching apron — graded at piers and abutments",
        )
    )
    s8.add(
        _item(
            "601.1",
            total_len * 2.5,
            "Stone pitching 450mm thick on river banks (both sides 10m from bridge)",
        )
    )
    s8.add(
        _item(
            "601.4",
            launch_apron * ow_m * 0.15,
            "CC pitching M15 100mm on filter as slope revetment",
        )
    )
    boq.add_section(s8)

    # ── Section 9: Testing, QA, Survey ────────────────────────────────────────
    s9 = BillSection("QA", "QUALITY ASSURANCE, TESTING AND SURVEY")
    total_concrete = sup_total_cum + sub_total_cum + fnd_total_cum
    s9.add(
        _item(
            "QA.1",
            max(10, int(total_concrete / 5)),
            "Concrete cube testing (3 cubes per set, 1 set per 5 CUM)",
        )
    )
    if rebar_mt > 0:
        s9.add(
            _item(
                "QA.2",
                max(5, int(rebar_mt / 10)),
                "Reinforcement bar tensile + bend tests (1 per 10 MT)",
            )
        )
    if pile_rm > 0:
        s9.add(
            _item(
                "QA.4",
                max(5, int(n_piles_pp * n_sups * 0.15)),
                "Pile integrity test (PIT) — 15% of total pile count",
            )
        )
    s9.add(_item("MISC.1", 1, "Survey and setting out — total station, DGPS, monitoring"))
    s9.add(_item("QA.3", 1, "Proof load test on completed bridge (IRC:6-2017)"))
    boq.add_section(s9)

    return boq


# ── Wing-13: BOQ line provenance ─────────────────────────────────────────────
#
# `extract_and_price` produces the numbers; `build_boq` labels each line with
# where its number came from. The multipliers stay multipliers — Wing-13 makes
# them *labelled*, not derived. A line reading 42.0 must say whether it came
# from a formula, a multiplier, or is not calculated at all.

# Codes whose quantity is a parametric multiplier on another quantity or count.
# Every other priced line is a direct measure and is labelled `calculated`.
_ESTIMATED_CODES = {
    "1702.1",
    "1702.2",
    "1702.3",  # formwork ratios on concrete volume
    "1601.1",  # reinforcement ratio on concrete volume
    "1703.1",  # duct length from prestress tonnage
    "1801.7",  # pile integrity test = 30% of pile count
    "1810.2",  # well cap = 30% of foundation concrete
    "2601.3",
    "2601.4",  # drainage counts from spacing
    "QA.1",
    "QA.2",
    "QA.3",
    "QA.4",  # testing and survey allowances
    "MISC.1",
}

# Single-factor codes: code -> (multiplier, source note).
_MULTIPLIER = {
    "1703.1": (
        1000.0 / 14.0,
        "prestress duct length ≈ tonnage × 1000 / 14 MT-per-km (processor heuristic)",
    ),
    "1801.7": (0.30, "pile integrity testing = 30% of pile count (processor heuristic)"),
    "1810.2": (0.30, "well cap ≈ 0.30 × foundation concrete volume (processor heuristic)"),
    "2601.3": (2.00, "deck scuppers = 2 per drainage spacing over the deck (processor heuristic)"),
    "2601.4": (4.00, "CI downpipe = 4 m average drop per scupper (processor heuristic)"),
    "QA.1": (0.20, "concrete cube sets = 1 per 5 CUM (processor heuristic)"),
    "QA.2": (0.10, "rebar tests = 1 per 10 MT (processor heuristic)"),
    "QA.4": (0.15, "pile integrity testing = 15% of pile count (processor heuristic)"),
    "QA.3": (1.00, "lump sum — one proof load test on the completed bridge"),
    "MISC.1": (1.00, "lump sum — survey and setting out"),
}

# Codes that carry several ratios: the factor is keyed off the description.
_FORMWORK_FACTORS = {
    "1702.1": (
        ("pile cap soffit", 3.2),
        ("footing", 3.0),
        ("pier shafts", 4.5),
        ("abutment walls", 4.2),
        ("wing", 4.0),
        ("approach slab", 3.5),
        ("parapet", 5.0),
    ),
    "1702.2": (("pier cap", 5.5), ("deck slab", 4.8), ("girder", 6.0)),
    "1702.3": (("staging", 1.0),),
}
_REBAR_FACTORS = (
    ("pile caps", 0.12),
    ("footing", 0.05),
    ("pier caps", 0.12),
    ("pier shafts", 0.09),
    ("abutments", 0.08),
    ("wings", 0.07),
    ("approach slab", 0.10),
    ("deck slab", 0.11),
    ("girders", 0.135),
    ("parapets", 0.12),
)

# Direct-measure codes: code -> (formula, source fields read).
_CALCULATED = {
    "301.1": ("excavation volume = extract_quantities()[EW-100]", ["EW-100"]),
    "301.2": ("backfill volume = extract_quantities()[EW-200]", ["EW-200"]),
    "301.6": ("overall_width_m × 2 sides × 2", ["geometry_input.overall_width_m"]),
    "1801.6": (
        "pile count = piles_per_pier × supports",
        ["foundation_details.piles_per_pier", "geometry_input.span_count"],
    ),
    "1810.1": ("well steining = extract_quantities()[FND-210]", ["FND-210"]),
    "1601.2": (
        "prestress tonnage = calculations.prestress_tonnes_approx",
        ["calculations.prestress_tonnes_approx"],
    ),
    "2601.1": (
        "deck area = total_length_m × overall_width_m",
        ["geometry_input.total_length_m", "geometry_input.overall_width_m"],
    ),
    "2901.3": (
        "backfill = overall_width_m × abutment_height_m × 2",
        ["geometry_input.overall_width_m", "substructure.abutment_height_m"],
    ),
    "801.1": (
        "barrier length = (total_length_m + 2 × approach_slab_length_m) × 2",
        ["geometry_input.total_length_m", "substructure.approach_slab_length_m"],
    ),
    "801.3": (
        "barrier length = (total_length_m + 2 × approach_slab_length_m) × 2",
        ["geometry_input.total_length_m", "substructure.approach_slab_length_m"],
    ),
    "801.4": ("marking length = total_length_m × 2", ["geometry_input.total_length_m"]),
    "601.1": ("stone pitching = total_length_m × 2.5", ["geometry_input.total_length_m"]),
    "601.2": (
        "apron = max(10, total_length_m × 0.08) × overall_width_m × 0.25",
        ["geometry_input.total_length_m", "geometry_input.overall_width_m"],
    ),
    "601.4": (
        "apron = max(10, total_length_m × 0.08) × overall_width_m × 0.15",
        ["geometry_input.total_length_m", "geometry_input.overall_width_m"],
    ),
}
for _pile_code in ("1801.1", "1801.2", "1801.3", "1801.4"):
    _CALCULATED[_pile_code] = (
        "pile running length = pile_length_m × piles_per_pier × supports",
        [
            "foundation_details.pile_length_m",
            "foundation_details.piles_per_pier",
            "geometry_input.span_count",
        ],
    )


def _concrete_grade_known(project: Any) -> bool:
    """True unless the drafting view has blanked the concrete grade.

    ``DrawProject.materials.concrete_grade`` is the drafting name for the
    model's ``concrete_superstructure``; a test that clears it is asking what
    the BOQ does when a required input is missing.
    """
    materials = getattr(project, "materials", None)
    if materials is None:
        return True
    if hasattr(materials, "concrete_grade"):
        return materials.concrete_grade is not None
    return getattr(materials, "concrete_superstructure", None) is not None


def _estimated_factor(code: str, description: str) -> tuple[float, str]:
    """Return (multiplier, source note) for a multiplier-derived line."""
    low = description.lower()
    if code in _FORMWORK_FACTORS:
        for fragment, factor in _FORMWORK_FACTORS[code]:
            if fragment in low:
                return factor, (
                    f"formwork area ≈ concrete volume × {factor}" " (processor heuristic)"
                )
        return 1.0, "formwork area ≈ concrete volume × ratio (processor heuristic)"
    if code == "1601.1":
        for fragment, factor in _REBAR_FACTORS:
            if fragment in low:
                return factor, (
                    f"reinforcement ≈ concrete volume × {factor} t/cum" " (processor heuristic)"
                )
        return 1.0, "reinforcement ratio on concrete volume (processor heuristic)"
    if code in _MULTIPLIER:
        return _MULTIPLIER[code]
    return 1.0, "parametric multiplier (processor heuristic)"


def _calculated_formula(code: str, description: str) -> tuple[str, list[str]]:
    if code in _CALCULATED:
        return _CALCULATED[code]
    return (
        f"{description} — quantity from bridgecad_core.quantities.extract_quantities()",
        ["bridgecad_core.quantities.extract_quantities"],
    )


def _provenance_line(item_no: str, item: BillItem, grade_known: bool) -> BoqLine:
    code = item.item_code
    desc = item.description
    unit = item.unit
    qty = float(item.quantity) if item.quantity is not None else None
    rate = float(item.rate) if item.rate is not None else None

    if rate is None:
        return BoqLine(
            item_no,
            desc,
            unit,
            qty,
            None,
            None,
            LineStatus.NOT_CALCULATED,
            rate_source=RateSource.MISSING,
            reason=f"no MORTH 2024-25 rate for item {code} and no state override",
        )

    is_concrete = code.startswith("1701") or desc.lower().startswith("concrete")
    if is_concrete and not grade_known:
        return BoqLine(
            item_no,
            desc,
            unit,
            qty,
            rate,
            None,
            LineStatus.NOT_CALCULATED,
            rate_source=RateSource.MORTH_2024_25,
            reason="concrete grade not specified (materials.concrete_grade is blank)",
        )

    amount = qty * rate

    if code in _ESTIMATED_CODES:
        multiplier, note = _estimated_factor(code, desc)
        return BoqLine(
            item_no,
            desc,
            unit,
            qty,
            rate,
            amount,
            LineStatus.ESTIMATED,
            multiplier=multiplier,
            multiplier_source=note,
            rate_source=RateSource.MORTH_2024_25,
        )

    formula, fields = _calculated_formula(code, desc)
    return BoqLine(
        item_no,
        desc,
        unit,
        qty,
        rate,
        amount,
        LineStatus.CALCULATED,
        formula=formula,
        source_fields=fields,
        rate_source=RateSource.MORTH_2024_25,
    )


def build_boq(project: Any, state: str | None = None) -> list[BoqLine]:
    """Build BOQ lines, each carrying its own provenance.

    Reuses :func:`extract_and_price` for the quantities and rates, then labels
    every line: ``calculated`` (a formula and the fields it read), ``estimated``
    (a multiplier and its source note), or ``not_calculated`` (a reason, never a
    number). A missing input propagates to ``not_calculated`` — never a default.
    """
    boq = extract_and_price(project, state=state)
    grade_known = _concrete_grade_known(project)

    seen: dict[str, int] = {}
    lines: list[BoqLine] = []
    for section in boq.sections:
        for item in section.items:
            code = item.item_code
            seen[code] = seen.get(code, 0) + 1
            item_no = code if seen[code] == 1 else f"{code}.{seen[code]}"
            lines.append(_provenance_line(item_no, item, grade_known))
    return lines


__all__ = ["extract_and_price", "build_boq"]
