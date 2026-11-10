# GAD Module Mapping — DERIVED / UNVERIFIED COPY

> ## ⚠️ NOT THE ARCHIVED `gad.lsp` — DO NOT CITE AS SOURCE
>
> This table was pasted into the project by the repository owner from an
> **outside/generated source**. It is **not** from
> [Explanation of LISP Code for Solid Slab GAD Drawing](https://www.yogipwd.com/2023/05/explanation-of-lisp-code-for-solid-slab.html)
> and it does **not** describe Shri. P.M. Baviskar's archived `gad.lsp`.
>
> **Verified discrepancy.** A search of `ATTACHED ASSETS/` returns **zero** matches
> for every function name in this table — `GAD_INIT`, `DRAW_WELL`, `DRAW_PIER`,
> `DRAW_ABUT`, `DRAW_GIRDER`, `DRAW_DECK`, `GAD_DIM`, `GEN_TEXT`, `steining`. The
> preserved `gad.lsp` contains only:
>
> `opn()` · `reed()` · `vpos()` · `hpos()` · `v2pos()` · `h2pos()` · `st()` ·
> `layout()` · `cs()` · `pier()` · `pt()` · `p2t()` · `abt1()`
>
> It is a **solid-slab** routine (open footings/piles) with no well foundation, no
> girders, no crash barriers and no HFL/OFL/LWL block.
>
> **Purpose of this file.** Kept only as a *derived / aspirational* module map so the
> intent is not lost. It must not be presented as the archived LISP. For the
> source-faithful mapping see the function-by-function table in
> [`README.md`](../README.md) and the complete listing in
> [`LISP_Solid_Slab_GAD_In_Toto.lsp`](LISP_Solid_Slab_GAD_In_Toto.lsp).
>
> The table below is reproduced **verbatim** as pasted; nothing has been corrected.

---

Structured mapping of the basic guiding principles as written in the source article
for `gad.lsp` by Shri. P.M. Baviskar, showing each core functional module mapped
directly to its architectural BridgeCAD drawing engine code segment.

## GAD Module Mappings & Drawing Segments

| Sl. No. | AutoLISP Function / Module (gad.lsp) | Core Guiding Principle & Architectural Segment | BridgeCAD Drawing Engine Code Segment |
|---|---|---|---|
| 1 | `(defun c:GAD_INIT () ...)` | **Environment Setup:** Standardizes the architectural drawing canvas, scaling parameters, layer structures (e.g., Centerline, Foundation, Text), and system variables (OSMODE, CMDECHO). | `(command "-layer" "m" "BRIDGE_GAD" "c" "7" "" "")`<br>`(setq scale (getreal "\nEnter GAD Scale (e.g. 100): "))` |
| 2 | `(defun c:DRAW_WELL () ...)` | **Substructure Principle:** Plots the foundation elements based on soil strata requirements. Standardizes well curb thickness and steining reinforcement profiles. | `(command "pline" p1 p2 p3 p4 "c")`<br>`(command "hatch" "ANSI31" 1.0 0.0 (entlast) "")` |
| 3 | `(defun c:DRAW_PIER () ...)` | **Vertical Load Transmission:** Governs structural symmetry. Automatically centers the pier shaft, calculates the batter/taper ratio, and scales the pier cap dimensions to match bearing spaces. | `(command "line" pier_cl pier_top "")`<br>`(command "offset" (/ pier_width 2.0) ...)` |
| 4 | `(defun c:DRAW_ABUT () ...)` | **Earth Retention & Support:** Defines structural boundaries at the endpoints. Generates the dirt wall, ballast wall, weep holes, and the dynamic angle of the wing walls. | `(command "pline" top_abut heel toe "c")`<br>`(command "line" dirt_wall_top dirt_wall_bottom "")` |
| 5 | `(defun c:DRAW_GIRDER () ...)` | **Superstructure Span Layout:** Calculates depth-to-span ratios according to load distributions. Draws the longitudinal GAD elevation of PSC/Steel girders with precise bearing locations. | `(command "rectang" brg_start brg_end)`<br>`(command "line" girder_top girder_bottom "")` |
| 6 | `(defun c:DRAW_DECK () ...)` | **Wearing Surface & Drainage:** Standardizes the cross-sectional geometry of the bridge deck, including cross-fall percentages, footpaths, crash barriers, and drainage spouts. | `(command "pline" deck_start slope deck_end ...)`<br>`(command "mirror" (entlast) "" cl_axis "")` |
| 7 | `(defun c:GAD_DIM () ...)` | **Geometric Clarity:** Implements standardized dimension styles (DIMSTYLE). Automates linear, aligned, and cumulative dimensioning across spans, clearances, and formation levels. | `(command "dimlinear" p_start p_end text_pos)`<br>`(setvar "DIMSCALE" scale)` |
| 8 | `(defun c:GEN_TEXT () ...)` | **Information Hierarchy:** Automatically prints structural labels, span annotations, hydraulic data (HFL, OFL, LWL), and the general technical notes block. | `(command "text" "s" "Standard" text_pt text_ht 0.0 label)`<br>`(command "chprop" (entlast) "" "la" "GAD_TEXT" "")` |

---

If you want to tailor or modify this routine, let me know:

- Would you like the full source code logic for a specific block (e.g., the Pier Cap tapering formulas)?
- Are you adapting this to handle skew bridges or standard orthogonal alignments?
