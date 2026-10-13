"""
bridgecad_core.quantities — BOM extractor (concrete, steel, earthwork, surfacing).
M1 Week 2 implementation. Covers:
  - Deck slab + wearing coat concrete + surfacing area
  - T-beam / I-girder / box-girder longitudinal girder concrete + diaphragms
  - Pier caps + pier shafts (wall / rectangular / circular / hammerhead)
  - Abutment body + return walls + wing walls + approach slab
  - Pile group (Npiles per pier × pier_count + 2 abutments) concrete + pile caps
  - Well / caisson steining + plug concrete
  - Open / stepped / raft footings
  - HFL/LWL scour excavation + backfill (rough default 2 m embedment if no HFL)
  - Rebar (kg) by component using IRC rule-of-thumb rebar %
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import Decimal

from .models import BridgeProject


# ===========================================================================
# Data classes
# ===========================================================================


@dataclass
class BillItem:
    code: str
    description: str
    unit: str
    qty: float
    rate: float | None = None
    amount: float | None = None


@dataclass
class BillOfQuantities:
    items: list[BillItem] = field(default_factory=list)
    total_cost: float = 0.0

    def add(self, item: BillItem) -> None:
        self.items.append(item)


# ===========================================================================
# Internal helpers
# ===========================================================================


_MATH_PI = float(math.pi)


def _f(x: Decimal | float | int | None, default: float = 0.0) -> float:
    if x is None:
        return default
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _name(enum) -> str:
    return getattr(enum, "name", str(enum)).upper()


# ----- Rebar density & rule-of-thumb percentages (IRC/IS standard recipes) --
_REBAR_DENSITY_TON_PER_M3 = 7.85          # ton / m3 steel  (≈ 7850 kg/m3)

# Rebar as % of gross concrete volume, per typical BOQ
_REBAR_PCT = {
    "deck_slab":      1.10,  # typical ~1.1% rebar in deck slab
    "wearing_coat":   0.00,  # bituminous — no steel
    "girders":        1.35,  # T/I-girder main steel + stirrups ~1.35%
    "diaphragm":      0.80,
    "pier_cap":       1.20,
    "pier_shaft":     0.90,
    "pier_pedestal":  1.00,
    "abutment_body":  0.80,
    "abutment_wing":  0.70,
    "abutment_return":0.70,
    "approach_slab":  1.00,
    "pile_cap":       1.20,
    "piles":          1.50,  # long spiral cages — higher %
    "well_steining":  0.80,
    "well_plugs":     0.60,
    "footings":       0.40,  # raft/open footing — minimal steel
    "raft":           0.60,
}


def _rebar_kg(concrete_m3: float, pct_key: str) -> float:
    """Rebar mass in kg for a component given its gross concrete volume."""
    pct = _REBAR_PCT.get(pct_key, 0.5) / 100.0
    return concrete_m3 * pct * _REBAR_DENSITY_TON_PER_M3 * 1000.0


# ----- Helpers: component geometry (returns float m3 or m2 / m / kg) -------


def _deck_slab_cum(proj: BridgeProject) -> float:
    L = _f(proj.geometry_input.total_length_m)
    W = _f(proj.geometry_input.overall_width_m)
    t = _f(proj.superstructure.deck_thickness_mm) / 1000.0
    return L * W * t


def _wearing_coat_cum(proj: BridgeProject) -> float:
    """Wearing coat (bituminous) volume, counted only on carriageway."""
    L = _f(proj.geometry_input.total_length_m)
    Wcarriage = _f(proj.geometry_input.carriageway_width_m)
    t = _f(proj.superstructure.wearing_coat_thickness_mm) / 1000.0
    return L * Wcarriage * t


def _wearing_coat_area_m2(proj: BridgeProject) -> float:
    L = _f(proj.geometry_input.total_length_m)
    Wcarriage = _f(proj.geometry_input.carriageway_width_m)
    return L * Wcarriage


def _girders_cum(proj: BridgeProject) -> float:
    """Sum of all longitudinal girder concrete m3.
    T-beam: web rectangle + slab effective flange approximated by slab_volume already.
    Girder "stem" = girder_depth_mm × 1/2 girder_spacing × total_length × n_girders.
    I-girder: web rectangle only (flanges approximated with web*1.15).
    Box girder: overall_width × deck_thickness is deck, box stem =
                (overall_width - 0.4) × girder_depth × total_length × fill ratio.
    Slab-only types: 0 (all slab accounted under deck_slab).
    """
    ss = proj.superstructure
    sst = _name(ss.type)

    n_girders = int(ss.girders_per_deck_count or 0)
    if n_girders <= 0:
        return 0.0
    L = _f(proj.geometry_input.total_length_m)
    D = _f(ss.girder_depth_mm) / 1000.0
    s = _f(ss.girder_spacing_m)
    if D <= 0 or L <= 0:
        return 0.0

    girder_shape = _name(ss.girder_type or "")
    # ----- Web width recipes per shape: -----
    if any(k in sst for k in ("PSC_BOX", "STEEL_BOX")):
        # Box girder — total cross-section ~ overall_width × depth * 0.55 hollow ratio
        W = _f(proj.geometry_input.overall_width_m)
        return L * W * D * 0.55
    if "T_BEAM" in girder_shape or "TBEAM" in girder_shape or sst == "RCC_TBEAM":
        # Stem width = 0.35 m typical for T-beam stem; L includes all spans
        stem_w = min(0.45, max(0.25, D * 0.25))
        return L * D * stem_w * n_girders
    if "I_GIRDER" in girder_shape or "IGIRDER" in girder_shape or sst in {
        "PSC_IGIRDER", "PSC_I_GIRDER_COMPOSITE", "PSC_U_GIRDER"
    }:
        # I-girder: web rectangle + two flanges ~ 15%
        stem_w = min(0.35, max(0.18, D * 0.18))
        return L * D * stem_w * n_girders * 1.15
    if "PLATE_GIRDER" in girder_shape or sst in {"STEEL_PLATE_GIRDER", "STEEL_TRUSS"}:
        # Concrete deck only, girder is steel → 0
        return 0.0
    # Fallback: generic rectangular web
    stem_w = D * 0.22
    return L * D * stem_w * n_girders


def _diaphragm_cum(proj: BridgeProject) -> float:
    """Cross / intermediate diaphragm m3 (between girders) + end diaphragms."""
    ss = proj.superstructure
    n_girders = int(ss.girders_per_deck_count or 0)
    if n_girders <= 1:
        return 0.0
    t = _f(getattr(ss, "diaphragm_thickness_mm", 0)) / 1000.0
    if t <= 0:
        t = 0.25  # default 250 mm
    D = _f(ss.girder_depth_mm) / 1000.0
    s = _f(ss.girder_spacing_m)
    if D <= 0 or s <= 0:
        return 0.0
    n_intermediate = int(getattr(ss, "longitudinal_diaphragm_count", 0) or 0)
    # Spans each need 2 end diaphragms (at supports) + n_internal diaphragms
    n_spans = int(proj.geometry_input.span_count or 1)
    n_gaps = n_girders - 1
    per_span = (n_intermediate + 2) * n_gaps  # end diaphragms at both ends
    total_diaph = n_spans * per_span
    return total_diaph * (D * s * t)


# ===========================================================================
# Substructure (piers + abutments)
# ===========================================================================


def _pier_count(proj: BridgeProject) -> int:
    n_spans = int(proj.geometry_input.span_count or 1)
    return max(0, n_spans - 1)


def _pier_concrete(proj: BridgeProject) -> tuple[float, float, float]:
    """Return (pier_cap_m3, pier_shaft_m3, pier_pedestal_m3)."""
    sub = proj.substructure
    n_piers = _pier_count(proj)
    if n_piers <= 0:
        return 0.0, 0.0, 0.0
    # Pier cap
    W = _f(sub.pier_cap_width_m)
    L = _f(sub.pier_cap_length_m)
    D = _f(sub.pier_cap_depth_m)
    cap = n_piers * (W * L * D) if W > 0 and L > 0 and D > 0 else 0.0

    # Pier shaft — 3 shape recipes
    shape = _name(sub.pier_shaft_shape or "")
    h = _f(sub.pier_height_typical_m)
    if h <= 0:
        shaft = 0.0
    elif "CIRCULAR" in shape or "ROUND" in shape or "OCTAGONAL" in shape:
        d = _f(sub.pier_diameter_m)
        shaft_area = _MATH_PI / 4 * d * d if d > 0 else 0.0
        shaft = n_piers * h * shaft_area
    else:
        # Wall or rectangular multi-shaft
        sw = _f(sub.pier_shaft_width_m)
        sl = _f(sub.pier_shaft_length_m)
        if sw <= 0 or sl <= 0:
            shaft = 0.0
        else:
            shaft = n_piers * h * sw * sl

    # Pedestal(s) — bearings_per_pier pads, 0.4m×0.4m typical on cap top
    npad = int(sub.bearings_per_pier or 0)
    hp = _f(sub.pier_pedestal_height_m)
    pad_w = _f(getattr(proj.superstructure, "bearing_pad_size_mm", 0)) / 1000.0
    if pad_w <= 0:
        pad_w = 0.4
    pedestal = n_piers * npad * hp * (pad_w * pad_w) if hp > 0 and npad > 0 else 0.0

    # Hammerhead overhang volume (additional) — approximate as 2 cantilevers
    hh = _f(getattr(sub, "pier_hammerhead_overhang_m", 0))
    if hh > 0 and n_piers > 0 and D > 0 and L > 0:
        cap += n_piers * 2.0 * hh * D * W * 0.5

    return cap, shaft, pedestal


def _abutment_concrete(proj: BridgeProject) -> tuple[float, float, float, float]:
    """Return (abutment_body_m3, wing_walls_m3, return_walls_m3, approach_slab_m3)."""
    sub = proj.substructure
    # Body (2 abutments)
    W = _f(sub.abutment_width_m)
    L = _f(sub.abutment_length_m)
    H = _f(sub.abutment_height_m)
    body = 2.0 * (W * L * H) if W > 0 and L > 0 and H > 0 else 0.0

    # Pedestals at abutment are part of body; skip double-counting

    # Wing walls — 2 abutments × 2 sides × splay length × height × thickness
    sw_L = _f(sub.wing_wall_splay_length_m)
    sw_H = _f(sub.wing_wall_height_m)
    sw_t = 0.35  # typical 350 mm RCC wing wall
    wing = 4.0 * (sw_L * sw_H * sw_t) if sw_L > 0 and sw_H > 0 else 0.0

    # Return walls — 2 abutments × 1 rear wall × length × height × thickness
    rw_L = _f(sub.return_wall_length_m)
    rw_H = _f(sub.return_wall_height_m)
    rw_t = 0.35
    ret = 2.0 * (rw_L * rw_H * rw_t) if rw_L > 0 and rw_H > 0 else 0.0

    # Approach slab — 2 abutments × length × transverse length × thickness
    aL = _f(sub.approach_slab_length_m)
    aT_mm = int(sub.approach_slab_thickness_mm or 0)
    if aL > 0 and aT_mm > 0:
        # Transverse width ≈ overall_width
        Wtrans = _f(proj.geometry_input.overall_width_m)
        t = aT_mm / 1000.0
        app = 2.0 * aL * Wtrans * t
    else:
        app = 0.0

    return body, wing, ret, app


# ===========================================================================
# Foundations
# ===========================================================================


def _foundation_concrete(proj: BridgeProject) -> tuple[float, float, float, float, float]:
    """Return (piles_m3, pile_caps_m3, well_steining_m3, well_plugs_m3, footings_m3)."""
    fn = proj.foundation_details
    ftype = _name(fn.type)
    n_piers = _pier_count(proj)
    n_sups = n_piers + 2  # piers + 2 abutments

    # --- PILES ---
    piles_m3 = 0.0
    caps_m3 = 0.0
    n_per = int(fn.piles_per_pier or 0)
    d_mm = int(fn.pile_diameter_mm or 0)
    Lm = _f(fn.pile_length_m)
    cap_t_mm = int(fn.pile_cap_thickness_mm or 0)
    s = _f(fn.pile_spacing_m)

    if n_per > 0 and d_mm > 0 and Lm > 0 and "PILE" in ftype:
        d = d_mm / 1000.0
        area = _MATH_PI / 4 * d * d
        piles_m3 = n_sups * n_per * Lm * area
        # Pile caps: 2 piles across → (s*(n_cols-1) + d*2)
        # Guess grid: if group config 2x2, 4x2, 3x3 parse rows/cols
        cfg = (fn.pile_group_config or "").replace("×", "x").upper()
        rows_cols = None
        for token in cfg.split():
            if "X" in token and not token.startswith("@"):
                try:
                    a, b = token.split("X", 1)
                    rc = int(a), int(b)
                    if 1 <= rc[0] <= 20 and 1 <= rc[1] <= 20:
                        rows_cols = rc
                        break
                except Exception:
                    continue
        if rows_cols is None:
            # Evenly split into as-square-as-possible grid
            cols = int(math.ceil(math.sqrt(n_per)))
            rows = int(math.ceil(n_per / cols))
            rows_cols = (rows, cols)
        rows, cols = rows_cols
        clear_c = max(d, 0.3)  # concrete cover beyond edge pile
        s_eff = s if s > 0 else 2.5 * d
        cap_L = cols * s_eff + d + 2 * clear_c
        cap_W = rows * s_eff + d + 2 * clear_c
        if cap_t_mm > 0:
            cap_t = cap_t_mm / 1000.0
            caps_m3 = n_sups * cap_L * cap_W * cap_t

    # --- WELL / CAISSON ---
    well_s = 0.0
    well_p = 0.0
    if "WELL" in ftype or "CAISSON" in ftype:
        D = _f(fn.well_diameter_m)
        t_steining = _f(fn.well_steining_tmm) / 1000.0
        h_bed = _f(fn.well_depth_below_bed_m)
        h_bank = 3.0  # default 3 m above bed to cutoff
        if D > 0 and t_steining > 0 and h_bed > 0:
            h_total = h_bed + h_bank
            outer = _MATH_PI / 4 * D * D
            inner_d = max(0.0, D - 2 * t_steining)
            inner = _MATH_PI / 4 * inner_d * inner_d
            ring_area = outer - inner
            well_s = n_sups * h_total * ring_area
            # Top & bottom plug — 2 × (D × π/4 × t_plug), t_plug ~ 1.5 m
            t_plug = max(1.2, D * 0.25)
            well_p = n_sups * 2 * (outer * t_plug)

    # --- OPEN FOOTING / RAFT ---
    foot_m3 = 0.0
    if "OPEN" in ftype or "STEPPED" in ftype:
        fx = _f(fn.open_length_m)
        fy = _f(fn.open_width_m)
        ft = _f(fn.open_depth_m)
        if fx <= 0:
            fx = _f(getattr(fn, "combined_footing_length_m", 0))
            fy = _f(getattr(fn, "combined_footing_width_m", 0))
        if fx > 0 and fy > 0 and ft > 0:
            foot_m3 = n_sups * fx * fy * ft
        # Stepped: 2 extra smaller steps, each 0.75 × prior
        if getattr(fn, "open_stepped_flag", False):
            foot_m3 *= 1.35
    if "RAFT" in ftype or "MAT" in ftype:
        L = _f(proj.geometry_input.total_length_m)
        W = _f(proj.geometry_input.overall_width_m)
        t = _f(fn.raft_thickness_mm) / 1000.0
        if t > 0 and L > 0 and W > 0:
            foot_m3 = max(foot_m3, L * W * t)

    return piles_m3, caps_m3, well_s, well_p, foot_m3


# ===========================================================================
# Earthwork (excavation + backfill)
# ===========================================================================


def _earthwork(proj: BridgeProject) -> tuple[float, float, float]:
    """Return (excavation_m3, backfill_m3, grading_m3)."""
    fn = proj.foundation_details
    ftype = _name(fn.type)
    n_piers = _pier_count(proj)
    n_sups = n_piers + 2
    # Default founding depth: embedment below GL (m)
    # If well depth present use that + 1.0m; if pile length: min(pile_len, 3) default cut-off 1.5m
    embed_m = 1.5
    if "WELL" in ftype or "CAISSON" in ftype:
        embed_m = max(embed_m, _f(fn.well_depth_below_bed_m) + 1.0)
    elif "PILE" in ftype:
        cutoff = 1.5  # 1.5 m below GL cutoff level typical
        # HFL scour: try hydraulic data
        try:
            hyd = proj.hydraulic_design
            scour = _f(getattr(hyd, "scour_depth_m", 0))
            embed_m = max(cutoff, scour + 0.5)
        except Exception:
            embed_m = cutoff
    else:
        embed_m = 1.2  # open footings — shallower

    # Excavation per support — working space 1.5 m around outer dimension
    # Pick the best available footing plan size per foundation type
    if "WELL" in ftype or "CAISSON" in ftype:
        fx = fy = _f(fn.well_diameter_m) or 4.0
    elif "PILE" in ftype:
        # Fallback excavation size per pile-cap
        n_per = int(getattr(fn, "piles_per_pier", 0) or 0)
        s = _f(getattr(fn, "pile_spacing_m", 0))
        d_m = _f(getattr(fn, "pile_diameter_mm", 0)) / 1000.0
        if n_per > 0 and s > 0 and d_m > 0:
            cols = int(__import__("math").ceil(__import__("math").sqrt(n_per)))
            rows = int(__import__("math").ceil(n_per / cols))
            fx = cols * s + d_m * 2
            fy = rows * s + d_m * 2
        else:
            fx = fy = _f(getattr(fn, "pile_cap_thickness_mm", 0)) / 1000.0 * 4.0
            if fx <= 0:
                fx = fy = 4.0
    else:
        fx = _f(getattr(fn, "open_length_m", 0))
        fy = _f(getattr(fn, "open_width_m", 0))
        if fx <= 0:
            fx = _f(getattr(fn, "combined_footing_length_m", 0))
            fy = _f(getattr(fn, "combined_footing_width_m", 0))
        if fx <= 0:
            fx = fy = 4.0
    ws = 1.5
    exca = n_sups * (fx + 2 * ws) * (fy + 2 * ws) * embed_m
    # Backfill ~ excav − concrete volume for foundations
    found_conc = sum(_foundation_concrete(proj))
    backfill = max(0.0, exca - found_conc * 1.25)  # shrinkage + forms buffer
    grading = n_sups * (fx + 2 * ws) * (fy + 2 * ws) * 0.15  # 150 mm blinding/blanketing
    return exca, backfill, grading


# ===========================================================================
# Main entrypoint
# ===========================================================================


def extract_quantities(project: BridgeProject) -> BillOfQuantities:
    """Compute concrete/steel/earthwork/surfacing quantities from a BridgeProject.

    Concrete recipes are rule-of-thumb suitable for GAD-level Bill of Quantities
    (±25 % before detailed design).
    """
    boq = BillOfQuantities()

    gi = project.geometry_input
    ss = project.superstructure
    sst = _name(ss.type)

    # =======================================================================
    # 1. DECK / SUPERSTRUCTURE
    # =======================================================================
    deck_cum = _deck_slab_cum(project)
    wc_cum = _wearing_coat_cum(project)
    wc_area = _wearing_coat_area_m2(project)
    gird_cum = _girders_cum(project)
    diaph_cum = _diaphragm_cum(project)

    # ---- Deck slab ----
    try:
        grade_str = str(getattr(ss.deck_material, "value", ss.deck_material))
        grade_num = int("".join(c for c in grade_str if c.isdigit()))
    except Exception:
        grade_num = 30
    boq.add(BillItem(
        code="SST-101",
        description="RCC Deck Slab in-situ (M%d) including parapet upstands, haunches, bearing stiffeners." % grade_num,
        unit="cum", qty=round(deck_cum, 3),
    ))
    boq.add(BillItem(
        code="SST-101A",
        description="Reinforcement steel for Deck Slab (kg, bundled & placed in forms).",
        unit="kg", qty=round(_rebar_kg(deck_cum, "deck_slab"), 1),
    ))

    # ---- Wearing coat (bituminous) ----
    if wc_cum > 0 or wc_area > 0:
        boq.add(BillItem(
            code="SST-110",
            description="Bituminous wearing course (BC/SMA/DBST as specified) — carriageway compacted thickness.",
            unit="sqm", qty=round(wc_area, 2),
        ))
        boq.add(BillItem(
            code="SST-110A",
            description="Bituminous wearing course concrete volume (for rate / cum estimation).",
            unit="cum", qty=round(wc_cum, 3),
        ))

    # ---- Parapets (RCC): 2 sides × length × height × t_typical 0.25 m ----
    if getattr(ss, "parapet_height_mm", 0):
        L = _f(gi.total_length_m)
        H = _f(ss.parapet_height_mm) / 1000.0
        t_par = 0.25
        par_cum = 2 * L * H * t_par
        boq.add(BillItem(
            code="SST-130",
            description="RCC Parapet / Crash Barrier wall on both kerb lines, including weep holes, fixings, railing inserts.",
            unit="cum", qty=round(par_cum, 3),
        ))
        boq.add(BillItem(
            code="SST-130A",
            description="Reinforcement steel for Parapets (kg).",
            unit="kg", qty=round(_rebar_kg(par_cum, "deck_slab"), 1),
        ))

    # ---- Girders ----
    if gird_cum > 0:
        boq.add(BillItem(
            code="SST-210",
            description="RCC / PSC %s longitudinal superstructure — girders (precast/cast-in-situ) with haunches & stirrups." % _name(ss.girder_type or sst),
            unit="cum", qty=round(gird_cum, 3),
        ))
        boq.add(BillItem(
            code="SST-210A",
            description="Reinforcement / Prestressing steel (kg) for longitudinal girders.",
            unit="kg", qty=round(_rebar_kg(gird_cum, "girders"), 1),
        ))

    # ---- Diaphragms ----
    if diaph_cum > 0:
        boq.add(BillItem(
            code="SST-220",
            description="RCC Cross/Intermediate Diaphragms (including end diaphragms at all supports).",
            unit="cum", qty=round(diaph_cum, 3),
        ))
        boq.add(BillItem(
            code="SST-220A",
            description="Reinforcement steel for diaphragms (kg).",
            unit="kg", qty=round(_rebar_kg(diaph_cum, "diaphragm"), 1),
        ))

    # =======================================================================
    # 2. SUBSTRUCTURE
    # =======================================================================
    cap_c, shaft_c, ped_c = _pier_concrete(project)
    ab_body, ab_wing, ab_ret, ab_app = _abutment_concrete(project)

    # ---- Piers ----
    if cap_c > 0:
        boq.add(BillItem(
            code="SUB-110",
            description="RCC Pier Caps (including bearing stiffeners & pedestals, dowels to pier shaft).",
            unit="cum", qty=round(cap_c, 3),
        ))
        boq.add(BillItem(code="SUB-110A", description="Reinforcement steel for Pier Caps (kg).",
                         unit="kg", qty=round(_rebar_kg(cap_c, "pier_cap"), 1)))
    if shaft_c > 0:
        boq.add(BillItem(
            code="SUB-120",
            description="RCC Pier shafts — %s section (all piers)." % _name(project.substructure.pier_shaft_shape or "WALL/RECTANGULAR"),
            unit="cum", qty=round(shaft_c, 3),
        ))
        boq.add(BillItem(code="SUB-120A", description="Reinforcement steel for Pier Shafts (kg).",
                         unit="kg", qty=round(_rebar_kg(shaft_c, "pier_shaft"), 1)))
    if ped_c > 0:
        boq.add(BillItem(
            code="SUB-130", description="RCC Bearing Pedestals on pier caps.",
            unit="cum", qty=round(ped_c, 3),
        ))
        boq.add(BillItem(code="SUB-130A", description="Reinforcement steel for Bearing Pedestals (kg).",
                         unit="kg", qty=round(_rebar_kg(ped_c, "pier_pedestal"), 1)))

    # ---- Abutments ----
    if ab_body > 0:
        boq.add(BillItem(
            code="SUB-210",
            description="RCC Abutment body — %s type (both abutments incl. bearings pedestals, weep holes, bearing shelf)." % _name(project.substructure.abutment_type),
            unit="cum", qty=round(ab_body, 3),
        ))
        boq.add(BillItem(code="SUB-210A", description="Reinforcement steel for Abutment Body (kg).",
                         unit="kg", qty=round(_rebar_kg(ab_body, "abutment_body"), 1)))
    if ab_wing > 0:
        boq.add(BillItem(
            code="SUB-220", description="RCC Wing walls (splayed / tapered / parallel — 4 nos.).",
            unit="cum", qty=round(ab_wing, 3),
        ))
        boq.add(BillItem(code="SUB-220A", description="Reinforcement steel for Wing walls (kg).",
                         unit="kg", qty=round(_rebar_kg(ab_wing, "abutment_wing"), 1)))
    if ab_ret > 0:
        boq.add(BillItem(
            code="SUB-230", description="RCC Return / Rear walls behind abutments (2 nos.).",
            unit="cum", qty=round(ab_ret, 3),
        ))
        boq.add(BillItem(code="SUB-230A", description="Reinforcement steel for Return walls (kg).",
                         unit="kg", qty=round(_rebar_kg(ab_ret, "abutment_return"), 1)))
    if ab_app > 0:
        boq.add(BillItem(
            code="SUB-240", description="RCC Approach / Transition Slab both ends (with joint filler, dowels to abutment).",
            unit="cum", qty=round(ab_app, 3),
        ))
        boq.add(BillItem(code="SUB-240A", description="Reinforcement steel for Approach Slab (kg).",
                         unit="kg", qty=round(_rebar_kg(ab_app, "approach_slab"), 1)))

    # =======================================================================
    # 3. FOUNDATIONS
    # =======================================================================
    pil_c, capc_c, ws_c, wp_c, ft_c = _foundation_concrete(project)

    if pil_c > 0:
        boq.add(BillItem(
            code="FND-110",
            description="Bored / Driven cast-in-situ RCC piles, incl. reinforcement cage placement & concreting under water (if required).",
            unit="cum", qty=round(pil_c, 3),
        ))
        boq.add(BillItem(code="FND-110A", description="Reinforcement steel for Pile cages (kg).",
                         unit="kg", qty=round(_rebar_kg(pil_c, "piles"), 1)))
    if capc_c > 0:
        boq.add(BillItem(
            code="FND-120", description="RCC Pile caps (with dowel starter bars, blinding concrete).",
            unit="cum", qty=round(capc_c, 3),
        ))
        boq.add(BillItem(code="FND-120A", description="Reinforcement steel for Pile caps (kg).",
                         unit="kg", qty=round(_rebar_kg(capc_c, "pile_cap"), 1)))
    if ws_c > 0:
        boq.add(BillItem(
            code="FND-210", description="RCC Well / Caisson steining (including curb, cutting edge, sinking).",
            unit="cum", qty=round(ws_c, 3),
        ))
        boq.add(BillItem(code="FND-210A", description="Reinforcement steel for Well steining (kg).",
                         unit="kg", qty=round(_rebar_kg(ws_c, "well_steining"), 1)))
    if wp_c > 0:
        boq.add(BillItem(
            code="FND-220", description="RCC Well bottom plug + top plug (plug concrete).",
            unit="cum", qty=round(wp_c, 3),
        ))
        boq.add(BillItem(code="FND-220A", description="Reinforcement steel for Well plugs (kg).",
                         unit="kg", qty=round(_rebar_kg(wp_c, "well_plugs"), 1)))
    if ft_c > 0:
        boq.add(BillItem(
            code="FND-310", description="RCC Open / Stepped / Raft / Mat footings (with blinding & anti-termite treatment).",
            unit="cum", qty=round(ft_c, 3),
        ))
        boq.add(BillItem(code="FND-310A", description="Reinforcement steel for Footings (kg).",
                         unit="kg", qty=round(_rebar_kg(ft_c, "footings"), 1)))

    # =======================================================================
    # 4. EARTHWORK
    # =======================================================================
    ex_c, bf_c, gr_c = _earthwork(project)
    if ex_c > 0:
        boq.add(BillItem(
            code="EW-100", description="Earthwork in excavation for all foundations (including dewatering, shoring, disposal within lead).",
            unit="cum", qty=round(ex_c, 1),
        ))
    if bf_c > 0:
        boq.add(BillItem(
            code="EW-200", description="Backfilling around foundations with approved moorum/sand/gravel in layers 250 mm incl. compaction.",
            unit="cum", qty=round(bf_c, 1),
        ))
    if gr_c > 0:
        boq.add(BillItem(
            code="EW-300", description="Blinding / Sand blanketing / Geotextile / Soling below footings & pile caps.",
            unit="cum", qty=round(gr_c, 1),
        ))

    # =======================================================================
    # 5. MISC. SUMMARY ITEMS
    # =======================================================================
    # Total concrete (excl. earthwork & bituminous) — for validation
    all_concrete_m3 = deck_cum + gird_cum + diaph_cum
    if getattr(ss, "parapet_height_mm", 0):
        L = _f(gi.total_length_m); H = _f(ss.parapet_height_mm)/1000.0
        all_concrete_m3 += 2*L*H*0.25
    all_concrete_m3 += cap_c + shaft_c + ped_c + ab_body + ab_wing + ab_ret + ab_app
    all_concrete_m3 += pil_c + capc_c + ws_c + wp_c + ft_c
    all_rebar_kg = sum(it.qty for it in boq.items if it.unit == "kg")

    if all_concrete_m3 > 0:
        boq.add(BillItem(
            code="SUM-100", description="Control total — gross RCC/PCC concrete volume (excl. bituminous).",
            unit="cum", qty=round(all_concrete_m3, 2),
        ))
    if all_rebar_kg > 0:
        boq.add(BillItem(
            code="SUM-200", description="Control total — reinforcement / prestressing steel mass.",
            unit="kg", qty=round(all_rebar_kg, 1),
        ))
        boq.add(BillItem(
            code="SUM-201", description="Control total — reinforcement / prestressing steel mass (tonnes).",
            unit="tonne", qty=round(all_rebar_kg / 1000.0, 3),
        ))

    return boq


__all__ = ["BillItem", "BillOfQuantities", "extract_quantities"]
