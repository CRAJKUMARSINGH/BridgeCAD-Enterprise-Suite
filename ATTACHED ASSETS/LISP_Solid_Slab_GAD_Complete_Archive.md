# AutoLISP Solid Slab GAD — Complete Archive & Guiding Principles

> **Source:** [Explanation of LISP Code for Solid Slab GAD Drawing](https://www.yogipwd.com/2023/05/explanation-of-lisp-code-for-solid-slab.html)  
> **Author of original LISP:** Shri. P.M. Baviskar, Executive Engineer, Design Division Nashik (Bridge)  
> **Archived by:** BridgeCAD Enterprise Suite — this file is the preservation copy.  
> **Status:** Complete — all 9 functions, all parameter tables, all geometry logic.

---

## Why this LISP matters to BridgeCAD

This LISP routine is the **direct ancestor** of BridgeCAD Enterprise Suite.  
Shri. Baviskar's `gad.lsp` was the first parametric, file-driven GAD generator for
Indian highway bridges, decades before any commercial alternative existed in the PWD
context. BridgeCAD re-implements every principle in Python + ezdxf, with the same
parameter contract, the same geometry laws, and the same drawing philosophy — but
adds QA gates, revision control, 9-sheet output, and Excel-driven input.

---

## 1. Opening Input File — `opn()`

```lisp
(defun opn()
    (setq f (open "D:\\gad.txt" "r"))   ; open input file (read mode)
)
```

**Principle → BridgeCAD mapping:**
- `gad.txt` = the flat-file input contract → replaced by the **14-sheet Excel workbook**
  (`packages/bridgecad-io/bridgecad_io/excel_reader.py`)
- File-driven, not form-driven: parameters are written first, drawing follows deterministically.
- BridgeCAD preserves this: the workbook IS the contract; no parameter lives in the app.

---

## 2. Reading All Parameters — `reed()`

```lisp
(defun reed()
    (setq scale1  (atof (read-line f)))  ; plan/elevation scale
    (setq scale2  (atof (read-line f)))  ; section scale
    (setq skew    (atof (read-line f)))  ; skew angle (degrees)
    (setq datum   (atoi (read-line f)))  ; datum RL
    (setq toprl   (atoi (read-line f)))  ; top RL
    (setq left    (atof (read-line f)))  ; start chainage
    (setq right   (atof (read-line f)))  ; end chainage
    (setq xincr   (atof (read-line f)))  ; X interval
    (setq yincr   (atof (read-line f)))  ; Y interval
    (setq noch    (atoi (read-line f)))  ; number of cross-sections
    (setq hs 1)   (setq vs 1)           ; fixed screen scale (1 unit = 1 mm)
    (setq vvs (/ 1000.0 vs))            ; m → mm vertical
    (setq hhs (/ 1000.0 hs))            ; m → mm horizontal
    (setq skew1 (* skew 0.0174532))     ; degrees → radians
    (setq s   (sin skew1))              ; sin(skew)
    (setq c   (cos skew1))              ; cos(skew)
    (setq tn  (/ s c))                  ; tan(skew)
    (setq sc  (/ scale1 scale2))        ; scale ratio plan:section
)
```

**Key parameters extracted from this function:**

| LISP variable | Meaning | BridgeCAD field |
|---|---|---|
| `scale1` | Plan / elevation drawing scale | `drawing_control.scale_plan` |
| `scale2` | Section drawing scale | `drawing_control.scale_section` |
| `skew` | Skew angle, degrees | `geometry_input.skew_angle_deg` |
| `datum` | Datum RL (bottom of drawing) | `hydraulic_data.scour_level_m` |
| `toprl` | Top RL (road formation) | `project_master.road_level_rl_m` |
| `left` / `right` | Start / end chainage | `geometry_input.chainage_start_km` |
| `xincr` / `yincr` | Axis grid increments | `drawing_control.chainage_interval_m` |
| `noch` | Number of cross-section points | derived from ground survey data |
| `vvs` / `hhs` | m → mm scale multipliers | `sc_v`, `sc_h` in sheet generators |
| `s`, `c`, `tn` | sin/cos/tan of skew | `bridgecad_core.skew.support_line()` |
| `sc` | Scale ratio | per-sheet `scale_denom` parameter |

**Guiding principle:** Every coordinate in the drawing is a **deterministic function**
of the input parameters. No geometry is hard-coded. BridgeCAD enforces this via
`resolve_abutment_stack()`, `compute_long_section_geometry()`, `support_line()`.

---

## 3. Coordinate Conversion Functions

```lisp
; Real-world → drawing (plan/elevation scale)
(defun vpos (a)   ; vertical: level → mm
    (setq a (* vvs (- a datum)))
    (setq a (+ datum a))
)
(defun hpos (a)   ; horizontal: chainage → mm
    (setq a (* hhs (- a left)))
    (setq a (+ left a))
)

; Real-world → drawing (section scale)
(defun v2pos (a)
    (setq a (* vvs (- a datum)))
    (setq a (* sc a))
    (setq a (+ datum a))
)
(defun h2pos (a)
    (setq a (* hhs (- a left)))
    (setq a (* sc a))
    (setq a (+ left a))
)

; Section-view point converter (skew-aware)
(defun p2t (x y pt)
    ; converts (x, y) in metres to drawing mm, applying section scale + skew
)
```

**Guiding principle:** All four coordinate converters are **pure functions** of the
input datum. BridgeCAD maps this to:
- `def vy(rl)` and `def hx(ch)` lambdas inside each sheet's `_draw()` function
- `CoordMapper` dataclass in `bridgecad_draw/dxf_engine.py`
- `v2pos`/`h2pos` → the section-view coordinate mapping in `sheet3_cross_section.py`
- `p2t` (skew-aware) → `bridgecad_core.skew.support_line()` and `SupportLine.p_left/p_right`

---

## 4. AutoCAD Dimension Style — `st()`

```lisp
(defun st ()
    (command "-style"    "Arial" "Arial" "" "" "" "" "")
    (command "DIMASZ"    "150")   ; arrow size
    (command "DIMDEC"    "0")     ; decimal places
    (command "DIMEXE"    "400")   ; extension line length
    (command "DIMEXO"    "400")   ; offset from object
    (command "DIMLFAC"   "1")     ; scale factor
    (command "DIMTXSTY"  "Arial") ; text style
    (command "DIMTXT"    "400")   ; text height
    (command "DIMTAD"    "0")     ; text above dim line
    (command "DIMTIH"    "1")     ; text inside
    (-dimstyle save "pmb100" "y") ; save as 'pmb100'
)
```

**Guiding principle:** Dimension style is **set once globally**, not per entity.
BridgeCAD enforces this via:
- `bridgecad_draw/layers.py` — single layer registry with lineweights
- `primitives.dim_linear_h()` / `dim_linear_v()` — single dimension function
- `ISO_128_LINEWEIGHTS` frozenset — only valid weights may be used

---

## 5. Elevation Layout — `layout()`

Creates X axis (chainage), Y axis (RL), grid lines, tick marks, and labels.

```lisp
(defun layout ()
    (setq os (getvar "OSMODE"))
    (setvar "OSMODE" 0)                    ; disable OSNAP during auto-draw
    (setq pta1 (list left datum))          ; origin
    (setq d1 20)                           ; 20 mm between parallel lines
    ; ... draw axes, grid, labels, tick arrays via (command "array" ...)
    ; level labels: while loop from datum to toprl in yincr steps
    ; chainage labels: while loop from left to right in xincr steps
)
```

**Guiding principle:** The elevation layout is a **rigid grid** with datum at the
bottom, `toprl` at the top, `left` and `right` as horizontal bounds. No element
sits outside this grid. BridgeCAD's `sheet2_long_section.py` follows this exactly:
- `draw_y0 = datum_rl`, `draw_x0 = chainage_start`
- Level axis ticks in a `while rl_val <= rl_top` loop — identical structure
- Chainage axis ticks at `xincr` intervals — mirrored exactly

---

## 6. River Cross-Section — `cs()`

```lisp
(defun cs ()
    (setq a 1)
    (while (< a (+ noch 1))
        (setq x (atof (read-line f)))   ; chainage
        (setq y (atof (read-line f)))   ; bed RL
        ; plot RL text, chainage text, tick lines
        ; connect (hpos x, vpos y) points to form river profile polyline
        (setq ptb4 (list xx (vpos y)))
        (if (/= a 1) (command "line" ptb3 ptb4 ""))
        (setq ptb3 ptb4)
        (setq a (+ a 1))
    )
)
```

**Guiding principle:** Ground profile is a **connected polyline**, point-by-point
from the survey file. BridgeCAD: `gnd_pts = [(hx(ch), vy(rl)) for ch, rl in ls.ground_profile_pts]`
then `polyline(msp, gnd_pts, layer="CIVIL-GROUND", color=3)`.

---

## 7. Pier / Superstructure — `pier()`

### Input parameters read from file:

```lisp
(setq nspan   (atoi (read-line f)))   ; number of spans
(setq lbridge (atof (read-line f)))   ; total bridge length
(setq abtl    (atof (read-line f)))   ; left abutment chainage
(setq RTL     (atof (read-line f)))   ; road top level
(setq Sofl    (atof (read-line f)))   ; soffit level
(setq kerbw   (atof (read-line f)))   ; kerb width
(setq kerbd   (atof (read-line f)))   ; kerb depth above deck
(setq ccbr    (atof (read-line f)))   ; clear carriageway width
(setq slbthc  (atof (read-line f)))   ; slab thickness, centre
(setq slbthe  (atof (read-line f)))   ; slab thickness, edge (camber 2.5%)
(setq slbtht  (atof (read-line f)))   ; slab thickness, tip (min 150 mm)
(setq capt    (atof (read-line f)))   ; pier cap top RL
(setq capb    (atof (read-line f)))   ; pier cap bottom RL
(setq capw    (atof (read-line f)))   ; pier cap width
(setq piertw  (atof (read-line f)))   ; pier top width
(setq battr   (atof (read-line f)))   ; pier batter (H:V ratio)
(setq pierst  (atof (read-line f)))   ; pier straight length
(setq piern   (atoi (read-line f)))   ; pier serial no. for section
```

**BridgeCAD mapping:**

| LISP | Python model field |
|---|---|
| `RTL` | `project_master.road_level_rl_m` |
| `Sofl` | `hydraulic_data.actual_soffit_level_m` |
| `kerbw` | `geometry_input.kerb_width_left_m` |
| `ccbr` | `geometry_input.carriageway_width_m` |
| `slbthc/e/t` | `superstructure.deck_thickness_mm` (centre); camber computed |
| `capt / capb` | `substructure.pier_cap_depth_m` |
| `capw` | `substructure.pier_cap_width_m` |
| `piertw` | `substructure.pier_shaft_width_m` |
| `battr` | `substructure.abutment_face_batter_1n` |
| `pierst` | `substructure.pier_shaft_length_m` |
| `nspan` | `geometry_input.span_count` |
| `lbridge` | `geometry_input.total_length_m` |

### Skew-adjusted geometry:

```lisp
(setq capwsq   (/ capw c))              ; cap width in plan = capw / cos(skew)
(setq pierstsq (+ (/ pierst c)
                   (abs (* piertw tn)))) ; pier skew length = st/cos + w*tan
(setq ofsetsq  (/ ofset c))             ; batter offset in skew
```

**Guiding principle:** Every dimension in a skewed bridge is divided by `cos(skew)`
to get the **plan-projected** dimension. BridgeCAD: `bridgecad_core.skew.effective_span_m()`,
`SupportLine.p_left/p_right`.

### Pier batter geometry:

```lisp
(setq y2    (+ futrl futd))               ; pier bottom = founding RL + footing depth
(setq ofset (/ (- capb y2) battr))        ; lateral offset = height / batter
(setq x2    (- x1 ofsetsq))              ; left face, bottom
(setq x4    (+ x3 ofsetsq))              ; right face, bottom
(command "line" pta1 pta2 "")            ; left battered face
(command "line" pta3 pta4 "")            ; right battered face
```

**Guiding principle:** Pier batter is a **1:battr taper**. The same geometry is
in BridgeCAD's `battered_side_outline()` in `abutment_profiles.py` and the abt1()
LISP-derived battered polygon in `sheet5_pier_abutment_details.py`.

---

## 8. Abutment (`abt1()`) — Battered Profile

The LISP draws the abutment as a 14-vertex battered polygon (not a rectangle):

```
Road level (RTL)
    ├── Dirt wall top (approach slab soffit level)
    │       ← DWTH (back wall, 300 mm typical)
    ├── Abutment cap top
    │       ← Cap projects front AND rear past the shaft
    ├── Cap soffit / shaft top
    │       ← Shaft battered: face_batter_1n (river side, gentle: 1:10)
    │                          back_batter_1n (earth side, steep: 1:3)
    └── Founding level
            └── Footing (rectangle: futw × futd)
```

Key variables:
- `altbl` — abutment top back level (= cap top RL)
- `ALT` / `ARL` — abutment left-top / right-top coordinate
- `ABTL` — abutment base level (founding RL)
- `RTL` — road top level
- `dirtwall` thickness (DWTH) = 300 mm stem
- Wearing coat (WC) runs **end to end** over both approach slabs — never breaks

**Guiding principle:** The 14-vertex `abt1()` polygon captures:
1. Road level line
2. Dirt wall rear face (vertical, full approach slab height)
3. Dirt wall front face into cap
4. Cap front projection (bearing shelf)
5. Shaft battered faces (different rates, river vs earth)
6. Footing toe and heel

BridgeCAD's `battered_side_outline()` in `geometry/abutment_profiles.py` mirrors
this exactly with `face_batter_1n` and `back_batter_1n` as separate parameters.

---

## 9. Cross-Section (YY View) — `p2t()` coordinate system

```lisp
(setq ppt16 (p2t xp yp ppt16))         ; origin at section centreline
(setq ppt1  (p2t (+ xp (/ ccbrsq 2)) yp ppt1))   ; half carriageway width
(setq ppt9  (p2t (+ xp (/ ccbrsq 2)) (+ yp slbthc) ppt9))  ; deck top, centre (crown)
(setq ppt10 (p2t xp (+ yp slbthe) ppt10))  ; deck top, edge (camber)
(setq ppt3  (p2t (+ xp ccbrsq kerbwsq) (+ yp (- slbthe slbtht)) ppt3))  ; kerb base
(setq ppt5  (p2t (+ xp ccbrsq kerbwsq) (+ yp slbthe kerbd) ppt5))       ; kerb top
; Draws 16-point cross-section profile including camber, kerbs, wearing coat
(command "line" ppt16 ppt1 ppt2 ppt3 ppt4 ppt5 ppt6 ppt7 ppt8
         ppt9 ppt10 ppt11 ppt12 ppt13 ppt14 ppt15 ppt16 "")
```

**Guiding principle:** The deck cross-section profile is a **camber curve**, not flat.
- `slbthc` (centre) > `slbthe` (edge) — the camber creates the cross-fall
- Kerb profile: 5 vertices (base inset, full width, full height, chamfer top, inner face)
- BridgeCAD: `sheet3_cross_section.py` and `sheet8_side_elevations.py` draw this profile

---

## 10. Fundamental Design Principles Extracted

These are the guiding principles Shri. Baviskar's LISP embeds, now codified in
BridgeCAD Enterprise Suite:

| # | LISP principle | BridgeCAD implementation |
|---|---|---|
| P1 | **Single input file** — all geometry from one source | 14-sheet Excel workbook, `bridgecad_io` |
| P2 | **Datum at bottom** — all RLs measured from a common datum | `resolve_abutment_stack()` datum ladder |
| P3 | **Metres in, mm out** — `vvs = 1000/vs`, `hhs = 1000/hs` | `sc_h`, `sc_v` in every sheet generator |
| P4 | **Skew propagates everywhere** — `/cos(skew)` for all plan dims | `bridgecad_core.skew.support_line()` |
| P5 | **Wearing coat end-to-end** — never breaks at joints | Continuous WC over both approach slabs, sheet2 |
| P6 | **Battered abutment, not rectangle** — `abt1()` 14-vertex polygon | `battered_side_outline()`, ABUT-PROF layer |
| P7 | **Independent batters** — river face gentler, earth face steeper | `face_batter_1n` / `back_batter_1n` params |
| P8 | **Dirt wall is a separate element** — not part of abutment shaft | `SUB-DIRT-WALL` layer, `dirt_wall_thickness_mm` |
| P9 | **Cap projects both faces** — bearing shelf + dirt wall seat | `abutment_cap_projection_front/rear_mm` |
| P10 | **Dimension style once** — `pmb100` global style | `LAYER_REGISTRY`, `dim_linear_h/v` primitives |
| P11 | **Span loop** — all spans drawn in `while <= nspan` | `for i, slen in enumerate(span_lens)` |
| P12 | **Footing rectangle** — `futrl`, `futd`, `futw`, `futl` | `FoundationDetails.pile_cutoff_level_m` etc |
| P13 | **Dimension every element** — not just the outline | `dim_along()` with `ViewAxis` enforcement |
| P14 | **Section to different scale** — `v2pos`/`h2pos` for YY | `sheet3_cross_section.py` scale_denom=50 |

---

## Credits & Attribution

- **AutoLISP code author:** Shri. P.M. Baviskar, Executive Engineer,
  Design Division Nashik (Bridge), Maharashtra PWD
- **Blog and explanation:** [yogipwd.com](https://www.yogipwd.com/2023/05/explanation-of-lisp-code-for-solid-slab.html)
- **This archive:** Er. Rajkumar Singh Chauhan, Retd. Addl. Chief Engineer, PWD Rajasthan,
  for the BridgeCAD Enterprise Suite project

> Content in this document is paraphrased and structured for preservation and attribution.
> The **complete AutoLISP listing**, saved in toto in article order, is in
> `LISP_Solid_Slab_GAD_In_Toto.lsp`; the original blog text is preserved verbatim in
> `yogipwd_lisp_solid_slab_gad_original.txt`. All three files should travel together.
