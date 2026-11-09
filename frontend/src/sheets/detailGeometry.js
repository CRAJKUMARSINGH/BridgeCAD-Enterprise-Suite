/**
 * detailGeometry.js — framework-free geometry for Sheet 04 (foundation) and
 * Sheet 05 (pier / abutment / wing wall details).
 *
 * Geometry is emitted as neutral primitives (line/rect/circle/text/poly) tagged
 * with an IRC layer, so the same stream drives the SVG preview, the DXF export
 * and the robotic audit. Units are millimetres of sheet at 1:100, y-up; the
 * renderer flips to SVG y-down.
 *
 * The Python sheets (sheet4_foundation.py, sheet5_pier_abutment_details.py)
 * remain the source of truth for the CAD package; this module restores the same
 * content on the static deploy, where no Python runs.
 */

export const SHEET = Object.freeze({ W: 841, H: 594, MARGIN: 12, SCALE: 100 });
const TEXT_H = 2.5;
/** @param {number} m @returns {number} */
const mm = (m) => (m * 1000) / SHEET.SCALE;

/** @param {*} v @param {number} d @returns {number} */
const NUM = (v, d) => {
  const n = typeof v === "number" ? v : Number.parseFloat(String(v ?? ""));
  return Number.isFinite(n) ? n : d;
};
/** @param {number} n @param {number} lo @param {number} hi @returns {number} */
const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n));
/** @param {number} n @returns {number} */
const r2 = (n) => Math.round(n * 100) / 100;

/** Layer table: name -> [colour, linetype]. */
export const LAYERS = Object.freeze({
  "FOUND-CAP": ["#d9c26a", "CONTINUOUS"],
  "FOUND-PILE": ["#d9c26a", "CONTINUOUS"],
  "FOUND-WELL": ["#d9c26a", "CONTINUOUS"],
  "SUB-PIER": ["#9fc3d8", "CONTINUOUS"],
  "SUB-ABUT": ["#9fc3d8", "CONTINUOUS"],
  "ABUT-PROF": ["#9fc3d8", "CONTINUOUS"],
  "SUB-BEARING": ["#e08a5a", "CONTINUOUS"],
  "SUPER-GIRDER": ["#7fb2cc", "CONTINUOUS"],
  "SUPER-DECK": ["#7fb2cc", "CONTINUOUS"],
  "SUPER-WEARING": ["#8ec7a8", "CONTINUOUS"],
  "SUPER-CAMBER": ["#8ec7a8", "DASHED"],
  "STRUC-DETAIL": ["#b8c4cc", "CONTINUOUS"],
  "STRUC-SECTION": ["#b8c4cc", "CONTINUOUS"],
  "STRUC-OUTLINE": ["#b8c4cc", "CONTINUOUS"],
  HTCH: ["#7a8894", "CONTINUOUS"],
  HIDD: ["#7a8894", "DASHED"],
  CL: ["#c76a9c", "DASHDOT"],
  DIM: ["#c9a227", "CONTINUOUS"],
  TEXT: ["#dfe6ea", "CONTINUOUS"],
  "TEXT-HEADER": ["#ffffff", "CONTINUOUS"],
  "TEXT-LEVEL": ["#e08a5a", "CONTINUOUS"],
  "CIVIL-SCOUR": ["#5fb0c8", "DASHED"],
  "CIVIL-HFL": ["#5fb0c8", "DASHED"],
  FRAME: ["#8a969e", "CONTINUOUS"],
});

const P = {
  /** @param {string} layer @param {number} x1 @param {number} y1 @param {number} x2 @param {number} y2 @returns {object} */
  line: (layer, x1, y1, x2, y2) => ({ k: "line", layer, x1: r2(x1), y1: r2(y1), x2: r2(x2), y2: r2(y2) }),
  /** @param {string} layer @param {number} x @param {number} y @param {number} w @param {number} h @returns {object} */
  rect: (layer, x, y, w, h) => ({ k: "rect", layer, x: r2(x), y: r2(y), w: r2(w), h: r2(h) }),
  /** @param {string} layer @param {number} cx @param {number} cy @param {number} r @returns {object} */
  circle: (layer, cx, cy, r) => ({ k: "circle", layer, cx: r2(cx), cy: r2(cy), r: r2(r) }),
  /** @param {string} layer @param {number} x @param {number} y @param {string} s @param {number} [size] @param {string} [anchor] @returns {object} */
  text: (layer, x, y, s, size = TEXT_H, anchor = "start") => ({ k: "text", layer, x: r2(x), y: r2(y), s: String(s), size, anchor }),
  /** @param {string} layer @param {number[] | number[][]} pts @param {boolean} [closed] @returns {object} */
  poly: (layer, pts, closed = true) => ({ k: "poly", layer, pts: pts.flat().map(r2), closed }),
};

/** @param {any[]} out @param {string} layer @param {number} x @param {number} y @param {number} w @param {number} h @param {number} [step] */
function hatch(out, layer, x, y, w, h, step = 3) {
  if (w <= 0 || h <= 0) return;
  for (let o = -h; o < w; o += step) {
    const x1 = x + Math.max(o, 0);
    const y1 = y + Math.max(-o, 0);
    const run = Math.min(w - Math.max(o, 0), h - Math.max(-o, 0));
    if (run > 0) out.push(P.line(layer, x1, y1, x1 + run, y1 + run));
  }
}

/**
 * Hatch a (possibly rotated) polygon. `hatch` fills an axis-aligned box, so on a
 * splayed wing wall most of the ink lands outside the outline. This clips 45°
 * scan lines to the polygon's edges instead.
 */
/** @param {any[]} out @param {string} layer @param {number[]} pts @param {number} [step] */
function hatchPoly(out, layer, pts, step = 3) {
  const n = pts.length / 2;
  if (n < 3) return;
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  for (let i = 0; i < n; i += 1) {
    const x = pts[2 * i];
    const y = pts[2 * i + 1];
    minX = Math.min(minX, x); maxX = Math.max(maxX, x);
    minY = Math.min(minY, y); maxY = Math.max(maxY, y);
  }
  // Scan lines of slope 1: y - x = c.
  for (let c = minY - maxX; c <= maxY - minX; c += step) {
    /** @type {number[][]} */
    const hits = [];
    for (let i = 0; i < n; i += 1) {
      const ax = pts[2 * i], ay = pts[2 * i + 1];
      const j = (i + 1) % n;
      const bx = pts[2 * j], by = pts[2 * j + 1];
      const fa = ay - ax;
      const fb = by - bx;
      if (fa === fb || (fa - c) * (fb - c) > 0) continue;
      const t = (c - fa) / (fb - fa);
      if (t < 0 || t > 1) continue;
      hits.push([ax + t * (bx - ax), ay + t * (by - ay)]);
    }
    hits.sort((a, b) => a[0] - b[0]);
    for (let i = 0; i + 1 < hits.length; i += 2) {
      out.push(P.line(layer, hits[i][0], hits[i][1], hits[i + 1][0], hits[i + 1][1]));
    }
  }
}

/** @param {any[]} out @param {number} x1 @param {number} x2 @param {number} y @param {string} text */
function dimH(out, x1, x2, y, text) {
  out.push(P.line("DIM", x1, y, x2, y));
  out.push(P.line("DIM", x1, y - 2, x1, y + 2));
  out.push(P.line("DIM", x2, y - 2, x2, y + 2));
  out.push(P.text("DIM", (x1 + x2) / 2, y + 3.2, text, TEXT_H, "middle"));
}

/** @param {any[]} out @param {number} x @param {number} y1 @param {number} y2 @param {string} text */
function dimV(out, x, y1, y2, text) {
  out.push(P.line("DIM", x, y1, x, y2));
  out.push(P.line("DIM", x - 2, y1, x + 2, y1));
  out.push(P.line("DIM", x - 2, y2, x + 2, y2));
  out.push(P.text("DIM", x - 1.6, (y1 + y2) / 2, text, TEXT_H, "middle"));
}

/* ── parameter normalisation: every downstream guarantee lives here ───────── */

/** One recorded substitution: the caller's value was not the value used. */
/** @param {string[]} notes @param {string} label @param {number} from @param {number} to @param {string} unit */
const noteAdjust = (notes, label, from, to, unit) => {
  if (!Number.isFinite(from) || Math.abs(from - to) < 1e-9) return;
  notes.push(`${label} ${from.toFixed(2)} → ${to.toFixed(2)} ${unit}`);
};

/** @param {Record<string, any>} [input] @returns {Record<string, any>} */
export function normalizeParams(input = {}) {
  /** @type {string[]} */
  const notes = [];

  const cwRaw = NUM(input.carriageway, 7.5);
  const carriageway = clamp(cwRaw, 5, 12);
  noteAdjust(notes, "Carriageway", cwRaw, carriageway, "m");

  // Resolve the ABTL ladder from the RAW inputs, before the carriageway floor
  // runs. Resolving on the normalised object made `abtl` the first rung on every
  // call, so FUTL/FOOTL/FUTRL/ALCL/ALCW could never fire.
  const { valueM: abtlLadder, source: abtlSource } = resolveAbtlRaw(input);
  const abtlClamped = clamp(abtlLadder, 6, 26);
  const abtl = Math.max(abtlClamped, carriageway + 2);
  noteAdjust(notes, `ABTL (${abtlSource})`, abtlLadder, abtl, "m");

  const splayRaw = NUM(input.splay, 45);
  const splay = clamp(splayRaw, 15, 60);
  noteAdjust(notes, "Splay", splayRaw, splay, "°");

  const deckRl = clamp(NUM(input.deckRl, 112.4), 0, 400);
  const foundingRl = clamp(NUM(input.foundingRl, 96.2), -50, deckRl);
  noteAdjust(notes, "Founding level RL", NUM(input.foundingRl, 96.2), foundingRl, "m");
  // The founding level is the cap soffit (= pile cut-off). The scour level is a
  // separate datum; when the caller supplies none the two coincide, and the
  // sheet prints one number rather than claiming one RL means two things.
  const scourRl = clamp(NUM(input.scourRl, NUM(input.foundingRl, 96.2)), -50, deckRl);
  const hflRl = clamp(NUM(input.hflRl, 104.5), foundingRl, deckRl);
  const lwlRl = clamp(NUM(input.lwlRl, 99.8), foundingRl, hflRl);

  const rowsRaw = NUM(input.rows, 2);
  const rows = Math.round(clamp(rowsRaw, 1, 3));
  noteAdjust(notes, "Pile rows", rowsRaw, rows, "");
  const colsRaw = NUM(input.cols, 2);
  const cols = Math.round(clamp(colsRaw, 1, 3));
  noteAdjust(notes, "Pile columns", colsRaw, cols, "");

  const spanRaw = NUM(input.spans, 3);
  const spans = Math.round(clamp(spanRaw, 1, 12));
  noteAdjust(notes, "Spans", spanRaw, spans, "");

  const pileDiaRaw = NUM(input.pileDiaMm, 1000);
  const pileDiaMm = clamp(pileDiaRaw, 600, 1500);
  noteAdjust(notes, "Pile diameter", pileDiaRaw, pileDiaMm, "mm");

  const pileLenRaw = NUM(input.pileLenM, 12);
  const pileLenM = clamp(pileLenRaw, 4, 25);
  noteAdjust(notes, "Pile length", pileLenRaw, pileLenM, "m");

  const capTRaw = NUM(input.capTMm, 1200);
  const capTMm = clamp(capTRaw, 800, 1800);
  noteAdjust(notes, "Cap thickness", capTRaw, capTMm, "mm");

  return {
    projectName: String(input.projectName || "Untitled bridge").slice(0, 48),
    number: String(input.number || "GAD-001").slice(0, 18),
    revision: String(input.revision || "R0").slice(0, 6),
    spans,
    carriageway,
    abtl,
    abtlSource,
    futl: NUM(input.futl, 0),
    footl: NUM(input.footl, 0),
    futrl: NUM(input.futrl, 0),
    alcl: NUM(input.alcl, 0),
    alcw: NUM(input.alcw, 0),
    abutmentType: String(input.abutmentType || "").toUpperCase().slice(0, 40),
    splay,
    deckRl,
    hflRl,
    lwlRl,
    foundingRl,
    scourRl,
    pileDiaMm,
    pileLenM,
    capTMm,
    spacingM: clamp(NUM(input.spacingM, 2), 1.5, 4),
    rows,
    cols,
    wellDiaM: clamp(NUM(input.wellDiaM, 0), 0, 6),
    mainBarMm: clamp(NUM(input.mainBarMm, 25), 12, 32),
    sbckPa: clamp(NUM(input.sbckPa, 240), 80, 600),
    pierLenM: clamp(NUM(input.pierLenM, 9), 3, 10),
    pierWidM: clamp(NUM(input.pierWidM, 1.2), 0.8, 2.5),
    pierHgtM: clamp(NUM(input.pierHgtM, 6), 3, 12),
    capWidM: clamp(NUM(input.capWidM, 1.8), 1.2, 3),
    capDepM: clamp(NUM(input.capDepM, 0.65), 0.4, 1.2),
    abtHgtM: clamp(NUM(input.abtHgtM, 2.8), 1.5, 6),
    retHgtM: clamp(NUM(input.retHgtM, 2.5), 1.2, 5),
    girders: Math.round(clamp(NUM(input.girders, 4), 2, 8)),
    girderDepthMm: clamp(NUM(input.girderDepthMm, 900), 600, 1800),
    deckThickMm: clamp(NUM(input.deckThickMm, 200), 150, 400),
    bearingsPerPier: Math.round(clamp(NUM(input.bearingsPerPier, 4), 2, 8)),
    notes,
  };
}

/* ── ABTL ladder: ABTL -> FUTL -> FOOTL -> FUTRL -> ALCL -> ALCW -> 13.0 ──── */

const LADDER = ["abtl", "futl", "footl", "futrl", "alcl", "alcw"];

/** Resolve the ladder from raw caller inputs. */
/** @param {Record<string, any>} [input] @returns {{ valueM: number, source: string }} */
export function resolveAbtlRaw(input = {}) {
  for (const rung of LADDER) {
    const v = NUM(input[rung], 0);
    if (v > 0) return { valueM: v, source: rung.toUpperCase() };
  }
  return { valueM: 13, source: "DEFAULT" };
}

/** The rung that fired for an already-normalised param set. */
/** @param {Record<string, any>} p @returns {{ valueM: number, source: string }} */
export function resolveAbtl(p) {
  if (p && p.abtlSource) return { valueM: NUM(p.abtl, 13), source: p.abtlSource };
  return resolveAbtlRaw(p || {});
}

/* ── wing walls, measured from the abutment face ─────────────────────────── */

/** @param {Record<string, any>} p @returns {any} */
export function wingWallGeometry(p) {
  const { valueM: abtl, source } = resolveAbtl(p);
  const splay = clamp(NUM(p.splay, 45), 0, 88.999);
  const faceRunM = Math.max((abtl - p.carriageway) / 2, 0);
  const rad = (splay * Math.PI) / 180;
  const lengthM = Math.cos(rad) ? faceRunM / Math.cos(rad) : 0;
  const returnM = lengthM * Math.sin(rad);
  const topLevelM = p.deckRl - 1.2;
  const scourRl = NUM(p.scourRl, p.foundingRl);
  const baseLevelM = Math.min(scourRl, topLevelM) - 0.5;
  const walls = ["left", "right"].map((side) => ({
    side, splayDeg: splay, faceRunM, lengthM, returnM, topLevelM, baseLevelM,
  }));
  return { abtl, source, splayDeg: splay, faceRunM, lengthM, returnM, walls };
}

/* ── abutment battered profile (LISP abt1()) ─────────────────────────────── */

/**
 * LISP abt1() abutment parameters, in metres. The abutment faces carry the
 * project's abutment height as the stem; the section geometry is the abt1()
 * default set (ALCW/ALCD/ALFB/ALFO/ALFD/ALBB/DWTH and RTL−CAPT). A1 is the
 * AL* family (dirt wall outward on −x), A2 the mirrored AR* family.
 */
const ABT_PROFILE = Object.freeze({
  capW: 0.75,      // ALCW / ARCW — cap width
  capD: 1.2,       // ALCD / ARCD — cap depth
  frontBatter: 10, // ALFB / ARFB — face batter, 1:n
  backBatter: 3,   // ALBB / ARBB — back batter, 1:n
  toeOff: 1.5,     // ALFO / ARFO — toe and footing offset
  footD: 1.0,      // ALFD / ARFD — footing depth
  above: 0.98,     // RTL − CAPT — face upstand above the cap
  dirtW: 0.3,      // DWTH — dirt wall thickness
});

/**
 * The 14-vertex LISP abt1() battered abutment elevation, in sheet mm:
 *
 *   (x1,RTL) (x1,capt) (x3,capt) (x3,capB) (x5,alfbl) (x6,altbl) (x7,altbl)
 *   (x7,y8) (x10,y8) (x10,altbl) (x12,altbl) (x12,albbl) (x14,capB) (x14,RTL)
 *
 * `side` "left" is A1 (dirt wall outward at −x), "right" is A2 (mirrored, dirt
 * wall outward at +x). The cap soffit sits on `yCapB` and the face is anchored
 * at `xFace`; the stem height is the project's abutment height.
 */
/** @param {"left" | "right"} side @param {number} xFace @param {number} yCapB @param {number} stemHM @returns {any} */
export function abutmentProfile(side, xFace, yCapB, stemHM) {
  const A = ABT_PROFILE;
  const s = side === "right" ? -1 : 1;
  const stemH = Math.max(NUM(stemHM, 2.8), 0.5);
  const x1 = xFace;
  const capt = yCapB + mm(A.capD);
  const rtl = capt + mm(A.above);
  const altbl = yCapB - mm(stemH);
  const y8 = altbl - mm(A.footD);
  const x3 = x1 + s * mm(A.capW);
  const x5 = x3 + s * mm(stemH / A.frontBatter);
  const x6 = x5; // alfbl == altbl in abt1() defaults, so the toe drop is nil
  const x7 = x6 + s * mm(A.toeOff);
  const x14 = x1 - s * mm(A.dirtW);
  const x12 = x14 - s * mm(stemH / A.backBatter);
  const x10 = x12 - s * mm(A.toeOff);
  const pts = [
    x1, rtl, x1, capt, x3, capt, x3, yCapB,
    x5, altbl, x6, altbl, x7, altbl, x7, y8,
    x10, y8, x10, altbl, x12, altbl, x12, altbl,
    x14, yCapB, x14, rtl,
  ];
  return { pts, rtl, altbl, y8, x3, x7, x10, x12, x14, dirtWallX: x14 };
}

/* ── abutment SHAPE FAMILY (mirrors bridgecad_core.geometry.abutment_profiles) ─
 * Driven by abutment_type, not fixed. GRAVITY → trapezoid; CANTILEVER/
 * COUNTERFORT/BUTTRESS/STUB → inverted-T; else legacy block. Keep identical to
 * the Python module — a divergence re-opens defect D-13. */
const ABT_FAMILY = Object.freeze({ GRAVITY: "gravity", CANTILEVER: "cantilever", BATTERED: "battered" });
const ABT_FOOTING_FRAC    = 0.18;
const ABT_STEM_FRAC       = 0.5;
const ABT_TOP_BATTER_FRAC = 0.25;

/**
 * Map an abutment_type string to a shape family constant.
 * @param {string|null|undefined} abutmentType
 * @returns {"gravity"|"cantilever"|"battered"}
 */
export function abutmentFamily(abutmentType) {
  const n = String(abutmentType || "").toUpperCase();
  if (n.includes("GRAVITY")) return ABT_FAMILY.GRAVITY;
  if (n.includes("CANTILEVER") || n.includes("COUNTERFORT") ||
      n.includes("BUTTRESS") || n.includes("STUB")) return ABT_FAMILY.CANTILEVER;
  return ABT_FAMILY.BATTERED;
}

/**
 * Normalised [0,1] outline for an abutment shape family.
 * x=0 left face, x=1 right face, y=0 founding level, y=1 road level.
 * @param {"gravity"|"cantilever"|"battered"} family
 * @returns {number[]} flat [x0,y0, x1,y1, …] closed ring
 */
export function abutmentOutlineNorm(family) {
  if (family === ABT_FAMILY.GRAVITY) {
    const h = ABT_TOP_BATTER_FRAC;
    return [h, 1, 1 - h, 1, 1, 0, 0, 0];
  }
  if (family === ABT_FAMILY.CANTILEVER) {
    const lo = (1 - ABT_STEM_FRAC) / 2;
    const hi = 1 - lo;
    const fd = ABT_FOOTING_FRAC;
    return [lo, 1, hi, 1, hi, fd, 1, fd, 1, 0, 0, 0, 0, fd, lo, fd];
  }
  return [0, 1, 1, 1, 1, 0, 0, 0];
}

/** @param {Record<string, any>} p @returns {any} */
export function foundationLayout(p) {
  const rows = Math.round(clamp(NUM(p.rows, 2), 1, 3));
  const cols = Math.round(clamp(NUM(p.cols, 2), 1, 3));
  return {
    rows, cols, nPiles: rows * cols,
    capWm: Math.min(p.spacingM * (cols - 1) + 1.5, 12),
    capTm: p.capTMm / 1000,
    pileDm: p.pileDiaMm / 1000,
    pileLm: p.pileLenM,
    wellDiaM: p.wellDiaM,
    foundingRl: p.foundingRl,
  };
}

/** @param {Record<string, any>} p @param {number} sheet @returns {any} */
const baseMeta = (p, sheet) => ({
  sheet,
  projectName: p.projectName,
  number: p.number,
  revision: p.revision,
  scale: SHEET.SCALE,
  params: p,
  layersUsed: [],
});

/** @param {any[]} out @param {string} title @param {any} meta */
function frame(out, title, meta) {
  const M = SHEET.MARGIN;
  out.push(P.rect("FRAME", M, M, SHEET.W - 2 * M, SHEET.H - 2 * M));
  out.push(P.rect("FRAME", M + 4, M + 4, SHEET.W - 2 * M - 8, SHEET.H - 2 * M - 8));
  out.push(P.text("TEXT-HEADER", M + 8, SHEET.H - M - 10, title, 4.2));
  out.push(P.text("TEXT", SHEET.W - M - 8, SHEET.H - M - 10, "NOT FOR CONSTRUCTION · REVIEW ISSUE", 2.2, "end"));
  const tb = { x: SHEET.W - 205, y: 34 };
  out.push(P.rect("FRAME", tb.x, tb.y, 189, 96));
  [24, 24, 24].forEach((_d, i) => out.push(P.line("FRAME", tb.x, tb.y + 24 * (i + 1), tb.x + 189, tb.y + 24 * (i + 1))));
  out.push(P.line("FRAME", tb.x + 104, tb.y + 48, tb.x + 104, tb.y + 72));
  out.push(P.text("TEXT-HEADER", tb.x + 5, tb.y + 88, "BRIDGECAD · IRC / MoRTH", 2.6));
  out.push(P.text("TEXT", tb.x + 5, tb.y + 66, meta.projectName, 2.4));
  out.push(P.text("TEXT", tb.x + 5, tb.y + 42, `${meta.number} · REV ${meta.revision}`, 2.4));
  out.push(P.text("TEXT", tb.x + 109, tb.y + 42, `SCALE 1:${meta.scale}`, 2.4));
  out.push(P.text("TEXT", tb.x + 5, tb.y + 18, `SHEET ${String(meta.sheet).padStart(2, "0")}`, 2.4));
  out.push(P.text("TEXT", tb.x + 109, tb.y + 18, "DRAWN / CHECKED", 2.2));
}

/** @param {any[]} out @param {string[]} notes */
function noteBlock(out, notes) {
  notes.forEach((n, i) => out.push(P.text("TEXT", 30, 108 - i * 5.4, n, 2.2)));
}

/** @param {any[]} out @param {number} x @param {number} y */
function scaleBar(out, x, y) {
  out.push(P.line("FRAME", x, y, x + 50, y));
  for (let i = 0; i < 5; i += 1) {
    const bx = x + i * 10;
    out.push(P.rect("FRAME", bx, y, 10, 2.2));
    if (i % 2 === 0) out.push(P.line("FRAME", bx, y, bx + 10, y + 2.2));
    out.push(P.text("TEXT", bx + 5, y - 2, String(i), 2, "middle"));
  }
  out.push(P.text("TEXT", x + 50, y - 2, "5 m", 2, "start"));
  out.push(P.text("TEXT", x, y + 7, "SCALE 1:100 AT A1", 2));
  const nx = x + 72, ny = y + 2;
  out.push(P.poly("FRAME", [nx, ny - 9, nx - 4, ny + 3, nx, ny, nx + 4, ny + 3], true));
  out.push(P.text("TEXT-HEADER", nx, ny - 12, "N", 2.6, "middle"));
}

/* ── Sheet 04 — abutment / pier foundation ───────────────────────────────── */

/** @param {any[]} out @param {string} id @param {number} x @param {number} y @param {number} w @param {number} h @returns {number} */
const panel = (out, id, x, y, w, h) => out.push({ k: "panel", layer: "FRAME", id, x: r2(x), y: r2(y), w: r2(w), h: r2(h) });

/** @param {Record<string, any>} [raw] @returns {any} */
export function buildSheet4(raw) {
  const p = normalizeParams(raw);
  const f = foundationLayout(p);
  const meta = baseMeta(p, 4);
  /** @type {any[]} */
  const out = [];
  frame(out, "ABUTMENT & PIER FOUNDATION — GENERAL ARRANGEMENT", meta);

  const capW = mm(f.capWm);
  const capT = mm(f.capTm);
  const pileL = mm(Math.min(f.pileLm, 6));
  const pileW = mm(Math.max(f.pileDm, 0.8));

  // Three levels, three names. The input foundingRl is the cap soffit (= pile
  // cut-off); scour is a separate datum; the pile toe hangs a full pile length
  // below the cut-off — the cap thickness sits *above* the soffit, not below it.
  const capSoffitRl = p.foundingRl;
  const scourRl = p.scourRl;
  const pileToeRl = capSoffitRl - f.pileLm;
  const bearingRl = p.deckRl - p.deckThickMm / 1000 - p.girderDepthMm / 1000;

  /* panel A — foundation elevation */
  const xA = 45;
  const yCapB = 330;
  const yCapT = yCapB + capT;
  const yPileB = yCapB - pileL;
  const yBear = yCapT + 15;

  panel(out, "4A", 20, 300, 200, 90);
  out.push(P.rect("FOUND-CAP", xA, yCapB, capW, capT));
  hatch(out, "HTCH", xA, yCapB, capW, capT, 2.6);
  if (f.wellDiaM > 0) {
    const r = mm(f.wellDiaM / 2);
    out.push(P.rect("FOUND-WELL", xA + capW / 2 - r, yPileB, 2 * r, pileL));
    out.push(P.circle("FOUND-WELL", xA + capW / 2, yPileB, r));
  } else {
    for (let c = 0; c < f.cols; c += 1) {
      const px = xA + (capW * (c + 0.5)) / f.cols - pileW / 2;
      out.push(P.rect("FOUND-PILE", px, yPileB, pileW, pileL));
    }
  }
  const yScour = yCapB - (Math.abs(scourRl - capSoffitRl) > 1e-6 ? 12 : 0);
  out.push(P.line("CIVIL-SCOUR", xA - 16, yScour, xA + capW + 16, yScour));
  out.push(P.line("CIVIL-HFL", xA - 16, yCapT + 8, xA + capW + 16, yCapT + 8));
  out.push(P.line("HIDD", xA - 16, yBear, xA + capW + 16, yBear));
  out.push(P.text("TEXT-LEVEL", xA + capW + 5, yScour, `SCOUR LEVEL RL ${scourRl.toFixed(3)}`));
  if (Math.abs(scourRl - capSoffitRl) > 1e-6) {
    out.push(P.text("TEXT-LEVEL", xA + capW + 5, yCapB, `PILE CUT-OFF LEVEL RL ${capSoffitRl.toFixed(3)}`));
  }
  out.push(P.text("TEXT-LEVEL", xA + capW + 5, yPileB, `FOUNDATION LEVEL RL ${pileToeRl.toFixed(3)}`));
  out.push(P.text("TEXT-LEVEL", xA + capW + 5, yBear, `BEARING LEVEL RL ${bearingRl.toFixed(3)}`));
  out.push(P.text("TEXT-LEVEL", xA + capW + 5, yCapT + 8, `HFL RL ${p.hflRl.toFixed(3)}`));
  out.push(P.text("TEXT-HEADER", xA + capW / 2, yBear + 12, "FOUNDATION ELEVATION", 3, "middle"));

  /* panel B — foundation plan */
  const xB = 250;
  const yB = 250;
  panel(out, "4B", 240, 230, 150, 140);
  if (f.wellDiaM > 0) {
    const r = mm(f.wellDiaM / 2);
    out.push(P.circle("FOUND-WELL", xB + r, yB + r, r));
    out.push(P.circle("FOUND-WELL", xB + r, yB + r, Math.max(r - mm(0.8), r * 0.55)));
    out.push(P.text("TEXT", xB, yB + 2 * r + 6, `WELL Ø ${f.wellDiaM.toFixed(2)} m`, 2.4));
  } else {
    const cell = mm(p.spacingM);
    const r = mm(Math.max(f.pileDm / 2, 0.4));
    for (let i = 0; i < f.rows; i += 1) {
      for (let j = 0; j < f.cols; j += 1) {
        const cx = xB + r + j * cell;
        const cy = yB + r + i * cell;
        out.push(P.circle("FOUND-PILE", cx, cy, r));
        out.push(P.line("CL", cx - 2 * r, cy, cx + 2 * r, cy));
        out.push(P.line("CL", cx, cy - 2 * r, cx, cy + 2 * r));
      }
    }
    out.push(P.text("TEXT", xB, yB + f.rows * cell + 6, `${f.nPiles} No. PILES Ø ${p.pileDiaMm.toFixed(0)} mm`, 2.4));
    dimH(out, xB, xB + f.cols * cell, yB - 8, `PILE SPACING ${p.spacingM.toFixed(2)} m`);
  }
  out.push(P.text("TEXT-HEADER", xB, yB + f.rows * mm(p.spacingM) + 14, "FOUNDATION PLAN", 3));

  /* panel C — pile cap reinforcement */
  const xC = 45;
  const yC = 170;
  panel(out, "4C", 30, 160, 200, 80);
  out.push(P.rect("STRUC-DETAIL", xC, yC, capW, capT));
  hatch(out, "HTCH", xC, yC, capW, capT, 2.6);
  out.push(P.line("FOUND-CAP", xC, yC + capT * 0.82, xC + capW, yC + capT * 0.82));
  out.push(P.line("FOUND-CAP", xC, yC + capT * 0.18, xC + capW, yC + capT * 0.18));
  for (let i = 0; i < 5; i += 1) {
    const sx = xC + (capW * (i + 0.5)) / 5;
    out.push(P.line("FOUND-CAP", sx, yC + capT * 0.18, sx, yC + capT * 0.82));
  }
  out.push(P.text("TEXT-HEADER", xC + capW / 2, yC + capT + 10, "PILE CAP REINFORCEMENT DETAIL", 3, "middle"));
  const bar = `T${p.mainBarMm.toFixed(0)} @ 150 mm`;
  out.push(P.text("TEXT", xC + capW + 5, yC + capT * 0.18, `BOTTOM MAT ${bar} c/c`, 2.2));
  out.push(P.text("TEXT", xC + capW + 5, yC + capT * 0.82, `TOP MAT ${bar} c/c`, 2.2));
  out.push(P.text("TEXT", xC + capW + 5, yC - 3, `${f.nPiles} No. PILE HEADS`, 2.2));

  /* panel D — pile schedule */
  const xD = 470;
  const yD = 330;
  panel(out, "4D", 460, 300, 120, 60);
  out.push(P.text("TEXT-HEADER", xD, yD + 14, "PILE SCHEDULE", 3));
  /** @type {string[][]} */
  const rowsD = [["MARK", "Ø (mm)", "LENGTH"]];
  for (let i = 0; i < Math.min(f.nPiles, 6); i += 1) rowsD.push([`P${i + 1}`, p.pileDiaMm.toFixed(0), `${f.pileLm.toFixed(2)} m`]);
  rowsD.forEach((r, i) => {
    r.forEach((c, j) => out.push(P.text(i === 0 ? "TEXT-HEADER" : "TEXT", xD + j * 30, yD - i * 7, c, 2.2)));
    out.push(P.line("FRAME", xD, yD - i * 7 - 2, xD + 86, yD - i * 7 - 2));
  });

  dimH(out, xA, xA + capW, yCapB - 10, `CAP ${f.capWm.toFixed(2)} m`);
  dimV(out, xA - 8, yCapB, yCapT, `CAP ${p.capTMm.toFixed(0)} mm`);
  dimV(out, xA + capW + 26, yPileB, yCapB, `PILE ${f.pileLm.toFixed(2)} m`);
  // Offset from the cap dim: same x and a shared y span overprinted them.
  dimV(out, xA - 20, yCapB, yBear, "BEARING LEVEL");

  scaleBar(out, 30, 125);

  /** @type {string[]} */
  const noteLines = [
    "1. All dimensions in metres unless stated otherwise.",
    `2. Safe bearing capacity ${p.sbckPa.toFixed(0)} kPa at founding level RL ${pileToeRl.toFixed(3)}.`,
    `3. Pile cut-off (cap soffit) level RL ${capSoffitRl.toFixed(3)}; scour level RL ${scourRl.toFixed(3)}.`,
    "4. Founding stratum to be confirmed by the geotechnical report.",
    "5. Restored on the static deploy — parity with bridgecad_draw/sheets/sheet4_foundation.py.",
  ];
  // Item 4: a clamp that rewrites an engineering input must say so on the sheet.
  for (const n of p.notes) noteLines.push(`CLAMP: ${n}`);
  noteBlock(out, noteLines);

  meta.layersUsed = [...new Set(out.map((q) => q.layer))];
  meta.foundation = f;
  return { sheet: 4, prims: out, meta };
}

/* ── Sheet 05 — pier, abutment, wing wall / fire wall details ────────────── */

/** @param {Record<string, any>} [raw] @returns {any} */
export function buildSheet5(raw) {
  const p = normalizeParams(raw);
  const w = wingWallGeometry(p);
  const f = foundationLayout(p);
  const meta = baseMeta(p, 5);
  meta.walls = w.walls;
  meta.abtlSource = w.source;
  meta.abutmentFamily = abutmentFamily(p.abutmentType);
  /** @type {any[]} */
  const out = [];
  frame(out, "PIER, ABUTMENT & WING WALL / FIRE WALL DETAILS", meta);

  const h = TEXT_H;
  const footH = mm(f.capTm);
  const pierH = mm(p.pierHgtM);
  const capDep = mm(p.capDepM);
  const pileL = mm(Math.min(f.pileLm, 6));
  const pileW = mm(Math.max(f.pileDm, 0.8));
  const padH = h * 1.4;

  const yFootB = 250;
  const yFootT = yFootB + footH;
  const yShaftT = yFootT + pierH;
  const yCapT = yShaftT + capDep;
  const yBearT = yCapT + padH;
  const yPileB = yFootB - pileL;

  /* panel A — pier elevation */
  panel(out, "5A", 22, 180, 120, 180);
  const xA = 30;
  const wA = mm(p.pierLenM);
  const over = mm(0.6);

  out.push(P.rect("FOUND-CAP", xA - over, yFootB, wA + 2 * over, footH));
  hatch(out, "HTCH", xA - over, yFootB, wA + 2 * over, footH, 2.6);
  out.push(P.rect("SUB-PIER", xA, yFootT, wA, pierH));
  hatch(out, "HTCH", xA, yFootT, wA, pierH, 2.6);
  out.push(P.rect("SUB-PIER", xA - over, yShaftT, wA + 2 * over, capDep));
  for (let c = 0; c < f.cols; c += 1) {
    const px = xA + (wA * (c + 0.5)) / f.cols - pileW / 2;
    out.push(P.rect("FOUND-PILE", px, yPileB, pileW, pileL));
    hatch(out, "HTCH", px, yPileB, pileW, pileL, 2.6);
  }
  const padW = mm(0.35);
  for (let i = 0; i < p.bearingsPerPier; i += 1) {
    const bx = xA + (wA * (i + 0.5)) / p.bearingsPerPier - padW / 2;
    out.push(P.rect("SUB-BEARING", bx, yCapT, padW, padH));
  }
  out.push(P.line("CL", xA + wA / 2, yPileB - 5, xA + wA / 2, yBearT + 5));
  out.push(P.line("HIDD", xA - 8, yFootT, xA + wA + 8, yFootT));
  out.push(P.text("TEXT-HEADER", xA, yBearT + 11, "PIER ELEVATION", 3));
  out.push(P.text("TEXT", xA, yPileB - 6, `${f.nPiles} No. PILES Ø ${f.pileDm.toFixed(2)} m`, 2.2));
  out.push(P.text("TEXT", xA, yCapT + padH + 4, `${p.bearingsPerPier} No. BEARINGS ON PIER CAP`, 2.2));

  /* panel B — section A-A */
  panel(out, "5B", 150, 180, 150, 190);
  const xB = 160;
  const deckW = mm(p.carriageway + 1.4);
  const cxB = xB + deckW / 2;
  const wFoot = mm(p.pierWidM + 1.2);
  const wShaft = mm(p.pierWidM);
  const wCap = mm(p.capWidM);

  out.push(P.rect("FOUND-CAP", cxB - wFoot / 2, yFootB, wFoot, footH));
  hatch(out, "HTCH", cxB - wFoot / 2, yFootB, wFoot, footH, 2.6);
  out.push(P.rect("SUB-PIER", cxB - wShaft / 2, yFootT, wShaft, pierH));
  hatch(out, "HTCH", cxB - wShaft / 2, yFootT, wShaft, pierH, 2.6);
  out.push(P.rect("SUB-PIER", cxB - wCap / 2, yShaftT, wCap, capDep));
  for (let i = 0; i < p.bearingsPerPier; i += 1) {
    const bx = cxB - wCap / 2 + (wCap * (i + 0.5)) / p.bearingsPerPier - padW / 2;
    out.push(P.rect("SUB-BEARING", bx, yCapT, padW, padH));
  }
  const girderD = mm(p.girderDepthMm / 1000);
  const deckT = mm(p.deckThickMm / 1000);
  const yGirB = yBearT;
  const yGirT = yGirB + girderD;
  const yDeckT = yGirT + deckT;
  for (let i = 0; i < p.girders; i += 1) {
    const gx = xB + (deckW * (i + 0.5)) / p.girders - mm(0.3) / 2;
    out.push(P.rect("SUPER-GIRDER", gx, yGirB, mm(0.3), girderD));
  }
  out.push(P.rect("SUPER-DECK", xB, yGirT, deckW, deckT));
  hatch(out, "HTCH", xB, yGirT, deckW, deckT, 2.2);
  out.push(P.rect("SUPER-WEARING", xB, yDeckT, deckW, 1.6));
  const kerbW = mm(0.25);
  out.push(P.rect("SUPER-DECK", xB, yDeckT + 1.6, kerbW, 6));
  out.push(P.rect("SUPER-DECK", xB + deckW - kerbW, yDeckT + 1.6, kerbW, 6));
  out.push(P.rect("STRUC-OUTLINE", xB + kerbW, yDeckT + 7.6, kerbW * 0.8, 9));
  out.push(P.rect("STRUC-OUTLINE", xB + deckW - kerbW * 1.8, yDeckT + 7.6, kerbW * 0.8, 9));
  const camber = [0, 1, 2, 3, 4, 5, 6].map((i) => {
    const t = i / 6;
    return [xB + deckW * t, yDeckT + 1.6 + 2 * (1 - (2 * t - 1) ** 2)];
  });
  out.push(P.poly("SUPER-CAMBER", camber, false));
  out.push(P.line("CL", cxB, yFootT - 5, cxB, yDeckT + 20));
  out.push(P.text("TEXT-HEADER", xB, yDeckT + 26, "SECTION A-A THROUGH PIER", 3));
  out.push(P.text("TEXT", xB, yGirB - 5, `PIER WALL ${p.pierWidM.toFixed(2)} m THICK × ${p.pierHgtM.toFixed(2)} m HIGH`, 2.2));
  out.push(P.text("TEXT", xB, yDeckT + 32, "KERB + PARAPET — READ FROM SUPERSTRUCTURE MODEL", 2.2));

  /* panel C — abutment elevation: the two LISP abt1() battered profiles.
     A1 (left end) uses the AL* family, dirt wall outward on −x; A2 (right end)
     mirrors it (AR*, dirt wall outward on +x). The cap, the battered face and
     stem, the toe and the footing all come from abt1(); the wing walls still
     spring from each abutment face on the cap soffit. */
  panel(out, "5C", 305, 130, 270, 170);
  const xC = 355;
  const wC = mm(w.abtl);
  const yAbtB = 235; // cap soffit — the profiles and both wing walls seat here
  const a1 = abutmentProfile("left", xC, yAbtB, p.abtHgtM);
  const a2 = abutmentProfile("right", xC + wC, yAbtB, p.abtHgtM);
  const yAbtT = a1.rtl;

  for (const [tag, a] of /** @type {[string, any][]} */ ([["A1", a1], ["A2", a2]])) {
    out.push(P.poly("ABUT-PROF", a.pts, true));
    hatchPoly(out, "HTCH", a.pts, 2.6);
    // Internal abt1() construction lines: the cap soffit and the toe/footing top.
    out.push(P.line("ABUT-PROF", a.x14, yAbtB, a.x3, yAbtB));
    out.push(P.line("ABUT-PROF", a.x10, a.altbl, a.x7, a.altbl));
    // abt1() also outlines the dirt wall itself: the back batter up to road level
    // and across the wall top to its outer face, so the wall reads as a wall.
    out.push(P.line("ABUT-PROF", a.x12, a.altbl, a.x12, a.rtl));
    out.push(P.line("ABUT-PROF", a.x12, a.rtl, a.x14, a.rtl));
    out.push(P.text("TEXT", a.dirtWallX, a.y8 - 5, `ABUTMENT ${tag} — BATTERED PROFILE (abt1(), DWTH 0.30 m)`, 2.2, tag === "A1" ? "start" : "end"));
  }
  out.push(P.line("CL", xC - 5, yAbtB, xC + wC + 5, yAbtB));
  out.push(P.text("TEXT-HEADER", xC, yAbtT + 24, `ABUTMENT A1 & A2 — BATTERED PROFILE · ABTL ${w.abtl.toFixed(2)} m (SOURCE: ${w.source})`, 3));
  out.push(P.text("TEXT-LEVEL", xC, yAbtT + 18, `DECK LEVEL RL ${p.deckRl.toFixed(3)}`));
  out.push(P.text("TEXT-LEVEL", xC, yAbtT + 13, `HFL RL ${p.hflRl.toFixed(3)}`));
  out.push(P.text("TEXT-LEVEL", xC, yAbtT + 8, `LWL RL ${p.lwlRl.toFixed(3)}`));
  out.push(P.text("TEXT-LEVEL", xC, yAbtT + 3, `FOUNDING LEVEL RL ${p.foundingRl.toFixed(3)}`));

  const thick = mm(0.4);
  const run = mm(w.faceRunM);
  const ret = mm(w.returnM);
  for (const wall of w.walls) {
    const sign = wall.side === "left" ? -1 : 1;
    // Each wall springs from its OWN end of the abutment — left from xC, right
    // from xC + wC — not both from one corner. The abutment face is horizontal,
    // so the face run is horizontal too; the return drops vertically, and the
    // wall is seated on the abutment soffit yAbtB rather than floating below it.
    const noseX = sign < 0 ? xC : xC + wC;
    const toeX = noseX + sign * run;
    const toeY = yAbtB - ret;
    const quad = [noseX, yAbtB, toeX, toeY, toeX, toeY - thick, noseX, yAbtB - thick];
    out.push(P.poly("SUB-ABUT", quad, true));
    hatchPoly(out, "HTCH", quad, 2.4);
    out.push(P.text("TEXT", toeX + sign * 4, toeY, `WING WALL ${wall.side.toUpperCase()} — ${wall.lengthM.toFixed(2)} m`, 2.2, sign < 0 ? "end" : "start"));
  }
  out.push(P.text("TEXT-HEADER", xC, 140, `WING WALL SPLAY ${w.splayDeg.toFixed(1)}° FROM ABUTMENT FACE (FACE RUN ${w.faceRunM.toFixed(2)} m, RETURN ${w.returnM.toFixed(2)} m)`, 2.4));
  dimH(out, xC, xC + wC, yAbtB - 12, `ABTL ${w.abtl.toFixed(2)} m`);
  dimV(out, xC + wC + mm(8), a1.altbl, yAbtB, `ABUTMENT ${p.abtHgtM.toFixed(2)} m`);
  dimV(out, xC + wC + mm(4), yAbtB, yAbtB + mm(p.retHgtM), `RETURN WALL ${p.retHgtM.toFixed(2)} m`);
  dimH(out, xC - run, xC, yAbtB - ret - 10, `FACE RUN ${w.faceRunM.toFixed(2)} m`);
  dimV(out, xC - run - 12, yAbtB - ret, yAbtB, `RETURN ${w.returnM.toFixed(2)} m`);

  /* panel H — abutment TRANSVERSE elevation, shape-family aware. Mirrors
     bridgecad_core.geometry.abutment_profiles.elevation_outline: GRAVITY →
     battered trapezoid; CANTILEVER/COUNTERFORT → inverted-T; else block.
     A1/A2 battered SIDE profiles stay in panel 5C (abt1()); this panel is the
     end-on view the family functions own. */
  panel(out, "5H", 305, 312, 270, 180);
  const fam = abutmentFamily(p.abutmentType);
  const xH = 320;
  const yHb = 352;
  const Lh = mm(w.abtl);
  const Hh = mm(p.abtHgtM);
  const capH = mm(p.capDepM);
  const shaftH = abutmentOutlineNorm(fam).map((v, i) => (i % 2 === 0 ? xH + v * Lh : yHb + v * Hh));
  out.push(P.poly("ABUT-PROF", shaftH, true));
  hatchPoly(out, "HTCH", shaftH, 2.6);
  out.push(P.rect("SUB-ABUT", xH, yHb + Hh, Lh, capH));
  hatch(out, "HTCH", xH, yHb + Hh, Lh, capH, 2.6);
  const yCapH = yHb + Hh + capH;
  // Rear stack edge-on: dirt wall → approach slab → continuous wearing coat.
  const stackLh = Lh * 0.96;
  const stackXh = xH + (Lh - stackLh) / 2;
  const dwEh = mm(0.3);
  const appEh = mm(0.38);
  out.push(P.rect("ABUT-PROF", stackXh, yCapH, stackLh, dwEh));
  out.push(P.rect("SUPER-DECK", stackXh, yCapH + dwEh, stackLh, appEh));
  out.push(P.rect("SUPER-WEARING", stackXh, yCapH + dwEh + appEh, stackLh, 1.2));
  // Wing walls: top falls at 1:10 from each cap end.
  for (const side of [-1, 1]) {
    const xe = xH + (side < 0 ? 0 : Lh);
    const wwRun = 24;
    out.push(P.poly("ABUT-PROF", [xe, yCapH, xe + side * wwRun, yCapH - wwRun / 10, xe + side * wwRun, yHb, xe, yHb], true));
  }
  out.push(P.line("CL", xH - 4, yHb, xH + Lh + 4, yHb));
  dimH(out, xH, xH + Lh, yHb - 6, `L=${w.abtl.toFixed(2)} m`);
  dimV(out, xH - 6, yHb, yHb + Hh, `H=${p.abtHgtM.toFixed(2)} m`);
  out.push(P.text("TEXT-HEADER", xH, yCapH + dwEh + appEh + 12, `ABUTMENT TRANSVERSE ELEVATION — ${fam.toUpperCase()} FAMILY`, 3));
  out.push(P.text("TEXT", xH, yHb - 12, `SHAPE FAMILY FROM abutment_type "${p.abutmentType || "battered"}"`, 2.2));

  /* panel D — bearing schedule */
  panel(out, "5D", 610, 300, 140, 60);
  const xD = 620;
  const yD = 340;
  out.push(P.text("TEXT-HEADER", xD, yD + 14, "BEARING SCHEDULE", 3));
  /** @type {string[][]} */
  const rowsD = [
    ["LOCATION", "TYPE", "SIZE", "LOAD", "FIXITY", "QTY"],
    ["A1", "ELASTOMERIC", "300x400", "450", "GUIDE", "4"],
    ["P1", "ELASTOMERIC", "300x400", "620", "FIXED", `${p.bearingsPerPier}`],
    ["P2", "ELASTOMERIC", "300x400", "620", "FREE", `${p.bearingsPerPier}`],
    ["A2", "ELASTOMERIC", "300x400", "450", "GUIDE", "4"],
  ];
  rowsD.forEach((r, i) => {
    r.forEach((c, j) => out.push(P.text(i === 0 ? "TEXT-HEADER" : "TEXT", xD + [0, 22, 48, 72, 90, 112][j], yD - i * 7, c, 2.1)));
    out.push(P.line("FRAME", xD, yD - i * 7 - 2, xD + 128, yD - i * 7 - 2));
  });

  /* panel E — pile foundation layout plan */
  panel(out, "5E", 150, 70, 130, 70);
  const xE = 160;
  const yE = 95;
  const planW = wA;
  const planD = mm(p.pierWidM + 1.2);
  out.push(P.rect("FOUND-CAP", xE, yE, planW, planD));
  hatch(out, "HTCH", xE, yE, planW, planD, 2.4);
  for (let r = 0; r < f.rows; r += 1) {
    for (let c = 0; c < f.cols; c += 1) {
      out.push(P.circle("FOUND-PILE", xE + (planW * (c + 0.5)) / f.cols, yE + (planD * (r + 0.5)) / f.rows, pileW / 2));
    }
  }
  out.push(P.line("CL", xE + planW / 2, yE - 5, xE + planW / 2, yE + planD + 5));
  out.push(P.line("CL", xE - 5, yE + planD / 2, xE + planW + 5, yE + planD / 2));
  out.push(P.text("TEXT-HEADER", xE, yE + planD + 10, "PIER — PILE FOUNDATION LAYOUT PLAN", 3));
  out.push(P.text("TEXT", xE, yE - 8, `PILE GROUP ${f.rows}×${f.cols} — ${f.nPiles} No. Ø ${f.pileDm.toFixed(2)} m`, 2.2));
  out.push(P.text("TEXT", xE, yE - 13, `PILE CAP ${p.pierLenM.toFixed(2)} m × ${(p.pierWidM + 1.2).toFixed(2)} m`, 2.2));
  dimH(out, xE, xE + planW, yE - 18, `PILE CAP ${p.pierLenM.toFixed(2)} m`);

  /* panel F — pile foundation schedule */
  panel(out, "5F", 325, 70, 120, 55);
  const xF = 330;
  const yF = 95;
  out.push(P.text("TEXT-HEADER", xF, yF + 14, "PILE FOUNDATION SCHEDULE", 3));
  /** @type {string[][]} */
  const rowsF = [
    ["PARAMETER", "VALUE"],
    ["Pile diameter", `${f.pileDm.toFixed(2)} m`],
    ["Pile group", `${f.rows}×${f.cols} = ${f.nPiles} No.`],
    ["Pile cap", `${p.pierLenM.toFixed(2)} × ${(p.pierWidM + 1.2).toFixed(2)} m`],
    ["Pile length", `${f.pileLm.toFixed(2)} m`],
    ["Cap thickness", `${p.capTMm.toFixed(0)} mm`],
  ];
  rowsF.forEach((r, i) => {
    r.forEach((c, j) => out.push(P.text(i === 0 ? "TEXT-HEADER" : "TEXT", xF + j * 52, yF - i * 7, c, 2.1)));
    out.push(P.line("FRAME", xF, yF - i * 7 - 2, xF + 104, yF - i * 7 - 2));
  });

  /* panel G — dirt wall in abutment: drainage, filter and backfill detail.
     Reads the practice in the referenced dirt-wall article: the wall is DWTH
     thin (0.3 m) and rises from the cap soffit to road level; weep holes plus a
     granular/geotextile filter relieve hydrostatic pressure; the retained
     embankment behind it is compacted in layers and capped by the approach slab. */
  panel(out, "5G", 590, 150, 235, 115);
  const xG = 590;
  const yG = 150;
  const dwth = mm(0.3);
  const slabT = mm(0.38);
  const capHG = mm(p.capTMm / 1000);
  const gCapB = yG + 12;
  const gCapT = gCapB + capHG;
  const yRoad = gCapT + mm(p.abtHgtM);
  const ySlabB = yRoad - slabT;
  const xWall = xG + 92;
  const wallH = Math.max(ySlabB - gCapT, 1);

  // Abutment cap the dirt wall is seated on.
  out.push(P.rect("FOUND-CAP", xWall, gCapB, 68, capHG));
  hatch(out, "HTCH", xWall, gCapB, 68, capHG, 2.6);
  // Thin dirt wall (DWTH) rising from the cap soffit to road level.
  out.push(P.rect("SUB-ABUT", xWall, gCapT, dwth, wallH));
  // Retained embankment, compacted in layers, behind the wall.
  const embank = [xWall - 62, gCapB, xWall, gCapB, xWall, ySlabB, xWall - 62, ySlabB];
  out.push(P.poly("HTCH", embank, true));
  hatchPoly(out, "HTCH", embank, 2.4);
  // Granular filter / geotextile immediately behind the wall.
  out.push(P.rect("STRUC-DETAIL", xWall - mm(0.3), gCapT, mm(0.3), wallH));
  // Granular sub-base (GSB) compacted under the dirt wall — prewallcivil §5
  // ("place granular sub-base material and compact it to improve stability").
  out.push(P.rect("STRUC-DETAIL", xWall - mm(1.0), gCapT, mm(1.0) + dwth, mm(0.1)));
  // Geogrid / MSE reinforcement between compacted backfill layers — §5.
  for (const frac of [0.3, 0.55, 0.8]) {
    out.push(P.line("HIDD", xWall - 58, gCapT + frac * wallH, xWall, gCapT + frac * wallH));
  }
  // Drainage pipe at the backfill heel, discharging the drained fill — §5.
  out.push(P.circle("STRUC-DETAIL", xWall - 54, gCapT + 6, 1.5));
  // Weep holes through the wall, discharging to the abutment face.
  for (const frac of [0.25, 0.55]) {
    const wy = gCapT + frac * wallH;
    out.push(P.circle("STRUC-DETAIL", xWall + dwth / 2, wy, 1.2));
    out.push(P.line("CIVIL-HFL", xWall + dwth, wy, xWall + 10, wy));
  }
  // Approach slab (APTHK thin) seated on the embankment at road level.
  out.push(P.rect("SUPER-DECK", xWall - 62, ySlabB, 62 + dwth, slabT));
  out.push(P.rect("SUPER-WEARING", xWall - 62, yRoad, 62 + dwth, 1.2));
  out.push(P.text("TEXT-HEADER", xG, yG + 110, "DIRT WALL IN ABUTMENT — DRAINAGE & BACKFILL DETAIL", 3));
  out.push(P.text("TEXT-LEVEL", xWall + 6, yRoad + 3, `ROAD LEVEL RL ${p.deckRl.toFixed(3)}`));
  out.push(P.text("TEXT", xWall + 6, gCapT + wallH * 0.5, "DIRT WALL DWTH 0.30 m (THIN)", 2.2));
  out.push(P.text("TEXT", xWall + 6, gCapB + capHG + 4, "ABUTMENT CAP", 2.2));
  out.push(P.text("TEXT", xWall + 14, gCapT + 4, "WEEP HOLES Ø100 @ 3 m c/c", 2.2));
  out.push(P.text("TEXT", xWall - 62, ySlabB + 8, "APPROACH SLAB APTHK", 2.2));
  out.push(P.text("TEXT", xWall - 62, ySlabB - 3, "GRANULAR FILTER / GEOTEXTILE", 2.2));
  out.push(P.text("TEXT", xWall - 62, gCapT + 6, "RETAINED EMBANKMENT — COMPACTED IN LAYERS", 2.2));
  out.push(P.text("TEXT", xG, yG + 5, "NOTE: WEEP HOLES + FILTER DRAIN THE BACKFILL, LIMITING HYDROSTATIC PRESSURE.", 2.1));
  out.push(P.text("TEXT", xG, yG + 1, "REF: GSB + GEOGRID LAYERS COMPACTED, DRAINAGE PIPE AT HEEL (prewallcivil.com dirt-wall).", 2.0));

  scaleBar(out, 30, 125);

  noteBlock(out, [
    "1. All dimensions in metres unless stated otherwise.",
    `2. ABTL ${w.abtl.toFixed(2)} m resolved from the ${w.source} rung of the ABTL ladder.`,
    `3. ${p.spans > 1 ? `${p.spans - 1} intermediate PIER(S) — see pier schedule.` : "Simple span: no intermediate pier."}`,
    `4. Wing wall splay ${w.splayDeg.toFixed(1)}° from the abutment face; ${w.walls.length} wing wall(s) drawn.`,
    `5. Spans on this structure: ${p.spans}; plot scale 1:${SHEET.SCALE}. Restored on static deploy.`,
  ]);

  meta.layersUsed = [...new Set(out.map((q) => q.layer))];
  meta.foundation = f;
  return { sheet: 5, prims: out, meta };
}

/* ── audit: the contract the robotic test asserts ────────────────────────── */

/** @type {Record<number, string[]>} */
const REQUIRED_LABELS = {
  4: ["FOUNDATION ELEVATION", "SCOUR LEVEL RL", "FOUNDATION LEVEL RL", "BEARING LEVEL RL", "HFL RL", "PILE CAP REINFORCEMENT DETAIL", "PILE SCHEDULE", "FOUNDATION PLAN"],
  5: ["PIER ELEVATION", "SECTION A-A THROUGH PIER", "ABUTMENT A1", "ABTL", "SOURCE:", "WING WALL LEFT", "WING WALL RIGHT", "WING WALL SPLAY", "FACE RUN", "RETURN", "FIRE WALL", "DIRT WALL", "WEEP HOLES", "GRANULAR FILTER", "RETAINED EMBANKMENT", "BEARING SCHEDULE", "PILE FOUNDATION LAYOUT PLAN", "PILE FOUNDATION SCHEDULE"],
};

/** @type {Record<number, string[]>} */
const REQUIRED_LAYERS = {
  4: ["FOUND-CAP", "CIVIL-SCOUR", "CIVIL-HFL", "TEXT-LEVEL", "DIM", "HTCH", "FRAME"],
  5: ["SUB-ABUT", "ABUT-PROF", "SUB-PIER", "SUB-BEARING", "FOUND-PILE", "TEXT-HEADER", "DIM", "FRAME"],
};

/** @param {any[]} arr @returns {number[]} */
const finite = (arr) => arr.filter((n) => typeof n === "number" && Number.isFinite(n));

/** @param {{ sheet: number, prims: any[], meta: any }} sheet @returns {any} */
export function audit(sheet) {
  /** @type {any[]} */
  const issues = [];
  /** @param {string} code @param {string} detail */
  const add = (code, detail) => issues.push({ code, detail });
  const { prims, meta } = sheet;
  const p = meta.params;

  for (const [k, v] of Object.entries(p)) {
    if (typeof v === "number" && !Number.isFinite(v)) add("E_NONFINITE", k);
  }
  if (!prims.length) add("E_EMPTY", "no primitives");

  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const q of prims) {
    const nums = [q.x1, q.y1, q.x2, q.y2, q.x, q.y, q.cx, q.cy, q.r, q.w, q.h, ...(q.pts || [])];
    for (const n of nums) if (typeof n === "number" && !Number.isFinite(n)) add("E_NAN_PRIM", `${q.k}/${q.layer}`);
    if (q.k === "rect" && (q.w <= 0 || q.h <= 0)) add("E_ZERO_RECT", `${q.layer} ${q.w}×${q.h}`);
    if (q.k === "circle" && q.r <= 0) add("E_ZERO_CIRCLE", q.layer);
    if (q.k === "text" && (!q.s || q.s.length > 96)) add("E_TEXT", String(q.s).slice(0, 24));

    // Extents per primitive kind. A rect stores its lower-left corner (x,y) with
    // (w,h) — sampling x-w/x+w would read it as a centre and report phantom
    // out-of-frame geometry, so each kind contributes its own true corners.
    const xs = finite([
      q.x1, q.x2,
      q.k === "rect" ? q.x : undefined,
      q.k === "rect" ? q.x + q.w : undefined,
      q.k === "circle" ? q.cx - q.r : undefined,
      q.k === "circle" ? q.cx + q.r : undefined,
      q.k === "text" ? q.x : undefined,
      ...(q.k === "poly" ? q.pts.filter(/** @param {number} _ @param {number} i @returns {boolean} */ (_, i) => i % 2 === 0) : []),
    ]);
    const ys = finite([
      q.y1, q.y2,
      q.k === "rect" ? q.y : undefined,
      q.k === "rect" ? q.y + q.h : undefined,
      q.k === "circle" ? q.cy - q.r : undefined,
      q.k === "circle" ? q.cy + q.r : undefined,
      q.k === "text" ? q.y : undefined,
      ...(q.k === "poly" ? q.pts.filter(/** @param {number} _ @param {number} i @returns {boolean} */ (_, i) => i % 2 === 1) : []),
    ]);
    if (q.k === "text") {
      const w = q.s.length * q.size * 0.52;
      if (q.anchor === "end") xs.push(q.x - w);
      else if (q.anchor === "middle") xs.push(q.x - w / 2, q.x + w / 2);
      else xs.push(q.x + w);
    }
    if (xs.length) { minX = Math.min(minX, ...xs); maxX = Math.max(maxX, ...xs); }
    if (ys.length) { minY = Math.min(minY, ...ys); maxY = Math.max(maxY, ...ys); }
  }
  const M = SHEET.MARGIN;
  if (!Number.isFinite(minX) || minX < M - 6 || maxX > SHEET.W - M + 6 || minY < M - 6 || maxY > SHEET.H - M + 6) {
    add("E_EXTENTS", `${minX.toFixed(1)},${minY.toFixed(1)} → ${maxX.toFixed(1)},${maxY.toFixed(1)}`);
  }

  // Panel collision: each drawing panel declares its bounding box as a "panel"
  // primitive the renderer ignores. Overlapping boxes mean a panel has drifted
  // into its neighbour's band at extreme parameters.
  const panels = prims.filter((q) => q.k === "panel");
  for (let i = 0; i < panels.length; i += 1) {
    for (let j = i + 1; j < panels.length; j += 1) {
      const a = panels[i], b = panels[j];
      const hit = a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
      if (hit) add("E_OVERLAP", `${a.id} ∩ ${b.id}`);
    }
  }

  const layers = new Set(prims.map((q) => q.layer));
  const needLayers = [...REQUIRED_LAYERS[sheet.sheet]];
  if (sheet.sheet === 4 && meta.foundation && meta.foundation.wellDiaM > 0) needLayers.push("FOUND-WELL");
  for (const l of needLayers) if (!layers.has(l)) add("E_LAYER_MISSING", l);

  const text = prims.filter((q) => q.k === "text").map((q) => q.s).join(" | ");
  for (const label of REQUIRED_LABELS[sheet.sheet]) if (!text.includes(label)) add("E_LABEL_MISSING", label);

  if (sheet.sheet === 5) {
    /** @type {any[]} */
    const walls = meta.walls || [];
    if (walls.length !== 2) add("E_WALL_COUNT", `${walls.length}`);
    const sides = new Set(walls.map((x) => x.side));
    if (!sides.has("left") || !sides.has("right")) add("E_WALL_SIDE", [...sides].join(","));

    // The walls are emitted as polygons on SUB-ABUT. Auditing the *drawn*
    // geometry — not the formula that produced it — is what catches a wall that
    // springs from the wrong nose, or is rotated 90° out of the abutment face.
    // The formula checks below only fire when a clamp is removed; these fire on
    // the drawing itself, which is the failure the ABTL floor cannot hide.
    const wallPolys = prims.filter((q) => q.k === "poly" && q.layer === "SUB-ABUT");
    if (wallPolys.length !== walls.length) {
      add("E_WALL_GEOM", `${wallPolys.length} wing-wall polygon(s) for ${walls.length} wall(s)`);
    }
    const noses = wallPolys.map((q) => q.pts[0]);
    if (new Set(noses).size !== noses.length) add("E_WALL_ANCHOR", `wing walls share a nose: ${noses.join(", ")}`);

    walls.forEach((wall, i) => {
      if (!(wall.returnM > 0)) add("E_RETURN", `${wall.side} return ${wall.returnM}`);
      if (!(wall.lengthM >= wall.faceRunM)) add("E_HYPOTENUSE", `${wall.lengthM} < ${wall.faceRunM}`);
      if (wall.splayDeg < 14 || wall.splayDeg > 61) add("E_SPLAY_RANGE", `${wall.splayDeg}`);
      const q = wallPolys[i];
      if (!q) return;
      // The face run is measured along the abutment face, which is horizontal: a
      // drawn wall whose horizontal extent is not the face run has been rotated
      // out of plane (run and return swapped).
      const xs = q.pts.filter(/** @param {number} _ @param {number} k @returns {boolean} */ (_, k) => k % 2 === 0);
      const drawnRun = Math.max(...xs) - Math.min(...xs);
      if (!(drawnRun > 0) || Math.abs(drawnRun - mm(wall.faceRunM)) > mm(0.5)) {
        add("E_FACE_RUN", `${wall.side} drawn ${drawnRun.toFixed(1)} vs face run ${mm(wall.faceRunM).toFixed(1)}`);
      }
    });
    if (!/SOURCE: [A-Z]+/.test(text)) add("E_ABTL_SOURCE", "no ladder rung printed");
    // Guards the `carriageway + 2` floor in normalizeParams. Unreachable on real
    // input by design — exercised by the `no-abtl-clamp` mutation drill.
    if (p.abtl < p.carriageway + 2) add("E_ABTL_SHORT", `${p.abtl} vs cw ${p.carriageway}`);
  }

  if (sheet.sheet === 4) {
    const f = meta.foundation;
    if (f.nPiles !== f.rows * f.cols) add("E_PILE_COUNT", `${f.nPiles}`);
    if (f.nPiles < 1 || f.nPiles > 9) add("E_PILE_RANGE", `${f.nPiles}`);
  }

  return { ok: issues.length === 0, issues };
}

/* ── DXF export of the same primitive stream ─────────────────────────────── */

/** AutoCAD Color Index entries, as [aci, r, g, b] — used to map a layer's hex. */
const ACI_PALETTE = [
  [1, 255, 0, 0], [2, 255, 255, 0], [3, 0, 255, 0], [4, 0, 255, 255],
  [5, 0, 0, 255], [6, 255, 0, 255], [7, 255, 255, 255], [8, 128, 128, 128],
  [9, 192, 192, 192], [30, 255, 128, 0], [40, 255, 191, 128], [50, 255, 255, 128],
  [90, 128, 255, 128], [130, 128, 255, 255], [150, 128, 191, 255], [170, 128, 128, 255],
  [190, 191, 128, 255], [210, 255, 128, 255], [250, 51, 51, 51], [251, 91, 91, 91],
  [252, 132, 132, 132], [253, 173, 173, 173], [254, 214, 214, 214],
];

/** Dash patterns for the linetypes the layer table references: name -> segments. */
const LTYPES = { CONTINUOUS: [], DASHED: [12.7, -6.35], DASHDOT: [12.7, -6.35, 0, -6.35] };

/** @param {string} hex @returns {number[]} */
const hexToRgb = (hex) => {
  const h = hex.replace("#", "");
  return [Number.parseInt(h.slice(0, 2), 16), Number.parseInt(h.slice(2, 4), 16), Number.parseInt(h.slice(4, 6), 16)];
};

/** Nearest ACI to a layer's hex colour, so the DXF matches the preview. */
/** @param {string} hex @returns {number} */
const aciFor = (hex) => {
  const [r, g, b] = hexToRgb(hex);
  let best = 7;
  let bestD = Infinity;
  for (const [aci, pr, pg, pb] of ACI_PALETTE) {
    const d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2;
    if (d < bestD) { bestD = d; best = aci; }
  }
  return best;
};

/** Axis-aligned extents of the primitive stream, for $EXTMIN / $EXTMAX. */
/** @param {any[]} prims @returns {{ minX: number, minY: number, maxX: number, maxY: number }} */
function dxfExtents(prims) {
  let minX = 0, minY = 0, maxX = 0, maxY = 0;
  for (const q of prims) {
    const xs = [];
    const ys = [];
    if (q.k === "line") { xs.push(q.x1, q.x2); ys.push(q.y1, q.y2); }
    else if (q.k === "rect" || q.k === "panel") { xs.push(q.x, q.x + q.w); ys.push(q.y, q.y + q.h); }
    else if (q.k === "circle") { xs.push(q.cx - q.r, q.cx + q.r); ys.push(q.cy - q.r, q.cy + q.r); }
    else if (q.k === "poly") { for (let i = 0; i < q.pts.length; i += 2) { xs.push(q.pts[i]); ys.push(q.pts[i + 1]); } }
    else if (q.k === "text") { xs.push(q.x); ys.push(q.y); }
    for (const v of xs) { minX = Math.min(minX, v); maxX = Math.max(maxX, v); }
    for (const v of ys) { minY = Math.min(minY, v); maxY = Math.max(maxY, v); }
  }
  return { minX: r2(minX), minY: r2(minY), maxX: r2(maxX), maxY: r2(maxY) };
}

/** @param {{ prims: any[] }} sheet @returns {string} */
export function toDxf(sheet) {
  const ext = dxfExtents(sheet.prims);
  const head = [
    "0", "SECTION", "2", "HEADER",
    "9", "$ACADVER", "1", "AC1015",
    "9", "$INSUNITS", "70", "4",
    "9", "$EXTMIN", "10", String(ext.minX), "20", String(ext.minY), "30", "0",
    "9", "$EXTMAX", "10", String(ext.maxX), "20", String(ext.maxY), "30", "0",
    "0", "ENDSEC",
    "0", "SECTION", "2", "TABLES",
    "0", "TABLE", "2", "LTYPE", "70", String(Object.keys(LTYPES).length),
  ];
  // Layer records reference DASHED / DASHDOT; without an LTYPE table a strict
  // reader cannot resolve them and the import degrades.
  for (const [name, segs] of Object.entries(LTYPES)) {
    const total = segs.reduce((a, s) => a + Math.abs(s), 0);
    head.push("0", "LTYPE", "2", name, "70", "0", "3", `${name} line`, "72", "65", "73", String(segs.length), "40", String(total));
    for (const s of segs) head.push("49", String(s));
  }
  head.push("0", "ENDTAB", "0", "TABLE", "2", "LAYER", "70", String(Object.keys(LAYERS).length));
  for (const [name, [color, lt]] of Object.entries(LAYERS)) {
    head.push("0", "LAYER", "2", name, "70", "0", "62", String(aciFor(color)), "6", lt);
  }
  head.push("0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES");
  const body = [];
  for (const q of sheet.prims) {
    if (q.k === "line") body.push("0", "LINE", "8", q.layer, "10", String(q.x1), "20", String(q.y1), "11", String(q.x2), "21", String(q.y2));
    else if (q.k === "rect") {
      const c = [[q.x, q.y], [q.x + q.w, q.y], [q.x + q.w, q.y + q.h], [q.x, q.y + q.h]];
      for (let i = 0; i < 4; i += 1) {
        const a = c[i], b = c[(i + 1) % 4];
        body.push("0", "LINE", "8", q.layer, "10", String(a[0]), "20", String(a[1]), "11", String(b[0]), "21", String(b[1]));
      }
    } else if (q.k === "circle") body.push("0", "CIRCLE", "8", q.layer, "10", String(q.cx), "20", String(q.cy), "40", String(q.r));
    else if (q.k === "poly") {
      // A closed poly must close: append the first vertex so the chain returns.
      const pts = q.closed === false ? q.pts : [...q.pts, q.pts[0], q.pts[1]];
      for (let i = 0; i + 3 < pts.length; i += 2) {
        body.push("0", "LINE", "8", q.layer, "10", String(pts[i]), "20", String(pts[i + 1]), "11", String(pts[i + 2]), "21", String(pts[i + 3]));
      }
    } else if (q.k === "text") {
      const just = q.anchor === "middle" ? "1" : q.anchor === "end" ? "2" : "0";
      body.push("0", "TEXT", "8", q.layer, "10", String(q.x), "20", String(q.y), "40", String(q.size), "1", q.s, "72", just);
      // Justified TEXT needs the second alignment point (11/21) or CAD ignores it.
      if (just !== "0") body.push("11", String(q.x), "21", String(q.y));
    }
  }
  return [...head, ...body, "0", "ENDSEC", "0", "EOF"].join("\n");
}

export const DETAIL_DEFAULTS = Object.freeze({
  projectName: "Yogendra Borse Bridge", number: "GAD-001", revision: "R0", spans: 3,
  carriageway: 7.5, abtl: 13, splay: 45, deckRl: 112.4, hflRl: 104.5, lwlRl: 99.8,
  foundingRl: 96.2, pileDiaMm: 1000, pileLenM: 12, capTMm: 1200, spacingM: 2,
  rows: 2, cols: 2, wellDiaM: 0, mainBarMm: 25, sbckPa: 240, pierLenM: 9,
  pierWidM: 1.2, pierHgtM: 6, capWidM: 1.8, capDepM: 0.65, abtHgtM: 2.8,
  retHgtM: 2.5, girders: 4, girderDepthMm: 900, deckThickMm: 200, bearingsPerPier: 4,
});
