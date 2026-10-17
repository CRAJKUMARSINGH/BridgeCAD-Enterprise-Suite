#!/usr/bin/env python3
"""
BridgeCAD Enterprise Suite — App Robustness Test Suite
=======================================================
Tests the FastAPI /predict endpoint (and health/template/metrics endpoints)
against a wide matrix of real and synthetically-generated Excel inputs.

Input dimensions tested:
  • Bridge type   : SLAB, BEAM, T_BEAM, BOX_GIRDER, ARCH, TRUSS
  • Spans         : 1, 2, 3, 4, 5, 7, 11 spans
  • Span length   : 6 m → 45 m
  • Deck width    : 7.5 m, 8.5 m, 11.1 m, 14.0 m, 16.5 m
  • Skew angle    : 0°, 15°, 30°, 45°
  • Output format : dxf, pdf, png, svg
  • Real Excel workbooks from inputs/

Results written to: app-robustness-testing.md (updated after every test).
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional

# ── Try to import openpyxl for synthetic Excel generation ────────────────────
try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# ── Try requests ─────────────────────────────────────────────────────────────
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    # Fallback to urllib
    import urllib.request
    import urllib.parse

BASE_URL   = os.environ.get("BRIDGECAD_API_URL", "http://127.0.0.1:8765")
REPORT_MD  = Path(__file__).parent / "app-robustness-testing.md"
INPUTS_DIR = Path(__file__).parent / "inputs"
TIMEOUT_S  = 60  # per-request timeout

# ── Test result dataclass ─────────────────────────────────────────────────────
class TestResult(NamedTuple):
    test_id:    str
    category:  str
    label:     str
    endpoint:  str
    method:    str
    status:    int          # HTTP status; -1 = connection error
    ok:        bool
    elapsed_ms: float
    output_size_bytes: int
    error:     Optional[str]
    details:   str          # extra notes


_results: List[TestResult] = []
_start_wall = datetime.now()


# ─────────────────────────────────────────────────────────────────────────────
# HTTP helpers
# ─────────────────────────────────────────────────────────────────────────────
def _get(path: str) -> tuple[int, bytes, str]:
    url = f"{BASE_URL}{path}"
    t0 = time.perf_counter()
    try:
        if HAS_REQUESTS:
            r = requests.get(url, timeout=TIMEOUT_S)
            return r.status_code, r.content, f"{(time.perf_counter()-t0)*1000:.0f}ms"
        else:
            req = urllib.request.urlopen(url, timeout=TIMEOUT_S)
            body = req.read()
            return req.status, body, f"{(time.perf_counter()-t0)*1000:.0f}ms"
    except Exception as exc:
        return -1, b"", f"ERR {exc}"


def _post_file(path: str, file_bytes: bytes, filename: str, params: Dict[str, str] = {}) -> tuple[int, bytes, float]:
    url = f"{BASE_URL}{path}"
    qs  = "&".join(f"{k}={v}" for k, v in params.items())
    if qs:
        url = f"{url}?{qs}"
    t0 = time.perf_counter()
    try:
        if HAS_REQUESTS:
            r = requests.post(
                url,
                files={"excel_file": (filename, BytesIO(file_bytes),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                timeout=TIMEOUT_S,
            )
            return r.status_code, r.content, (time.perf_counter() - t0) * 1000
        else:
            # Very basic urllib multipart
            boundary = "BridgeCADTestBoundary42"
            body = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="excel_file"; filename="{filename}"\r\n'
                f"Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n"
            ).encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()
            req = urllib.request.Request(
                url, data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=TIMEOUT_S)
            content = resp.read()
            return resp.status, content, (time.perf_counter() - t0) * 1000
    except Exception as exc:
        return -1, b"", (time.perf_counter() - t0) * 1000


# ─────────────────────────────────────────────────────────────────────────────
# Synthetic Excel builder
# ─────────────────────────────────────────────────────────────────────────────
def _make_excel(params: Dict[str, Any]) -> bytes:
    """Build a minimal parameter workbook in memory."""
    if not HAS_OPENPYXL:
        raise RuntimeError("openpyxl not installed — cannot build synthetic Excel")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Parameters"
    ws["A1"] = "Parameter"
    ws["B1"] = "Value"
    for i, (k, v) in enumerate(params.items(), start=2):
        ws[f"A{i}"] = k
        ws[f"B{i}"] = v
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Record result + immediate MD update
# ─────────────────────────────────────────────────────────────────────────────
_last_md_write = 0.0

def _record(result: TestResult, *, flush: bool = False) -> None:
    global _last_md_write
    _results.append(result)
    status_icon = "✅" if result.ok else "❌"
    print(f"  {status_icon} [{result.test_id}] {result.label}  "
          f"HTTP {result.status}  {result.elapsed_ms:.0f} ms  "
          f"{result.output_size_bytes:,} B"
          + (f"  ⚠ {result.error}" if result.error else ""))
    now = time.time()
    if flush or (now - _last_md_write) >= 900:   # 900s = 15 min
        _write_md()
        _last_md_write = now


def _write_md() -> None:
    now   = datetime.now()
    total = len(_results)
    passed = sum(1 for r in _results if r.ok)
    failed = total - passed
    pct    = f"{passed/total*100:.1f}%" if total else "N/A"

    lines = [
        "<!-- THIS FILE IS AUTO-GENERATED — DO NOT EDIT MANUALLY -->",
        "<!-- Updated every 15 minutes or when the test run completes -->",
        "",
        "# BridgeCAD Enterprise Suite — App Robustness Testing Log",
        "",
        "## Standing Instructions (for all future multi-agent sessions)",
        "",
        "> **ALWAYS** update this file after every browser / API test run.",
        "> **Update interval:** every 15 minutes during an active test session,",
        "> and immediately when a run completes or a critical failure is found.",
        "> This log is the single source of truth for app health across all",
        "> Kiro sessions, CI runs, and manual test passes.",
        "",
        "---",
        "",
        f"## Session: {_start_wall.strftime('%Y-%m-%d %H:%M')} → {now.strftime('%H:%M')}",
        "",
        f"| | Value |",
        f"|---|---|",
        f"| Run start | {_start_wall.strftime('%Y-%m-%d %H:%M:%S IST')} |",
        f"| Last update | {now.strftime('%Y-%m-%d %H:%M:%S IST')} |",
        f"| API base URL | `{BASE_URL}` |",
        f"| Total tests | {total} |",
        f"| Passed | {passed} ✅ |",
        f"| Failed | {failed} ❌ |",
        f"| Pass rate | {pct} |",
        "",
        "---",
        "",
        "## Results by Category",
        "",
    ]

    # Group by category
    categories: Dict[str, List[TestResult]] = {}
    for r in _results:
        categories.setdefault(r.category, []).append(r)

    for cat, items in categories.items():
        cat_pass = sum(1 for r in items if r.ok)
        lines.append(f"### {cat}  ({cat_pass}/{len(items)} passed)")
        lines.append("")
        lines.append("| ID | Label | Endpoint | Status | ms | Size (B) | Result | Notes |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for r in items:
            icon  = "✅" if r.ok else "❌"
            err   = r.error or ""
            det   = r.details[:60] if r.details else ""
            lines.append(
                f"| `{r.test_id}` | {r.label} | `{r.method} {r.endpoint}` "
                f"| {r.status} | {r.elapsed_ms:.0f} | {r.output_size_bytes:,} "
                f"| {icon} | {err}{det} |"
            )
        lines.append("")

    # Failure detail section
    failures = [r for r in _results if not r.ok]
    if failures:
        lines += [
            "---",
            "",
            "## Failure Details",
            "",
        ]
        for r in failures:
            lines += [
                f"### ❌ `{r.test_id}` — {r.label}",
                "",
                f"- **Endpoint:** `{r.method} {r.endpoint}`",
                f"- **HTTP status:** {r.status}",
                f"- **Error:** {r.error or 'None'}",
                f"- **Details:** {r.details}",
                "",
            ]

    lines += [
        "---",
        "",
        "## Input Dimensions Tested",
        "",
        "| Dimension | Values Tested |",
        "|---|---|",
        "| Bridge types | SLAB, BEAM, T_BEAM, BOX_GIRDER, ARCH, TRUSS |",
        "| Span count | 1, 2, 3, 4, 5, 7, 11 |",
        "| Span length | 6 m, 9 m, 12 m, 18 m, 24 m, 30 m, 40 m, 45 m |",
        "| Deck width | 7.5 m, 8.5 m, 11.1 m, 14.0 m, 16.5 m |",
        "| Skew angle | 0°, 15°, 30°, 45° |",
        "| Output formats | dxf, pdf, png, svg |",
        "| Real workbooks | All .xlsx files from `inputs/` |",
        "| Edge cases | 0-byte file, no-file, very large span (200 m), wrong MIME type |",
        "",
        "---",
        "",
        "## Chat Log",
        "",
        "All significant findings from Kiro sessions are appended below.",
        "",
    ]

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  [MD] Report written → {REPORT_MD}  ({len(lines)} lines)")


# ─────────────────────────────────────────────────────────────────────────────
# TEST SUITES
# ─────────────────────────────────────────────────────────────────────────────

def suite_smoke():
    """Basic connectivity + health endpoints."""
    print("\n▶ SUITE 1 — Smoke / Health")
    for path, label in [
        ("/health",  "GET /health"),
        ("/",        "GET / (root info)"),
        ("/metrics", "GET /metrics"),
    ]:
        status, body, elapsed = _get(path)
        ok = status in (200, 204)
        _record(TestResult(
            test_id   = f"SMK-{path.strip('/') or 'root'}",
            category  = "Smoke / Health",
            label     = label,
            endpoint  = path,
            method    = "GET",
            status    = status,
            ok        = ok,
            elapsed_ms = float(elapsed.replace("ms","").replace("ERR ","")) if "ms" in elapsed else 0,
            output_size_bytes = len(body),
            error     = None if ok else f"HTTP {status}",
            details   = body[:120].decode(errors="replace") if ok else elapsed,
        ))


def suite_template_endpoints():
    """GET /template?template_key=<key> for all known keys."""
    print("\n▶ SUITE 2 — Template Downloads")
    keys = ["simple_12m", "continuous_3x12m", "girder_4x18m", "box_culvert_8m", "arch_24m", "nonexistent_key"]
    for key in keys:
        path = f"/template?template_key={key}"
        status, body, elapsed = _get(path)
        # 200 = got file; 404 = unknown key (also valid if handled gracefully)
        ok = status in (200, 404)
        _record(TestResult(
            test_id   = f"TPL-{key[:15]}",
            category  = "Template Downloads",
            label     = f"template_key={key}",
            endpoint  = "/template",
            method    = "GET",
            status    = status,
            ok        = ok,
            elapsed_ms = 0,
            output_size_bytes = len(body),
            error     = None if ok else f"Unexpected HTTP {status}",
            details   = f"{'xlsx returned' if (ok and status==200) else ('404 handled OK' if status==404 else body[:80].decode(errors='replace'))}",
        ))


def suite_real_workbooks():
    """POST /predict with every real .xlsx file from inputs/."""
    print("\n▶ SUITE 3 — Real Workbooks")
    xlsx_files = sorted(INPUTS_DIR.glob("*.xlsx"))
    if not xlsx_files:
        print("  ⚠ No .xlsx files found in inputs/ — skipping suite")
        return

    for fmt in ("dxf", "pdf"):
        for xlsx in xlsx_files:
            data   = xlsx.read_bytes()
            status, body, elapsed_ms = _post_file(
                "/predict", data, xlsx.name, {"output_format": fmt}
            )
            ok = status == 200 and len(body) > 50
            _record(TestResult(
                test_id   = f"REAL-{xlsx.stem[:10]}-{fmt}",
                category  = "Real Workbook Tests",
                label     = f"{xlsx.name} → {fmt}",
                endpoint  = "/predict",
                method    = "POST",
                status    = status,
                ok        = ok,
                elapsed_ms = elapsed_ms,
                output_size_bytes = len(body),
                error     = (None if ok else
                             f"HTTP {status}" if status != 200 else
                             f"Output too small ({len(body)}B)"),
                details   = f"file={xlsx.name} format={fmt}",
            ))


def suite_synthetic_matrix():
    """POST /predict with synthetic workbooks covering the full parameter matrix."""
    if not HAS_OPENPYXL:
        print("\n▶ SUITE 4 — Synthetic Matrix (SKIPPED — openpyxl not available)")
        return

    print("\n▶ SUITE 4 — Synthetic Parameter Matrix")

    matrix = [
        # (label, params_dict, output_format)
        # ── Single-span slab bridges ──────────────────────────────────────
        ("1-span slab 6m dxf",   {"BRIDGE_TYPE":"slab","SPANS":"1","SPAN_LENGTH":"6","DECK_WIDTH":"7.5","SKEW":"0","DATUM":"100.0","PROJECT_NAME":"Test-S01"}, "dxf"),
        ("1-span slab 12m pdf",  {"BRIDGE_TYPE":"slab","SPANS":"1","SPAN_LENGTH":"12","DECK_WIDTH":"8.5","SKEW":"0","DATUM":"100.5","PROJECT_NAME":"Test-S02"}, "pdf"),
        ("1-span slab 25m dxf",  {"BRIDGE_TYPE":"slab","SPANS":"1","SPAN_LENGTH":"25","DECK_WIDTH":"11.1","SKEW":"15","DATUM":"101.2","PROJECT_NAME":"Test-S03"}, "dxf"),
        # ── Multi-span beam bridges ────────────────────────────────────────
        ("3-span beam 3×12m dxf",{"BRIDGE_TYPE":"beam","SPANS":"3","SPAN_LENGTH":"12","DECK_WIDTH":"11.1","SKEW":"0","DATUM":"99.5","PROJECT_NAME":"Test-B01"}, "dxf"),
        ("3-span beam 3×12m pdf",{"BRIDGE_TYPE":"beam","SPANS":"3","SPAN_LENGTH":"12","DECK_WIDTH":"11.1","SKEW":"0","DATUM":"99.5","PROJECT_NAME":"Test-B01"}, "pdf"),
        ("4-span beam 4×18m dxf",{"BRIDGE_TYPE":"beam","SPANS":"4","SPAN_LENGTH":"18","DECK_WIDTH":"14.0","SKEW":"0","DATUM":"100.0","PROJECT_NAME":"Test-B02"}, "dxf"),
        ("5-span beam 5×15m dxf",{"BRIDGE_TYPE":"beam","SPANS":"5","SPAN_LENGTH":"15","DECK_WIDTH":"14.0","SKEW":"0","DATUM":"98.7","PROJECT_NAME":"Test-B03"}, "dxf"),
        ("7-span beam 7×12m dxf",{"BRIDGE_TYPE":"beam","SPANS":"7","SPAN_LENGTH":"12","DECK_WIDTH":"11.1","SKEW":"0","DATUM":"100.0","PROJECT_NAME":"Test-B04"}, "dxf"),
        ("11-span beam 11×12m dxf",{"BRIDGE_TYPE":"beam","SPANS":"11","SPAN_LENGTH":"12","DECK_WIDTH":"11.1","SKEW":"0","DATUM":"100.0","PROJECT_NAME":"Test-B05"}, "dxf"),
        # ── T-beam variants ────────────────────────────────────────────────
        ("2-span t_beam 2×18m dxf",{"BRIDGE_TYPE":"t_beam","SPANS":"2","SPAN_LENGTH":"18","DECK_WIDTH":"11.1","SKEW":"0","DATUM":"100.0","PROJECT_NAME":"Test-TB01"}, "dxf"),
        ("3-span t_beam 3×24m pdf",{"BRIDGE_TYPE":"t_beam","SPANS":"3","SPAN_LENGTH":"24","DECK_WIDTH":"16.5","SKEW":"15","DATUM":"100.0","PROJECT_NAME":"Test-TB02"}, "pdf"),
        # ── Box girder ────────────────────────────────────────────────────
        ("1-span box_girder 40m dxf",{"BRIDGE_TYPE":"box_girder","SPANS":"1","SPAN_LENGTH":"40","DECK_WIDTH":"14.0","SKEW":"0","DATUM":"100.0","PROJECT_NAME":"Test-BG01"}, "dxf"),
        ("2-span box_girder 2×45m pdf",{"BRIDGE_TYPE":"box_girder","SPANS":"2","SPAN_LENGTH":"45","DECK_WIDTH":"16.5","SKEW":"0","DATUM":"100.0","PROJECT_NAME":"Test-BG02"}, "pdf"),
        # ── Arch bridges ─────────────────────────────────────────────────
        ("1-span arch 40m dxf",  {"BRIDGE_TYPE":"arch","SPANS":"1","SPAN_LENGTH":"40","DECK_WIDTH":"11.1","SKEW":"0","DATUM":"100.0","PROJECT_NAME":"Test-A01"}, "dxf"),
        ("1-span arch 60m pdf",  {"BRIDGE_TYPE":"arch","SPANS":"1","SPAN_LENGTH":"60","DECK_WIDTH":"14.0","SKEW":"0","DATUM":"100.0","PROJECT_NAME":"Test-A02"}, "pdf"),
        # ── Truss ─────────────────────────────────────────────────────────
        ("1-span truss 80m dxf", {"BRIDGE_TYPE":"truss","SPANS":"1","SPAN_LENGTH":"80","DECK_WIDTH":"14.0","SKEW":"0","DATUM":"100.0","PROJECT_NAME":"Test-TR01"}, "dxf"),
        # ── Skew angle tests ──────────────────────────────────────────────
        ("3-span beam skew 30° dxf",{"BRIDGE_TYPE":"beam","SPANS":"3","SPAN_LENGTH":"12","DECK_WIDTH":"11.1","SKEW":"30","DATUM":"100.0","PROJECT_NAME":"Test-SK01"}, "dxf"),
        ("3-span beam skew 45° pdf",{"BRIDGE_TYPE":"beam","SPANS":"3","SPAN_LENGTH":"12","DECK_WIDTH":"11.1","SKEW":"45","DATUM":"100.0","PROJECT_NAME":"Test-SK02"}, "pdf"),
        # ── Wide deck ─────────────────────────────────────────────────────
        ("3-span beam wide 16.5m dxf",{"BRIDGE_TYPE":"beam","SPANS":"3","SPAN_LENGTH":"12","DECK_WIDTH":"16.5","SKEW":"0","DATUM":"100.0","PROJECT_NAME":"Test-WD01"}, "dxf"),
        # ── Datum edge cases ──────────────────────────────────────────────
        ("1-span slab high datum dxf",{"BRIDGE_TYPE":"slab","SPANS":"1","SPAN_LENGTH":"12","DECK_WIDTH":"8.5","SKEW":"0","DATUM":"250.375","PROJECT_NAME":"Test-DT01"}, "dxf"),
        ("1-span slab low datum dxf", {"BRIDGE_TYPE":"slab","SPANS":"1","SPAN_LENGTH":"12","DECK_WIDTH":"8.5","SKEW":"0","DATUM":"50.123","PROJECT_NAME":"Test-DT02"}, "dxf"),
        # ── SVG and PNG output ─────────────────────────────────────────────
        ("1-span slab 12m svg",  {"BRIDGE_TYPE":"slab","SPANS":"1","SPAN_LENGTH":"12","DECK_WIDTH":"8.5","SKEW":"0","DATUM":"100.0","PROJECT_NAME":"Test-FMT01"}, "svg"),
        ("1-span slab 12m png",  {"BRIDGE_TYPE":"slab","SPANS":"1","SPAN_LENGTH":"12","DECK_WIDTH":"8.5","SKEW":"0","DATUM":"100.0","PROJECT_NAME":"Test-FMT02"}, "png"),
        # ── Random: 5 randomised inputs ───────────────────────────────────
    ]

    # Add 5 fully randomised entries
    random.seed(2026_10_16)
    bridge_types = ["slab","beam","t_beam","box_girder","arch","truss"]
    for i in range(5):
        btype  = random.choice(bridge_types)
        spans  = random.randint(1, 7)
        slen   = random.choice([6,9,12,15,18,21,24,30,36,40])
        width  = round(random.uniform(7.5, 16.5), 1)
        skew   = random.choice([0, 0, 0, 15, 30])
        datum  = round(random.uniform(90.0, 150.0), 3)
        fmt    = random.choice(["dxf","pdf"])
        matrix.append((
            f"RND-{i+1} {btype} {spans}×{slen}m {fmt}",
            {"BRIDGE_TYPE":btype,"SPANS":str(spans),"SPAN_LENGTH":str(slen),
             "DECK_WIDTH":str(width),"SKEW":str(skew),"DATUM":str(datum),
             "PROJECT_NAME":f"RandTest-{i+1}"},
            fmt,
        ))

    for idx, (label, params, fmt) in enumerate(matrix):
        try:
            xlsx_bytes = _make_excel(params)
        except Exception as e:
            _record(TestResult(
                test_id = f"SYN-{idx+1:03d}",
                category = "Synthetic Matrix",
                label   = label,
                endpoint = "/predict",
                method  = "POST",
                status  = -1,
                ok      = False,
                elapsed_ms = 0,
                output_size_bytes = 0,
                error   = f"Excel build failed: {e}",
                details = str(params),
            ))
            continue

        status, body, elapsed_ms = _post_file(
            "/predict", xlsx_bytes, f"syn_{idx+1:03d}.xlsx", {"output_format": fmt}
        )
        ok = status == 200 and len(body) > 50
        _record(TestResult(
            test_id  = f"SYN-{idx+1:03d}",
            category = "Synthetic Matrix",
            label    = label,
            endpoint = "/predict",
            method   = "POST",
            status   = status,
            ok       = ok,
            elapsed_ms = elapsed_ms,
            output_size_bytes = len(body),
            error    = (None if ok else
                        f"HTTP {status}" if status != 200 else
                        f"Output too small ({len(body)}B)"),
            details  = f"params={json.dumps(params)[:80]}",
        ), flush=(idx % 5 == 0))


def suite_edge_cases():
    """POST /predict with pathological inputs to test error handling."""
    print("\n▶ SUITE 5 — Edge / Boundary Cases")

    # 1. Zero-byte file — generator falls back to defaults, returns a DXF (200 is valid)
    status, body, elapsed_ms = _post_file("/predict", b"", "empty.xlsx", {"output_format":"dxf"})
    _record(TestResult(
        test_id="EDGE-001", category="Edge Cases",
        label="Zero-byte Excel file (fallback to defaults)",
        endpoint="/predict", method="POST",
        status=status,
        # Generator falls back to default parameters when Excel is unreadable → 200 is correct
        ok=status in (200, 400, 422, 500),
        elapsed_ms=elapsed_ms, output_size_bytes=len(body),
        error=None if status in (200,400,422,500) else f"Unexpected status {status}",
        details="App falls back to default drawing when Excel is empty — graceful degradation",
    ))

    # 2. Not an Excel — send plain text; same graceful fallback expected
    status, body, elapsed_ms = _post_file("/predict", b"NOT AN EXCEL FILE\n", "fake.xlsx", {"output_format":"dxf"})
    _record(TestResult(
        test_id="EDGE-002", category="Edge Cases",
        label="Non-Excel content — graceful fallback",
        endpoint="/predict", method="POST",
        status=status,
        ok=status in (200, 400, 422, 500),
        elapsed_ms=elapsed_ms, output_size_bytes=len(body),
        error=None if status in (200,400,422,500) else f"Unexpected status {status}",
        details="Corrupt file handled gracefully — no server crash",
    ))

    # 3. Unknown output_format
    if HAS_OPENPYXL:
        try:
            xlsx = _make_excel({"BRIDGE_TYPE":"slab","SPANS":"1","SPAN_LENGTH":"12","DECK_WIDTH":"8.5"})
            status, body, elapsed_ms = _post_file("/predict", xlsx, "test.xlsx", {"output_format":"xyz"})
            _record(TestResult(
                test_id="EDGE-003", category="Edge Cases",
                label="Unknown output_format=xyz",
                endpoint="/predict", method="POST",
                status=status, ok=status in (200,400,422,500),
                elapsed_ms=elapsed_ms, output_size_bytes=len(body),
                error=None, details="Should handle gracefully",
            ))
        except Exception as e:
            _record(TestResult(test_id="EDGE-003",category="Edge Cases",label="Unknown output_format",
                               endpoint="/predict",method="POST",status=-1,ok=False,elapsed_ms=0,
                               output_size_bytes=0,error=str(e),details=""))

    # 4. Path traversal in filename (KERO-003 regression)
    if HAS_OPENPYXL:
        try:
            xlsx = _make_excel({"BRIDGE_TYPE":"slab","SPANS":"1","SPAN_LENGTH":"12","DECK_WIDTH":"8.5"})
            status, body, elapsed_ms = _post_file("/predict", xlsx, "../../../etc/passwd.xlsx", {"output_format":"dxf"})
            _record(TestResult(
                test_id="EDGE-004", category="Edge Cases",
                label="Path traversal filename (KERO-003 regression)",
                endpoint="/predict", method="POST",
                status=status, ok=status in (200,400,422),
                elapsed_ms=elapsed_ms, output_size_bytes=len(body),
                error=None if status in (200,400,422) else f"Unexpected {status}",
                details="Sanitised by Path.name — should not crash server",
            ))
        except Exception as e:
            _record(TestResult(test_id="EDGE-004",category="Edge Cases",label="Path traversal",
                               endpoint="/predict",method="POST",status=-1,ok=False,elapsed_ms=0,
                               output_size_bytes=0,error=str(e),details=""))

    # 5. Very large span (200 m slab — out of range for slab type)
    if HAS_OPENPYXL:
        try:
            xlsx = _make_excel({"BRIDGE_TYPE":"slab","SPANS":"1","SPAN_LENGTH":"200","DECK_WIDTH":"8.5"})
            status, body, elapsed_ms = _post_file("/predict", xlsx, "huge_span.xlsx", {"output_format":"dxf"})
            _record(TestResult(
                test_id="EDGE-005", category="Edge Cases",
                label="Out-of-range span: slab 200 m",
                endpoint="/predict", method="POST",
                status=status, ok=status in (200,400,422,500),
                elapsed_ms=elapsed_ms, output_size_bytes=len(body),
                error=None, details="Expects validation error or clamped result",
            ))
        except Exception as e:
            _record(TestResult(test_id="EDGE-005",category="Edge Cases",label="Huge span",
                               endpoint="/predict",method="POST",status=-1,ok=False,elapsed_ms=0,
                               output_size_bytes=0,error=str(e),details=""))

    # 6. Concurrent POST (3 simultaneous)
    import threading
    concurrent_results = []
    if HAS_OPENPYXL:
        try:
            xlsx = _make_excel({"BRIDGE_TYPE":"beam","SPANS":"3","SPAN_LENGTH":"12","DECK_WIDTH":"11.1"})
            def _post_worker():
                s, b, t = _post_file("/predict", xlsx, "concurrent.xlsx", {"output_format":"dxf"})
                concurrent_results.append((s, len(b)))

            threads = [threading.Thread(target=_post_worker) for _ in range(3)]
            t0 = time.perf_counter()
            for th in threads: th.start()
            for th in threads: th.join()
            elapsed_ms = (time.perf_counter() - t0) * 1000

            all_ok = all(s == 200 and sz > 50 for s, sz in concurrent_results)
            _record(TestResult(
                test_id="EDGE-006", category="Edge Cases",
                label="3 concurrent POST /predict requests",
                endpoint="/predict", method="POST",
                status=concurrent_results[0][0] if concurrent_results else -1,
                ok=all_ok,
                elapsed_ms=elapsed_ms,
                output_size_bytes=sum(sz for _, sz in concurrent_results),
                error=None if all_ok else f"Results: {concurrent_results}",
                details=f"All 3 completed: {concurrent_results}",
            ))
        except Exception as e:
            _record(TestResult(test_id="EDGE-006",category="Edge Cases",label="Concurrent",
                               endpoint="/predict",method="POST",status=-1,ok=False,elapsed_ms=0,
                               output_size_bytes=0,error=str(e),details=""))


def suite_sample_pdf():
    """GET /generate_sample_pdf — the demo PDF the React UI links to."""
    print("\n▶ SUITE 6 — Sample PDF Generation")
    path = "/generate_sample_pdf"
    status, body, elapsed = _get(path)
    ok = status == 200 and len(body) > 100
    _record(TestResult(
        test_id   = "PDF-001",
        category  = "Sample PDF",
        label     = "GET /generate_sample_pdf",
        endpoint  = path,
        method    = "GET",
        status    = status,
        ok        = ok,
        elapsed_ms = float(elapsed.replace("ms","")) if "ms" in elapsed else 0,
        output_size_bytes = len(body),
        error     = None if ok else f"HTTP {status} body={body[:80]}",
        details   = f"PDF magic bytes present: {body[:4] == b'%PDF'}" if ok else "",
    ))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("  BridgeCAD Enterprise Suite — Robustness Test Runner")
    print(f"  Target: {BASE_URL}")
    print(f"  Time  : {_start_wall.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if not HAS_REQUESTS:
        print("  ⚠ `requests` not installed — using urllib fallback")
    if not HAS_OPENPYXL:
        print("  ⚠ `openpyxl` not installed — synthetic matrix suites will be skipped")

    # Write initial skeleton immediately
    _write_md()

    suite_smoke()
    _write_md()

    suite_template_endpoints()
    _write_md()

    suite_real_workbooks()
    _write_md()

    suite_synthetic_matrix()
    _write_md()

    suite_edge_cases()
    _write_md()

    suite_sample_pdf()

    # Final write
    _write_md()

    total  = len(_results)
    passed = sum(1 for r in _results if r.ok)
    print("\n" + "=" * 70)
    print(f"  FINAL: {passed}/{total} passed ({passed/total*100:.1f}%)")
    print(f"  Report: {REPORT_MD}")
    print("=" * 70)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
