"""
bridgecad_bill.rates_db — MORTH Schedule of Rates lookup database.

100 seed items covering the main bridge construction chapters.
Rates are indicative 2024-25 values (INR); State PWD override chain supported.

Usage:
    from bridgecad_bill.rates_db import RatesDB
    db = RatesDB()
    rate = db.get("1701.1")          # M25 concrete in foundation
    rate = db.get("1701.1", state="MH")  # Maharashtra state rate
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional


# ---------------------------------------------------------------------------
# Seed rate table: (item_code, description, unit, base_rate_INR, morth_ref)
# ---------------------------------------------------------------------------
_SEED_RATES: list[tuple[str, str, str, float, str]] = [
    # ── 300 EARTHWORK ───────────────────────────────────────────────────────
    ("301.1",  "Earthwork in excavation for foundations",          "CUM",   350.0,  "MORTH 301"),
    ("301.2",  "Earthwork in embankment with imported moorum",     "CUM",   620.0,  "MORTH 301"),
    ("301.3",  "Earthwork in embankment with granular material",   "CUM",   780.0,  "MORTH 301"),
    ("301.4",  "Dewatering during excavation (provisional)",       "LS",  45000.0,  "MORTH 301"),
    # ── 401 GRANULAR SUB-BASE ───────────────────────────────────────────────
    ("401.1",  "Granular sub-base (GSB) — well-graded material",  "CUM",  1250.0,  "MORTH 401"),
    ("401.2",  "Wet mix macadam (WMM) base course",               "CUM",  1850.0,  "MORTH 401"),
    # ── 500 BITUMINOUS WORKS ────────────────────────────────────────────────
    ("501.1",  "Tack coat with bitumen emulsion (RS-1)",           "SQM",    25.0,  "MORTH 503"),
    ("501.2",  "Dense bituminous macadam (DBM) base — 75 mm",     "SQM",   450.0,  "MORTH 505"),
    ("501.3",  "Bituminous concrete (BC) wearing coat — 40 mm",   "SQM",   380.0,  "MORTH 510"),
    ("501.4",  "Stone matrix asphalt (SMA) — 40 mm",              "SQM",   520.0,  "MORTH 510"),
    ("501.5",  "Semi-dense bituminous concrete (SDBC) — 25 mm",   "SQM",   320.0,  "MORTH 510"),
    # ── 600 RIVER TRAINING ──────────────────────────────────────────────────
    ("601.1",  "Stone pitching (random rubble) — 450 mm thick",   "SQM",  1100.0,  "MORTH 608"),
    ("601.2",  "Boulder apron / launching apron",                  "CUM",  2200.0,  "MORTH 608"),
    ("601.3",  "Gabion boxes (2×1×1 m galv wire mesh)",           "EACH", 4500.0,  "MORTH 608"),
    ("601.4",  "CC pitching M15 — 100 mm thick",                  "SQM",  1400.0,  "MORTH 608"),
    # ── 800 SAFETY WORKS ────────────────────────────────────────────────────
    ("801.1",  "Metal beam crash barrier (W-beam) HDG",            "RM",   4200.0,  "MORTH 810"),
    ("801.2",  "SS 304 pipe railing 3-rail",                       "RM",   8500.0,  "MORTH 800"),
    ("801.3",  "RCC parapet (precast) H=1.0 m",                   "RM",   6800.0,  "MORTH 800"),
    ("801.4",  "Thermoplastic road marking — 100 mm wide",         "RM",    120.0,  "MORTH 803"),
    # ── 1600 REINFORCEMENT ──────────────────────────────────────────────────
    ("1601.1", "Reinforcement steel Fe500D (supply & fix)",        "MT",  75000.0,  "MORTH 1601"),
    ("1601.2", "Prestressing strand 12.7mm (supply, fix, stress)","MT", 145000.0,  "MORTH 1601"),
    ("1601.3", "HDPE sheathing for prestress tendons",             "RM",    185.0,  "MORTH 1601"),
    ("1601.4", "High-strength bar coupler (rebar splicing)",       "EACH",  350.0,  "MORTH 1601"),
    # ── 1700 CONCRETE WORKS ─────────────────────────────────────────────────
    ("1701.1", "Concrete M20 — plain (PCC) levelling course",     "CUM",  5800.0,  "MORTH 1700"),
    ("1701.2", "Concrete M25 — foundation (pile cap / footing)",  "CUM",  7200.0,  "MORTH 1700"),
    ("1701.3", "Concrete M30 — substructure (pier & abutment)",   "CUM",  8400.0,  "MORTH 1700"),
    ("1701.4", "Concrete M35 — superstructure girder / deck",     "CUM",  9600.0,  "MORTH 1700"),
    ("1701.5", "Concrete M40 — superstructure (high strength)",   "CUM", 11000.0,  "MORTH 1700"),
    ("1701.6", "Concrete M45 — PSC girder",                       "CUM", 13500.0,  "MORTH 1700"),
    ("1701.7", "Concrete M50 — PSC box girder",                   "CUM", 16000.0,  "MORTH 1700"),
    ("1702.1", "Formwork — ordinary (plain slab / wall)",          "SQM",   950.0,  "MORTH 1700"),
    ("1702.2", "Formwork — curved soffit (T-beam / box girder)",  "SQM",  1850.0,  "MORTH 1700"),
    ("1702.3", "Formwork — elevated deck (staging > 5 m)",        "SQM",  2400.0,  "MORTH 1700"),
    ("1703.1", "Grouting of prestress ducts (cement grout)",      "RM",    280.0,  "MORTH 1700"),
    # ── 1800 PILING ─────────────────────────────────────────────────────────
    ("1801.1", "Bored cast-in-situ pile dia 600 mm",              "RM",  2800.0,   "MORTH 1800"),
    ("1801.2", "Bored cast-in-situ pile dia 1000 mm",             "RM",  5500.0,   "MORTH 1800"),
    ("1801.3", "Bored cast-in-situ pile dia 1200 mm",             "RM",  7800.0,   "MORTH 1800"),
    ("1801.4", "Bored cast-in-situ pile dia 1500 mm",             "RM", 11500.0,   "MORTH 1800"),
    ("1801.5", "Pile load test (initial / routine)",               "EACH",250000.0, "MORTH 1800"),
    ("1801.6", "Cut off pile head (M25 concrete)",                "EACH",  5500.0,  "MORTH 1800"),
    # ── 2400 STEEL WORKS ────────────────────────────────────────────────────
    ("2401.1", "Structural steel fabrication & erection (Fe410W)","MT",  95000.0,  "MORTH 2401"),
    ("2401.2", "HSFG bolts M20 grade 8.8",                        "EACH",   185.0,  "MORTH 2401"),
    ("2401.3", "Anti-corrosion paint system (3-coat epoxy)",       "SQM",  1250.0,  "MORTH 2401"),
    ("2401.4", "Hot-dip galvanising (fasteners & brackets)",       "KG",     85.0,  "MORTH 2401"),
    # ── 2500 RIVER TRAINING WORKS ───────────────────────────────────────────
    ("2501.1", "Guide bund (stone-pitched embankment)",            "CUM",  1800.0,  "MORTH 2500"),
    ("2501.2", "Groyne / spur dyke (pervious stone)",              "CUM",  2200.0,  "MORTH 2500"),
    ("2501.3", "Marginal bund flood protection",                   "CUM",   950.0,  "MORTH 2500"),
    # ── 2600 WATERPROOFING ──────────────────────────────────────────────────
    ("2601.1", "Bituminous waterproofing membrane — deck",         "SQM",   850.0,  "MORTH 2600"),
    ("2601.2", "Epoxy waterproofing coating — substructure",       "SQM",   650.0,  "MORTH 2600"),
    ("2601.3", "Drainage scupper (precast RCC) 150 mm dia",        "EACH",  2800.0,  "MORTH 2600"),
    ("2601.4", "Drainage downpipe (CI) 150 mm dia per metre",      "RM",    850.0,  "MORTH 2600"),
    # ── 2700 BEARINGS ────────────────────────────────────────────────────────
    ("2701.1", "Elastomeric bearing pad (400×400×65 mm IRHD60)",   "EACH", 12000.0, "MORTH 2701"),
    ("2701.2", "Elastomeric bearing pad (500×500×75 mm IRHD60)",   "EACH", 18000.0, "MORTH 2701"),
    ("2701.3", "POT-PTFE bearing (design load 1000-2000 kN)",      "EACH", 85000.0, "MORTH 2701"),
    ("2701.4", "POT-PTFE bearing (design load 2000-5000 kN)",      "EACH",150000.0, "MORTH 2701"),
    ("2701.5", "Spherical bearing (design load > 5000 kN)",        "EACH",320000.0, "MORTH 2701"),
    # ── 2800 EXPANSION JOINTS ────────────────────────────────────────────────
    ("2801.1", "Compression seal joint (±10 mm movement)",        "RM",   4500.0,  "MORTH 2801"),
    ("2801.2", "Strip seal joint (±40 mm movement)",              "RM",  12500.0,  "MORTH 2801"),
    ("2801.3", "Single modular joint (±80 mm movement)",          "RM",  28000.0,  "MORTH 2801"),
    ("2801.4", "Double modular joint (±160 mm movement)",         "RM",  52000.0,  "MORTH 2801"),
    # ── 2900 MISC BRIDGE ITEMS ───────────────────────────────────────────────
    ("2901.1", "Approach slab M30 — 3.5 m × full width",          "CUM",  8500.0,  "MORTH 2900"),
    ("2901.2", "Weep holes (PVC pipe 100 mm dia)",                 "EACH",   350.0,  "MORTH 2900"),
    ("2901.3", "Bored pile integrity test (PIT)",                  "EACH",  3500.0,  "MORTH 1800"),
    ("2901.4", "Backfill of abutment (select granular)",           "CUM",   850.0,  "MORTH 2900"),
    # ── 3000 ELECTRICAL / ILLUMINATION ──────────────────────────────────────
    ("3001.1", "Street lighting (LED 80W on 8m pole)",             "EACH", 38000.0, "MORTH 3000"),
    ("3001.2", "Electrical cabling (2×16 sqmm)",                   "RM",    280.0,  "MORTH 3000"),
    # ── TESTING & QA ────────────────────────────────────────────────────────
    ("QA.1",   "Concrete cube testing (per 5 CUM batch)",          "EACH",  1200.0,  "IS 456"),
    ("QA.2",   "Rebar pull-out / bend test (per 10 MT)",           "EACH",  2800.0,  "IS 1786"),
    ("QA.3",   "Load test on completed bridge",                    "LS",  350000.0,  "IRC 6"),
    ("QA.4",   "NDT — ultrasonic pulse velocity test (pile)",      "EACH",  4500.0,  "IS 13311"),
    # ── PROVISIONAL / CONTINGENCY ────────────────────────────────────────────
    ("PROV.1", "Provisional sum — utility shifting",               "LS",  500000.0, "MORTH"),
    ("PROV.2", "Provisional sum — temporary traffic management",   "LS",  250000.0, "IRC SP 55"),
    ("PROV.3", "Day works — unskilled labour (provisional)",       "DAY",    800.0,  "MORTH"),
    ("PROV.4", "Day works — plant hire excavator (provisional)",   "HR",   4500.0,  "MORTH"),
    # ── WELL FOUNDATION ─────────────────────────────────────────────────────
    ("WF.1",   "Well sinking (RCC steining) per metre depth",      "RM",  28000.0,  "MORTH 1800"),
    ("WF.2",   "Well cap concrete M25",                            "CUM",  7200.0,  "MORTH 1800"),
    ("WF.3",   "Sand/concrete plugging of well",                   "CUM",  4500.0,  "MORTH 1800"),
    # ── ADDITIONAL CONCRETE ITEMS ───────────────────────────────────────────
    ("1701.8", "Concrete M55 — special high-performance (HPC)",    "CUM", 22000.0,  "MORTH 1700"),
    ("1701.9", "Concrete M60 — cable-stayed / long-span tower",    "CUM", 28000.0,  "MORTH 1700"),
    ("1704.1", "Shotcrete M30 with steel fibre — slope protection","SQM",  2800.0,  "MORTH 1700"),
    # ── DECK ACCESSORIES ────────────────────────────────────────────────────
    ("2902.1", "Cast iron / MS scupper box (300×300 mm)",          "EACH",  3800.0,  "MORTH"),
    ("2902.2", "Elastomeric deck joint seal (sealant type)",       "RM",   1800.0,  "MORTH 2801"),
    ("2902.3", "Stainless steel 316 pipe railing (50mm OD 3-rail)","RM",  12500.0,  "MORTH"),
    ("2902.4", "Aluminium alloy railing — pedestrian",             "RM",   9800.0,  "MORTH"),
    # ── PAVEMENT APPROACH ────────────────────────────────────────────────────
    ("402.1",  "Sub-grade improvement (lime stabilisation 300mm)", "SQM",   380.0,  "MORTH 402"),
    ("402.2",  "Vibratory compaction of embankment layers",        "SQM",    85.0,  "MORTH 402"),
    ("402.3",  "Portland cement concrete pavement (PQC) 300mm",   "SQM",  1950.0,  "MORTH 600"),
    # ── MISCELLANEOUS ────────────────────────────────────────────────────────
    ("MISC.1", "Demolition of existing structure",                 "LS",  800000.0, "MORTH"),
    ("MISC.2", "Environmental mitigation lump sum",                "LS",  200000.0, "EIA"),
    ("MISC.3", "Survey & setting out (total station / DGPS)",      "LS",   85000.0, "IRC SP 55"),
]


class RatesDB:
    """In-memory rate lookup with state PWD override support."""

    def __init__(self) -> None:
        # base_rates: item_code → Decimal rate (INR/unit)
        self._base: dict[str, Decimal] = {
            code: Decimal(str(rate))
            for code, _, _, rate, _ in _SEED_RATES
        }
        # metadata: item_code → (description, unit, morth_ref)
        self._meta: dict[str, tuple[str, str, str]] = {
            code: (desc, unit, ref)
            for code, desc, unit, _, ref in _SEED_RATES
        }
        # state overrides: state_code → {item_code → Decimal}
        self._state_overrides: dict[str, dict[str, Decimal]] = {}

    def get(self, item_code: str,
            state: str | None = None) -> Optional[Decimal]:
        """Return rate for *item_code*, optionally using state override."""
        if state:
            override = self._state_overrides.get(state.upper(), {})
            if item_code in override:
                return override[item_code]
        return self._base.get(item_code)

    def meta(self, item_code: str) -> tuple[str, str, str] | None:
        """Return (description, unit, morth_ref) for an item code."""
        return self._meta.get(item_code)

    def add_state_override(self, state: str,
                            item_code: str, rate: Decimal) -> None:
        """Register a state-PWD rate override."""
        self._state_overrides.setdefault(state.upper(), {})[item_code] = rate

    def all_codes(self) -> list[str]:
        return sorted(self._base.keys())

    def __len__(self) -> int:
        return len(self._base)


# Module-level singleton
_DB = RatesDB()


def get_rates_db() -> RatesDB:
    return _DB


__all__ = ["RatesDB", "get_rates_db"]
