# BridgeCAD: incorporate ATTACHED ASSETS LISP as a verified geometry reference

Date: 2026-11-13. Repository baseline: `5d5f99e68b3efcc36fdfaf295d2e76d986d1fa69`, with the preceding local BridgeCAD patches present.

## Verdict

**Yes: these assets can enrich the code, especially source traceability, coordinate invariants and solid-slab abutment geometry.** They are not a complete source for all 15 PWD configurations. Several principles are already implemented, so duplicating their code would create competing models.

I inspected the four checked-in files at `ATTACHED ASSETS` in the available checkout. I cannot inspect additional files that exist only on `E:\Rajkumar\BridgeCAD-Enterprise-Suite\ATTACHED ASSETS`. The original assets were neither modified nor executed.

## Asset inventory and authority

| Checked-in file | Bytes | SHA-256 |
|---|---:|---|
| `GAD_Module_Mapping_Derived_Unverified.md` | 4677 | `3d8843195ce8325c2e2f774a4bbaa2283724f41d82469c61c56785681212bf2e` |
| `LISP_Solid_Slab_GAD_Complete_Archive.md` | 15864 | `aa135530f9b91d85fbaf1160e20e9a11a88ac1f51973c92c99153f7e5f8c2c88` |
| `LISP_Solid_Slab_GAD_In_Toto.lsp` | 31209 | `8c820fe4e832d3021cc79a4d3d3f9739432cdfc9a0170da6570fceb3c9b3a1d6` |
| `yogipwd_lisp_solid_slab_gad_original.txt` | 46881 | `0842b93b25c8c3f1f2dc276bc80773760b379cf443d98fc04a8305bc94a81ed2` |

| File role | How to incorporate it |
|---|---|
| `LISP_Solid_Slab_GAD_In_Toto.lsp` | Primary local code listing for formula extraction and static inventory. It is a preservation of published fragments, not proof of a complete runnable application. |
| `yogipwd_lisp_solid_slab_gad_original.txt` | Raw article capture; use to cross-check extracted formulas and explanations. Prose/repeated fragments are not another executable module. |
| `LISP_Solid_Slab_GAD_Complete_Archive.md` | Secondary explanation. Reconcile its claims against the listing before using them as implementation requirements. |
| `GAD_Module_Mapping_Derived_Unverified.md` | Aspirational map only. Its own warning says it is not the archived source. Do not treat its well/girder/module names as implemented LISP. |

The source listing attributes the original AutoLISP to Shri P.M. Baviskar and names the article from which it was preserved. This review relies on the local files, not an independent online/authorship or licence investigation. Preserve their attribution and do not assume the repository's general licence establishes permission to redistribute third-party source elsewhere.

## What the source actually contains

Static inspection observes 13 function definitions:

`opn`, `reed`, `vpos`, `hpos`, `v2pos`, `h2pos`, `st`, `layout`, `cs`, `pier`, `pt`, `p2t`, `abt1`.

The explanatory archive's nine-function completeness statement does not match that observed count. The derived map's `GAD_INIT`, `DRAW_WELL`, `DRAW_GIRDER` and similar names are not those source functions. No claim of an implemented well, girder, precast-arch or full PWD catalogue follows from this LISP.

The corrected inventory reports **57 static drawing-command occurrences**, **250 distinct assignment symbols** and **143 numeric atom occurrences** for this listing. Those are source-level facts; loops and conditionals mean they are not runtime entity counts. Zero candidate layer-like strings in this inventory does not mean the program draws no relevant geometry.

## Source-to-code mapping and decisions

| Source routine / fact | Existing BridgeCAD location | Decision |
|---|---|---|
| `opn` / `reed`: read parameters before drawing | Existing Excel reader, typed project model and Python catalogue | Preserve one validated model. Do not introduce a second global `gad.txt` source of truth. A future legacy importer should be an explicit adapter. |
| `hpos` / `vpos`: offsets from chainage and datum | `bridgecad_draw/dxf_engine.py::CoordMapper` | Already present. Added tests for relative metre-to-mm displacement and explicit plot offsets. |
| `h2pos` / `v2pos`: section ratio `scale1 / scale2` | CoordMapper scale factors and current per-sheet plotting helpers | Added a ratio invariant. Keep model units separate from paper-space scale. |
| `st`: one global dimension style | `dxf_engine.py` style registration / `pmb100` | Already present. Verify plotted text height and dimension values; do not copy model-space constants directly as paper millimetres. |
| `layout` and `cs`: grid and surveyed chainage/RL profile | Long-section renderer and survey/profile data paths | Keep grid/layout independent of model geometry. A full source-versus-output fixture still needs actual survey input. |
| `pier`: skewed member lengths and multi-view construction | Plan, cross-section, long-section and detail renderers | Reuse verified formulas per member and view. Do not apply `1/cos(skew)` indiscriminately to every plan dimension. |
| `abt1`: front/back transition RLs and toe batter | `bridgecad_core/geometry/abutment_profiles.py::battered_side_outline` | Incorporated three optional geometry inputs with validation and source-derived regression checks. Existing defaults retain the former outline. |
| Derived/unverified map | Reference documentation only | Excluded from executable capabilities and geometry oracles. |

## Applied code enrichment

### 1. Comment-aware, reproducible source inventory

The inventory utility now distinguishes code symbols, quoted strings and comments; handles line and nested block comments; records SHA-256; and collects actual `setq` assignment targets rather than values. Its report calls drawing commands *static occurrences*, not emitted entities. Candidate layer strings remain explicitly heuristic.

Run without executing any AutoLISP:

```powershell
python scripts/refs_lisp.py "ATTACHED ASSETS/LISP_Solid_Slab_GAD_In_Toto.lsp" -o artifacts/lisp_inventory.md
```

This is a lexical inventory, not an AutoLISP interpreter, syntax validator, full def-use analysis or geometric acceptance tool. Quoted forms and control flow still require review before attributing runtime behavior.

### 2. Restore independent abutment transition levels in the geometry helper

The source's relevant relationships are:

- Upper front run: `(capb - alfbl) / alfb`.
- Lower/toe transition run: `(alfbl - altbl) / altb`.
- Back run: `(capb - albbl) / albb`.

The previous helper simplified `alfbl == altbl` and `albbl == altbl`, eliminating both independent break levels. The patch adds:

| New helper argument | Unit | Source adapter relationship |
|---|---|---|
| `front_break_h_m` | m above footing top | `alfbl - altbl` |
| `back_break_h_m` | m above footing top | `albbl - altbl` |
| `toe_batter_1n` | dimensionless 1:n | `altb` |

Both break heights default to zero; toe batter defaults to one and has no effect when the lower transition height is zero. The helper validates finite break heights within its resolved stem height and finite positive batter denominators. It retains the existing 0.5 m minimum stem-height behavior rather than changing that unrelated legacy rule.

These arguments are implemented and tested in the core helper. **They are not yet wired to workbook columns, API payloads, catalogue overrides or browser controls.** Do not advertise `--set front_break_h_m=...` as supported until the schema/mapper/sheet paths implement it.

Illustrative regression call, not a bridge-design recommendation:

```python
from bridgecad_core.geometry.abutment_profiles import battered_side_outline

profile = battered_side_outline(
    2.0, cap_w_m=1.0, cap_d_m=0.5,
    face_batter_1n=3.0, back_batter_1n=4.0,
    toe_m=0.5, foot_d_m=1.0, above_m=0.4, dirt_w_m=0.3,
    front_break_h_m=0.6, back_break_h_m=0.4, toe_batter_1n=2.0,
)
```

The test independently checks the upper-front run `1.4/3`, lower-front run `0.6/2` and back run `1.6/4`, with the corresponding transition elevations. It does not merely check that a polygon exists.

## Archive inconsistencies that must not become production defaults

1. The listing uses `lspan` at its pier/superstructure entry without a corresponding assignment found in that listing. Do not silently invent a uniform span from total length when the project can have unequal spans.
2. `reed` sets `hs = vs = 1`, then `hhs = vvs = 1000`. The introductory principle saying conversion is always `1000 / scale` is not the literal implementation there. Preserve model units and plotting scale as separate contracts.
3. The legacy transforms add the numeric `left`/`datum` as graph-origin offsets. That is a plotting convention, not permission to mix metres and millimetres in the physical model. CoordMapper provides explicit offsets.
4. `abt1` explicitly replaces some cosine denominators with one in its side/elevation construction while using sine/cosine shifts in plan. A blanket skew correction would double-transform or misproject some views.
5. The source is a collection of fragments, including top-level calculations between function definitions and unresolved contextual variables. It has not been certified to load or execute correctly in AutoCAD.
6. The folder contains no verified `gad.txt` input fixture or matching original LISP-generated DWG/DXF. Static agreement cannot establish full output parity without them.

## Next wiring patch, with acceptance gates

| Step | Required change | Gate |
|---|---|---|
| 1 | Add optional, named transition-height and toe-batter fields to the current typed model / workbook contract | Old workbooks retain previous output; invalid finite/range inputs fail clearly |
| 2 | Map source RLs to relative heights using the same footing datum | No raw RL is passed as a relative height; units tested |
| 3 | Pass the fields through the existing Python sheet renderers | Old default fixture unchanged; nonzero transitions alter the intended vertices |
| 4 | Add equivalent browser fields and canonical mapping | Python/JS numeric parity for the same fixture; no second formula source |
| 5 | Add member-specific skew fixtures | Test zero, nominal and maximum supported skew; support axes and dimensions agree |
| 6 | Compare LISP-produced and BridgeCAD-produced outputs from identical, authorized inputs | Entity semantics, numeric dimensions, annotations and view composition reviewed |
| 7 | Extend only to bridge families the source actually supports | Keep PSC box/arch/well/other PWD families on their own verified references |

Do not replace working nine-sheet orchestration with the archived AutoCAD command sequence. Treat the LISP as a source reference and regression oracle for its supported formulas.

## Validation performed

- Focused source-inventory, coordinate-invariant and abutment tests: **22 passed** (one external pytest-plugin deprecation warning).
- The existing abutment-shape test file is included in that count.
- The actual archive's 13-function list and absence of the derived map's names are checked.
- Source hashes were recorded; original .lsp, .txt and .md assets were not modified.
- `git diff --check` passed for the changed code/documentation.
- No AutoCAD/AutoLISP execution, full reference-drawing comparison or engineering approval was performed.

## Apply this Markdown patch on Windows

The following diff is incremental to the inspected checkout. Code files affected: reference inventory, core abutment helper, focused tests and LISP-baseline documentation. No previous renderer/landing changes are overwritten by this patch.

1. Save this Markdown file and copy it into the repository's docs folder.
2. Extract the single diff block below into a temporary patch file.
3. Check reverse applicability first (already applied), then forward applicability. Stop on conflicts.
4. Apply, run the focused tests and inspect the diff. Do not push or release without reviewing it.

PowerShell example, executed by you on your Windows computer:

```powershell
$Repo = 'E:\Rajkumar\BridgeCAD-Enterprise-Suite'
$Guide = (Resolve-Path '.\BRIDGECAD_ATTACHED_ASSETS_LISP_PATCH.md').Path
$Text = [System.IO.File]::ReadAllText($Guide)
$Match = [regex]::Match($Text, '(?ms)^```diff\r?\n(.*?)^```\s*$')
if (-not $Match.Success) { throw 'No patch block found.' }
$Patch = Join-Path $env:TEMP 'bridgecad-attached-assets-lisp.patch'
[System.IO.File]::WriteAllText($Patch, $Match.Groups[1].Value, [System.Text.UTF8Encoding]::new($false))
Push-Location $Repo
try {
    git apply --reverse --check $Patch 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host 'Already applied.'; return }
    git apply --check $Patch
    if ($LASTEXITCODE -ne 0) { throw 'Patch conflicts; reconcile files without overwriting local changes.' }
    git apply $Patch
    if ($LASTEXITCODE -ne 0) { throw 'Patch application failed.' }
    $Target = Join-Path $Repo 'docs\BRIDGECAD_ATTACHED_ASSETS_LISP_PATCH.md'
    if ([System.IO.Path]::GetFullPath($Guide) -ne [System.IO.Path]::GetFullPath($Target)) { Copy-Item $Guide $Target }
    git diff --check
    if ($LASTEXITCODE -ne 0) { throw 'Review whitespace diagnostics.' }
    python -m pytest tests/refs/test_lisp_assets.py tests/draw/test_abutment_shape_families.py -q
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed; inspect the results before committing.' }
} finally { Pop-Location }
```

Use the project's established virtual environment or installation so the workspace packages are importable. The validation here used explicit package paths for refs, draw and core.

## Incremental implementation diff

```diff
diff --git a/packages/bridgecad-refs/bridgecad_refs/lisp_baseline.py b/packages/bridgecad-refs/bridgecad_refs/lisp_baseline.py
--- a/packages/bridgecad-refs/bridgecad_refs/lisp_baseline.py
+++ b/packages/bridgecad-refs/bridgecad_refs/lisp_baseline.py
@@ -1,25 +1,18 @@
 """Inventory an AutoLISP GAD source without executing it.
 
-Regex-level only: AutoLISP has no stable grammar worth importing for this, and
-the questions the audit asks are lexical — which entities are emitted, which
-layers are named, which values are parameters versus constants.
+Lexical inspection only: comments and string literals are distinguished from
+code symbols. No AutoLISP is executed, and static command occurrences must not
+be interpreted as emitted-entity counts or engineering capability.
 """
 
 from __future__ import annotations
 
 import re
+import hashlib
 from dataclasses import dataclass, field
 from pathlib import Path
 
-_ENTITY = re.compile(
-    r'\(\s*command\s+"(?P<cmd>LINE|PLINE|RECTANG|CIRCLE|TEXT|MTEXT|HATCH|DIMLINEAR|INSERT)"',
-    re.IGNORECASE,
-)
 _LAYER = re.compile(r'"(?P<layer>[A-Z][A-Z0-9_-]*(?:-[A-Z0-9]+)+)"')
-_SETQ = re.compile(r"\(\s*setq\b", re.IGNORECASE)
-_NUMERIC_LITERAL = re.compile(r"(?<![\w.])(?P<num>-?\d+\.\d+)(?![\w.])")
-_DEFUN = re.compile(r"\(\s*defun\s+(?P<name>[^\s()]+)", re.IGNORECASE)
-
 # Entities whose presence the audit cares about, matched against layer names
 _GEOMETRY_OF_INTEREST = {
     "wearing_coat": re.compile(r"WEAR|WC|ASPH|SURFAC", re.IGNORECASE),
@@ -37,58 +30,119 @@
     setq_names: list[str] = field(default_factory=list)
     numeric_literal_count: int = 0
     interest_hits: dict[str, list[str]] = field(default_factory=dict)
+    sha256: str = ""
+
+
+def _tokens(text: str) -> list[tuple[str, str]]:
+    """Read lexical tokens only; never evaluate AutoLISP or open its data files.
+
+    Ignore line and nested block comments. Keep quoted strings separate from
+    symbols so prose and strings cannot invent definitions or assignments.
+    """
+    tokens: list[tuple[str, str]] = []
+    i = 0
+    while i < len(text):
+        ch = text[i]
+        if ch.isspace() or ch == "\ufeff":
+            i += 1
+        elif text.startswith(";|", i):
+            depth = 1
+            i += 2
+            while i < len(text) and depth:
+                if text.startswith(";|", i):
+                    depth += 1
+                    i += 2
+                elif text.startswith("|;", i):
+                    depth -= 1
+                    i += 2
+                else:
+                    i += 1
+            if depth:
+                raise ValueError("Unterminated AutoLISP block comment")
+        elif ch == ";":
+            end = text.find("\n", i)
+            i = len(text) if end < 0 else end + 1
+        elif ch == '"':
+            i += 1
+            value = ""
+            while i < len(text) and text[i] != '"':
+                if text[i] == "\\" and i + 1 < len(text):
+                    value += text[i + 1]
+                    i += 2
+                else:
+                    value += text[i]
+                    i += 1
+            if i >= len(text):
+                raise ValueError("Unterminated AutoLISP string")
+            tokens.append(("string", value))
+            i += 1
+        elif ch in "()'":
+            tokens.append((ch, ch))
+            i += 1
+        else:
+            end = i
+            while i < len(text) and not text[i].isspace() and text[i] not in "();'\"":
+                i += 1
+            tokens.append(("atom", text[end:i]))
+    return tokens
+
+
+def _expression_end(tokens: list[tuple[str, str]], index: int) -> int:
+    while index < len(tokens) and tokens[index][0] == "'":
+        index += 1
+    if index >= len(tokens):
+        return index
+    if tokens[index][0] != "(":
+        return index + 1
+    depth = 1
+    index += 1
+    while index < len(tokens) and depth:
+        if tokens[index][0] == "(":
+            depth += 1
+        elif tokens[index][0] == ")":
+            depth -= 1
+        index += 1
+    return index
+
+
+def _setq_from_tokens(tokens: list[tuple[str, str]]) -> list[str]:
+    names: list[str] = []
+    for i in range(len(tokens) - 1):
+        if tokens[i][0] != "(" or (tokens[i + 1][0] != "atom" or tokens[i + 1][1].lower() != "setq"):
+            continue
+        j = i + 2
+        while j < len(tokens) and tokens[j][0] != ")":
+            if tokens[j][0] != "atom" or j + 1 >= len(tokens) or tokens[j + 1][0] == ")":
+                break
+            names.append(tokens[j][1])
+            j = _expression_end(tokens, j + 1)
+    return names
 
 
 def _setq_symbols(text: str) -> list[str]:
-    """Symbols bound by each ``(setq ...)`` form.
-
-    ``setq`` takes ``name value`` pairs and values may be nested lists, so a
-    flat regex cannot find the form's end.  Scan instead: after ``setq``, walk
-    the text tracking paren depth and collect the atoms at depth 1 — those are
-    the bound names interleaved with their literal values; numeric atoms and
-    nested-list contents are not names.
-    """
-    names: list[str] = []
-    for m in _SETQ.finditer(text):
-        i = m.end()
-        depth = 1
-        token = ""
-        while i < len(text) and depth > 0:
-            ch = text[i]
-            if ch == "(":
-                depth += 1
-                token = ""
-            elif ch == ")":
-                depth -= 1
-                token = ""
-            elif depth == 1 and not ch.isspace():
-                token += ch
-            elif ch.isspace() and token:
-                if not _NUMERIC_LITERAL.fullmatch(token) and not token.startswith('"'):
-                    names.append(token)
-                token = ""
-            i += 1
-        if (
-            token
-            and depth <= 1
-            and not _NUMERIC_LITERAL.fullmatch(token)
-            and not token.startswith('"')
-        ):
-            names.append(token)
-    return names
+    return _setq_from_tokens(_tokens(text))
 
 
 def inventory(path: str | Path) -> LispInventory:
-    text = Path(path).read_text(encoding="utf-8", errors="replace")
-    inv = LispInventory(path=str(path))
-
-    inv.defuns = [m.group("name") for m in _DEFUN.finditer(text)]
-    for m in _ENTITY.finditer(text):
-        cmd = m.group("cmd").upper()
-        inv.entity_counts[cmd] = inv.entity_counts.get(cmd, 0) + 1
-    inv.layers = sorted({m.group("layer") for m in _LAYER.finditer(text)})
-    inv.setq_names = _setq_symbols(text)
-    inv.numeric_literal_count = len(_NUMERIC_LITERAL.findall(text))
+    raw = Path(path).read_bytes()
+    text = raw.decode("utf-8-sig", errors="replace")
+    tokens = _tokens(text)
+    # AutoLISP symbols are case-insensitive; string content keeps its case.
+    tokens = [(kind, value.lower() if kind == "atom" else value) for kind, value in tokens]
+    inv = LispInventory(path=str(path), sha256=hashlib.sha256(raw).hexdigest())
+    commands = {"LINE", "PLINE", "RECTANG", "CIRCLE", "TEXT", "MTEXT", "HATCH", "DIMLINEAR", "INSERT"}
+    for i in range(len(tokens) - 2):
+        if tokens[i][0] != "(":
+            continue
+        if tokens[i + 1] == ("atom", "defun") and tokens[i + 2][0] == "atom":
+            inv.defuns.append(tokens[i + 2][1])
+        if tokens[i + 1] == ("atom", "command") and tokens[i + 2][0] == "string":
+            cmd = tokens[i + 2][1].upper()
+            if cmd in commands:
+                inv.entity_counts[cmd] = inv.entity_counts.get(cmd, 0) + 1
+    inv.layers = sorted({value for kind, value in tokens if kind == "string" and _LAYER.fullmatch('"' + value + '"')})
+    inv.setq_names = _setq_from_tokens(tokens)
+    inv.numeric_literal_count = sum(bool(re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", value)) for kind, value in tokens if kind == "atom")
 
     for key, pattern in _GEOMETRY_OF_INTEREST.items():
         inv.interest_hits[key] = [layer for layer in inv.layers if pattern.search(layer)]
@@ -105,26 +159,34 @@
     lines = [
         "# LISP baseline inventory",
         "",
-        f"Files: {len(inventories)} · entities emitted: {total_entities} · "
-        f"distinct layers: {len(layers)} · `setq` symbols: {len(names)}",
+        f"Files: {len(inventories)} · static drawing-command occurrences: {total_entities} · "
+        f"candidate layer-like strings: {len(layers)} · `setq` symbols: {len(names)}",
+        "",
+        "Static inspection only: no AutoCAD execution, runtime entity count, or geometric fidelity is established.",
+        "",
+        "## Source provenance",
+        "",
+        "| source | SHA-256 | functions observed |",
+        "| --- | --- | --- |",
+        *[f"| `{i.path}` | `{i.sha256}` | {', '.join(f'`{n}`' for n in i.defuns)} |" for i in inventories],
         "",
         "## Parametrisation",
         "",
-        "Numeric literals versus `setq` symbols is the parametrisation signal:",
-        "literals in geometry code mean the value was hard-coded.",
+        "Counts exclude comments and keep literal values distinct from assigned symbols.",
+        "Numeric constants alone do not establish a defect; review their meaning and units.",
         "",
         f"- numeric literals: {sum(i.numeric_literal_count for i in inventories)}",
         f"- `setq` symbols: {len(names)}",
         "",
         "## Geometry of interest",
         "",
-        "| element | layers found in the LISP |",
+        "| element | candidate layer-like strings |",
         "| --- | --- |",
     ]
     for key in _GEOMETRY_OF_INTEREST:
         hits = sorted({h for i in inventories for h in i.interest_hits[key]})
         lines.append(f"| {key} | {', '.join(f'`{h}`' for h in hits) or '**none**'} |")
-    lines += ["", "## Layers named", ""]
+    lines += ["", "## Candidate layer-like strings", ""]
     lines += [f"- `{layer}`" for layer in layers]
     return "\n".join(lines) + "\n"
 
diff --git a/packages/bridgecad-core/bridgecad_core/geometry/abutment_profiles.py b/packages/bridgecad-core/bridgecad_core/geometry/abutment_profiles.py
--- a/packages/bridgecad-core/bridgecad_core/geometry/abutment_profiles.py
+++ b/packages/bridgecad-core/bridgecad_core/geometry/abutment_profiles.py
@@ -13,6 +13,7 @@
 from __future__ import annotations
 
 from typing import Any
+import math
 
 __all__ = [
     "Family",
@@ -105,6 +106,9 @@
     foot_d_m: float = 1.0,
     above_m: float = 0.98,
     dirt_w_m: float = 0.3,
+    front_break_h_m: float = 0.0,
+    back_break_h_m: float = 0.0,
+    toe_batter_1n: float = 1.0,
 ) -> BatteredSide:
     """LISP abt1() 14-vertex battered abutment side profile, in metres.
 
@@ -113,8 +117,19 @@
     batters as 1:n (horizontal run = height / n).  The polygon is drawn for
     the +x orientation (A2): face anchor at x=0, dirt wall outward at +x;
     mirror x for A1.
+
+    Optional front/back break heights preserve the source's independent
+    ``alfbl``/``albbl`` levels above footing top ``altbl``. Zero defaults keep
+    the former simplified outline. ``toe_batter_1n`` is source ``altb``.
+    These are geometry inputs, not a foundation design or a global default.
     """
     stem_h = max(float(stem_h_m), 0.5)
+    for name, value in (("front_break_h_m", front_break_h_m), ("back_break_h_m", back_break_h_m)):
+        if not math.isfinite(value) or not 0 <= value <= stem_h:
+            raise ValueError(f"{name} must be finite and between 0 and stem height")
+    for name, value in (("face_batter_1n", face_batter_1n), ("back_batter_1n", back_batter_1n), ("toe_batter_1n", toe_batter_1n)):
+        if not math.isfinite(value) or value <= 0:
+            raise ValueError(f"{name} must be finite and positive")
     y_cap_bot = foot_d_m + stem_h  # cap soffit
     y_foot_top = foot_d_m  # altbl — stem bottom / footing top
     y_foot_bot = 0.0  # y8
@@ -123,11 +138,13 @@
 
     x1 = 0.0  # riverside face anchor
     x3 = cap_w_m  # cap earth-side edge
-    x5 = x3 + stem_h / face_batter_1n  # gentle battered stem-back face
-    x6 = x5  # alfbl == altbl → toe drop nil (LISP default)
+    # abt1(): capb -> alfbl uses alfb, then alfbl -> altbl uses altb.
+    # Break heights are measured above footing top, not absolute RL values.
+    x5 = x3 + (stem_h - front_break_h_m) / face_batter_1n
+    x6 = x5 + front_break_h_m / toe_batter_1n
     x7 = x6 + toe_m  # toe
     x14 = x1 - dirt_w_m  # dirt wall outer face (earthside, −x in this frame)
-    x12 = x14 - stem_h / back_batter_1n  # steep battered face
+    x12 = x14 - (stem_h - back_break_h_m) / back_batter_1n
     x10 = x12 - toe_m
 
     pts = [
@@ -135,14 +152,14 @@
         (x1, y_cap_top),
         (x3, y_cap_top),
         (x3, y_cap_bot),
-        (x5, y_foot_top),
+        (x5, y_foot_top + front_break_h_m),
         (x6, y_foot_top),
         (x7, y_foot_top),
         (x7, y_foot_bot),
         (x10, y_foot_bot),
         (x10, y_foot_top),
         (x12, y_foot_top),
-        (x12, y_foot_top),
+        (x12, y_foot_top + back_break_h_m),
         (x14, y_cap_bot),
         (x14, y_rtl),
     ]
diff --git a/tests/refs/test_lisp_assets.py b/tests/refs/test_lisp_assets.py
new file mode 100644
--- /dev/null
+++ b/tests/refs/test_lisp_assets.py
@@ -0,0 +1,89 @@
+"""Static archive provenance and independently stated legacy invariants."""
+from pathlib import Path
+import hashlib
+import pytest
+from bridgecad_refs.lisp_baseline import inventory, report
+from bridgecad_draw.dxf_engine import CoordMapper
+from bridgecad_core.geometry.abutment_profiles import battered_side_outline
+
+ROOT = Path(__file__).resolve().parents[2]
+
+
+def test_inventory_ignores_comments_strings_and_collects_assignment_targets(tmp_path):
+    path=tmp_path/'source.lsp'
+    path.write_text('''; (defun fake () (command "LINE"))
+;| (defun blocked ()) ;| (setq nested 9) |; |;
+(defun REAL ()
+ (setq x 1 y (+ x 2) note "semi; (defun invented ())")
+ (SETQ points '(1 2 3) alias x)
+ (command "LINE" '(0 0) '(1 1) ""))
+''')
+    inv=inventory(path)
+    assert inv.defuns==['real']
+    assert inv.setq_names==['x','y','note','points','alias']
+    assert inv.entity_counts=={'LINE':1}
+    assert inv.sha256==hashlib.sha256(path.read_bytes()).hexdigest()
+    assert 'static drawing-command occurrences' in report([inv])
+
+
+def test_string_escape_does_not_turn_comment_into_code(tmp_path):
+    path=tmp_path/'source.lsp'
+    path.write_text('(setq label "a \\\"quoted\\\" ; value" x 3)')
+    assert inventory(path).setq_names==['label','x']
+
+
+@pytest.mark.parametrize('text',[';| no terminator','(setq x "no terminator)'])
+def test_unterminated_literals_report_error(tmp_path,text):
+    path=tmp_path/'bad.lsp';path.write_text(text)
+    with pytest.raises(ValueError,match='Unterminated'):inventory(path)
+
+
+def test_actual_preservation_copy_has_thirteen_observed_functions():
+    path=ROOT/'ATTACHED ASSETS/LISP_Solid_Slab_GAD_In_Toto.lsp'
+    inv=inventory(path)
+    assert inv.defuns==['opn','reed','vpos','hpos','v2pos','h2pos','st','layout','cs','pier','pt','p2t','abt1']
+    assert not {'draw_well','draw_girder','gad_init'} & set(inv.defuns)
+
+
+@pytest.mark.parametrize('delta',[0.125,1.0,3.75])
+def test_lisp_relative_metre_to_mm_invariant(delta):
+    # reed(): hs=vs=1; hpos/vpos use 1000 * the difference from origin.
+    mapper=CoordMapper(datum_rl=100,origin_ch=1200,x_offset=20,y_offset=30)
+    assert mapper.hpos(1200+delta)-mapper.hpos(1200)==pytest.approx(delta*1000)
+    assert mapper.vpos(100+delta)-mapper.vpos(100)==pytest.approx(delta*1000)
+
+
+def test_lisp_section_ratio_invariant():
+    # v2pos/h2pos multiply the relative displacement by scale1/scale2.
+    mapper=CoordMapper(h_scale=100/25,v_scale=100/25)
+    assert mapper.h_len(1.25)==5000
+    assert mapper.v_len(.5)==2000
+
+
+def test_abt1_two_face_batters_preserve_independent_runs():
+    # abt1: x5-x3=(capb-alfbl)/alfb; x14-x12=(capb-albbl)/albb.
+    profile=battered_side_outline(2,cap_w_m=1,cap_d_m=.5,face_batter_1n=3,
+        back_batter_1n=10,toe_m=.5,foot_d_m=1,above_m=.4,dirt_w_m=.3)
+    assert len(profile.points)==14
+    assert profile.points[4][0]-profile.points[2][0]==pytest.approx(2/3)
+    assert profile.points[12][0]-profile.points[10][0]==pytest.approx(.2)
+    assert profile.points[6]==pytest.approx((1+2/3+.5,1))
+    assert profile.points[7][1]==0
+    assert profile.cap_bot_y==3
+
+
+def test_abt1_independent_break_levels_and_toe_batter():
+    p=battered_side_outline(2,cap_w_m=1,cap_d_m=.5,face_batter_1n=3,
+        back_batter_1n=4,toe_m=.5,foot_d_m=1,above_m=.4,dirt_w_m=.3,
+        front_break_h_m=.6,back_break_h_m=.4,toe_batter_1n=2)
+    # Source abt1: upper front run=(3-1.6)/3; lower run=(1.6-1)/2.
+    assert p.points[4]==pytest.approx((1+1.4/3,1.6))
+    assert p.points[5]==pytest.approx((1+1.4/3+.6/2,1))
+    # Source back run=(3-1.4)/4 from dirt-wall x=-.3.
+    assert p.points[10]==pytest.approx((-.3-1.6/4,1))
+    assert p.points[11]==pytest.approx((-.3-1.6/4,1.4))
+
+
+@pytest.mark.parametrize('kwargs',[{'front_break_h_m':-1},{'back_break_h_m':3},{'toe_batter_1n':0},{'front_break_h_m':float('nan')},{'back_batter_1n':float('inf')}])
+def test_abt1_rejects_invalid_breaks_and_batters(kwargs):
+    with pytest.raises(ValueError):battered_side_outline(2,**kwargs)
diff --git a/docs/lisp-baseline.md b/docs/lisp-baseline.md
--- a/docs/lisp-baseline.md
+++ b/docs/lisp-baseline.md
@@ -20,3 +20,32 @@
 
 Rows 1–3 are geometry; a `superseded` there needs an IRC clause, not an
 opinion.
+
+## ATTACHED ASSETS audit and bounded incorporation (2026-11-13)
+
+The checked-in folder contains a preserved .lsp listing, raw article text,
+an explanatory Markdown archive and an explicitly derived/unverified module
+map. The observed LISP list has 13 functions, not the explanatory archive's
+nine-function claim. The derived map must not be used as source evidence for
+well, girder or other absent modules.
+
+Run the real archive through the comment-aware inventory without executing it:
+
+```powershell
+python scripts/refs_lisp.py "ATTACHED ASSETS/LISP_Solid_Slab_GAD_In_Toto.lsp" -o artifacts/lisp_inventory.md
+```
+
+The inventory now records SHA-256, excludes comments/string literals from
+function detection, reports only assignment targets for setq, and distinguishes
+static command occurrences from runtime entity counts. Layer-like strings are
+only lexical candidates; their absence does not prove missing geometry.
+
+The core battered_side_outline helper now accepts optional front_break_h_m,
+back_break_h_m and toe_batter_1n. They preserve source abt1's independent alfbl,
+albbl and altb geometry; zero transition-height defaults retain the old outline.
+These new inputs are not yet exposed through the workbook, API, catalogue or
+browser controls. Their explicit model/mapper/renderer wiring requires further
+fixtures and engineering review. No original asset was changed or executed.
+
+See BRIDGECAD_ATTACHED_ASSETS_LISP_PATCH.md for the source-to-code mapping,
+known archive inconsistencies, complete incremental diff and application gates.
```

This patch has been applied only in the available checkout. It has not been written directly to E: or pushed to your GitHub repository.
