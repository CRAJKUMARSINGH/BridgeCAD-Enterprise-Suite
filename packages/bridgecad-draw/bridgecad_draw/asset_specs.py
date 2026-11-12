"""bridgecad_draw.asset_specs — the two drawing sets reproduced by the asset pack.

SOURCE OF EVERY NUMBER
    ``sample-gad-drawings/ilide.info-01-gad-at-ch-2-300-7x9-0-pr_*.pdf``
        PMGSY minor bridge, ODR 58 - Malsur - Rajura Ansing road, CH 2300.
        Schedule read off the sheet: FRL 102.625, bed level 97.610, height
        5.015 (= FRL - BL, so the pair is self-checking), span 7 x 9.0 m,
        overall width 8.400 m, carriageway 7.500 m, kerb 450 mm, B1 1.90,
        B2 0.95, B3 2.25, B4 0.67.
    ``sample-gad-drawings/ilide.info-gad-final-3-340-1-pr_*.pdf``
        1 x 6.0 m high-level bridge, Amarwada - Ramgarh road, CH 3+340.
        FRL 158.820, soffit 158.145, HFL 157.395, founding level 152.450,
        overall 12.0 m, carriageway 10.9 m, abutment face chain 1523 + 700 +
        2135 = 4358, approach slab 4500 (3500 effective), 75 mm wearing coat,
        20 mm expansion gap.

WHAT IS *NOT* INVENTED
    Where a value does not appear on the source sheets (the PMGSY HFL, the
    railing height, intermediate ground levels) the field stays ``None`` and
    the drawing either omits the tag or marks the value as interpolated.  A
    fabricated level on a GAD is worse than a missing one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class SheetIdentity:
    """Fields that print in the title block of every sheet in a set."""

    set_name: str
    project: str
    road: str
    chainage: str
    client: str
    consultant: str
    drawing_prefix: str
    total_sheets: int
    date: str = ""
    drawn: str = ""
    designed: str = ""
    approved: str = ""
    revision: str = "R-00"


@dataclass(frozen=True)
class SlabBridgeSpec:
    """PMGSY 7 x 9.0 m RCC solid-slab minor bridge (multi-span)."""

    ident: SheetIdentity
    spans: int = 7
    span_m: float = 9.0
    deck_width_m: float = 8.4
    carriageway_m: float = 7.5
    kerb_mm: float = 450.0
    frl: float = 102.625
    bed_level: float = 97.610
    found_level: float = 95.610  # 2.0 m below bed, per general note 11
    deck_slab_mm: float = 600.0
    wearing_mm: float = 75.0
    approach_slab_mm: float = 300.0
    levelling_mm: float = 150.0
    footing_depth_mm: float = 1200.0
    weep_hole_mm: float = 100.0
    b1: float = 1.90
    b2: float = 0.95
    b3: float = 2.25
    b4: float = 0.67
    pier_stem_m: float = 0.90
    pier_step_m: float = 0.30
    pier_steps_m: tuple[float, float, float, float] = (9.3, 9.9, 10.5, 11.1)
    hfl: float | None = None  # not scheduled on the source sheet
    notes: tuple[str, ...] = (
        "ALL DIMENSIONS ARE IN mm AND LEVELS IN METRES UNLESS OTHERWISE STATED.",
        "DRAWING IS NOT TO SCALE. DO NOT SCALE THE PRINT.",
        "CONCRETE GRADES :- LEVELLING COURSE PCC M15, FOUNDATION PCC M15, "
        "SUB-STRUCTURE PCC M20, ABUTMENT CAP M20, DIRT WALL M20, "
        "SLAB M25, RETURN WALL PCC M20, APPROACH SLAB M30.",
        "REINFORCEMENT :- Fe 500 CONFORMING TO IS 1786.",
        "BEARING :- TAR PAPER BEARING OVER LEVELLING COURSE.",
        "DESIGN LOADING :- ONE LANE OF CLASS 70-R FOR EVERY TWO LANES WITH ONE LANE "
        "OF CLASS A FOR THE REMAINING LANES, OR ONE LANE OF CLASS A FOR EACH LANE.",
        "WEEP HOLES 100 mm dia. @ 1000 mm c/c STAGGERED, THROUGH ABUTMENT AND RETURN WALL.",
        "BACKFILL :- C = 0, phi > 30 DEG., DENSITY 18 kN/cu.m, COMPACTED IN 200 mm LAYERS.",
        "EXPANSION JOINT AS PER MoRTH SPECIFICATION, 20 mm EXP. GAP WITH SEALANT.",
        "WEARING COAT 75 mm THK VRCC M30 OVER THE FULL DECK WIDTH.",
        "MINIMUM FOUNDATION DEPTH 2.0 m BELOW SCOUR LEVEL / 0.6 m INTO HARD ROCK.",
        "DRAINAGE SPOUTS 100 mm dia. THROUGH DECK AT THE LOW END OF CAMBER.",
        "DISTANCE BETWEEN K.T. WEIR AND BRIDGE 20.0 m.",
    )

    # -- derived (single definition, used by several sheets) -------------
    @property
    def length_m(self) -> float:
        return self.spans * self.span_m

    @property
    def soffit(self) -> float:
        return round(self.frl - (self.wearing_mm + self.deck_slab_mm) / 1000.0, 3)

    @property
    def deck_thickness_m(self) -> float:
        return (self.wearing_mm + self.deck_slab_mm) / 1000.0

    @property
    def height_m(self) -> float:
        """FRL - bed level; must reproduce the scheduled 5.015 m."""
        return round(self.frl - self.bed_level, 3)

    def pier_chainages(self) -> list[float]:
        return [i * self.span_m for i in range(1, self.spans)]

    def schedule_rows(self) -> list[list[str]]:
        return [
            ["CHAINAGE", self.ident.chainage],
            ["STRUCTURE", "MNB (RCC SOLID SLAB)"],
            ["SPAN", f"{self.spans} x {self.span_m:.1f} m"],
            ["FORMATION LEVEL (FRL)", f"{self.frl:.3f} m"],
            ["BED LEVEL (BL)", f"{self.bed_level:.3f} m"],
            ["HEIGHT (FRL - BL)", f"{self.height_m:.3f} m"],
            ["OVERALL WIDTH", f"{self.deck_width_m * 1000:.0f} mm"],
            ["CARRIAGEWAY WIDTH", f"{self.carriageway_m * 1000:.0f} mm"],
            ["B1 (ABUTMENT BASE)", f"{self.b1:.2f} m"],
            ["B2 (FOOTING STEP)", f"{self.b2:.2f} m"],
            ["B3 (RETURN WALL BASE)", f"{self.b3:.2f} m"],
            ["B4 (DIRT WALL)", f"{self.b4:.2f} m"],
        ]


@dataclass(frozen=True)
class SingleSpanSpec:
    """1 x 6.0 m high-level bridge — Amarwada to Ramgarh road, CH 3+340."""

    ident: SheetIdentity
    span_m: float = 6.0
    deck_len_m: float = 6.4
    deck_width_m: float = 12.0
    carriageway_m: float = 10.9
    frl: float = 158.820
    soffit: float = 158.145
    hfl: float = 157.395
    found_level: float = 152.450
    bed_level: float = 154.450
    wearing_mm: float = 75.0
    expansion_mm: float = 20.0
    approach_slab_m: float = 4.5
    approach_eff_m: float = 3.5
    abut_face_mm: float = 4358.0
    abut_steps_mm: tuple[float, float, float] = (1523.0, 700.0, 2135.0)
    sbc_t_sqm: float = 30.0
    seismic_zone: str = "III"
    boreholes: tuple[tuple[str, float, float, float], ...] = (
        # (name, ground RL, top of hard rock RL, termination RL)
        ("A1", 154.914, 153.050, 149.050),
        ("A2", 154.835, 153.050, 149.050),
    )
    level_rows: tuple[tuple[str, float, float], ...] = (
        # (chainage, ground level, founding level) — read off the level table;
        # the middle row is the river bed. Rows marked + are interpolated.
        ("3+327.8", 158.820, 152.450),
        ("3+334.0", 156.900, 152.450),
        ("3+340.0", 154.450, 152.450),
        ("3+346.0", 156.900, 152.450),
        ("3+352.2", 158.820, 152.450),
    )
    notes: tuple[str, ...] = (
        "TYPE OF BRIDGE :- HIGH LEVEL.",
        "SPAN ARRANGEMENT :- 1 x 6.0 m (TOTAL LENGTH OF BRIDGE 6.4 m).",
        "OVERALL WIDTH :- 12.0 m.   CARRIAGEWAY WIDTH :- 10.9 m.",
        "FORMATION LEVEL :- 158.820 m.   SOFFIT LEVEL :- 158.145 m.",
        "H.F.L. :- 157.395 m.   L.W.L. :- NOT AVAILABLE.",
        "FOUNDATION LEVEL :- VARIABLE, TYPE :- OPEN FOUNDATION.",
        "SUB-STRUCTURE :- ABUTMENT PCC M20, ABUTMENT CAP & DIRT WALL RCC M25, "
        "RETURN WALL PCC M20.",
        "SUPER-STRUCTURE :- RCC SOLID SLAB M25, WEARING COAT 75 mm RCC M30.",
        "APPROACH SLAB RCC M30, RCC RAILING M30.",
        "DESIGN LOADING :- CLASS 70-R / CLASS A.",
        "SOIL BEARING CAPACITY :- ABUTMENT 30 T/sq.m.   SEISMIC ZONE :- III.",
        "ALL DIMENSIONS IN mm, LEVELS IN METRES. DRAWING NOT TO SCALE.",
        "IF FOUNDATION DEPTH INCREASES UP TO 1.0 m THE SAME DESIGN MAY BE FOLLOWED; "
        "IF MORE THAN 1.0 m REFER THE DESIGNER.",
    )

    @property
    def deck_thickness_m(self) -> float:
        return round(self.frl - self.soffit, 3)

    @property
    def span_chain_mm(self) -> float:
        return sum(self.abut_steps_mm)


# ---------------------------------------------------------------------------
# The two canonical sets
# ---------------------------------------------------------------------------

PMGSY_SLAB = SlabBridgeSpec(
    ident=SheetIdentity(
        set_name="PMGSY 7 x 9.0 m RCC SOLID SLAB MINOR BRIDGE",
        project="GENERAL ARRANGEMENT DRAWING OF MINOR BRIDGE",
        road="ODR 58 TO MALSUR TO RAJURA ANSING ROAD - BRIDGE CH 2300",
        chainage="CH 2300 (2+300)",
        client="EXECUTIVE ENGINEER, PMGSY, MRRDA DIVISION WASHIM",
        consultant="PMGSY, MRRDA DIVISION WASHIM",
        drawing_prefix="PMGSY / GAD",
        total_sheets=3,
    )
)

AMARWADA_SINGLE = SingleSpanSpec(
    ident=SheetIdentity(
        set_name="1 x 6.0 m HIGH LEVEL BRIDGE - AMARWADA RAMGARH ROAD",
        project="AMARWADA - RAMGARH ROAD",
        road="AMARWADA - RAMGARH ROAD, BRIDGE AT CH. 3+340",
        chainage="CH. 3+340",
        client="EXECUTIVE ENGINEER, M.P. P.W.D. DIVISION CHHINDWARA",
        consultant="SAWYTECH ENGINEERING SERVICES",
        drawing_prefix="MPPWDC / AR",
        total_sheets=1,
        date="04-01-2020",
        drawn="A.A.R",
    )
)

#: Registry used by the CLI / API to resolve a set name.
SPECS: dict[str, object] = {
    "pmgsy_slab": PMGSY_SLAB,
    "amarwada_single": AMARWADA_SINGLE,
}

__all__ = [
    "AMARWADA_SINGLE",
    "PMGSY_SLAB",
    "SPECS",
    "SheetIdentity",
    "SingleSpanSpec",
    "SlabBridgeSpec",
]
