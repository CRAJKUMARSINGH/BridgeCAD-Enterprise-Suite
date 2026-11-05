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
const mm = (m) => (m * 1000) / SHEET.SCALE;

const NUM = (v, d) => {
  const n = typeof v === "number" ? v : Number.parseFloat(String(v ?? ""));
  return Number.isFinite(n) ? n : d;
};
const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n));
const r2 = (n) => Math.round(n * 100) / 100;

/** Layer table: name -> [colour, linetype]. */
export const LAYERS = Object.freeze({
  "FOUND-CAP": ["#d9c26a", "CONTINUOUS"],
  "FOUND-PILE": ["#d9c26a", "CONTINUOUS"],
  "FOUND-WELL": ["#d9c26a", "CONTINUOUS"],
  "SUB-PIER": ["#9fc3d8", "CONTINUOUS"],
  "SUB-ABUT": ["#9fc3d8", "CONTINUOUS"],
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
  line: (layer, x1, y1, x2, y2) => ({ k: "line", layer, x1: r2(x1), y1: r2(y1), x2: r2(x2), y2: r2(y2) }),
  rect: (layer, x, y, w, h) => ({ k: "rect", layer, x: r2(x), y: r2(y), w: r2(w), h: r2(h) }),
  circle: (layer, cx, cy, r) => ({ k: "circle", layer, cx: r2(cx), cy: r2(cy), r: r2(r) }),
  text: (layer, x, y, s, size = TEXT_H, anchor = "start") => ({ k: "text", layer, x: r2(x), y: r2(y), s: String(s), size, anchor }),
  poly: (layer, pts, closed = true) => ({ k: "poly", layer, pts: pts.flat().map(r2), closed }),
};

function hatch(out, layer, x, y, w, h, step = 3) {
  if (w <= 0 || h <= 0) return;
  for (let o = -h; o < w; o += step) {
    const x1 = x + Math.max(o, 0);
    const y1 = y + Math.max(-o, 0);
    const run = Math.min(w - Math.max(o, 0), h - Math.max(-o, 0));
    if (run > 0) out.push(P.line(layer, x1, y1, x1 + run, y1 + run));
  }
}

function dimH(out, x1, x2, y, text) {
  out.push(P.line("DIM", x1, y, x2, y));
  out.push(P.line("DIM", x1, y - 2, x1, y + 2));
  out.push(P.line("DIM", x2, y - 2, x2, y + 2));
  out.push(P.text("DIM", (x1 + x2) / 2, y + 3.2, text, TEXT_H, "middle"));
}

function dimV(out, x, y1, y2, text) {
  out.push(P.line("DIM", x, y1, x, y2));
  out.push(P.line("DIM", x - 2, y1, x + 2, y1));
  out.push(P.line("DIM", x - 2, y2, x + 2, y2));
  out.push(P.text("DIM", x - 1.6, (y1 + y2) / 2, text, TEXT_H, "middle"));
}

/* ── parameter normalisation: every downstream guarantee lives here ───────── */

export function normalizeParams(input = {}) {
  const carriageway = clamp(NUM(input.carriageway, 7.5), 5, 12);
  const abtlRaw = clamp(NUM(input.abtl, 13), 6, 26);
  const abtl = Math.max(abtlRaw, carriageway + 2);
  const splay = clamp(NUM(input.splay, 45), 15, 60);
  const deckRl = clamp(NUM(input.deckRl, 112.4), 0, 400);
  const foundingRl = clamp(NUM(input.foundingRl, 96.2), -50, deckRl);
  const hflRl = clamp(NUM(input.hflRl, 104.5), foundingRl, deckRl);
  const lwlRl = clamp(NUM(input.lwlRl, 99.8), foundingRl, hflRl);
  const rows = Math.round(clamp(NUM(input.rows, 2), 1, 3));
  const cols = Math.round(clamp(NUM(input.cols, 2), 1, 3));
  return {
    projectName: String(input.projectName || "Untitled bridge").slice(0, 48),
    number: String(input.number || "GAD-001").slice(0, 18),
    revision: String(input.revision || "R0").slice(0, 6),
    spans: Math.round(clamp(NUM(input.spans, 3), 1, 12)),
    carriageway,
    abtl,
    futl: NUM(input.futl, 0),
    footl: NUM(input.footl, 0),
    futrl: NUM(input.futrl, 0),
    alcl: NUM(input.alcl, 0),
    alcw: NUM(input.alcw, 0),
    splay,
    deckRl,
    hflRl,
    lwlRl,
    foundingRl,
    pileDiaMm: clamp(NUM(input.pileDiaMm, 1000), 600, 1500),
    pileLenM: clamp(NUM(input.pileLenM, 12), 4, 25),
    capTMm: clamp(NUM(input.capTMm, 1200), 800, 1800),
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
  };
}

/* ── ABTL ladder: ABTL -> FUTL -> FOOTL -> FUTRL -> ALCL -> ALCW -> 13.0 ──── */

const LADDER = ["abtl", "futl", "footl", "futrl", "alcl", "alcw"];

export function resolveAbtl(p) {
  for (const rung of LADDER) {
    const v = NUM(p[rung], 0);
    if (v > 0) return { valueM: v, source: rung.toUpperCase() };
  }
  return { valueM: 13, source: "DEFAULT" };
}

/* ── wing walls, measured from the abutment face ─────────────────────────── */

export function wingWallGeometry(p) {
  const { valueM: abtl, source } = resolveAbtl(p);
  const splay = clamp(NUM(p.splay, 45), 0, 88.999);
  const faceRunM = Math.max((abtl - p.carriageway) / 2, 0);
  const rad = (splay * Math.PI) / 180;
  const lengthM = Math.cos(rad) ? faceRunM / Math.cos(rad) : 0;
  const returnM = lengthM * Math.sin(rad);
  const topLevelM = p.deckRl - 1.2;
  const baseLevelM = Math.min(p.foundingRl, topLevelM) - 0.5;
  const walls = ["left", "right"].map((side) => ({
    side, splayDeg: splay, faceRunM, lengthM, returnM, topLevelM, baseLevelM,
  }));
  return { abtl, source, splayDeg: splay, faceRunM, lengthM, returnM, walls };
}

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

const baseMeta = (p, sheet) => ({
  sheet,
  projectName: p.projectName,
  number: p.number,
  revision: p.revision,
  scale: SHEET.SCALE,
  params: p,
  layersUsed: [],
});

function frame(out, title, meta) {
  const M = SHEET.MARGIN;
  out.push(P.rect("FRAME", M, M, SHEET.W - 2 * M, SHEET.H - 2 * M));
  out.push(P.rect("FRAME", M + 4, M + 4, SHEET.W - 2 * M - 8, SHEET.H - 2 * M - 8));
  out.push(P.text("TEXT-HEADER", M + 8, SHEET.H - M - 10, title, 4.2));
  out.push(P.text("TEXT", SHEET.W - M - 8, SHEET.H - M - 10, "NOT FOR CONSTRUCTION · REVIEW ISSUE", 2.2, "end"));
  const tb = { x: SHEET.W - 205, y: 34 };
  out.push(P.rect("FRAME", tb.x, tb.y, 189, 96));
  [24, 24, 24].forEach((d, i) => out.push(P.line("FRAME", tb.x, tb.y + 24 * (i + 1), tb.x + 189, tb.y + 24 * (i + 1))));
  out.push(P.line("FRAME", tb.x + 104, tb.y + 48, tb.x + 104, tb.y + 72));
  out.push(P.text("TEXT-HEADER", tb.x + 5, tb.y + 88, "BRIDGECAD · IRC / MoRTH", 2.6));
  out.push(P.text("TEXT", tb.x + 5, tb.y + 66, meta.projectName, 2.4));
  out.push(P.text("TEXT", tb.x + 5, tb.y + 42, `${meta.number} · REV ${meta.revision}`, 2.4));
  out.push(P.text("TEXT", tb.x + 109, tb.y + 42, `SCALE 1:${meta.scale}`, 2.4));
  out.push(P.text("TEXT", tb.x + 5, tb.y + 18, `SHEET ${String(meta.sheet).padStart(2, "0")}`, 2.4));
  out.push(P.text("TEXT", tb.x + 109, tb.y + 18, "DRAWN / CHECKED", 2.2));
}

function noteBlock(out, notes) {
  notes.forEach((n, i) => out.push(P.text("TEXT", 30, 108 - i * 5.4, n, 2.2)));
}

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

const panel = (out, id, x, y, w, h) => out.push({ k: "panel", layer: "FRAME", id, x: r2(x), y: r2(y), w: r2(w), h: r2(h) });

export function buildSheet4(raw) {
  const p = normalizeParams(raw);
  const f = foundationLayout(p);
  const meta = baseMeta(p, 4);
  const out = [];
  frame(out, "ABUTMENT & PIER FOUNDATION — GENERAL ARRANGEMENT", meta);

  const capW = mm(f.capWm);
  const capT = mm(f.capTm);
  const pileL = mm(Math.min(f.pileLm, 6));
  const pileW = mm(Math.max(f.pileDm, 0.8));

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
  out.push(P.line("CIVIL-SCOUR", xA - 16, yCapB, xA + capW + 16, yCapB));
  out.push(P.line("CIVIL-HFL", xA - 16, yCapT + 8, xA + capW + 16, yCapT + 8));
  out.push(P.line("HIDD", xA - 16, yBear, xA + capW + 16, yBear));
  out.push(P.text("TEXT-LEVEL", xA + capW + 5, yCapB, `SCOUR LEVEL RL ${f.foundingRl.toFixed(3)}`));
  out.push(P.text("TEXT-LEVEL", xA + capW + 5, yPileB, `FOUNDATION LEVEL RL ${(f.foundingRl - f.pileLm - f.capTm).toFixed(3)}`));
  out.push(P.text("TEXT-LEVEL", xA + capW + 5, yBear, `BEARING LEVEL RL ${p.deckRl.toFixed(3)}`));
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
  const rowsD = [["MARK", "Ø (mm)", "LENGTH"]];
  for (let i = 0; i < Math.min(f.nPiles, 6); i += 1) rowsD.push([`P${i + 1}`, p.pileDiaMm.toFixed(0), `${f.pileLm.toFixed(2)} m`]);
  rowsD.forEach((r, i) => {
    r.forEach((c, j) => out.push(P.text(i === 0 ? "TEXT-HEADER" : "TEXT", xD + j * 30, yD - i * 7, c, 2.2)));
    out.push(P.line("FRAME", xD, yD - i * 7 - 2, xD + 86, yD - i * 7 - 2));
  });

  dimH(out, xA, xA + capW, yCapB - 10, `CAP ${f.capWm.toFixed(2)} m`);
  dimV(out, xA - 8, yCapB, yCapT, `CAP ${p.capTMm.toFixed(0)} mm`);
  dimV(out, xA + capW + 26, yPileB, yCapB, `PILE ${f.pileLm.toFixed(2)} m`);
  dimV(out, xA - 8, yCapB, yBear, "BEARING LEVEL");

  scaleBar(out, 30, 125);

  noteBlock(out, [
    "1. All dimensions in metres unless stated otherwise.",
    `2. Safe bearing capacity ${p.sbckPa.toFixed(0)} kPa at founding level RL ${(f.foundingRl - f.pileLm - f.capTm).toFixed(3)}.`,
    `3. Pile cut-off level RL ${f.foundingRl.toFixed(3)}.`,
    "4. Founding stratum to be confirmed by the geotechnical report.",
    "5. Restored on the static deploy — parity with bridgecad_draw/sheets/sheet4_foundation.py.",
  ]);

  meta.layersUsed = [...new Set(out.map((q) => q.layer))];
  meta.foundation = f;
  return { sheet: 4, prims: out, meta };
}

/* ── Sheet 05 — pier, abutment, wing wall / fire wall details ────────────── */

export function buildSheet5(raw) {
  const p = normalizeParams(raw);
  const w = wingWallGeometry(p);
  const f = foundationLayout(p);
  const meta = baseMeta(p, 5);
  meta.walls = w.walls;
  meta.abtlSource = w.source;
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

  /* panel C — abutment elevation, ABTL and both splayed wing walls */
  panel(out, "5C", 305, 130, 270, 170);
  const xC = 320;
  const wC = mm(w.abtl);
  const yAbtB = 235;
  const yAbtT = yAbtB + mm(p.abtHgtM);

  out.push(P.rect("SUB-ABUT", xC, yAbtB, wC, mm(p.abtHgtM)));
  hatch(out, "HTCH", xC, yAbtB, wC, mm(p.abtHgtM), 2.6);
  out.push(P.rect("SUB-ABUT", xC - mm(0.4), yAbtB, mm(0.4), mm(p.retHgtM)));
  out.push(P.rect("SUB-ABUT", xC + wC, yAbtB, mm(0.4), mm(p.retHgtM)));
  out.push(P.line("CL", xC - 5, yAbtB, xC + wC + 5, yAbtB));
  out.push(P.text("TEXT-HEADER", xC, yAbtT + 20, `ABUTMENT A1 — ABTL ${w.abtl.toFixed(2)} m (SOURCE: ${w.source})`, 3));
  out.push(P.text("TEXT-LEVEL", xC, yAbtT + 13, `DECK LEVEL RL ${p.deckRl.toFixed(3)}`));
  out.push(P.text("TEXT-LEVEL", xC, yAbtT + 8, `HFL RL ${p.hflRl.toFixed(3)}`));
  out.push(P.text("TEXT-LEVEL", xC, yAbtT + 3, `LWL RL ${p.lwlRl.toFixed(3)}`));
  out.push(P.text("TEXT-LEVEL", xC, yAbtB - 4, `FOUNDING LEVEL RL ${p.foundingRl.toFixed(3)}`));

  const yWp = 200;
  const thick = mm(0.4);
  for (const wall of w.walls) {
    const sign = wall.side === "left" ? -1 : 1;
    const run = mm(wall.faceRunM);
    const ret = mm(wall.returnM);
    out.push(P.poly("SUB-ABUT", [xC, yWp, xC + ret, yWp + sign * run, xC + ret, yWp + sign * run + sign * thick, xC, yWp + sign * thick], true));
    hatch(out, "HTCH", xC, Math.min(yWp, yWp + sign * run), Math.max(ret, 1), Math.abs(run) || 1, 2.4);
    out.push(P.text("TEXT", xC + ret + 4, yWp + sign * run, `WING WALL ${wall.side.toUpperCase()} — ${wall.lengthM.toFixed(2)} m`, 2.2));
  }
  out.push(P.text("TEXT-HEADER", xC, yWp - 10, `WING WALL SPLAY ${w.splayDeg.toFixed(1)}° FROM ABUTMENT FACE (FACE RUN ${w.faceRunM.toFixed(2)} m, RETURN ${w.returnM.toFixed(2)} m)`, 2.4));
  dimH(out, xC, xC + wC, yAbtB - 12, `ABTL ${w.abtl.toFixed(2)} m`);
  dimV(out, xC - 10, yAbtB, yAbtT, `ABUTMENT ${p.abtHgtM.toFixed(2)} m`);
  dimV(out, xC + wC + 22, yAbtB, yAbtB + mm(p.retHgtM), `RETURN WALL ${p.retHgtM.toFixed(2)} m`);
  dimH(out, xC, xC + mm(w.faceRunM), yWp - 14, `FACE RUN ${w.faceRunM.toFixed(2)} m`);
  dimV(out, xC + mm(w.returnM) + 22, yWp, yWp + mm(w.faceRunM), `RETURN ${w.returnM.toFixed(2)} m`);

  /* panel D — bearing schedule */
  panel(out, "5D", 610, 300, 140, 60);
  const xD = 620;
  const yD = 340;
  out.push(P.text("TEXT-HEADER", xD, yD + 14, "BEARING SCHEDULE", 3));
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

const REQUIRED_LABELS = {
  4: ["FOUNDATION ELEVATION", "SCOUR LEVEL RL", "FOUNDATION LEVEL RL", "BEARING LEVEL RL", "HFL RL", "PILE CAP REINFORCEMENT DETAIL", "PILE SCHEDULE", "FOUNDATION PLAN"],
  5: ["PIER ELEVATION", "SECTION A-A THROUGH PIER", "ABUTMENT A1", "ABTL", "SOURCE:", "WING WALL LEFT", "WING WALL RIGHT", "WING WALL SPLAY", "FACE RUN", "RETURN", "FIRE WALL", "BEARING SCHEDULE", "PILE FOUNDATION LAYOUT PLAN", "PILE FOUNDATION SCHEDULE"],
};

const REQUIRED_LAYERS = {
  4: ["FOUND-CAP", "CIVIL-SCOUR", "CIVIL-HFL", "TEXT-LEVEL", "DIM", "HTCH", "FRAME"],
  5: ["SUB-ABUT", "SUB-PIER", "SUB-BEARING", "FOUND-PILE", "TEXT-HEADER", "DIM", "FRAME"],
};

const finite = (arr) => arr.filter((n) => typeof n === "number" && Number.isFinite(n));

export function audit(sheet) {
  const issues = [];
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
      ...(q.k === "poly" ? q.pts.filter((_, i) => i % 2 === 0) : []),
    ]);
    const ys = finite([
      q.y1, q.y2,
      q.k === "rect" ? q.y : undefined,
      q.k === "rect" ? q.y + q.h : undefined,
      q.k === "circle" ? q.cy - q.r : undefined,
      q.k === "circle" ? q.cy + q.r : undefined,
      q.k === "text" ? q.y : undefined,
      ...(q.k === "poly" ? q.pts.filter((_, i) => i % 2 === 1) : []),
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
    const walls = meta.walls || [];
    if (walls.length !== 2) add("E_WALL_COUNT", `${walls.length}`);
    const sides = new Set(walls.map((x) => x.side));
    if (!sides.has("left") || !sides.has("right")) add("E_WALL_SIDE", [...sides].join(","));
    for (const wall of walls) {
      if (!(wall.faceRunM > 0)) add("E_FACE_RUN", `${wall.faceRunM}`);
      if (!(wall.returnM > 0)) add("E_RETURN", `${wall.returnM}`);
      if (!(wall.lengthM >= wall.faceRunM)) add("E_HYPOTENUSE", `${wall.lengthM} < ${wall.faceRunM}`);
      if (wall.splayDeg < 14 || wall.splayDeg > 61) add("E_SPLAY_RANGE", `${wall.splayDeg}`);
    }
    if (!/SOURCE: [A-Z]+/.test(text)) add("E_ABTL_SOURCE", "no ladder rung printed");
    if (p.abtl < p.carriageway + 1.9) add("E_ABTL_SHORT", `${p.abtl} vs cw ${p.carriageway}`);
  }

  if (sheet.sheet === 4) {
    const f = meta.foundation;
    if (f.nPiles !== f.rows * f.cols) add("E_PILE_COUNT", `${f.nPiles}`);
    if (f.nPiles < 1 || f.nPiles > 9) add("E_PILE_RANGE", `${f.nPiles}`);
  }

  return { ok: issues.length === 0, issues };
}

/* ── DXF export of the same primitive stream ─────────────────────────────── */

export function toDxf(sheet) {
  const head = [
    "0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1015",
    "9", "$INSUNITS", "70", "4", "0", "ENDSEC",
    "0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER", "70", String(Object.keys(LAYERS).length),
  ];
  for (const [name, [color, lt]] of Object.entries(LAYERS)) {
    head.push("0", "LAYER", "2", name, "70", "0", "62", String((Math.abs(hashInt(name)) % 250) + 1), "6", lt);
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
      for (let i = 0; i < q.pts.length - 2; i += 2) body.push("0", "LINE", "8", q.layer, "10", String(q.pts[i]), "20", String(q.pts[i + 1]), "11", String(q.pts[i + 2]), "21", String(q.pts[i + 3]));
    } else if (q.k === "text") body.push("0", "TEXT", "8", q.layer, "10", String(q.x), "20", String(q.y), "40", String(q.size), "1", q.s, "72", q.anchor === "middle" ? "1" : "0");
  }
  return [...head, ...body, "0", "ENDSEC", "0", "EOF"].join("\n");
}

function hashInt(s) {
  let h = 0;
  for (let i = 0; i < s.length; i += 1) h = (h * 31 + s.charCodeAt(i)) | 0;
  return h;
}

export const DETAIL_DEFAULTS = Object.freeze({
  projectName: "Yogendra Borse Bridge", number: "GAD-001", revision: "R0", spans: 3,
  carriageway: 7.5, abtl: 13, splay: 45, deckRl: 112.4, hflRl: 104.5, lwlRl: 99.8,
  foundingRl: 96.2, pileDiaMm: 1000, pileLenM: 12, capTMm: 1200, spacingM: 2,
  rows: 2, cols: 2, wellDiaM: 0, mainBarMm: 25, sbckPa: 240, pierLenM: 9,
  pierWidM: 1.2, pierHgtM: 6, capWidM: 1.8, capDepM: 0.65, abtHgtM: 2.8,
  retHgtM: 2.5, girders: 4, girderDepthMm: 900, deckThickMm: 200, bearingsPerPier: 4,
});
