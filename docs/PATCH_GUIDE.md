# Patch guide — by defect class

Patterns for what this app actually produces. Each shows the wrong shape and the
right one. One patch = one class; cross-referenced from
[TRIAGE_AND_DEBUG.md](TRIAGE_AND_DEBUG.md) Step 6.

**See also:** [ROBOTIC-TEST-GUIDE.MD](../ROBOTIC-TEST-GUIDE.MD) ·
[TRIAGE_LOG.md](../artifacts/TRIAGE_LOG.md).

---

## 1. Zero / negative numeric input reaches the math

**Symptom:** `ZeroDivisionError`, `inf` depth, `NaN` in the DXF.
**Fix:** validate at the boundary *and* guard the math.

```diff
-# --- engine module (resolve via scripts/robot/personas.py ENGINE_CANDIDATES) ---
-def design_girder(span_m, carriageway_m, grade):
-    return Girder(depth_m=span_m / 18.0, ...)
+from pydantic import BaseModel, Field
+
+class GirderInput(BaseModel):
+    span_m: float = Field(gt=0, le=500)
+    carriageway_m: float = Field(gt=0, le=60)
+    grade: str = Field(pattern=r"^M(20|25|30|35|40|45|50|60)$")
+
+def design_girder(span_m: float, carriageway_m: float, grade: str) -> Girder:
+    GirderInput(span_m=span_m, carriageway_m=carriageway_m, grade=grade)
+    depth = max(span_m / 18.0, 0.6)          # never below the practical minimum
+    return Girder(depth_m=depth, ...)
```

The same `GirderInput` gets reused by the FastAPI route → 422 for free, no
duplicated checks.

## 2. Streamlit widget state resets on rerun

**Symptom:** values blank after any interaction; the robot fills span, then it is
gone.
**Cause:** a widget created with a value derived from another widget, without a key.

```diff
-span = st.number_input("Span (m)", value=20.0)
+if "span_m" not in st.session_state:
+    st.session_state.span_m = 20.0
+span = st.number_input("Span (m)", key="span_m",
+                       min_value=1.0, max_value=500.0, step=0.5)
```

Rule: **every** interactive widget gets a stable `key`. Never derive `value=`
from `session_state` while also writing it.

## 3. Export writes into a shared temp path → parallel users collide

**Symptom:** intermittently truncated DXF/ZIP under concurrent export.
**Fix:** per-request directory.

```diff
-OUT = Path("/tmp/bridgecad")
-def export_dxf(cfg):
-    p = OUT / "out.dxf"
+def export_dxf(cfg):
+    p = Path(tempfile.mkdtemp(prefix="bcad_")) / "out.dxf"
     build_dxf(cfg, p)
     return p.read_bytes()
```

## 4. DXF float noise → nondeterministic, un-auditable output

**Symptom:** determinism test fails; `audit()` errors on stray points.

```diff
-pts = [(x * 1000, y * 1000) for x, y in coords]
+def q(v: float) -> float:
+    return round(v, 6)
+pts = [(q(x * 1000.0), q(y * 1000.0)) for x, y in coords]
+doc.header["$INSUNITS"] = 4        # millimetres, always declared
```

## 5. Hardcoded 7-sheet assumption

**Symptom:** adding a sheet breaks the count assertion; removing one silently
exports 6.
**Fix:** a registry, and the count derives from it.

```diff
-def build_sheets(cfg):
-    return [general(cfg), ga(cfg), rebar(cfg), ...]   # 7 literals
+SHEETS = ("general", "ga", "rebar", "tendon", "bearing", "deck", "bbs")
+def build_sheets(cfg):
+    return [REGISTRY[n](cfg) for n in SHEETS]
```

## 6. Unbounded file upload

**Symptom:** a 50 MB PDF hangs the worker; a 0-byte file → `IndexError` downstream.

```diff
 up = st.file_uploader("PDF", type=["pdf"])
 if up:
+    if up.size == 0:
+        st.error("Empty file.")
+        st.stop()
+    if up.size > 25 * 1024 * 1024:
+        st.error("Max 25 MB.")
+        st.stop()
+    if not up.getvalue()[:5].startswith(b"%PDF"):
+        st.error("Not a valid PDF (magic bytes).")
+        st.stop()
```

## 7. Exception text leaks into the UI

**Symptom:** the user sees a Python traceback with internal paths.

```diff
-try:
-    run()
-except Exception:
-    st.exception(sys.exc_info())
+try:
+    run()
+except InputError as e:
+    st.error(f"Input problem: {e}")
+except Exception as e:
+    st.error("Generation failed — see log.")
+    st.caption(f"ref: {uuid.uuid4().hex[:8]}")
+    logger.exception("generation failed")
```

## 8. Export blocks the event loop

**Symptom:** perf test over budget; the UI freezes on a max-span run.
**Fix:** cache by config hash, and move the heavy build to a thread.

```diff
-@st.cache_data
-def build(cfg_json): ...
+@st.cache_data(show_spinner=False, max_entries=32)
+def build(cfg_json: str) -> bytes: ...
+
+with st.spinner("Generating…"):
+    data = await asyncio.to_thread(build, cfg.model_dump_json())
```

## 9. Filename injection

**Symptom:** `a b/c:d` becomes a nested path, or truncates.

```diff
-name = f"{cfg.project_name}.dxf"
+safe = re.sub(r"[^A-Za-z0-9._-]+", "_", cfg.project_name).strip("._") or "project"
+name = f"{safe}.dxf"
```

## 10. Unicode mojibake in exports

**Symptom:** Devanagari or CJK glyphs become `????` in PDF/Excel.
**Fix:** declare the encoding everywhere and use a Unicode-capable font.

```diff
-ws.cell(row=1, column=1, value=cfg.project_name)
+from openpyxl.styles import Font
+ws.cell(row=1, column=1, value=cfg.project_name).font = Font(name="Noto Sans Devanagari")
+ws.column_dimensions["A"].width = min(max(len(cfg.project_name) * 1.4, 12), 60)
```

---

## Patch hygiene

- One class per PR. Title: `fix(<area>): <symptom> [S1]`.
- Body links the minimized trace and the regression test.
- No `# type: ignore`, no bare `except:`, no `time.sleep` added to hide a race.
- The [pull request template](../.github/PULL_REQUEST_TEMPLATE.md) carries the
  triage block these rules attach to.
