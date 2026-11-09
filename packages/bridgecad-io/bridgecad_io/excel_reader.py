"""
bridgecad_io.excel_reader — Parse a 14-sheet BridgeCAD Excel workbook into a
validated BridgeProject Pydantic model.

Sheet order (1-indexed):
  S01 PROJECT_MASTER      S02 BRIDGE_SELECTION    S03 GEOMETRY_INPUT
  S04 SUPERSTRUCTURE      S05 SUBSTRUCTURE        S06 FOUNDATION_DETAILS
  S07 APPROACHES          S08 HYDRAULIC_DATA       S09 MATERIALS
  S10 BEARINGS_JOINTS     S11 COMPONENTS_LIB       S12 DRAWING_CONTROL
  S13 CALCULATIONS        S14 VALIDATION

Each sheet uses the canonical 3-column layout:
  Col A: Field name (matches Pydantic field names, case-insensitive)
  Col B: Value
  Col C: Unit / Notes (ignored during parse)

Bearing and expansion-joint schedules (S10) use a tabular block starting
at the row after the ``bearing_schedule:`` / ``expansion_joint_schedule:``
sentinel rows, with column headers in the next row.

M2 Week 2 implementation.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from ._fields import cell_to_value, flat_kind
from ._fields import coerce as _coerce
from ._fields import lookup_enum as _lookup_enum
from .exceptions import ExcelParseError

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # real import is lazy, see _core()
    from bridgecad_core.models import BridgeProject

try:
    import openpyxl

    _OPENPYXL_AVAILABLE = True
except ImportError:
    _OPENPYXL_AVAILABLE = False
    logger.warning("openpyxl not installed — excel_reader will not function")


# Lazy import of bridgecad_core so bridgecad_io can be imported even when
# bridgecad_core is not yet installed (test environments, CI stub runs).
def _core() -> tuple[Any, Any]:
    from bridgecad_core import models as _m
    from bridgecad_core import types as _t

    return _m, _t


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def _cell_value(ws: Any, row: int, col: int) -> Any:
    """Return the value of a cell, stripping leading/trailing whitespace."""
    v = ws.cell(row=row, column=col).value
    if isinstance(v, str):
        v = v.strip()
    return v


def _sheet_to_dict(ws: Any) -> dict[str, Any]:
    """Read a 3-column (Field / Value / Notes) sheet into a plain dict."""
    result: dict[str, Any] = {}
    for row in ws.iter_rows(min_row=1, values_only=True):
        if not row or row[0] is None:
            continue
        key = str(row[0]).strip().lower().replace(" ", "_")
        value = row[1] if len(row) > 1 else None
        if key and value is not None and value != "":
            result[key] = value
    return result


def _model_sheet_parser(model_cls: Any, *, extra: Callable | None = None) -> Callable:
    """Build a parser that reads a flat ``Field | Value`` sheet into *model_cls*.

    Every flat field the model declares is read straight from the sheet, so the
    reader can never silently drop a column the writer emitted. Computed fields
    (which are not part of the input contract) are skipped. ``extra`` may add
    sheet-specific handling for the tabular blocks.
    """
    computed = set(getattr(model_cls, "model_computed_fields", ()) or ())

    def _parse(ws: Any, m: Any, t: Any) -> dict[str, Any]:
        d = _sheet_to_dict(ws)
        out: dict[str, Any] = {}
        for name, field in model_cls.model_fields.items():
            key = name.lower()
            if name in computed or key not in d:
                continue
            if flat_kind(field.annotation) is None:
                continue
            out[name] = cell_to_value(d[key], field.annotation)
        if extra is not None:
            out.update(extra(ws, d, m, t))
        return out

    return _parse


def _generic(model_name: str) -> Callable:
    """A parser that reads a flat sheet straight into ``models.<model_name>``."""

    def _parse(ws: Any, m: Any, t: Any) -> dict[str, Any]:
        return _model_sheet_parser(getattr(m, model_name))(ws, m, t)

    return _parse


# ---------------------------------------------------------------------------
# Per-sheet parsers
# ---------------------------------------------------------------------------


def _parse_project_master(ws: Any, m: Any, t: Any) -> dict:
    d = _sheet_to_dict(ws)
    return {
        "project_title": _coerce(d.get("project_title"), str),
        "project_code": _coerce(d.get("project_code"), str),
        "bridge_name": _coerce(d.get("bridge_name"), str),
        "chainage_km": _coerce(d.get("chainage_km"), Decimal),
        "package_no": _coerce(d.get("package_no"), str),
        "client": _lookup_enum(t.ClientType, d.get("client")),
        "consultant": _lookup_enum(t.ConsultantType, d.get("consultant")),
        "contractor": _lookup_enum(t.ContractorType, d.get("contractor")),
        "drawing_no": _coerce(d.get("drawing_no"), str),
        "drawing_title": _coerce(d.get("drawing_title"), str),
        "revision": _lookup_enum(t.RevisionTag, d.get("revision")),
        "date_issued": _coerce(d.get("date_issued"), date),
        "designed_by": _coerce(d.get("designed_by"), str),
        "checked_by": _coerce(d.get("checked_by"), str),
        "approved_by": _coerce(d.get("approved_by"), str),
        "road_level_rl_m": _coerce(d.get("road_level_rl_m"), Decimal),
        "ground_level_rl_m": _coerce(d.get("ground_level_rl_m"), Decimal),
        "survey_date": _coerce(d.get("survey_date"), date),
        "state_code": _lookup_enum(t.IndianStateCode, d.get("state_code")),
        "district_code": _coerce(d.get("district_code"), str),
        "language": _lookup_enum(t.Language, d.get("language")),
        "latitude_deg": _coerce(d.get("latitude_deg"), Decimal) or None,
        "longitude_deg": _coerce(d.get("longitude_deg"), Decimal) or None,
        "total_estimated_cost_inr": _coerce(d.get("total_estimated_cost_inr"), Decimal),
        "tender_no": _coerce(d.get("tender_no"), str),
        "contract_no": _coerce(d.get("contract_no"), str),
        "project_phase": _lookup_enum(t.ProjectPhase, d.get("project_phase")),
        "currency": _lookup_enum(t.Currency, d.get("currency")),
    }


def _parse_bridge_selection(ws: Any, m: Any, t: Any) -> dict:
    d = _sheet_to_dict(ws)
    return {
        "bridge_category": _lookup_enum(t.BridgeCategory, d.get("bridge_category")),
        "bridge_type": _lookup_enum(t.SuperstructureType, d.get("bridge_type")),
        "span_configuration": _lookup_enum(t.SpanConfiguration, d.get("span_configuration")),
        "span_count": _coerce(d.get("span_count"), int),
        "carriageway_config": _lookup_enum(t.CarriagewayLaneConfig, d.get("carriageway_config")),
        "design_code": _lookup_enum(t.DesignCode, d.get("design_code")),
        "loading_class": _lookup_enum(t.LoadClass, d.get("loading_class")),
        "seismic_zone": _lookup_enum(t.SeismicZone, d.get("seismic_zone")),
        "wind_zone_ms": _lookup_enum(t.WindSpeedBasic_ms, d.get("wind_zone_ms")),
        "foundation_type": _lookup_enum(t.FoundationType, d.get("foundation_type")),
    }


def _parse_geometry_input(ws: Any, m: Any, t: Any) -> dict:
    d = _sheet_to_dict(ws)
    # span_lengths_m may be comma-separated or individual keys span_length_1 .. N
    spans_raw = d.get("span_lengths_m", "")
    span_lengths: list[Decimal] = []
    if spans_raw:
        for part in str(spans_raw).split(","):
            v = _coerce(part.strip(), Decimal)
            if v is not None:
                span_lengths.append(v)
    # Fallback: span_length_1, span_length_2, ...
    if not span_lengths:
        i = 1
        while True:
            key = f"span_length_{i}"
            if key not in d:
                break
            v = _coerce(d[key], Decimal)
            if v is not None:
                span_lengths.append(v)
            i += 1
    span_count = _coerce(d.get("span_count"), int) or len(span_lengths) or 1
    if not span_lengths:
        span_lengths = [Decimal("12.0")]
    return {
        "span_count": span_count,
        "span_lengths_m": span_lengths,
        "alignment_type": _lookup_enum(t.AlignmentType, d.get("alignment_type")),
        "gradient_pct": _coerce(d.get("gradient_pct"), Decimal),
        "carriageway_width_m": _coerce(d.get("carriageway_width_m"), Decimal),
        "footpath_left_m": _coerce(d.get("footpath_left_m"), Decimal),
        "footpath_right_m": _coerce(d.get("footpath_right_m"), Decimal),
        "crash_barrier_width_left_m": _coerce(d.get("crash_barrier_width_left_m"), Decimal),
        "crash_barrier_width_right_m": _coerce(d.get("crash_barrier_width_right_m"), Decimal),
        "kerb_width_left_m": _coerce(d.get("kerb_width_left_m"), Decimal),
        "kerb_width_right_m": _coerce(d.get("kerb_width_right_m"), Decimal),
        "median_width_m": _coerce(d.get("median_width_m"), Decimal),
        "skew_angle_deg": _coerce(d.get("skew_angle_deg"), Decimal),
        "skew_direction": _lookup_enum(t.SkewDirection, d.get("skew_direction")),
        "curved_bridge_flag": _coerce(d.get("curved_bridge_flag"), bool),
        "camber_mm": _coerce(d.get("camber_mm"), int),
        "camber_method": _lookup_enum(t.CamberMethod, d.get("camber_method")),
        "pavement_thickness_total_mm": _coerce(d.get("pavement_thickness_total_mm"), int),
        "crust_layer_count": _coerce(d.get("crust_layer_count"), int),
        "chainage_unit": _lookup_enum(t.ChainageUnit, d.get("chainage_unit")),
        "chainage_start_km": _coerce(d.get("chainage_start_km"), Decimal),
        "chainage_end_km": _coerce(d.get("chainage_end_km"), Decimal),
        "bearing_pad_spacing_m": _coerce(d.get("bearing_pad_spacing_m"), Decimal),
        "kerb_type": _lookup_enum(t.KerbType, d.get("kerb_type")),
        "footpath_type": _lookup_enum(t.FootpathType, d.get("footpath_type")),
        "median_type": _lookup_enum(t.MedianType, d.get("median_type")),
        "crash_barrier_type": _lookup_enum(t.CrashBarrierType, d.get("crash_barrier_type")),
    }


def _parse_bearings_joints(ws: Any, m: Any, t: Any) -> dict:
    """Parse S10 — bearing_schedule and expansion_joint_schedule tabular blocks."""
    bearing_rows: list[dict] = []
    expansion_rows: list[dict] = []

    rows = list(ws.iter_rows(values_only=True))
    mode: str | None = None
    headers: list[str] = []

    for row in rows:
        if not row:
            continue
        # A fully-empty row terminates the active tabular block. It must be
        # checked BEFORE the row[0]-is-None skip, otherwise trailing
        # field|value rows are silently swallowed as schedule records.
        if all(c is None or str(c).strip() == "" for c in row):
            mode = None
            headers = []
            continue
        if row[0] is None:
            continue
        key0 = str(row[0]).strip().lower()
        if key0 in ("bearing_schedule:", "bearing_schedule"):
            mode = "bearing"
            headers = []
            continue
        if key0 in ("expansion_joint_schedule:", "expansion_joint_schedule"):
            mode = "expansion"
            headers = []
            continue
        if mode and not headers:
            # Next non-empty row after sentinel = header row
            headers = [str(c).strip().lower().replace(" ", "_") if c else "" for c in row]
            continue
        if mode and headers:
            if all(c is None or str(c).strip() == "" for c in row):
                mode = None
                headers = []
                continue
            rec = {}
            for i, h in enumerate(headers):
                if h:
                    rec[h] = row[i] if i < len(row) else None
            if any(v is not None and str(v).strip() != "" for v in rec.values()):
                if mode == "bearing":
                    bearing_rows.append(rec)
                else:
                    expansion_rows.append(rec)

    def _mk_bearing(r: dict) -> dict:
        out = {
            "location": _coerce(r.get("location"), str),
            "bearing_type": _lookup_enum(t.BearingType, r.get("bearing_type")),
            "size_x_mm": _coerce(r.get("size_x_mm"), int),
            "size_y_mm": _coerce(r.get("size_y_mm"), int),
            "design_load_kn": _coerce(r.get("design_load_kn"), Decimal),
            "fixed_or_guide_or_free": _coerce(r.get("fixed_or_guide_or_free"), str),
            "elastomeric_layers_count": _coerce(r.get("elastomeric_layers_count"), int),
            "steel_back_bool": _coerce(r.get("steel_back_bool"), bool),
            "pot_pressure_mpa": _coerce(r.get("pot_pressure_mpa"), Decimal),
            "ptfe_sliding_surface_flag": _coerce(r.get("ptfe_sliding_surface_flag"), bool),
            "quantity": _coerce(r.get("quantity"), int) or 1,
        }
        # A blank cell yields None; drop it so the model default (False for the
        # bool flags) applies instead of a None that fails Pydantic validation.
        return {k: v for k, v in out.items() if v is not None}

    def _mk_expansion(r: dict) -> dict:
        return {
            "location": _coerce(r.get("location"), str),
            "joint_type": _lookup_enum(t.ExpansionJointType, r.get("joint_type")),
            "width_mm": _coerce(r.get("width_mm"), int),
            "movement_range_mm": _coerce(r.get("movement_range_mm"), int),
            "gap_mm": _coerce(r.get("gap_mm"), int),
            "transverse_length_m": _coerce(r.get("transverse_length_m"), Decimal),
            "quantity": _coerce(r.get("quantity"), int) or 1,
        }

    # Flat bearing/joint demand parameters (appended after the schedules as
    # field|value rows; _sheet_to_dict picks them up alongside the tables).
    flat = _sheet_to_dict(ws)

    return {
        "bearing_schedule": [_mk_bearing(r) for r in bearing_rows],
        "expansion_joint_schedule": [_mk_expansion(r) for r in expansion_rows],
        "bearing_type": _lookup_enum(t.BearingType, flat.get("bearing_type")),
        "restrained_longitudinal": _coerce(flat.get("restrained_longitudinal"), bool),
        "restrained_transverse": _coerce(flat.get("restrained_transverse"), bool),
        "bearing_seat_width_mm": _coerce(flat.get("bearing_seat_width_mm"), int),
        "bearing_clearance_mm": _coerce(flat.get("bearing_clearance_mm"), int),
        "design_movement_mm": _coerce(flat.get("design_movement_mm"), int),
    }


# ---------------------------------------------------------------------------
# Sheet name normaliser — tolerates minor spelling variations
# ---------------------------------------------------------------------------
_SHEET_ALIASES: dict[str, str] = {
    "project_master": "S01",
    "project master": "S01",
    "s01": "S01",
    "bridge_selection": "S02",
    "bridge selection": "S02",
    "s02": "S02",
    "geometry_input": "S03",
    "geometry input": "S03",
    "s03": "S03",
    "superstructure": "S04",
    "s04": "S04",
    "substructure": "S05",
    "s05": "S05",
    "foundation_details": "S06",
    "foundation details": "S06",
    "s06": "S06",
    "approaches": "S07",
    "s07": "S07",
    "hydraulic_data": "S08",
    "hydraulic data": "S08",
    "s08": "S08",
    "materials": "S09",
    "s09": "S09",
    "bearings_joints": "S10",
    "bearings joints": "S10",
    "s10": "S10",
    "components_lib": "S11",
    "components lib": "S11",
    "s11": "S11",
    "drawing_control": "S12",
    "drawing control": "S12",
    "s12": "S12",
    "calculations": "S13",
    "s13": "S13",
    "validation": "S14",
    "s14": "S14",
    "seismic_data": "S15",
    "seismic data": "S15",
    "s15": "S15",
}

_PARSERS = {
    # Bespoke parsers: the workbook's own spellings / multi-row layouts.
    "S01": _parse_project_master,
    "S02": _parse_bridge_selection,
    "S03": _parse_geometry_input,
    "S10": _parse_bearings_joints,
    # Flat sheets: read every declared field straight from the model, so the
    # reader can never silently drop a column the writer emitted.
    "S04": _generic("Superstructure"),
    "S05": _generic("Substructure"),
    "S06": _generic("FoundationDetails"),
    "S07": _generic("Approaches"),
    "S08": _generic("HydraulicData"),
    "S09": _generic("Materials"),
    "S11": _generic("ComponentsLib"),
    "S12": _generic("DrawingControl"),
    "S13": _generic("Calculations"),
    "S14": _generic("ValidationModel"),
    "S15": _generic("SeismicData"),
}

_MODEL_KEYS = {
    "S01": "project_master",
    "S02": "bridge_selection",
    "S03": "geometry_input",
    "S04": "superstructure",
    "S05": "substructure",
    "S06": "foundation_details",
    "S07": "approaches",
    "S08": "hydraulic_data",
    "S09": "materials",
    "S10": "bearings_joints",
    "S11": "components_lib",
    "S12": "drawing_control",
    "S13": "calculations",
    "S14": "validation",
    "S15": "seismic_data",
}


# ---------------------------------------------------------------------------
# Per-sheet import (guide: per-sheet Excel import)
# ---------------------------------------------------------------------------

#: 1-indexed workbook position -> canonical sheet ID (S01..S15).
_SHEET_NUMBERS: dict[int, str] = {i + 1: f"S{i + 1:02d}" for i in range(15)}


class SheetNotFoundError(LookupError):
    """Raised when the requested sheet number has no canonical section."""


def _section_model(model_key: str) -> Any:
    from bridgecad_core.models import BridgeProject

    annotation = BridgeProject.model_fields[model_key].annotation
    return annotation


def read_sheet(source: str | Path | bytes, sheet: int) -> Any:
    """Parse one workbook sheet into its validated section model.

    Resolves sheet number → canonical sheet → section model through the same
    ``_PARSERS`` / ``_MODEL_KEYS`` maps the full reader uses, so the two can
    never diverge.  ``source`` may be a path or raw workbook bytes.
    """
    if not _OPENPYXL_AVAILABLE:
        raise ImportError("openpyxl is required: pip install openpyxl")

    sid = _SHEET_NUMBERS.get(int(sheet))
    if sid is None:
        raise SheetNotFoundError(f"sheet {sheet} is outside the 1..15 section range")

    if isinstance(source, bytes):
        from io import BytesIO

        wb = openpyxl.load_workbook(BytesIO(source), data_only=True)
    else:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Workbook not found: {path}")
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
        except Exception as exc:
            raise ExcelParseError(
                f"Workbook could not be opened ({type(exc).__name__}: {exc})",
                file=path,
            ) from exc

    target_ws = None
    for ws in wb.worksheets:
        if _SHEET_ALIASES.get(ws.title.strip().lower()) == sid:
            target_ws = ws
            break
    if target_ws is None:
        raise SheetNotFoundError(f"workbook has no sheet mapping to {sid}")

    m, t = _core()
    data = _PARSERS[sid](target_ws, m, t)
    model_cls = _section_model(_MODEL_KEYS[sid])
    cleaned = {k: v for k, v in data.items() if v is not None}
    return model_cls.model_validate(cleaned)


# ---------------------------------------------------------------------------
# Legacy (pre-14-sheet) workbook support
# ---------------------------------------------------------------------------
# The suite contract is the 14-sheet workbook. Older workbooks — and the
# workbooks shipped under ``public/samples/`` — use the legacy single-sheet
# layout the original GAD app wrote: three columns ``Value, Variable,
# Description`` with ALL-CAPS parameter codes (NSPAN, SKEW, LBRIDGE, ...).
# Those are not silently accepted as a canonical workbook; they are recognised
# and translated by the small, explicit map below, so a legacy file still
# yields a BridgeProject instead of a hard failure.

_CANONICAL_SHEET_NAMES = (
    "PROJECT_MASTER",
    "BRIDGE_SELECTION",
    "GEOMETRY_INPUT",
    "SUPERSTRUCTURE",
    "SUBSTRUCTURE",
    "FOUNDATION_DETAILS",
    "APPROACHES",
    "HYDRAULIC_DATA",
    "MATERIALS",
    "BEARINGS_JOINTS",
    "COMPONENTS_LIB",
    "DRAWING_CONTROL",
    "CALCULATIONS",
    "VALIDATION",
    "SEISMIC_DATA",
)

#: Legacy parameter codes that must be present before a workbook is treated as
#: the legacy layout. A workbook of random `A1 / B2` pairs is not a bridge.
_LEGACY_MARKER_CODES = frozenset({"NSPAN", "LBRIDGE", "SPAN1", "SKEW", "RTL", "SOFL", "TOPRL"})

_LEGACY_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _no_sheets_error(path: Path) -> str:
    """The message a workbook that is neither canonical nor legacy receives."""
    return (
        f"No recognised BridgeCAD sheets found in '{path.name}'. "
        f"Expected a {len(_CANONICAL_SHEET_NAMES)}-sheet workbook named: {', '.join(_CANONICAL_SHEET_NAMES)}. "
        "See docs/excel-contract.md, or generate a template with "
        "`bridgecad-cli template new`. Older 1-4 sheet workbooks are only "
        "supported through legacy mode (Value / Variable / Description)."
    )


def _legacy_code_map(wb: Any) -> dict[str, Any]:
    """Read a legacy workbook into ``{CODE: value}`` from its code/value rows.

    Two column orders are accepted: the GAD app's ``Value, Variable`` order and
    the LISP-export ``Parameter, Value`` order. A row counts only when exactly
    one of the first two cells is an ALL-CAPS parameter code, so the
    ``Span_No, Length, ...`` and ``Value, Variable, Description`` header rows are
    skipped rather than mistaken for data.
    """
    out: dict[str, Any] = {}
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            if not row or len(row) < 2:
                continue
            first, second = row[0], row[1]
            if isinstance(second, str) and _LEGACY_CODE_RE.match(second.strip()):
                code, value = second.strip(), first
            elif isinstance(first, str) and _LEGACY_CODE_RE.match(first.strip()):
                code, value = first.strip(), second
            else:
                continue
            if value is not None and value != "":
                out[code] = value
    return out


def _legacy_kwargs(wb: Any, t: Any) -> dict[str, Any] | None:
    """Translate a legacy workbook into BridgeProject kwargs, or None.

    Only the codes the legacy GAD app actually writes are mapped, and only onto
    fields the core model owns. Everything else is left to the same IRC-derived
    defaults a blank 14-sheet workbook gets, so nothing is invented.
    """
    codes = _legacy_code_map(wb)
    if not _LEGACY_MARKER_CODES.intersection(codes):
        return None

    kwargs: dict[str, Any] = {}

    def _put(section: str, **fields: Any) -> None:
        target = kwargs.setdefault(section, {})
        for key, val in fields.items():
            if val is not None:
                target[key] = val

    span_count = _coerce(codes.get("NSPAN"), int)

    span_lengths: list[Decimal] = []
    index = 1
    while f"SPAN{index}" in codes:
        val = _coerce(codes[f"SPAN{index}"], Decimal)
        if val is not None:
            span_lengths.append(val)
        index += 1

    # Legacy files often carry only SPAN1 (the first span) next to a multi-digit
    # NSPAN. An explicit list that disagrees with the count is rejected by the
    # model, so drop it and divide the total length across the span count instead.
    if span_count and len(span_lengths) != span_count:
        span_lengths = []
    if not span_lengths and span_count:
        total = _coerce(codes.get("LBRIDGE"), Decimal)
        if total is not None:
            span_lengths = [(total / span_count).quantize(Decimal("0.001"))] * span_count

    road_level = codes.get("RTL")
    if road_level is None:
        road_level = codes.get("TOPRL")

    _put("bridge_selection", span_count=span_count)
    _put(
        "geometry_input",
        span_count=span_count or (len(span_lengths) or None),
        span_lengths_m=span_lengths or None,
        skew_angle_deg=_coerce(codes.get("SKEW"), Decimal),
    )
    _put(
        "project_master",
        road_level_rl_m=_coerce(road_level, Decimal),
        ground_level_rl_m=_coerce(codes.get("DATUM"), Decimal),
    )
    _put("hydraulic_data", actual_soffit_level_m=_coerce(codes.get("SOFL"), Decimal))
    # Legacy workbooks have no superstructure block. These three mirror the
    # template generator's own prefill so a girder base type validates; every
    # other value is left to the shared IRC-derived defaults below.
    _put(
        "superstructure",
        girder_depth_mm=1200,
        girder_spacing_m=Decimal("2.5"),
        girders_per_deck_count=4,
    )

    logger.info("Legacy workbook: mapped %d parameter code(s)", len(codes))
    return kwargs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def read_excel(path: str | Path) -> BridgeProject:
    """Parse a BridgeCAD Excel workbook and return a BridgeProject.

    The canonical input is a 14-sheet workbook (see ``docs/excel-contract.md``).
    A legacy single-sheet ``Value / Variable / Description`` workbook is also
    accepted and translated through a small, explicit code map.

    Parameters
    ----------
    path : str | Path
        Path to the .xlsx file.

    Returns
    -------
    BridgeProject
        Fully-validated Pydantic model instance.

    Raises
    ------
    ImportError
        If openpyxl is not installed.
    FileNotFoundError
        If the workbook does not exist.
    ExcelParseError
        If the file is not a readable workbook (truncated, renamed, corrupt).
    ValueError
        If the workbook is neither a 14-sheet contract workbook nor a
        recognisable legacy workbook.
    """
    if not _OPENPYXL_AVAILABLE:
        raise ImportError("openpyxl is required: pip install openpyxl")

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Workbook not found: {path}")

    m, t = _core()
    try:
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception as exc:
        # A truncated or renamed file reaches openpyxl as a bad ZIP, and a
        # corrupt one as a missing-part KeyError. Both must arrive as the
        # documented parse error, not as a zipfile/openpyxl traceback.
        raise ExcelParseError(
            f"Workbook could not be opened ({type(exc).__name__}: {exc})",
            file=path,
            suggestion="the file must be an .xlsx workbook written by generate_template()",
        ) from exc

    # Map each worksheet to its canonical sheet ID
    sheet_map: dict[str, Any] = {}
    for ws in wb.worksheets:
        key = _SHEET_ALIASES.get(ws.title.strip().lower())
        if key:
            sheet_map[key] = ws

    kwargs: dict[str, Any] = {}
    if sheet_map:
        # Parse each found sheet; fall back to empty dict for missing ones
        parsed: dict[str, dict] = {}
        for sid, parser in _PARSERS.items():
            ws = sheet_map.get(sid)
            if ws is not None:
                try:
                    parsed[sid] = parser(ws, m, t)
                except Exception as exc:
                    logger.warning("Error parsing sheet %s: %s", sid, exc)
                    parsed[sid] = {}
            else:
                logger.info("Sheet %s not found in workbook — using defaults", sid)
                parsed[sid] = {}

        # Build BridgeProject kwargs, stripping None values so Pydantic defaults apply
        for sid, model_key in _MODEL_KEYS.items():
            sheet_data = {k: v for k, v in parsed[sid].items() if v is not None}
            if sheet_data:
                kwargs[model_key] = sheet_data
    else:
        # Not a 14-sheet workbook — try the legacy layout before failing.
        legacy = _legacy_kwargs(wb, t)
        if legacy is None:
            raise ValueError(_no_sheets_error(path))
        logger.warning(
            "Workbook '%s' is not the 14-sheet contract — parsed in legacy mode", path.name
        )
        kwargs = legacy

    # ── Inject defaults for required fields missing from blank templates ───
    # These are Pydantic "required" fields with no default — blank workbooks
    # leave them empty, which causes ValidationError. Inject sensible fallbacks.
    pm_kwargs = kwargs.setdefault("project_master", {})
    if not pm_kwargs.get("project_title"):
        pm_kwargs["project_title"] = "BRIDGE PROJECT"
    if not pm_kwargs.get("project_code"):
        pm_kwargs["project_code"] = "PROJ-2026-001"
    if not pm_kwargs.get("bridge_name"):
        pm_kwargs["bridge_name"] = "BRIDGE"
    if pm_kwargs.get("client") is None:
        pm_kwargs["client"] = t.ClientType.STATE_PWD
    if pm_kwargs.get("revision") is None:
        pm_kwargs["revision"] = t.RevisionTag.R0
    if pm_kwargs.get("state_code") is None:
        pm_kwargs["state_code"] = t.IndianStateCode.MH
    if pm_kwargs.get("language") is None:
        pm_kwargs["language"] = t.Language.EN
    if pm_kwargs.get("project_phase") is None:
        pm_kwargs["project_phase"] = t.ProjectPhase.DPR
    if pm_kwargs.get("currency") is None:
        pm_kwargs["currency"] = t.Currency.INR
    # Lat/lon: blank template sends 0.0 which may fail ge constraint; keep as None
    if pm_kwargs.get("latitude_deg") is not None and float(pm_kwargs["latitude_deg"]) == 0.0:
        pm_kwargs["latitude_deg"] = None
    if pm_kwargs.get("longitude_deg") is not None and float(pm_kwargs["longitude_deg"]) == 0.0:
        pm_kwargs["longitude_deg"] = None

    bs_kwargs = kwargs.setdefault("bridge_selection", {})
    if bs_kwargs.get("bridge_category") is None:
        bs_kwargs["bridge_category"] = t.BridgeCategory.MINOR_BRIDGE
    if bs_kwargs.get("bridge_type") is None:
        bs_kwargs["bridge_type"] = t.SuperstructureType.RCC_TBEAM
    if bs_kwargs.get("span_configuration") is None:
        bs_kwargs["span_configuration"] = t.SpanConfiguration.SIMPLY_SUPPORTED
    if bs_kwargs.get("span_count") is None:
        bs_kwargs["span_count"] = 1
    if bs_kwargs.get("carriageway_config") is None:
        bs_kwargs["carriageway_config"] = t.CarriagewayLaneConfig.LANE_2
    if bs_kwargs.get("design_code") is None:
        bs_kwargs["design_code"] = t.DesignCode.IRC_112_2020
    if bs_kwargs.get("loading_class") is None:
        bs_kwargs["loading_class"] = t.LoadClass.CLASS_A
    if bs_kwargs.get("seismic_zone") is None:
        bs_kwargs["seismic_zone"] = t.SeismicZone.ZONE_III
    if bs_kwargs.get("wind_zone_ms") is None:
        bs_kwargs["wind_zone_ms"] = t.WindSpeedBasic_ms.VB_44_ms_ZONE_3
    if bs_kwargs.get("foundation_type") is None:
        bs_kwargs["foundation_type"] = t.FoundationType.PILE

    gi_kwargs = kwargs.setdefault("geometry_input", {})
    if not gi_kwargs.get("span_lengths_m"):
        n = bs_kwargs.get("span_count", 1) or 1
        gi_kwargs["span_lengths_m"] = [Decimal("12.0")] * n
    if gi_kwargs.get("span_count") is None:
        gi_kwargs["span_count"] = len(gi_kwargs["span_lengths_m"])
    if gi_kwargs.get("carriageway_width_m") is None:
        gi_kwargs["carriageway_width_m"] = Decimal("7.50")
    if gi_kwargs.get("skew_angle_deg") is None:
        gi_kwargs["skew_angle_deg"] = Decimal("0.0")
    if gi_kwargs.get("alignment_type") is None:
        gi_kwargs["alignment_type"] = t.AlignmentType.STRAIGHT
    if gi_kwargs.get("chainage_unit") is None:
        gi_kwargs["chainage_unit"] = t.ChainageUnit.METER

    ss_kwargs = kwargs.setdefault("superstructure", {})
    if ss_kwargs.get("type") is None:
        ss_kwargs["type"] = t.SuperstructureType.RCC_TBEAM
    if ss_kwargs.get("deck_material") is None:
        ss_kwargs["deck_material"] = t.ConcreteGrade.M30

    sub_kwargs = kwargs.setdefault("substructure", {})
    if sub_kwargs.get("pier_type") is None:
        sub_kwargs["pier_type"] = t.PierType.WALL
    if sub_kwargs.get("pier_material") is None:
        sub_kwargs["pier_material"] = t.ConcreteGrade.M25
    if sub_kwargs.get("abutment_type") is None:
        sub_kwargs["abutment_type"] = t.AbutmentType.CANTILEVER
    if sub_kwargs.get("abutment_material") is None:
        sub_kwargs["abutment_material"] = t.ConcreteGrade.M25

    fd_kwargs = kwargs.setdefault("foundation_details", {})
    if fd_kwargs.get("type") is None:
        fd_kwargs["type"] = t.FoundationType.PILE

    mt_kwargs = kwargs.setdefault("materials", {})
    if mt_kwargs.get("concrete_superstructure") is None:
        mt_kwargs["concrete_superstructure"] = t.ConcreteGrade.M30
    if mt_kwargs.get("concrete_substructure") is None:
        mt_kwargs["concrete_substructure"] = t.ConcreteGrade.M25
    if mt_kwargs.get("concrete_foundation") is None:
        mt_kwargs["concrete_foundation"] = t.ConcreteGrade.M25
    if mt_kwargs.get("reinforcement_steel_grade") is None:
        mt_kwargs["reinforcement_steel_grade"] = t.SteelGrade.Fe500D
    if mt_kwargs.get("prestressing_steel") is None:
        mt_kwargs["prestressing_steel"] = t.PrestressGrade.G1860
    if mt_kwargs.get("bearing_type") is None:
        mt_kwargs["bearing_type"] = t.BearingType.ELASTOMERIC_NEOPRENE
    if mt_kwargs.get("expansion_joint_type") is None:
        mt_kwargs["expansion_joint_type"] = t.ExpansionJointType.COMPRESSION_SEAL

    dc_kwargs = kwargs.setdefault("drawing_control", {})
    if not dc_kwargs.get("output_formats"):
        dc_kwargs["output_formats"] = [t.OutputFormat.DXF]
    if dc_kwargs.get("autocad_version") is None:
        dc_kwargs["autocad_version"] = t.AcadVersion.R2018
    if dc_kwargs.get("sheet_size") is None:
        dc_kwargs["sheet_size"] = t.SheetSize.A1
    if dc_kwargs.get("drawing_scale") is None:
        dc_kwargs["drawing_scale"] = t.DrawingScale.S100
    if dc_kwargs.get("layer_standard") is None:
        dc_kwargs["layer_standard"] = t.LayerStandard.IRC
    if dc_kwargs.get("title_block_style") is None:
        dc_kwargs["title_block_style"] = t.TitleBlockStyle.STANDARD

    # Ensure bearings_joints has minimum 1 bearing + 1 joint for validation
    bj_kwargs = kwargs.setdefault("bearings_joints", {})
    if not bj_kwargs.get("bearing_schedule"):
        bj_kwargs["bearing_schedule"] = [
            {
                "location": "A1-Default",
                "bearing_type": t.BearingType.ELASTOMERIC_NEOPRENE,
                "quantity": 4,
            }
        ]
    if not bj_kwargs.get("expansion_joint_schedule"):
        bj_kwargs["expansion_joint_schedule"] = [
            {
                "location": "A1-End",
                "joint_type": t.ExpansionJointType.COMPRESSION_SEAL,
                "width_mm": 40,
                "movement_range_mm": 20,
                "gap_mm": 12,
                "transverse_length_m": Decimal("8.5"),
                "quantity": 1,
            }
        ]

    # ── Strip zero-values for optional fields with ge > 0 constraints ────────
    # A blank template cell returns 0.0 which fails ge=3.5 / ge=6.0 etc.
    # Setting these to None lets Pydantic use its field default (None / default value).
    _ZERO_STRIP_FIELDS = {
        "project_master": [
            "latitude_deg",
            "longitude_deg",
            "road_level_rl_m",
            "ground_level_rl_m",
            "chainage_km",
            "total_estimated_cost_inr",
        ],
        "geometry_input": ["carriageway_width_m", "horizontal_curve_R_m", "bearing_pad_spacing_m"],
        "hydraulic_data": [],  # handled with explicit defaults above
        "foundation_details": ["pile_diameter_mm", "pile_length_m", "pile_cap_thickness_mm"],
    }
    for section, fields in _ZERO_STRIP_FIELDS.items():
        sec = kwargs.get(section, {})
        for fld in fields:
            val = sec.get(fld)
            if val is not None:
                try:
                    if float(val) == 0.0:
                        sec[fld] = None
                except (TypeError, ValueError):
                    pass
    hd_kwargs = kwargs.setdefault("hydraulic_data", {})
    for field, default in [
        ("hfl_m", Decimal("110.0")),
        ("lwl_m", Decimal("107.0")),
        ("scour_level_m", Decimal("105.0")),
        ("design_scour_depth_m", Decimal("1.5")),
        ("freeboard_m", Decimal("1.0")),
        ("actual_soffit_level_m", Decimal("112.0")),
        ("lacey_silt_factor", Decimal("0.85")),
        ("design_discharge_cumecs", Decimal("50.0")),
    ]:
        if hd_kwargs.get(field) is None:
            hd_kwargs[field] = default

    return cast("BridgeProject", m.BridgeProject(**kwargs))


__all__ = ["read_excel"]
