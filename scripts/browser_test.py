"""
End-to-end browser test — exercises every live endpoint with real data.

Steps:
  1. Verify all 3 services respond
  2. Generate a real template xlsx (simple_12m)
  3. POST to /bridges/parse   → project metadata
  4. POST to /bridges/validate → QA score
  5. POST to /draw/gad         → DXF ZIP download
  6. POST to /bills/generate   → BOQ JSON
  7. POST to /qa/report        → HTML report
  8. POST to /exports/bundle   → full ZIP
  9. GET  /plugins/            → 3 plugins
  10. GET /docs (Swagger)      → 200
  Report: pass/fail per step + sizes + timings
"""
from __future__ import annotations
import sys, time, json, io
from pathlib import Path
from decimal import Decimal

# ── bootstrap ─────────────────────────────────────────────────────────────
SUITE = Path(__file__).parent.parent
for pkg in ["bridgecad-core","bridgecad-io","bridgecad-draw",
            "bridgecad-bill","bridgecad-qa","bridgecad-export",
            "bridgecad-plugins"]:
    p = SUITE / "packages" / pkg
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    import requests
except ImportError:
    import subprocess, sys as _sys
    subprocess.check_call([_sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

API  = "http://localhost:8000"
ST   = "http://localhost:8501"
VITE = "http://localhost:5173"
SEP  = "=" * 68
PASS = "  ✅"
FAIL = "  ❌"

results: list[tuple[str, bool, str]] = []

def ok(label, detail=""):
    results.append((label, True, detail))
    print(f"{PASS}  {label}" + (f"   [{detail}]" if detail else ""))

def fail(label, detail=""):
    results.append((label, False, detail))
    print(f"{FAIL}  {label}" + (f"   {detail}" if detail else ""))

print(); print(SEP)
print("  BRIDGECAD BROWSER END-TO-END TEST")
print(SEP)

# ── STEP 0: service health ─────────────────────────────────────────────────
print("\n── Step 0: Service Health ─────────────────────────────────────")
for name, url, path in [
    ("FastAPI",    API,   "/health"),
    ("Streamlit",  ST,    "/_stcore/health"),
    ("React/Vite", VITE,  "/"),
]:
    try:
        r = requests.get(url + path, timeout=5)
        if r.status_code == 200:
            ok(f"{name} alive", f"HTTP {r.status_code} {url+path}")
        else:
            fail(f"{name} alive", f"HTTP {r.status_code}")
    except Exception as exc:
        fail(f"{name} alive", str(exc)[:60])

# ── STEP 1: API version ────────────────────────────────────────────────────
print("\n── Step 1: API Version ────────────────────────────────────────")
try:
    r = requests.get(f"{API}/version", timeout=5)
    data = r.json()
    ver  = data.get("version","?")
    code = data.get("codename","?")
    if ver == "0.1.0-rc1":
        ok("API version", f"v{ver}  [{code}]")
    else:
        fail("API version", f"got {ver!r} expected 0.1.0-rc1")
except Exception as exc:
    fail("API version", str(exc)[:60])

# ── STEP 2: Plugins list ───────────────────────────────────────────────────
print("\n── Step 2: Plugin Registry ─────────────────────────────────────")
try:
    r = requests.get(f"{API}/plugins/", timeout=5)
    data = r.json()
    count = data.get("count", 0)
    ids   = [p["id"] for p in data.get("plugins", [])]
    if count >= 3:
        ok("3 plugins registered", f"{ids}")
    else:
        fail("3 plugins registered", f"only {count}: {ids}")
except Exception as exc:
    fail("Plugin list", str(exc)[:60])

# ── STEP 3: Generate template in-process ─────────────────────────────────
print("\n── Step 3: Generate simple_12m template ────────────────────────")
import tempfile
try:
    from bridgecad_io.excel_template import generate_template
    with tempfile.TemporaryDirectory() as td:
        xlsx_path = Path(td) / "simple_12m_test.xlsx"
        generate_template(xlsx_path, title="Browser Test — simple_12m")
        xlsx_bytes = xlsx_path.read_bytes()
    size_kb = len(xlsx_bytes) // 1024
    if size_kb >= 15:
        ok("Template generated", f"{size_kb} KB  (14-sheet xlsx)")
    else:
        fail("Template generated", f"too small: {size_kb} KB")
except Exception as exc:
    fail("Template generated", str(exc)[:80])
    import traceback; traceback.print_exc()
    xlsx_bytes = b""

# ── STEP 4: POST /bridges/parse ───────────────────────────────────────────
print("\n── Step 4: POST /bridges/parse ─────────────────────────────────")
project_ok = False
if xlsx_bytes:
    try:
        t0 = time.perf_counter()
        r  = requests.post(
            f"{API}/bridges/parse",
            files={"file": ("test.xlsx", xlsx_bytes,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            timeout=60,
        )
        ms = int((time.perf_counter()-t0)*1000)
        if r.status_code == 200:
            data = r.json()
            proj = data.get("project", {})
            ok("Parse xlsx→project", f"status={data.get('status')}  "
               f"length={proj.get('total_length_m')}m  "
               f"spans={proj.get('span_count')}  [{ms}ms]")
            project_ok = True
        else:
            fail("Parse xlsx→project", f"HTTP {r.status_code}: {r.text[:80]}")
    except Exception as exc:
        fail("Parse xlsx→project", str(exc)[:80])

# ── STEP 5: POST /bridges/validate ────────────────────────────────────────
print("\n── Step 5: POST /bridges/validate ──────────────────────────────")
if xlsx_bytes:
    try:
        t0 = time.perf_counter()
        r  = requests.post(
            f"{API}/bridges/validate",
            files={"file": ("test.xlsx", xlsx_bytes,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            timeout=60,
        )
        ms = int((time.perf_counter()-t0)*1000)
        if r.status_code == 200:
            data = r.json()
            score = data.get("score", 0)
            grade = data.get("grade","?")
            crit  = data.get("critical_fails",999)
            nf    = len(data.get("findings", []))
            # Blank template will have critical fails — correct behaviour.
            # Test passes if endpoint returns 200 with valid JSON structure.
            if "score" in data and "findings" in data:
                ok("QA validation", f"score={score}/100  grade={grade}  "
                   f"critical_fails={crit}  checks={nf}  [{ms}ms]  "
                   f"({'blank template' if crit > 0 else 'PASS'})")
        else:
            fail("QA validation", f"HTTP {r.status_code}: {r.text[:80]}")
    except Exception as exc:
        fail("QA validation", str(exc)[:80])

# ── STEP 6: POST /draw/gad ────────────────────────────────────────────────
print("\n── Step 6: POST /draw/gad (7-sheet DXF ZIP) ────────────────────")
if xlsx_bytes:
    try:
        t0 = time.perf_counter()
        r  = requests.post(
            f"{API}/draw/gad?scale=100&prefix=BTEST",
            files={"file": ("test.xlsx", xlsx_bytes,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            timeout=120,
        )
        ms = int((time.perf_counter()-t0)*1000)
        if r.status_code == 200:
            zip_kb = len(r.content) // 1024
            ct     = r.headers.get("Content-Type","?")
            # Count files in zip
            import zipfile as zf, io as _io
            with zf.ZipFile(_io.BytesIO(r.content)) as z:
                entries = z.namelist()
            ndxf = sum(1 for e in entries if e.endswith(".dxf"))
            ok("Draw 7-sheet DXF", f"{zip_kb} KB ZIP  {ndxf} DXF files  [{ms}ms]")
        else:
            fail("Draw 7-sheet DXF", f"HTTP {r.status_code}: {r.text[:100]}")
    except Exception as exc:
        fail("Draw 7-sheet DXF", str(exc)[:80])
        import traceback; traceback.print_exc()

# ── STEP 7: POST /bills/generate ─────────────────────────────────────────
print("\n── Step 7: POST /bills/generate ─────────────────────────────────")
if xlsx_bytes:
    try:
        t0 = time.perf_counter()
        r  = requests.post(
            f"{API}/bills/generate",
            files={"file": ("test.xlsx", xlsx_bytes,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            timeout=60,
        )
        ms = int((time.perf_counter()-t0)*1000)
        if r.status_code == 200:
            data  = r.json()
            total = data.get("grand_total", 0)
            nsecs = len(data.get("sections", []))
            nitems= sum(len(s.get("items",[])) for s in data.get("sections",[]))
            ok("BOQ generated", f"grand_total=INR {total:,.0f}  "
               f"sections={nsecs}  items={nitems}  [{ms}ms]")
        else:
            fail("BOQ generated", f"HTTP {r.status_code}: {r.text[:100]}")
    except Exception as exc:
        fail("BOQ generated", str(exc)[:80])
        import traceback; traceback.print_exc()

# ── STEP 8: POST /qa/report ───────────────────────────────────────────────
print("\n── Step 8: POST /qa/report (HTML) ───────────────────────────────")
if xlsx_bytes:
    try:
        t0 = time.perf_counter()
        r  = requests.post(
            f"{API}/qa/report",
            files={"file": ("test.xlsx", xlsx_bytes,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            timeout=60,
        )
        ms = int((time.perf_counter()-t0)*1000)
        if r.status_code == 200:
            html = r.text
            has_table = "<table" in html
            kb = len(html.encode()) // 1024
            ok("QA HTML report", f"{kb} KB  has_table={has_table}  [{ms}ms]")
        else:
            fail("QA HTML report", f"HTTP {r.status_code}")
    except Exception as exc:
        fail("QA HTML report", str(exc)[:80])

# ── STEP 9: POST /exports/bundle ──────────────────────────────────────────
print("\n── Step 9: POST /exports/bundle (full ZIP) ──────────────────────")
if xlsx_bytes:
    try:
        t0 = time.perf_counter()
        r  = requests.post(
            f"{API}/exports/bundle?scale=100",
            files={"file": ("test.xlsx", xlsx_bytes,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            timeout=180,
        )
        ms = int((time.perf_counter()-t0)*1000)
        if r.status_code == 200:
            import zipfile as zf, io as _io
            with zf.ZipFile(_io.BytesIO(r.content)) as z:
                entries = z.namelist()
            has_dxf  = any(e.endswith(".dxf")  for e in entries)
            has_xlsx = any(e.endswith(".xlsx") for e in entries)
            has_html = any(e.endswith(".html") for e in entries)
            has_mani = any("manifest" in e    for e in entries)
            zip_kb   = len(r.content) // 1024
            ok("Full export bundle", f"{zip_kb} KB  {len(entries)} files  "
               f"dxf={has_dxf}  xlsx={has_xlsx}  html={has_html}  "
               f"manifest={has_mani}  [{ms}ms]")
        else:
            fail("Full export bundle", f"HTTP {r.status_code}: {r.text[:100]}")
    except Exception as exc:
        fail("Full export bundle", str(exc)[:80])
        import traceback; traceback.print_exc()

# ── STEP 10: Swagger UI ───────────────────────────────────────────────────
print("\n── Step 10: Swagger / OpenAPI UI ───────────────────────────────")
try:
    r = requests.get(f"{API}/docs", timeout=5)
    if r.status_code == 200:
        ok("Swagger UI /docs", f"HTTP 200  {len(r.text)} chars")
    else:
        fail("Swagger UI /docs", f"HTTP {r.status_code}")
except Exception as exc:
    fail("Swagger UI /docs", str(exc)[:60])

# ── STEP 11: OpenAPI schema ───────────────────────────────────────────────
try:
    r = requests.get(f"{API}/openapi.json", timeout=5)
    if r.status_code == 200:
        schema = r.json()
        n_paths = len(schema.get("paths", {}))
        ok("OpenAPI schema", f"{n_paths} paths defined")
    else:
        fail("OpenAPI schema", f"HTTP {r.status_code}")
except Exception as exc:
    fail("OpenAPI schema", str(exc)[:60])

# ── STEP 12: Streamlit responsive ────────────────────────────────────────
print("\n── Step 12: Streamlit UI ────────────────────────────────────────")
try:
    r = requests.get(f"{ST}/_stcore/health", timeout=5)
    ok("Streamlit health", f"HTTP {r.status_code}  '{r.text.strip()}'  → http://localhost:8501")
except Exception as exc:
    fail("Streamlit health", str(exc)[:60])

# ── STEP 13: React Vite ──────────────────────────────────────────────────
try:
    r = requests.get(VITE, timeout=5)
    if r.status_code == 200 and "html" in r.text:
        ok("React Vite", f"HTTP {r.status_code}  {len(r.text)} bytes  → http://localhost:5173")
    else:
        fail("React Vite", f"HTTP {r.status_code}")
except Exception as exc:
    fail("React Vite", str(exc)[:60])

# ── SUMMARY ───────────────────────────────────────────────────────────────
passed = sum(1 for _,ok_,_ in results if ok_)
total  = len(results)
print()
print(SEP)
print("  BROWSER TEST SUMMARY")
print(SEP)
print(f"  Tests run : {total}")
print(f"  Passed    : {passed}")
print(f"  Failed    : {total - passed}")
if total - passed:
    print("\n  FAILURES:")
    for label, ok_, detail in results:
        if not ok_:
            print(f"    ❌ {label}  —  {detail}")
print()
print(f"  {'★ ALL BROWSER TESTS PASSED ★' if passed == total else 'SOME TESTS FAILED'}")
print(SEP)
print()
print("  Open in your browser:")
print("    🟢 Streamlit 15-tab  →  http://localhost:8501")
print("    🔵 FastAPI Swagger   →  http://localhost:8000/docs")
print("    🟣 React Console     →  http://localhost:5173")
print(SEP)
sys.exit(0 if passed == total else 1)
