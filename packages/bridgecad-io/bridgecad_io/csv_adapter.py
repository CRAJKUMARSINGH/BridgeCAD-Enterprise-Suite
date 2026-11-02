"""CSV ↔ BridgeProject adapter.

``to_csv`` writes one ``<sub_model>.csv`` per top-level BridgeProject field
(``path,value`` rows, values JSON-encoded so types survive) plus two schedule
CSVs (``schedule_spans.csv``, ``schedule_bearings.csv``) for human review.
``from_csv`` reads the sub-model CSVs back; schedule CSVs are informational.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .exceptions import CsvParseError
from .json_adapter import project_from_dict, project_to_dict

_SCHEDULES = ("schedule_spans.csv", "schedule_bearings.csv")


def _flatten(obj: Any, prefix: str = "") -> list[tuple[str, Any]]:
    if isinstance(obj, dict) and obj:
        rows: list[tuple[str, Any]] = []
        for k, v in obj.items():
            rows.extend(_flatten(v, f"{prefix}.{k}" if prefix else str(k)))
        return rows
    return [(prefix, obj)]


def _unflatten(rows: list[tuple[str, Any]]) -> Any:
    root: dict[str, Any] = {}
    for path, value in rows:
        if path == "":
            return value
        cur = root
        parts = path.split(".")
        for part in parts[:-1]:
            cur = cur.setdefault(part, {})
        cur[parts[-1]] = value
    return root


def _write_rows(path: Path, header: list[str], rows: list[list[Any]]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return path


def to_csv(project: Any, out_dir: str | Path) -> list[Path]:
    """Write sub-model CSVs + 2 schedule CSVs; return the written paths."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    data = project_to_dict(project)
    written: list[Path] = []
    for name, value in data.items():
        rows = [[p, json.dumps(v, ensure_ascii=False)] for p, v in _flatten(value)]
        written.append(_write_rows(out / f"{name}.csv", ["path", "value"], rows))

    gi = data.get("geometry_input") or {}
    spans = gi.get("spans") or gi.get("span_lengths_m") or []
    span_rows = [[i + 1, json.dumps(s, ensure_ascii=False)] for i, s in enumerate(spans)]
    written.append(_write_rows(out / _SCHEDULES[0], ["span_no", "span"], span_rows))

    bj = data.get("bearings_joints") or {}
    bearings = bj.get("bearings") or []
    brg_rows = [[i + 1, json.dumps(b, ensure_ascii=False)] for i, b in enumerate(bearings)]
    written.append(_write_rows(out / _SCHEDULES[1], ["bearing_no", "bearing"], brg_rows))
    return written


def from_csv(in_dir: str | Path) -> Any:
    """Rebuild a BridgeProject from a directory written by :func:`to_csv`."""
    src = Path(in_dir)
    if not src.is_dir():
        raise CsvParseError(f"CSV directory not found: {src}")
    data: dict[str, Any] = {}
    for f in sorted(src.glob("*.csv")):
        if f.name in _SCHEDULES:
            continue
        try:
            with f.open(newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                rows = [(r["path"], json.loads(r["value"])) for r in reader]
        except (KeyError, json.JSONDecodeError) as exc:
            raise CsvParseError(f"{f.name}: malformed row ({exc})") from exc
        data[f.stem] = _unflatten(rows)
    if not data:
        raise CsvParseError(f"No sub-model CSV files in {src}")
    return project_from_dict(data)


__all__ = ["from_csv", "to_csv"]
