;;; ============================================================================
;;;  gad.lsp  —  General Arrangement Drawing (GAD) generator for Solid Slab
;;;              bridges, written in AutoLISP.
;;; ----------------------------------------------------------------------------
;;;  Author of the original AutoLISP :  Shri. P.M. Baviskar
;;;                                      Executive Engineer,
;;;                                      Design Division Nashik (Bridge),
;;;                                      Maharashtra PWD
;;;  Source article                   :  https://www.yogipwd.com/2023/05/
;;;                                      explanation-of-lisp-code-for-solid-slab.html
;;;  Archived for                     :  BridgeCAD Enterprise Suite
;;;                                      (Er. Rajkumar Singh Chauhan,
;;;                                       Retd. Addl. Chief Engineer, PWD Rajasthan)
;;; ----------------------------------------------------------------------------
;;;  THIS FILE IS THE "IN TOTO" (COMPLETE) PRESERVATION COPY.
;;;
;;;  Every AutoLISP fragment published in the source article is reproduced here,
;;;  in the article's own order:
;;;
;;;      opn()  ->  reed()  ->  vpos()/hpos()  ->  v2pos()/h2pos()  ->  st()
;;;             ->  layout()  ->  cs()  ->  pier()  ->  pt()/p2t()  ->  abt1()
;;;
;;;  Nothing has been invented.  Where the published article repeats a fragment
;;;  (it prints each routine once inline in the narrative and once again inside
;;;  the explanation block) or leaves a variable undefined, that fact is marked
;;;  in-line with  "; [article: ...]"  so the record stays faithful to source.
;;; ============================================================================
;;;
;;; ----------------------------------------------------------------------------
;;;  BASIC GUIDING PRINCIPLES  (as stated in the source article)
;;; ----------------------------------------------------------------------------
;;;  GP1   ONE flat input file (gad.txt) drives the entire drawing.
;;;  GP2   Read every parameter ONCE, up front  (reed()).
;;;  GP3   Metres in, millimetres out :  vvs = hhs = 1000 / scale.
;;;  GP4   Degrees in, radians out   :  skew1 = skew * 0.0174532.
;;;  GP5   All levels share ONE datum (vpos); all chainages share ONE start
;;;        chainage (hpos).
;;;  GP6   A section view is the SAME transform multiplied by ONE scale ratio
;;;        sc = scale1 / scale2   (v2pos / h2pos).
;;;  GP7   Every plan dimension of a skewed bridge is divided by cos(skew)
;;;        e.g.  capwsq = capw / c.
;;;  GP8   Dimension style is set ONCE, globally  (st() -> "pmb100").
;;;  GP9   The elevation plotting grid (X axis, Y axis, BED LEVEL, CHAINAGE,
;;;        level ticks, chainage ticks) is laid out first and separately
;;;        (layout()).
;;;  GP10  The river bed profile is a polyline through the surveyed
;;;        (chainage, RL) points  (cs()).
;;;  GP11  The pier is drawn in elevation + plan + side view from ONE parameter
;;;        block  (pier()).
;;;  GP12  The abutment is built from computed points — a 14-vertex battered
;;;        polygon — never a fixed rectangle  (abt1()).
;;;  GP13  Skew shifts plan coordinates by
;;;             x = L/2 * sin(phi) ,   y = L/2 * (1 - cos(phi)).
;;;  GP14  Every element is dimensioned  (a DIMLINEAR follows every shape).
;;; ----------------------------------------------------------------------------
;;; ============================================================================


;;; ============================================================================
;;;  1.0  OPENING INPUT AND OUTPUT FILES  —  opn()
;;; ============================================================================

(defun opn()

    (setq f (open "D:\\gad.txt" "r"))   ; open input file

    ;(setq h (open "E:\\program files\\AutoCAD 2004\\h.txt" "w"))
    ; open output file (commented)

)


;;; ============================================================================
;;;  2.0  READING DATA REQUIRED FOR LAYOUT  —  reed()
;;; ============================================================================

(defun reed()

    (setq scale1 (atof (read-line f))) ; scale for plan/elevation
    (setq scale2 (atof (read-line f))) ; scale for sections

    (setq skew  (atof (read-line f)))  ; skew angle
    (setq datum (atoi (read-line f)))  ; datum level
    (setq toprl (atoi (read-line f)))  ; top RL

    (setq left  (atof (read-line f)))  ; start chainage
    (setq right (atof (read-line f)))  ; end chainage
    (setq xincr (atof (read-line f)))  ; X interval
    (setq yincr (atof (read-line f)))  ; Y interval

    (setq noch (atoi (read-line f)))   ; total chainages

    ; fixed scale for screen plotting
    (setq hs 1)
    (setq vs 1)

    ; conversion (m to mm)
    (setq vvs (/ 1000.0 vs))
    (setq hhs (/ 1000.0 hs))

    ; skew angle conversion
    (setq skew1 (* skew 0.0174532))
    (setq s (sin skew1))
    (setq c (cos skew1))

)

; --- Additional calculations in reed() ---------------------------------------
(setq tn (/ s c))            ; tangent of skew angle
(setq sc (/ scale1 scale2))  ; scale ratio

; --- Debug lines (commented in the article) ----------------------------------
;(princ (list "Datum=" datum " toprl=" toprl
;             " left=" left " right=" right
;             " xincr=" xincr " yincr=" yincr
;             " vvs=" vvs " hhs=" hhs) h)
;(princ "\n" h)


;;; ============================================================================
;;;  3.0  VERTICAL / HORIZONTAL POSITION FUNCTIONS  —  vpos() / hpos()
;;; ============================================================================

(defun vpos (a)
  (setq a (* vvs (- a datum)))
  (setq a (+ datum a))
)


(defun hpos (a)
  (setq a (* hhs (- a left)))
  (setq a (+ left a))
)


;;; ============================================================================
;;;  4.0  SECTION-SCALE POSITION FUNCTIONS  —  v2pos() / h2pos()
;;; ============================================================================

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


;;; ============================================================================
;;;  5.0  SETTING AutoCAD DIMENSION STYLE  —  st()
;;; ============================================================================

(defun st ()
  (command "-style" "Arial" "Arial" "" "" "" "" "")
  (command "DIMASZ" "150")
  (command "DIMDEC" "0")
  (command "DIMEXE" "400")
  (command "DIMEXO" "400")
  (command "DIMLFAC" "1")
  (command "DIMTXSTY" "Arial")
  (command "DIMTXT" "400")
  (command "DIMTAD" "0")
  (command "DIMTIH" "1")
  (command "-dimstyle" "save" "pmb100" "y")
)


;;; ============================================================================
;;;  6.0  PLOTTING LAYOUT OF ELEVATION (X axis, Y axis, etc.)  —  layout()
;;; ============================================================================

(defun layout ()
  ; Save current OSNAP mode
  (setq os (getvar "OSMODE"))
  ; Turn off OSNAP
  (setvar "OSMODE" 0)

  ; Convert left to integer
  (setq left (- left (rem left 1.0)))

  ; Define axis points
  (setq pta1 (list left datum))
  (setq d1 20) ; Distance in mm between lines parallel to X axis
  (setq ptb1 (list left (- datum (* d1 scale1))))
  (setq pta2 (list (hpos right) datum))
  (setq ptb2 (list (hpos right) (- datum (* d1 scale1))))
  (setq ptc1 (list left (- datum (* d1 scale1 2))))
  (setq ptc2 (list (hpos right) (- datum (* d1 scale1 2))))
  (setq ptd1 (list left (vpos toprl)))

  ; Draw axes lines
  (command "line" pta1 pta2 "") ; X axis
  (command "line" ptb1 ptb2 "") ; parallel line below X axis
  (command "line" ptc1 ptc2 "") ; parallel line below X axis
  (command "line" ptc1 ptd1 "") ; Y axis

  ; Add axis labels
  (setq ptb3 (list (- left (* 25 scale1)) (- datum (* d1 0.5 scale1))))
  (command "text" ptb3 (* 2.5 scale1) 0 (princ "BED LEVEL"))

  (setq ptb3 (list (- left (* 25 scale1)) (- datum (* d1 1.5 scale1))))
  (command "text" ptb3 (* 2.5 scale1) 0 (princ "CHAINAGE"))

  ; Small Y-axis ticks
  (setq d2 2.5) ; half length of small line
  (setq pta1 (list (- left (* d2 scale1)) datum))
  (setq pta2 (list (+ left (* d2 scale1)) datum))
  (command "color" 7)
  (command "line" pta1 pta2 "")
  (setq e1 (entlast))

  ; Number of elevation increments
  (setq nov (- toprl datum))
  (setq nov (fix nov))
  (command "array" e1 "" "R" (+ nov 1) 1 vvs)

  ; Write elevation levels on Y axis
  (setq a 0)
  (setq n (/ nov yincr))
  (setq n (fix n))
  (while (< a (+ n 1))
    (setq lvl (+ datum (* a yincr)))
    (setq b1 (rtos lvl 2 3)) ; convert to 100.000 format
    (setq pta1 (list (- left (* 13 scale1)) (- (vpos lvl) (* 1.0 scale1))))
    (command "text" pta1 (* 2.0 scale1) 0 (princ b1))
    (setq a (+ a 1))
  )

  ; Write chainage on X axis
  (setq a 1)
  (setq noh (- right left))
  (setq n (/ noh xincr))
  (setq n (fix n))
  (while (< a (+ n 1))
    (setq ch (+ left (* a xincr)))
    (setq b1 (rtos ch 2 3))
    (setq d4 (* 2 d1))
    (setq d5 (- d4 2.0))
    (setq d6 (+ d1 2.0))
    (setq d7 (- d1 2.0))
    (setq d8 (- d4 4.0))
    (setq d9 (- d1 4.0))

    ; Draw chainage text
    (setq pta1 (list (+ scale1 (hpos ch)) (- datum (* d8 scale1))))
    (command "text" pta1 (* 2.0 scale1) 90 (princ b1))

    ; Draw small lines on X axis
    (setq pta1 (list (hpos ch) (- datum (* d4 scale1))))
    (setq pta2 (list (hpos ch) (- datum (* d5 scale1))))
    (setq pta3 (list (hpos ch) (- datum (* d6 scale1))))
    (setq pta4 (list (hpos ch) (- datum (* d7 scale1))))
    (command "color" 7)
    (command "line" pta1 pta2 "")
    (command "line" pta3 pta4 "")

    (setq a (+ a 1))
  )
)


;;; ============================================================================
;;;  7.0  PLOTTING CROSS SECTION OF THE RIVER AND WRITING CHAINAGES  —  cs()
;;; ============================================================================

(defun cs ()
  (setq a 1) ; Initialize chainage counter

  ; Loop through all chainages
  (while (< a (+ noch 1))
    ; Read chainage and RL from file
    (setq x (atof (read-line f))) ; Chainage
    (setq y (atof (read-line f))) ; RL at chainage

    ; Convert numbers to strings for text display
    (setq b1 (rtos x 2 3)) ; Chainage as string
    (setq b2 (rtos y 2 3)) ; RL as string

    ; Get plotting positions
    (setq xx (hpos x))
    (setq pta1 (list (+ xx (* 0.9 scale1)) (- datum (* d8 scale1)))) ; Chainage text
    (setq pta2 (list (+ xx (* 0.9 scale1)) (- datum (* d9 scale1)))) ; RL text

    ; Write RL along X-axis
    (command "text" pta2 (* 2 scale1) 90 (princ b2))

    ; Check if chainage is a multiple of increment
    (setq b (rem (- x left) xincr))
    (if (/= b 0.0)
      (command "text" pta1 (* 1.8 scale1) 90 (princ b1)) ; Write chainage if not already written
    )

    ; Draw small vertical lines on X-axis
    (setq pta1 (list xx (- datum (* d4 scale1))))
    (setq pta2 (list xx (- datum (* d5 scale1))))
    (setq pta3 (list xx (- datum (* d6 scale1))))
    (setq pta4 (list xx (- datum (* d7 scale1))))
    (if (/= b 0.0) (command "line" pta1 pta2 ""))
    (if (/= b 0.0) (command "line" pta3 pta4 ""))

    ; Draw line from X-axis to datum
    (setq pta5 (list xx (- datum (* 2 scale1))))
    (setq pta6 (list xx datum))
    (command "line" pta5 pta6 "")

    ; Draw river cross-section line
    (setq ptb4 (list xx (vpos y)))
    (if (/= a 1) (command "line" ptb3 ptb4 ""))
    (setq ptb3 ptb4)

    ; Increment chainage counter
    (setq a (+ a 1))
  )
)


;;; ============================================================================
;;;  8.0  PLOTTING PIER IN ELEVATION, PLAN AND SIDE VIEW  —  pier()
;;; ============================================================================

;;; --- 8.1  Reading data ------------------------------------------------------

(defun pier ()
  ; Read bridge and pier data from file "f"
  (setq nspan (atoi (read-line f)))   ; Number of spans
  (setq lbridge (atof (read-line f))) ; Total length of bridge
  (setq abtl (atof (read-line f)))    ; Chainage of left abutment
  (setq RTL (atof (read-line f)))     ; Road top level
  (setq rtl2 (- RTL (* 30 sc)))       ; Adjusted RTL for drawing (distance from datum to section top)
  (setq Sofl (atof (read-line f)))    ; Soffit level
  (setq kerbw (atof (read-line f)))   ; Width of kerb at deck top
  (setq kerbd (atof (read-line f)))   ; Depth of kerb above deck top
  (setq ccbr (atof (read-line f)))    ; Clear carriageway width
  (setq slbthc (atof (read-line f)))  ; Slab thickness at center
  (setq slbthe (atof (read-line f)))  ; Slab thickness at edge (camber 2.5%)
  (setq slbtht (atof (read-line f)))  ; Slab thickness at tip (usually 0.150)
  (setq capt (atof (read-line f)))    ; Pier cap top RL
  (setq capb (atof (read-line f)))    ; Pier cap bottom RL
  (setq capw (atof (read-line f)))    ; Cap width
  (setq piertw (atof (read-line f)))  ; Pier top width
  (setq battr (atof (read-line f)))   ; Pier batter
  (setq pierst (atof (read-line f)))  ; Straight length of pier
  (setq piern (atoi (read-line f)))   ; Pier serial number (shown in cross-section)

  ; Horizontal and vertical positions for drawing elevation view
  (setq x1 (hpos abtl))
  (setq y1 (vpos RTL))
  ; [article: `lspan` is used here but never defined anywhere in the article]
  (setq x2 (hpos (+ abtl lspan)))

;;; --- 8.2-8.4  Drawing the superstructure, pier caps and piers ----------------

  ; Set initial positions for elevation view
  ; [article: these three lines repeat the ones just read in §8.1]
  (setq x1 (hpos abtl))
  (setq y1 (vpos RTL))
  (setq x2 (hpos (+ abtl lspan)))
  (setq y2 (vpos sofl))

  ; Draw rectangle representing SS (superstructure)
  (setq pta1 (list (+ x1 25.0) y1))
  (setq pta2 (list (- x2 25.0) y2))
  (setq ptaa1 (list (+ x1 50) (+ y1 800)))
  (command "rectangle" pta1 pta2) ; draw SS rectangle
  (setq g1 (entlast))              ; get last entity (SS)

  ; Adjust starting point for pier caps
  (setq x1 (+ abtl lspan))
  (setq capwsq (/ capw c))
  (setq x1 (- x1 (/ capwsq 2)))
  (setq x2 (+ x1 capwsq))
  (setq x1 (hpos x1))
  (setq x2 (hpos x2))
  (setq y1 (vpos capt))
  (setq y2 (vpos capb))
  (setq pta1 (list x1 y1))
  (setq pta2 (list x2 y2))
  (command "rectangle" pta1 pta2) ; draw rectangle for pier cap
  (setq g2 (entlast))

  ; Initialize span chainage
  (setq spans abtl)

  ; Loop to draw piers for each span
  (setq a 1)
  (while (<= a nspan)
    (setq span1 (atof (read-line f))) ; read individual span length
    (setq futrl (atof (read-line f)))  ; founding RL of pier
    (setq futd (atof (read-line f)))   ; depth of footing
    (setq futw (atof (read-line f)))   ; width of footing
    (setq futl (atof (read-line f)))   ; length of footing along direction
    (setq spane (+ spans span1))       ; end chainage of span

    ; Draw SS rectangle for current span
    (setq x1 (hpos spans))
    (setq y1 (vpos RTL))
    (setq x2 (hpos spane))
    (setq y2 (vpos sofl))
    (setq pta1 (list (+ x1 25.0) y1)) ; 25 mm expansion gap
    (setq pta2 (list (- x2 25.0) y2))
    (command "rectangle" pta1 pta2)   ; SS rectangle

    ; Draw dimension line for span
    (setq pta1 (list x1 y1))
    (setq pta2 (list x2 y1))
    (setq ptaa1 (list (+ x1 50) (+ y1 2000)))
    (command "DIMLINEAR" pta1 pta2 ptaa1)

    ; Update starting x1 for next span
    (setq x1 spane)
    (setq spans spane)
    (setq a (+ a 1))

;;; --- 8.4  Drawing pier caps, piers and footings in elevation -----------------

    ; --- Pier Caps (skewed if needed) ---
    (setq capwsq (/ capw c))       ; skew width = normal width / cos(angle)
    (setq x1 (- x1 (/ capwsq 2)))
    (setq x2 (+ x1 capwsq))
    (setq x1 (hpos x1))
    (setq x2 (hpos x2))
    (setq y1 (vpos capt))
    (setq y2 (vpos capb))
    (setq pta1 (list x1 y1))
    (setq pta2 (list x2 y2))
    (command "rectangle" pta1 pta2) ; draw rectangle for pier cap

    ; Dimension for cap width
    (setq ptaa1 (list (+ x1 50) (- y2 400)))
    (command "DIMEXE" "300")
    (command "DIMEXO" "200")
    (command "DIMLINEAR" (list x1 y2) pta2 ptaa1)

    ; --- Start drawing pier ---
    (setq xc spane)
    (setq piertwsq (/ piertw c))
    (setq x1 (- xc (/ piertwsq 2))) ; left point of pier top
    (setq x3 (+ x1 piertwsq))       ; right point of pier top
    (setq y2 (+ futrl futd))        ; pier bottom = footing RL + depth
    (setq ofset (/ (- capb y2) battr)) ; pier batter = height / batter
    (setq ofsetsq (/ ofset c))
    (setq x2 (- x1 ofsetsq))        ; left bottom of pier
    (setq x4 (+ x3 ofsetsq))        ; right bottom of pier
    (setq y4 y2)

    (setq pta1 (pt x1 capb pta1))
    (setq pta2 (pt x2 y2 pta2))
    (setq pta3 (pt x3 capb pta3))
    (setq pta4 (pt x4 y4 pta4))

    (command "line" pta1 pta2 "")   ; left side of pier
    (command "line" pta3 pta4 "")   ; right side of pier

    ; Dimension for pier width
    (setq ptaa1 (list (+ (hpos x2) 50) (- (vpos y2) 300)))
    (command "DIMEXE" "200")
    (command "DIMEXO" "100")
    (command "DIMLINEAR" pta2 pta4 ptaa1)

    ; --- Footing ---
    (setq futwsq (/ futw c))
    (setq x5 (- xc (/ futwsq 2))) ; left point of footing
    (setq x6 (+ x5 futwsq))       ; right point of footing
    (setq y6 futrl)               ; bottom of footing
    (setq y5 y4)                  ; top of footing

    (setq pta5 (pt x5 y5 pta5))
    (setq pta6 (pt x6 y6 pta6))
    (command "rectangle" pta5 pta6) ; draw rectangle to represent footing

    (setq pt1 (list (hpos x5) (vpos y6))) ; store point for reference

    (setq pt2 pta6)

    (setq pt3 (list (+ (hpos x5) 100) (- (vpos y6) 600)))  ; pt3 coordinate

    (command "DIMEXE" "200")
    (command "DIMEXO" "400")  ; giving depth and width dimensions

    (command "DIMLINEAR" pt1 pt2 pt3)

    (setq pt2 pt1)
    (setq pt1 pta5)

    (setq pt3 (list (- (hpos x5) 700) (- (vpos y5) 100)))

    (command "DIMEXE" "400")
    (command "DIMEXO" "500")

    (command "DIMLINEAR" pt1 pt2 pt3)

;;; --- 8.5  Drawing pier in plan ----------------------------------------------

    (setq x7 (- xc (/ futw 2)))  ; left top point of footing
    (setq x8 (+ x7 futw))
    (setq yc (- datum 30.0))
    (setq y7 (+ yc (/ futl 2)))
    (setq y8 (- y7 futl))

    (setq pta7 (pt x7 y7 pta7))
    (setq pta8 (pt x8 y8 pta8))

    (command "rectangle" pta7 pta8)  ; draw rectangle representing footing

    (setq g2 (entlast))

    (setq pt1 (list (hpos x7) (vpos y8)))
    (setq pt2 pta8)
    (setq pt3 (list (+ (hpos x7) 100) (- (vpos y8) 600)))

    (command "DIMEXE" "200")
    (command "DIMEXO" "400")  ; giving length and width dimensions

    (command "DIMLINEAR" pt1 pt2 pt3)
    (setq g3 (entlast))

    (setq pt1 (list (hpos x8) (vpos y7)))
    (setq pt2 pta8)
    (setq pt3 (list (+ (hpos x8) 700) (- (vpos y7) 100)))

    (command "DIMEXE" "200")
    (command "DIMEXO" "500")
    (command "DIMLINEAR" pt1 pt2 pt3)
    (setq g4 (entlast))

    (setq ptc (pt xc yc ptc))
    (Command "rotate" g2 g3 g4 "" ptc skew)  ; rotate footing in plan to angle 'skew'

    (setq pierstsq (+ (/ pierst c) (abs (* piertw tn))))  ; pier skew length = st/cos(phi) + w*tan(phi)

    (setq x1 (- xc (/ piertw 2)))  ; left point of pier top
    (setq x3 (+ x1 piertw))        ; right point of pier top
    (setq x2 (- x1 ofset))          ; left point of pier bottom
    (setq x4 (+ x3 ofset))          ; right point of pier bottom

    (setq y9 (+ yc (/ pierstsq 2)))
    (setq y10 (- y9 pierstsq))

    (setq pta9  (pt x2 y9  pta9))
    (setq pta10 (pt x2 y10 pta10))
    (setq pta11 (pt x1 y9  pta11))
    (setq pta12 (pt x1 y10 pta12))
    (setq pta13 (pt x3 y9  pta13))
    (setq pta14 (pt x3 y10 pta14))
    (setq pta15 (pt x4 y9  pta15))
    (setq pta16 (pt x4 y10 pta16))

    (command "line" pta9  pta10 "")
    (setq g1 (entlast))
    (command "line" pta11 pta12 "")
    (setq g2 (entlast))
    (command "line" pta13 pta14 "")
    (setq g3 (entlast))
    (command "line" pta15 pta16 "")
    (setq g4 (entlast))

    (setq y17 (+ y9 (/ piertw 2)))
    (setq y18 (+ y17 ofset))
    (setq y19 (- y10 (/ piertw 2)))
    (setq y20 (- y19 ofset))

    (setq pta17 (pt xc y17 pta17))
    (setq pta18 (pt xc y18 pta18))
    (setq pta19 (pt xc y19 pta19))
    (setq pta20 (pt xc y20 pta20))

    (command "arc" pta9  pta18 pta15)
    (setq g5 (entlast))
    (command "arc" pta11 pta17 pta13)
    (setq g6 (entlast))
    (command "arc" pta12 pta19 pta14)
    (setq g7 (entlast))

    (command "arc" pta10 pta20 pta16)
    (setq g8 (entlast))

    (command "DIMEXE" "200")
    (command "DIMEXO" "500")

    (setq pt3 (list (+ (hpos x4) 700) (- (vpos y9) 100)))
    (command "DIMLINEAR" pta15 pta16 pt3)
    (setq g9 (entlast))

    (setq pt3 (list (+ (hpos x1) 100) (+ (vpos y9) 700)))
    (command "DIMLINEAR" pta11 pta13 pt3)
    (setq g10 (entlast))

    (setq pt3 (list (+ (hpos x2) 100) (+ (vpos y9) 1000)))
    (command "DIMLINEAR" pta9 pta15 pt3)
    (setq g11 (entlast))

    (Command "rotate" g1 g2 g3 g4 g5 g6 g7 g8 g9 g10 g11 "" ptc skew)
    ; rotate pier plan to skew angle

    (setq n a)
    (while (= n piern)        ; while loop 2
      (setq futprl futrl)     ; founding RL
      (setq futpd futd)       ; footing depth
      (setq futpw futw)       ; footing width
      (setq futpl futl)       ; footing length
      (setq n (+ n 1))
    )

    (setq a (+ 1 a))
    (setq spans spane)
  ) ; end first while loop

  ; 8.5  Drawing SS of last span
  (setq x1 (hpos spane))
  (setq y1 (vpos RTL))
  (setq x2 (hpos (+ abtl lbridge)))
  (setq y2 (vpos sofl))

  (setq pta1 (list (+ x1 25.0) y1))
  (setq pta2 (list (- x2 25.0) y2))
  (command "rectangle" pta1 pta2)
  ; SS rectangle drawn

  ; Dimension SS
  (setq pta1 (list x1 y1))
  (setq pta2 (list x2 y1))
  (setq ptaa1 (list (+ x1 50) (+ y1 2000)))
  (command "DIMLINEAR" pta1 pta2 ptaa1)

;;; --- 8.6  Drawing elevation and section YY -----------------------------------

  (setq xp (+ left 55))
  (setq yp rtl2)

  ; --- AutoLISP — Slab & pier cross section ---
  (setq ppt16 (p2t xp yp ppt16))

  (setq ccbrsq (/ ccbr c))

  (setq ppt1 (p2t (+ xp (/ ccbrsq 2)) yp ppt1))
  (setq ppt2 (p2t (+ xp ccbrsq) yp ppt2))

  (setq kerbwsq (/ kerbw c))

  (setq ppt3 (p2t (+ xp ccbrsq kerbwsq) (+ yp (- slbthe slbtht)) ppt3))
  (setq ppt4 (p2t (+ xp ccbrsq kerbwsq) (+ yp slbthe) ppt4))
  (setq ppt5 (p2t (+ xp ccbrsq kerbwsq) (+ yp slbthe kerbd) ppt5))

  (setq k1 (/ 0.05 c))     ; 50 mm in skew
  (setq k2 (/ 0.025 c))    ; 25 mm in skew

  (setq ppt6 (p2t (+ xp ccbrsq k1) (+ yp slbthe kerbd) ppt6))
  (setq ppt7 (p2t (+ xp ccbrsq k2) (+ yp slbthe kerbd -0.025) ppt7))
  (setq ppt8 (p2t (+ xp ccbrsq) (+ yp slbthe) ppt8))
  (setq ppt9 (p2t (+ xp (/ ccbrsq 2)) (+ yp slbthc) ppt9))
  (setq ppt10 (p2t xp (+ yp slbthe) ppt10))

  (setq ppt11 (p2t (- xp k2) (+ yp slbthe kerbd -0.025) ppt11))
  (setq ppt12 (p2t (- xp k1) (+ yp slbthe kerbd) ppt12))
  (setq ppt13 (p2t (- xp kerbwsq) (+ yp slbthe kerbd) ppt13))

  (setq ppt14 (list (car ppt13) (cadr ppt4)))
  (setq ppt15 (list (car ppt13) (cadr ppt3)))

  (command "line"
   ppt16 ppt1 ppt2 ppt3 ppt4 ppt5 ppt6 ppt7
   ppt8 ppt9 ppt10 ppt11 ppt12 ppt13 ppt14
   ppt15 ppt16 "")

  (command "line" ppt14 ppt10 "")
  (command "line" ppt8 ppt4 "")

  (setq diff (/ (- pierstsq ccbrsq) 2))
  (setq xp (- xp diff))

  (setq pedstl (- sofl capt))
  (setq yp (- yp pedstl))

  (setq ppt16 (p2t xp yp ppt16))

  (setq capd (- capt capb))

  (setq ppt17 (p2t (- xp (/ capw 2)) yp ppt17))
  (setq ppt18 (p2t (+ xp pierstsq (/ capw 2)) yp ppt18))
  (setq ppt19 (p2t (- xp (/ capw 2)) (- yp capd) ppt19))
  (setq ppt20 (p2t (+ xp pierstsq (/ capw 2)) (- yp capd) ppt20))

  (command "line" ppt17 ppt18 ppt20 ppt19 ppt17 "")

  (setq ppt21 (p2t (- xp (/ piertw 2)) (- yp capd) ppt21))
  (setq ppt22 (p2t xp (- yp capd) ppt22))
  (setq ppt23 (p2t (+ xp pierstsq) (- yp capd) ppt23))
  (setq ppt24 (p2t (+ xp pierstsq (/ piertw 2)) (- yp capd) ppt24))

  (setq xpc (+ xp (/ pierstsq 2)))

  (setq pierht (- capb futprl futpd))
  (setq pierbw (/ pierht battr))

  ; --- Pier geometry — AutoLISP code ---
  (setq pierbw (+ pierbw pierbw piertw))

  (setq h1 (- yp pierht capd))

  (setq ppt25 (p2t (- xpc (/ futpl 2)) h1 ppt25))
  (setq ppt26 (p2t (- xp (/ pierbw 2)) h1 ppt26))
  (setq ppt27 (p2t xp h1 ppt27))
  (setq ppt28 (p2t (+ xp pierstsq) h1 ppt28))
  (setq ppt29 (p2t (+ xp pierstsq (/ pierbw 2)) h1 ppt29))
  (setq ppt30 (p2t (+ xpc (/ futpl 2)) h1 ppt30))

  (setq h2 (- h1 futpd))

  (setq ppt31 (p2t (- xpc (/ futpl 2)) h2 ppt31))
  (setq ppt32 (p2t xpc h2 ppt32))
  (setq ppt33 (p2t (+ xpc (/ futpl 2)) h2 ppt33))

  (setq ppt2 (p2t (+ xp ccbrsq diff diff) yp ppt2))
  ; Redefined point ppt2 for skew bridges

  (command "line" ppt21 ppt26 "")
  (command "line" ppt16 ppt27 "")
  (command "line" ppt2 ppt28 "")
  (command "line" ppt24 ppt29 "")
  (command "line" ppt25 ppt30 ppt33 ppt31 ppt25 "")
  (command "line" ppt9 ppt32 "")

) ; End of pier subroutine


;;; ============================================================================
;;;  9.0  POINT CONVERSION SUBROUTINES  —  pt() / p2t()
;;; ============================================================================

(defun pt(a b z) ;subroutine to convert given point into point on graph

    (setq aa a)
    (setq aa (hpos aa))
    (setq bb b)
    (setq bb (vpos bb))
    (setq z (list aa bb))

)   ;defun pt is closed.
    ;(setq pta1 (pt (car nn1) (cadr nn1) pta1))


(defun p2t(a b z) ;subroutine to convert given point into point on graph

    (setq aa a)
    (setq aa (h2pos aa))
    (setq bb b)
    (setq bb (v2pos bb))
    (setq z (list aa bb))

)   ;defun p2t is closed.


;;; ============================================================================
;;;  10.0  LEFT ABUTMENT  —  abt1()
;;; ============================================================================

(defun abt1()

    ; 10.1 DATA
    ;(setq abtlen (atof (read-line f))) ; read length of abutment along the current

    (setq dwth (atof (read-line f)))   ; read dirtwall thickness.
    (setq alcw (atof (read-line f)))   ; read abutment left cap width (excluding d/w)
    (setq alcd (atof (read-line f)))   ; read abutment left cap depth
    (setq alfb (atof (read-line f)))   ; abt left front batter
    (setq alfbl (atof (read-line f)))  ; abt left front batter RL
    (setq altb (atof (read-line f)))   ; abt left toe batter
    (setq altbl (atof (read-line f)))  ; abt left toe batter level (footing top)
    (setq alfo (atof (read-line f)))   ; abutment left front offset to footing
    (setq alfd (atof (read-line f)))   ; abt left footing depth
    (setq albb (atof (read-line f)))   ; abt left back batter
    (setq albbl (atof (read-line f)))  ; abt left back batter RL

    ; 10.2
    (setq abtlen (+ ccbrsq kerbwsq kerbwsq))
    (setq x1 abtl)
    (setq alcwsq (/ alcw 1))           ; c changed to 1
    (setq x3 (+ x1 alcwsq))

    (setq capb (- capt alcd))
    (setq p1 (/ (- capb alfbl) alfb))
    (setq p1sq (/ p1 1))               ; c changed to 1
    (setq x5 (+ x3 p1sq))

    (setq p2 (/ (- alfbl altbl) altb))
    (setq p2sq (/ p2 1))               ; c changed to 1
    (setq x6 (+ x5 p2sq))

    (setq alfosq (/ alfo 1))           ; c changed to 1
    (setq x7 (+ x6 alfosq))

    (setq y8 (- altbl alfd))

    (setq dwthsq (/ dwth 1))           ; c changed to 1
    (setq x14 (- x1 dwthsq))

    (setq p3 (/ (- capb albbl) albb))
    (setq p3sq (/ p3 1))               ; c changed to 1
    (setq x12 (- x14 p3sq))

    (setq rt1s x12) ; ch. where left return starts in elevation
    (setq x10 (- x12 alfosq))

)

;;; --- 10.3  Elevation points of the abutment ----------------------------------

(setq pt1  (pt x1  rtl   pt1))    ; gives various points on elevation of abutment
(setq pt2  (pt x1  capt  pt2))
(setq pt3  (pt x3  capt  pt3))
(setq pt4  (pt x3  capb  pt4))
(setq pt5  (pt x5  alfbl pt5))
(setq pt6  (pt x6  altbl pt6))
(setq pt7  (pt x7  altbl pt7))
(setq pt8  (pt x7  y8    pt8))
(setq pt9  (pt x10 y8    pt9))
(setq pt10 (pt x10 altbl pt10))
(setq pt11 (pt x12 altbl pt11))
(setq pt12 (pt x12 albbl pt12))
(setq pt13 (pt x14 capb  pt13))
(setq pt14 (pt x14 rtl   pt14))
(setq pt15 (pt x12 rtl   pt15))

(command "line" pt1 pt2 pt3 pt4 pt5 pt6 pt7 pt8 pt9 pt10 pt11 pt12 pt13 pt14 pt1 "")
(command "line" pt13 pt4 "")
(command "line" pt10 pt7 "")
(command "line" pt12 pt15 pt14 "")


;;; --- 10.4  Drawing abutment left in plan -------------------------------------

(setq y20 (+ yc (/ abtlen 2)))     ; gives Y ordinate on D/S of abt
(setq y21 (- y20 abtlen))          ; gives Y ordinate on U/S of abt
(setq y16 (+ y20 0.15))            ; gives Y ordinate on D/S of footing
(setq y17 (- y21 0.15))            ; gives Y ordinate on U/S of footing

(setq footl (- y16 y17))
(setq footl (/ footl 2))
(setq x (* footl s))
(setq y (* footl (- 1 c)))

(setq pt16 (pt (- x10 x) (- y16 y) pt16))
(setq pt17 (pt (+ x10 x) (+ y17 y) pt17))
(setq pt18 (pt (- x7 x) (- y16 y) pt18))
(setq pt19 (pt (+ x7 x) (+ y17 y) pt19))

(setq pt14 (pt x14 rtl pta14))
(setq pt15 (pt x12 rtl pta15))

(command "line" pt16 pt17 pt19 pt18 pt16 "") ; drawing abt footing in plan

(setq xx (/ abtlen 2))
; due to skew , X and Y ordinates are shifted by:
; x = l/2 * sin(phi) , y = l/2(1-cos(phi))

(setq x (* xx s))
(setq y (* xx (- 1 c)))
(setq y20 (- y20 y))
(setq y21 (+ y21 y))

(setq pt20 (pt (- x12 x) y20 pt20))
(setq pt21 (pt (+ x12 x) y21 pt21))

(setq pt22 (pt (- x14 x) y20 pt22))
(setq pt23 (pt (+ x14 x) y21 pt23))
(setq pt24 (pt (- x1 x) y20 pt24))
(setq pt25 (pt (+ x1 x) y21 pt25))
(setq pt26 (pt (- x3 x) y20 pt26))
(setq pt27 (pt (+ x3 x) y21 pt27))
(setq pt28 (pt (- x5 x) y20 pt28))
(setq pt29 (pt (+ x5 x) y21 pt29))
(setq pt30 (pt (- x6 x) y20 pt30))
(setq pt31 (pt (+ x6 x) y21 pt31))

(command "line" pt20 pt21 "")
(command "line" pt22 pt23 "")
(command "line" pt24 pt25 "")
(command "line" pt26 pt27 "")
(command "line" pt28 pt29 "")
(command "line" pt30 pt31 "")
(command "line" pt21 pt31 "")
(command "line" pt20 pt30 "")  ; completed drawing plan abutment left


;;; ============================================================================
;;;  NOTE ON ARTICLE REPETITION
;;; ----------------------------------------------------------------------------
;;;  The source article prints several fragments twice — once inline in the
;;;  narrative, once inside a following "explanation" block.  The repetition is
;;;  faithful to the blog and includes:
;;;    * §2   reed()           — repeated with the tn / sc additions
;;;    * §8.1 pier()           — the x1/y1/x2 lines repeated at the head of
;;;                               §8.2-8.4
;;;    * §10  abt1()           — the whole function body printed a second time
;;;                               (without the 10.1/10.2 comment headings)
;;;  Both printings are identical in logic; this in-toto copy keeps the first,
;;;  comment-annotated printing and records the repetition here so nothing in
;;;  the published record is lost.
;;; ============================================================================

;;;  --- end of gad.lsp (in-toto preservation copy) ----------------------------
