"""Adapters between the Wing tests and the product API.

If bridgecad_draw exposes different names, adapt here — never in the tests.
Each function states its contract in the docstring.

WHY A FACADE
    The wing tests drive the model the way a drafting override does: they set
    ``geometry_input.nspan``, ``foundation_details.abtl``, ``levels.hfl_m``.
    The validated model forbids unknown fields (``extra="forbid"``) and keeps
    ``span_count`` and ``span_lengths_m`` consistent with each other, so a test
    cannot simply poke it. ``make_project`` therefore returns a ``DrawProject``
    facade that translates each override into the one attribute the core
    geometry actually reads. The translation lives here and nowhere else.
"""
from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GOLDEN = Path(__file__).parent / "golden"

SHEET_NAMES = (
    "sheet1_plan",
    "sheet2_long_section",
    "sheet3_cross_section",
    "sheet4_foundation",
    "sheet5_pier_abutment_details",
    "sheet6_bearings_joints",
    "sheet7_bill_of_quantities",
)

#: The fixture a "blank" project is grown from. A test that supplies every
#: parameter it cares about still needs a valid 14-sheet project underneath.
BLANK_FIXTURE = "tests/e2e/fixtures/simple_12m.json"

#: The ABTL ladder, in resolution order. Mirrors bridgecad_core.geometry.abutment.
LADDER = ("ABTL", "FUTL", "FOOTL", "FUTRL", "ALCL", "ALCW")


@dataclass(frozen=True)
class WingWall:
    side: str            # "left" | "right"
    length_m: float      # along the wall's own axis
    face_run_m: float    # projection along the abutment face
    return_m: float      # projection perpendicular to the face
    splay_deg: float
    top_level_m: float
    base_level_m: float
    toe_offset_m: float


# ── model accessors ──────────────────────────────────────────────────────────
def resolve_abtl(project) -> tuple[float, str]:
    """Resolve abutment total length.

    CONTRACT — ladder order is fixed and each rung is tried before the next:
        ABTL -> FUTL -> FOOTL -> FUTRL -> ALCL -> ALCW -> 13.0
    Returns (value_m, source) where source is the parameter name actually used,
    or "default" for the terminal fallback. source must never be empty.
    """
    from bridgecad_core.geometry.abutment import resolve_abtl as _impl
    return _impl(project)


def wing_wall_geometry(project) -> list[WingWall]:
    """Wing walls for both abutments.

    CONTRACT:
        face_run_m = (abtl_m - carriageway_width_m) / 2
        length_m   = face_run_m / cos(radians(splay_deg))
        return_m   = length_m * sin(radians(splay_deg))
    splay_deg is measured FROM THE ABUTMENT FACE. Must be in [0, 89].

    The core implementation keeps every length as ``Decimal`` so the drawing and
    the hand-check agree to the millimetre. The wing tests do float arithmetic
    (``w.length_m * math.sin(...)``, ``pytest.approx``), so the facade converts
    once, here — the product package keeps its precision for the reference
    corpus in test_reference_cases.
    """
    from bridgecad_core.geometry.abutment import wing_wall_geometry as _impl
    return [
        WingWall(
            side=w.side,
            length_m=float(w.length_m),
            face_run_m=float(w.face_run_m),
            return_m=float(w.return_m),
            splay_deg=float(w.splay_deg),
            top_level_m=float(w.top_level_m),
            base_level_m=float(w.base_level_m),
            toe_offset_m=float(w.toe_offset_m),
        )
        for w in _impl(project)
    ]


def span_boundaries(project) -> list[float]:
    """Chainages of every span boundary. CONTRACT: len == nspan + 1."""
    from bridgecad_core.geometry.long_section import span_boundaries as _impl
    return _impl(project)


def pier_positions(project) -> list[float]:
    """Chainages of INTERMEDIATE piers only. CONTRACT: len == max(nspan - 1, 0)."""
    from bridgecad_core.geometry.long_section import pier_positions as _impl
    return _impl(project)


def build_sheet(project, sheet: str):
    """Build one DXF sheet in memory. sheet is e.g. 'sheet5_pier_abutment_details'."""
    import importlib
    mod = importlib.import_module(f"bridgecad_draw.sheets.{sheet}")
    return mod.build(project)


def layer_registry() -> dict:
    from bridgecad_draw.layers import LAYERS
    return LAYERS


def serialise(doc) -> str:
    """A canonical, deterministic text dump of a drawing's model space.

    Used to prove that two builds of the same project produce the same drawing.
    Deliberately excludes the DXF header (which carries a timestamp) and entity
    handles (which record allocation order, not geometry).

    ezdxf's ``DXFEntity`` exposes no ``.tags`` in 1.4.x — the DXF tags are
    produced on demand by a ``TagCollector``, so ask for them that way.
    """
    from ezdxf.lldxf.tagwriter import TagCollector

    chunks: list[str] = []
    for entity in doc.modelspace():
        collector = TagCollector(dxfversion=doc.dxfversion)
        entity.export_dxf(collector)
        tags = [(t.code, t.value) for t in collector.tags if t.code not in (5, 330, 1001)]
        chunks.append(repr(tags))
    return "\n".join(chunks)


# ── golden cases ─────────────────────────────────────────────────────────────
def load_golden(slug: str) -> dict:
    return json.loads((GOLDEN / f"{slug}.json").read_text(encoding="utf-8"))


def golden_slugs() -> list[str]:
    return sorted(p.stem for p in GOLDEN.glob("*.json"))


# ── the facade ───────────────────────────────────────────────────────────────
def _float(value):
    if value is None:
        return None
    try:
        return float(Decimal(str(value)))
    except (InvalidOperation, ValueError):
        return None


def _dec(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


class _Levels:
    """The four levels a section sheet draws.

    Mutable on purpose: a review expires when one of them moves, and the test
    that proves it does ``project.levels.hfl_m += 0.25``.
    """

    def __init__(self, deck_level_m, hfl_m, lwl_m, founding_level_m):
        self.deck_level_m = deck_level_m
        self.hfl_m = hfl_m
        self.lwl_m = lwl_m
        self.founding_level_m = founding_level_m


class _Span:
    """One span, as the sheets and the golden cases want to read it."""

    def __init__(self, index: int, length_m: float):
        self.index = index
        self.length_m = length_m

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"_Span({self.index}, {self.length_m})"


class _GeometryView:
    """The span loop by name: nspan, span_m, and the piers that follow from them."""

    def __init__(self, facade: "DrawProject"):
        self._f = facade

    def _gi(self):
        return self._f._model.geometry_input

    @property
    def nspan(self) -> int:
        return int(self._gi().span_count)

    @nspan.setter
    def nspan(self, value):
        self._f.geometry_input.nspan = value

    @property
    def span_m(self):
        lengths = list(self._gi().span_lengths_m)
        return lengths[0] if lengths else None

    @span_m.setter
    def span_m(self, value):
        self._f.geometry_input.span_length_m = value

    @property
    def total_length_m(self) -> float:
        return float(self._gi().total_length_m)

    def span_lengths_m(self) -> list[float]:
        return [float(x) for x in self._gi().span_lengths_m]

    def span_boundaries(self) -> list[float]:
        return list(span_boundaries(self._f))

    def pier_positions(self) -> list[float]:
        return list(pier_positions(self._f))


class _GeometryInputProxy:
    """``geometry_input`` with the two aliases the tests speak.

    ``nspan`` and ``span_length_m`` are single-value spellings of the model's
    ``span_count`` and ``span_lengths_m``. Writing either one rewrites the pair
    together, because the model refuses a span count that disagrees with its
    span lengths — and a half-applied override would be worse than a refused one.
    """

    def __init__(self, facade: "DrawProject"):
        self._f = facade

    def _gi(self):
        return self._f._model.geometry_input

    def _replace(self, **changes) -> None:
        gi = self._gi()
        data = {name: getattr(gi, name) for name in type(gi).model_fields}
        data.update(changes)
        self._f._model.geometry_input = type(gi)(**data)

    def __getattr__(self, name):
        if name == "nspan":
            return int(self._gi().span_count)
        if name == "span_length_m":
            lengths = list(self._gi().span_lengths_m)
            return lengths[0] if lengths else None
        if name == "deck_level_m":
            return self._f.levels.deck_level_m
        return getattr(self._gi(), name)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        if name in ("nspan", "span_count"):
            count = int(value)
            lengths = list(self._gi().span_lengths_m)
            single = lengths[0] if lengths else Decimal("12.0")
            self._replace(span_count=count, span_lengths_m=[single] * count)
        elif name == "span_length_m":
            count = int(self._gi().span_count)
            self._replace(span_lengths_m=[_dec(value)] * count)
        elif name == "span_lengths_m":
            self._replace(span_lengths_m=[_dec(x) for x in value])
        elif name == "deck_level_m":
            self._f.levels.deck_level_m = _float(value)
        else:
            self._replace(**{name: value})


class _FoundationDetailsProxy:
    """``foundation_details`` with a place to write the ABTL ladder rungs.

    The validated model has no ABTL field and forbids extras, but the ladder is
    exactly how a source workbook names the parameter. The rungs therefore live
    on the drafting view; everything else is the model's own.
    """

    def __init__(self, model):
        object.__setattr__(self, "_model", model)
        object.__setattr__(self, "_rungs", {rung.lower(): None for rung in LADDER})

    def __getattr__(self, name):
        rungs = object.__getattribute__(self, "_rungs")
        if name in rungs:
            return rungs[name]
        return getattr(object.__getattribute__(self, "_model"), name)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        rungs = object.__getattribute__(self, "_rungs")
        if name in rungs:
            rungs[name] = value
        else:
            setattr(object.__getattribute__(self, "_model"), name, value)


class _MaterialsProxy:
    """``materials`` where a grade can be cleared to test the honest "unknown".

    ``concrete_grade`` is the drafting name for the model's
    ``concrete_superstructure``; a test that sets it to None is asking what the
    BOQ does when the input is missing, and the answer must be "not calculated".
    """

    def __init__(self, model):
        object.__setattr__(self, "_model", model)
        object.__setattr__(self, "_overrides", {})

    def __getattr__(self, name):
        overrides = object.__getattribute__(self, "_overrides")
        if name in overrides:
            return overrides[name]
        model = object.__getattribute__(self, "_model")
        if name == "concrete_grade":
            return getattr(model, "concrete_superstructure", None)
        return getattr(model, name)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        object.__getattribute__(self, "_overrides")[name] = value


class _HydraulicProxy:
    """``hydraulic_data`` read from the drawing's levels, not from a second copy.

    The sheets print HFL, LWL and the founding level straight off ``levels``.
    If this proxy kept its own copy, a moved level would print on one sheet and
    not another — the exact drift the level tests exist to catch.
    """

    _MAP = {"hfl_m": "hfl_m", "lwl_m": "lwl_m", "scour_level_m": "founding_level_m"}

    def __init__(self, facade: "DrawProject"):
        self._f = facade

    def __getattr__(self, name):
        target = self._MAP.get(name)
        if target is not None:
            return getattr(self._f.levels, target)
        return getattr(self._f._model.hydraulic_data, name)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        target = self._MAP.get(name)
        if target is not None:
            setattr(self._f.levels, target, _float(value))
        else:
            setattr(self._f._model.hydraulic_data, name, value)


class DrawProject:
    """A drafting view over a validated BridgeProject.

    Attribute access falls through to the model for everything the facade does
    not translate, so the sheets read ``project.project_master`` etc. unchanged.
    """

    def __init__(self, model):
        object.__setattr__(self, "_model", model)
        object.__setattr__(self, "_carriageway", None)

        pm = model.project_master
        hd = model.hydraulic_data
        deck = pm.road_level_rl_m
        if deck is None:
            deck = getattr(hd, "actual_soffit_level_m", None)

        self.levels = _Levels(
            deck_level_m=_float(deck),
            hfl_m=_float(hd.hfl_m),
            lwl_m=_float(hd.lwl_m),
            founding_level_m=_float(hd.scour_level_m),
        )
        self.splay_deg = None
        self.geometry = _GeometryView(self)
        self.geometry_input = _GeometryInputProxy(self)
        self.foundation_details = _FoundationDetailsProxy(model.foundation_details)
        self.materials = _MaterialsProxy(model.materials)
        self.hydraulic_data = _HydraulicProxy(self)

    # -- levels ------------------------------------------------------------
    @property
    def deck_level_m(self):
        return self.levels.deck_level_m

    @deck_level_m.setter
    def deck_level_m(self, value):
        self.levels.deck_level_m = _float(value)

    @property
    def hfl_m(self):
        return self.levels.hfl_m

    @hfl_m.setter
    def hfl_m(self, value):
        self.levels.hfl_m = _float(value)

    @property
    def lwl_m(self):
        return self.levels.lwl_m

    @lwl_m.setter
    def lwl_m(self, value):
        self.levels.lwl_m = _float(value)

    @property
    def founding_level_m(self):
        return self.levels.founding_level_m

    @founding_level_m.setter
    def founding_level_m(self, value):
        self.levels.founding_level_m = _float(value)

    # -- abutment / deck width --------------------------------------------
    @property
    def abtl_m(self):
        return self.foundation_details.abtl

    @abtl_m.setter
    def abtl_m(self, value):
        self.foundation_details.abtl = _dec(value)

    @property
    def carriageway_m(self):
        return self._carriageway

    @carriageway_m.setter
    def carriageway_m(self, value):
        object.__setattr__(self, "_carriageway", _dec(value))
        if value is not None:
            self.geometry_input.carriageway_width_m = value

    # -- spans -------------------------------------------------------------
    @property
    def spans(self) -> list[_Span]:
        lengths = self._model.geometry_input.span_lengths_m
        return [_Span(index=i, length_m=float(x)) for i, x in enumerate(lengths)]

    # -- ground ------------------------------------------------------------
    @property
    def ground_profile(self) -> list[tuple[float, float]]:
        """Natural ground as [(chainage_m, level_m), ...] — section input.

        The model keeps the profile in its long-section geometry rather than on
        the project; this view surfaces it in the shape the section sheets read.
        """
        from bridgecad_core.geometry.long_section import compute_long_section_geometry
        ls = compute_long_section_geometry(self._model)
        return [(float(ch), float(rl)) for ch, rl in ls.ground_profile_pts]

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return getattr(object.__getattribute__(self, "_model"), name)


# ── project construction ─────────────────────────────────────────────────────
def _build_from_fixture(data: dict):
    """The repo's canonical fixture-JSON → BridgeProject loader (tests/e2e)."""
    path = REPO / "tests" / "e2e" / "run_e2e.py"
    spec = importlib.util.spec_from_file_location("bridgecad_e2e_fixtures", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._build_from_fixture(data)


def _fixture_data(relative: str) -> dict:
    return json.loads((REPO / relative).read_text(encoding="utf-8"))


def _apply(project: DrawProject, key: str, value) -> None:
    """Route one override to the object that owns it, on the facade's terms."""
    if key in ("nspan", "span_m"):
        setattr(project.geometry, key, value)
    else:
        setattr(project, key, value)


def make_project(slug: str, **overrides) -> DrawProject:
    """Build the project a golden case describes, as a ``DrawProject`` facade.

    ``slug`` names tests/draw/golden/<slug>.json. The special slug ``"blank"``
    starts from the minimal fixture instead, for the sweeps that supply every
    parameter they care about.

    Overrides come from the golden case's own ``overrides`` block and then from
    the caller's keyword arguments, in that order.
    """
    if slug == "blank":
        model = _build_from_fixture(_fixture_data(BLANK_FIXTURE))
        golden = None
    else:
        golden = load_golden(slug)
        model = _build_from_fixture(_fixture_data(golden["fixture"]))

    project = DrawProject(model)
    for key, value in ((golden or {}).get("overrides") or {}).items():
        _apply(project, key, value)
    for key, value in overrides.items():
        _apply(project, key, value)
    return project
