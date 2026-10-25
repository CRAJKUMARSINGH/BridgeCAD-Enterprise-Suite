#!/usr/bin/env python3
"""Wing-09 — per-sheet review report.

Emits an HTML matrix and a JSON twin: structural contract results, geometry
metrics, wing wall values with provenance, sign-off state, and the blockers
between here and construction-ready.

The report is honest about the difference between CONSISTENT (tests pass) and
CORRECT (an engineer signed it off). Those are different columns.

Usage:
    python scripts/wing_report.py --html site-wing/report.html --json wing-report.json
    python scripts/wing_report.py --check          # exit 1 if any non-scaffold sheet fails
    python scripts/wing_report.py --compare prev.json
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tests"))

from draw import contract, dxf_assert, signoff

SHEETS = (
    "sheet1_plan",
    "sheet2_long_section",
    "sheet3_cross_section",
    "sheet4_foundation",
    "sheet5_pier_abutment_details",
    "sheet6_bearings_joints",
    "sheet7_bill_of_quantities",
)
SCAFFOLD = {"sheet2_long_section", "sheet4_foundation"}
SIGNOFF_DIR = REPO / "tests" / "draw" / "signoff"


@dataclass
class Cell:
    slug: str
    sheet: str
    status: str = "pass"  # pass | fail | scaffold
    checks: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    fingerprint: str = ""
    deterministic: bool = True
    signed_off: bool = False
    signoff: dict | None = None
    error: str = ""


def _git_sha() -> str:
    try:
        return (
            subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True
            ).stdout.strip()
            or "unknown"
        )
    except Exception:
        return "unknown"


def _load_signoffs() -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    if not SIGNOFF_DIR.exists():
        return out
    for p in SIGNOFF_DIR.glob("*.json"):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
            out[(rec["slug"], rec["sheet"])] = rec
        except Exception:
            continue
    return out


def collect_all() -> list[Cell]:
    signoffs = _load_signoffs()
    registry = contract.layer_registry()
    cells: list[Cell] = []

    for slug in contract.golden_slugs():
        try:
            project = contract.make_project(slug)
        except Exception as exc:
            for sheet in SHEETS:
                cells.append(
                    Cell(
                        slug,
                        sheet,
                        status="fail",
                        error=f"fixture load: {type(exc).__name__}: {exc}",
                    )
                )
            continue

        for sheet in SHEETS:
            cell = Cell(slug, sheet)
            scaffold = sheet in SCAFFOLD
            try:
                doc = contract.build_sheet(project, sheet)
                cell.checks = [
                    asdict(c) for c in dxf_assert.collect(doc, sheet, registry, scaffold=scaffold)
                ]
                cell.metrics = dxf_assert.metrics(doc)
                fp1 = dxf_assert.fingerprint(doc)
                fp2 = dxf_assert.fingerprint(contract.build_sheet(project, sheet))
                cell.fingerprint = fp1
                cell.deterministic = fp1 == fp2
                cell.status = (
                    "scaffold"
                    if scaffold
                    else ("fail" if any(c["status"] == "fail" for c in cell.checks) else "pass")
                )
            except Exception as exc:
                cell.status = "fail"
                cell.error = f"{type(exc).__name__}: {exc}"

            rec = signoffs.get((slug, sheet))
            cell.signed_off = bool(rec)
            cell.signoff = rec
            cells.append(cell)
    return cells


def wing_table(slug: str) -> list[dict]:
    """Geometry values an engineer reviews, each with provenance."""
    project = contract.make_project(slug)
    abtl, source = contract.resolve_abtl(project)
    rows = [
        {
            "metric": "abtl",
            "value": f"{abtl:.3f} m",
            "provenance": f"ladder: {source}",
            "hand": f"{abtl:.6f}",
        }
    ]
    for w in contract.wing_wall_geometry(project):
        if w.side != "left":
            continue
        rows += [
            {
                "metric": "face_run",
                "value": f"{w.face_run_m:.3f} m",
                "provenance": "(abtl - W) / 2",
                "hand": f"{w.face_run_m:.6f}",
            },
            {
                "metric": "splay",
                "value": f"{w.splay_deg:.1f} deg",
                "provenance": "drawing_control",
                "hand": "-",
            },
            {
                "metric": "wing length",
                "value": f"{w.length_m:.3f} m",
                "provenance": "face_run / cos(splay)",
                "hand": f"{w.length_m:.6f}",
            },
            {
                "metric": "wing return",
                "value": f"{w.return_m:.3f} m",
                "provenance": "length * sin(splay)",
                "hand": f"{w.return_m:.6f}",
            },
            {
                "metric": "top level",
                "value": f"{w.top_level_m:.3f} m",
                "provenance": "deck - kerb",
                "hand": "-",
            },
            {
                "metric": "base level",
                "value": f"{w.base_level_m:.3f} m",
                "provenance": "min(scour, footing)",
                "hand": "-",
            },
        ]
    return rows


def blockers(cells: list[Cell]) -> list[str]:
    out: list[str] = []
    failed = [c for c in cells if c.status == "fail"]
    if failed:
        out.append(f"{len(failed)} sheet-cell(s) fail the structural contract")
    if SCAFFOLD:
        out.append(f"sheets {sorted(SCAFFOLD)} are scaffolds - no dimension entities")
    unsigned = [c for c in cells if not c.signed_off]
    if unsigned:
        out.append(f"{len(unsigned)} of {len(cells)} sheet-cells have no engineer sign-off")
    nondet = [c for c in cells if not c.deterministic]
    if nondet:
        out.append(f"{len(nondet)} sheet-cell(s) are non-deterministic - baselines are unreliable")
    out.append("BOQ lines are estimated, not calculated (Phase 3)")
    return out


# scripts/wing_report.py — add
def review_state(project) -> list[dict]:
    out = []
    for so in signoff.load_all():
        out.append(
            {
                "sheet": so.sheet,
                "reviewed_by": so.reviewed_by,
                "reviewed_on": so.reviewed_on,
                "stale": signoff.is_stale(project, so),
                "outcome": so.outcome,
            }
        )
    return out


# ── HTML ─────────────────────────────────────────────────────────────────────
def render_html(cells: list[Cell], generated: str, sha: str) -> str:
    slugs = sorted({c.slug for c in cells})
    by_key = {(c.slug, c.sheet): c for c in cells}
    glyph = {
        "pass": ("&#9679;", "#22c55e"),
        "scaffold": ("&#9680;", "#f59e0b"),
        "fail": ("&#9675;", "#ef4444"),
    }

    counts = {k: sum(1 for c in cells if c.status == k) for k in ("pass", "scaffold", "fail")}
    signed = sum(1 for c in cells if c.signed_off)
    det = sum(1 for c in cells if c.deterministic)

    def chip(label: str, value: str, colour: str) -> str:
        return (
            f'<span style="font-size:11px;padding:3px 9px;border-radius:999px;'
            f'border:1px solid {colour}55;background:{colour}18;color:{colour}">{label} {value}</span>'
        )

    rows = []
    for slug in slugs:
        tds = []
        for sheet in SHEETS:
            c = by_key.get((slug, sheet))
            if c is None:
                tds.append('<td class="cell">&#183;</td>')
                continue
            g, col = glyph[c.status]
            mark = " &#9670;" if c.signed_off else ""
            tds.append(
                f'<td class="cell" style="color:{col};border-color:{col}44;background:{col}14">'
                f'{g}<span class="sign">{mark}</span></td>'
            )
        rows.append(f'<tr><th class="rowhead">{html.escape(slug)}</th>{"".join(tds)}</tr>')

    heads = "".join(
        f'<th class="colhead">{s.replace("sheet", "s").split("_")[0]}</th>' for s in SHEETS
    )

    # geometry
    geo_blocks = []
    for slug in slugs:
        try:
            rows_geo = wing_table(slug)
        except Exception as exc:
            geo_blocks.append(
                f"<h3>{html.escape(slug)}</h3><p class='err'>{html.escape(str(exc))}</p>"
            )
            continue
        body = "".join(
            f"<tr><td class='mono'>{html.escape(r['metric'])}</td>"
            f"<td class='ok'>{html.escape(r['value'])}</td>"
            f"<td class='dim'>{html.escape(r['provenance'])}</td>"
            f"<td class='mono right dim'>{html.escape(r['hand'])}</td></tr>"
            for r in rows_geo
        )
        geo_blocks.append(
            f"<h3>{html.escape(slug)}</h3><table><thead><tr>"
            f"<th>metric</th><th>value</th><th>provenance</th><th class='right'>hand-check</th>"
            f"</tr></thead><tbody>{body}</tbody></table>"
        )

    # per-sheet detail
    details = []
    for c in sorted(cells, key=lambda x: (x.slug, x.sheet)):
        if not c.checks and not c.error:
            continue
        bad = [ch for ch in c.checks if ch["status"] == "fail"]
        cls = "fail" if bad else ("scaffold" if c.status == "scaffold" else "pass")
        rows_chk = (
            "".join(
                f"<tr class='{ch['status']}'><td class='mono'>{html.escape(ch['name'])}</td>"
                f"<td>{ch['status']}</td><td class='dim'>{html.escape(ch['detail'])}</td></tr>"
                for ch in c.checks
            )
            or f"<tr class='fail'><td colspan='3'>{html.escape(c.error)}</td></tr>"
        )
        m = c.metrics
        details.append(
            f"<details class='{cls}'><summary><span class='mono'>{html.escape(c.slug)} / "
            f"{html.escape(c.sheet)}</span> <span class='dim'>"
            f"{m.get('entities', 0)} entities &#183; {m.get('dimensions', 0)} dims &#183; "
            f"fp {html.escape(c.fingerprint or '-')}"
            f"{' &#183; SIGNED OFF' if c.signed_off else ''}</span></summary>"
            f"<table class='chk'><tbody>{rows_chk}</tbody></table></details>"
        )

    ledger = [
        f"<div class='ledger'><span class='mono'>{html.escape(c.slug)} / {html.escape(c.sheet)}</span>"
        f"<span class='ok'>{html.escape(c.signoff['decision'])}</span>"
        f"<span class='dim right'>reviewer {html.escape(str(c.signoff['reviewed_by']))} &#183; "
        f"evidence {len(c.signoff.get('evidence', []))}</span></div>"
        for c in cells
        if c.signed_off
    ] or ["<p class='dim'>No sheet carries a sign-off record yet.</p>"]

    bl = "".join(f"<li>{html.escape(b)}</li>" for b in blockers(cells))

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wing geometry report</title>
<style>
  :root {{ --fg:#111827; --dim:#6b7280; --line:#e5e7eb; --bg:#fff; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --fg:#e5e7eb; --dim:#9ca3af; --line:#374151; --bg:#0b0f19; }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:28px; background:var(--bg); color:var(--fg);
         font:14px/1.55 Inter,system-ui,-apple-system,sans-serif; max-width:1180px; }}
  h1 {{ font-size:20px; font-weight:500; margin:0 0 4px; }}
  h2 {{ font-size:14px; font-weight:500; margin:26px 0 10px; }}
  h3 {{ font-size:12.5px; font-weight:500; margin:16px 0 6px; color:var(--dim); }}
  .meta, .mono, .dim {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:11.5px; }}
  .dim {{ color:var(--dim); }}
  .ok {{ color:#16a34a; }} .err {{ color:#dc2626; }}
  .right {{ text-align:right; }}
  .chips {{ display:flex; gap:7px; flex-wrap:wrap; margin:14px 0 18px; }}
  table {{ width:100%; border-collapse:collapse; font-size:11.5px; }}
  th, td {{ padding:4px 6px; text-align:left; border-bottom:1px solid var(--line); font-weight:400; }}
  th {{ color:var(--dim); }}
  .matrix td.cell {{ text-align:center; font-size:13px; border:1px solid; border-radius:5px; padding:3px 0; }}
  .matrix .rowhead, .matrix .colhead {{ border:0; color:var(--dim); }}
  .matrix .rowhead {{ font-family:ui-monospace,Menlo,monospace; font-size:11px; }}
  .sign {{ font-size:8px; color:#3b82f6; vertical-align:top; }}
  details {{ border:1px solid var(--line); border-radius:7px; margin-bottom:5px; padding:6px 9px; }}
  details summary {{ cursor:pointer; font-size:11.5px; }}
  details.pass summary span:first-child::before {{ content:"PASS  "; color:#16a34a; }}
  details.fail summary span:first-child::before {{ content:"FAIL  "; color:#dc2626; }}
  details.scaffold summary span:first-child::before {{ content:"SCAFF "; color:#d97706; }}
  table.chk {{ margin-top:6px; }}
  tr.fail td:nth-child(2) {{ color:#dc2626; }}
  tr.pass td:nth-child(2) {{ color:#16a34a; }}
  .ledger {{ display:flex; gap:10px; align-items:baseline; padding:6px 0; border-bottom:1px solid var(--line); font-size:11.5px; }}
  .ledger .right {{ flex:1; }}
  ul {{ margin:6px 0 0; padding-left:18px; }} li {{ font-size:12.5px; margin-bottom:3px; }}
  footer {{ margin-top:26px; padding-top:12px; border-top:1px solid var(--line); color:var(--dim); font-size:11px; }}
</style></head><body>
<h1>Wing geometry report</h1>
<div class="meta dim">generated {html.escape(generated)} &#183; commit {html.escape(sha)} &#183;
  {len(slugs)} golden cases &#183; {len(SHEETS)} sheets &#183; {len(cells)} sheet-cells</div>

<div class="chips">
  {chip("structural pass", str(counts["pass"]), "#22c55e")}
  {chip("scaffold", str(counts["scaffold"]), "#f59e0b")}
  {chip("fail", str(counts["fail"]), "#ef4444")}
  {chip("signed off", str(signed), "#3b82f6")}
  {chip("deterministic", str(det), "#22c55e")}
</div>

<h2>Sheet matrix</h2>
<table class="matrix"><thead><tr><th></th>{heads}</tr></thead><tbody>{"".join(rows)}</tbody></table>
<p class="dim">&#9679; pass &#160; &#9680; scaffold &#160; &#9675; fail &#160; &#9670; signed &#160;&#8212;
   a cell is the worst of its checks</p>

<h2>Wing wall geometry</h2>
{"".join(geo_blocks)}

<h2>Sign-off ledger</h2>
{"".join(ledger)}

<h2>Per-sheet detail</h2>
{"".join(details)}

<h2>Blockers to construction-ready</h2>
<ul>{bl}</ul>

<footer>reproduce: <span class="mono">make wing-report</span> &#183;
  a passing sheet is CONSISTENT, not CONFIRMED &#8212; only a sign-off record makes it confirmed</footer>
</body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", default="site-wing/wing-report.html")
    ap.add_argument("--json", default="wing-report.json")
    ap.add_argument("--check", action="store_true", help="exit 1 if any non-scaffold sheet fails")
    ap.add_argument("--compare", default=None, help="previous JSON, to show deltas")
    args = ap.parse_args()

    started = time.monotonic()
    cells = collect_all()
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    sha = _git_sha()

    payload = {
        "generated": generated,
        "commit": sha,
        "counts": {k: sum(1 for c in cells if c.status == k) for k in ("pass", "scaffold", "fail")},
        "signed_off": sum(1 for c in cells if c.signed_off),
        "deterministic": sum(1 for c in cells if c.deterministic),
        "blockers": blockers(cells),
        "cells": [asdict(c) for c in cells],
    }

    if args.compare:
        prev_path = Path(args.compare)
        if prev_path.exists():
            prev = json.loads(prev_path.read_text(encoding="utf-8"))
            before = {(c["slug"], c["sheet"]): c for c in prev.get("cells", [])}
            changed = [
                f"{c.slug}/{c.sheet}: {before[(c.slug, c.sheet)]['status']} -> {c.status}"
                for c in cells
                if (c.slug, c.sheet) in before and before[(c.slug, c.sheet)]["status"] != c.status
            ]
            payload["changes"] = changed

    html_path = REPO / args.html
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(render_html(cells, generated, sha), encoding="utf-8")

    json_path = REPO / args.json
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    ms = int((time.monotonic() - started) * 1000)
    c = payload["counts"]
    print(f"  report: {args.html}")
    print(f"  json:   {args.json}")
    print(
        f"  {c['pass']} pass, {c['scaffold']} scaffold, {c['fail']} fail, "
        f"{payload['signed_off']} signed off  ({ms} ms)"
    )
    for b in payload["blockers"]:
        print(f"    blocker: {b}")
    if payload.get("changes"):
        print(f"  {len(payload['changes'])} status change(s) since {args.compare}")

    if args.check and c["fail"]:
        print(f"  CHECK FAILED: {c['fail']} sheet-cell(s) failing")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
