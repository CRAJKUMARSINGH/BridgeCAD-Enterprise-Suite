import { abutmentProfile, SHEET, wingWallGeometry, type Prim } from "./detailGeometry";
import type { OverviewAbutment } from "./Sheet01Overview";

export const FIELD_GROUPS = [
  { title: "Deck & supports", fields: [
    ["deckWidth", "Overall deck width", "m", 5, 24, .05],
    ["carriageway", "Clear carriageway", "m", 5, 12, .05],
    ["slab", "Slab depth", "mm", 120, 1800, 10],
    ["girder", "Girder depth below slab", "mm", 0, 3500, 10],
    ["bearing", "Bearing / pedestal", "mm", 0, 600, 10],
    ["gap", "Pier joint gap", "mm", 0, 300, 5],
    ["pierWidth", "Pier shaft width", "m", .4, 5, .05],
  ] },
  { title: "Pier foundations", fields: [
    ["pierShaftAcross", "Shaft width across bridge", "m", .4, 12, .05],
    ["pierFootingAlong", "Footing length along bridge", "m", .5, 16, .05],
    ["pierFootingAcross", "Footing width across bridge", "m", .5, 18, .05],
    ["pierFootingDepth", "Footing thickness", "m", .2, 4, .05],
    ["pierScourCover", "Footing top below scour", "m", 0, 20, .05],
  ] },
  { title: "PCC pads · all footings", fields: [
    ["pccDepth", "PCC pad thickness", "mm", 0, 1500, 5],
    ["pccProjection", "PCC projection beyond each footing edge", "mm", 0, 1000, 5],
  ] },
  { title: "Abutment section", fields: [
    ["stemHeight", "Stem height", "m", .5, 12, .05],
    ["stemWidth", "Cantilever stem width", "m", .2, 3, .05],
    ["capWidth", "Cap width", "m", .45, 5, .05],
    ["capDepth", "Cap depth", "m", .2, 3, .05],
    ["frontBatter", "Face batter (1:n)", "n", 2, 40, .5],
    ["backBatter", "Back batter (1:n)", "n", 2, 40, .5],
    ["toe", "Toe projection", "m", 0, 6, .05],
    ["heel", "Heel projection", "m", 0, 6, .05],
    ["footing", "Footing depth", "m", .2, 3, .05],
    ["dirt", "Dirt wall thickness", "m", .15, .8, .025],
  ] },
  { title: "Plan & drainage", fields: [
    ["abtl", "Abutment face length", "m", 6, 26, .05],
    ["splay", "Wing splay from face", "°", 15, 60, 1],
    ["wingThickness", "Wing wall thickness", "m", .15, 1.2, .025],
    ["weepDiameter", "Weep hole diameter", "mm", 0, 200, 5],
    ["weepSpacing", "Weep hole pitch", "m", .5, 4, .05],
  ] },
  { title: "Levels", fields: [
    ["road", "Finished road RL", "m", -50, 400, .01],
    ["wear", "Wearing course", "mm", 0, 180, 5],
    ["hfl", "High flood RL", "m", -50, 400, .01],
    ["ofl", "Ordinary flood RL", "m", -50, 400, .01],
    ["ngl", "Natural ground RL", "m", -60, 400, .01],
    ["scour", "Design scour RL", "m", -60, 400, .01],
  ] },
] as const;

type Field = typeof FIELD_GROUPS[number]["fields"][number][0];
export type WingType = "SPLAYED" | "STRAIGHT" | "CURTAIN";
export const WING_TYPES: Array<{ id: WingType; label: string }> = [
  { id: "SPLAYED", label: "Splayed / flared" },
  { id: "STRAIGHT", label: "Straight return" },
  { id: "CURTAIN", label: "Inline curtain" },
];
export type Draft = {
  name: string; family: OverviewAbutment; spans: string; wingType: WingType;
  foundingLevels?: Record<string, string>;
} & Record<Field, string>;
export type ViewId = "elevation" | "section" | "front" | "plan" | "foundation" | "ga-plan";
export type DraftView = { id: ViewId; title: string; prims: Prim[]; box: [number, number, number, number] };

const BASE: Draft = {
  name: "River crossing", family: "CANTILEVER", spans: "12, 12, 12", wingType: "SPLAYED",
  deckWidth: "11.1", carriageway: "7.5", slab: "650", girder: "0", bearing: "150", gap: "40", pierWidth: "1.5",
  pierShaftAcross: "3", pierFootingAlong: "3.2", pierFootingAcross: "5", pierFootingDepth: "0.8", pierScourCover: "0.5",
  pccDepth: "300", pccProjection: "150",
  stemHeight: "3.2", stemWidth: "0.6", capWidth: "1.1", capDepth: "0.75", frontBatter: "10", backBatter: "3",
  toe: "1.5", heel: "1.5", footing: "0.8", dirt: "0.3", abtl: "13", splay: "35",
  wingThickness: "0.3", weepDiameter: "100", weepSpacing: "1.5", road: "110.98", wear: "65", hfl: "107.3", ofl: "108.4", ngl: "105.2", scour: "102.4",
};

export const DRAFT_PRESETS: Draft[] = [
  BASE,
  { ...BASE, name: "Gravity abutment", family: "GRAVITY", spans: "15, 18, 15", slab: "800", capWidth: "1.45", stemHeight: "4" },
  { ...BASE, name: "Full-height wall", family: "FULL_HEIGHT_WALL", spans: "18.75, 18.75, 18.75", slab: "230", girder: "1400", stemHeight: "4.2", hfl: "106" },
];

export function isDraft(value: unknown): value is Draft {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  const levels = item.foundingLevels;
  return typeof item.name === "string" && typeof item.spans === "string"
    && WING_TYPES.some((type) => type.id === item.wingType)
    && DRAFT_PRESETS.some((preset) => preset.family === item.family)
    && FIELD_GROUPS.every(({ fields }) => fields.every(([key]) => typeof item[key] === "string"))
    && (levels === undefined || (!!levels && typeof levels === "object" && !Array.isArray(levels)
      && Object.values(levels).every((level) => typeof level === "string")));
}

function parseSpanSchedule(input: string): number[] {
  const spans: number[] = [];
  for (const entry of input.split(",")) {
    const match = /^(?:(\d+)\s*[x×]\s*)?(\+?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)$/i.exec(entry.trim());
    if (!match) return [];
    const count = match[1] === undefined ? 1 : Number(match[1]);
    const length = Number(match[2]);
    if (count < 1 || spans.length + count > 12 || length < 4 || length > 80) return [];
    for (let i = 0; i < count; i++) spans.push(length);
  }
  return spans;
}

export function assessDraft(draft: Draft) {
  const spans = parseSpanSchedule(draft.spans);
  const values = Object.fromEntries(FIELD_GROUPS.flatMap(({ fields }) => fields.map(([key]) => [key, Number(draft[key])]))) as Record<Field, number>;
  const errors = FIELD_GROUPS.flatMap(({ fields }) => fields.flatMap(([key, label, unit, min, max]) =>
    !draft[key].trim() || !Number.isFinite(values[key]) || values[key] < min || values[key] > max
      ? [`${label} must be ${min}–${max} ${unit}.`] : []));
  const p = values;
  const slabTop = p.road - p.wear / 1000;
  const soffit = slabTop - (p.slab + p.girder) / 1000;
  const capTop = soffit - p.bearing / 1000;
  const capBase = capTop - p.capDepth;
  const stations = spans.reduce((all, span) => [...all, all[all.length - 1] + span], [0]);
  const total = stations[stations.length - 1];
  const abutmentDefault = capBase - p.stemHeight - p.footing;
  const pierDefault = p.scour - p.pierScourCover - p.pierFootingDepth;

  function footing(id: string, station: number, defaultRl: number, depth: number) {
    const input = draft.foundingLevels?.[id]?.trim();
    const base = input ? Number(input) : defaultRl;
    return { id, station, defaultRl, base, top: base + depth };
  }

  const a1 = footing("A1", 0, abutmentDefault, p.footing);
  const a2 = footing("A2", total, abutmentDefault, p.footing);
  const piers = stations.slice(1, -1).map((station, i) => footing(`P${i+1}`, station, pierDefault, p.pierFootingDepth));
  const supports = [a1, ...piers, a2];
  for (const support of supports) {
    if (!Number.isSafeInteger(Math.round(support.base * 1000))) {
      errors.push(`${support.id} footing base RL must be a valid level in metres.`);
    } else if (support.id.startsWith("A") && capBase - support.top < .5 - 1e-9) {
      errors.push(`${support.id} footing must leave at least 500 mm of stem below the cap.`);
    } else if (support.id.startsWith("P") && support.top >= capBase) {
      errors.push(`${support.id} footing top must be below the cap soffit.`);
    }
  }
  const checks = [
    { label: "Span schedule", ok: spans.length > 0, detail: "Enter 1–12 spans of 4–80 m each. Use commas or count × length, for example 3 x 12, 18." },
    { label: "Carriageway", ok: p.deckWidth >= p.carriageway, detail: "Overall deck width must cover the carriageway." },
    { label: "Abutment face", ok: p.abtl >= Math.max(p.deckWidth, p.carriageway + 2), detail: "Abutment face must cover the deck and exceed the carriageway by at least 2 m for this wing layout." },
    { label: "Wall fit", ok: p.dirt < p.capWidth && (draft.family !== "CANTILEVER" || p.stemWidth <= p.capWidth), detail: "Check dirt-wall and cantilever stem thickness against the cap width." },
    { label: "Pier footing fit", ok: spans.length <= 1 || (p.pierWidth < p.pierFootingAlong
      && p.pierShaftAcross < p.pierFootingAcross && p.pierFootingAlong < Math.min(...spans)),
    detail: "Fit the shaft inside the footing and keep the footing length below the shortest span." },
    { label: "Joint fit", ok: spans.length <= 1 || p.gap / 1000 < Math.min(...spans), detail: "Pier joint gap must fit between supports." },
    { label: "Flood clearance", ok: p.hfl < soffit, detail: "High flood RL must be below the structural soffit." },
    { label: "Scour datum", ok: p.scour < p.hfl, detail: "Design scour RL must be below high flood RL." },
  ];
  return { spans, stations, total, p, slabTop, soffit, capTop, capBase, a1, a2, piers, supports,
    checks, errors: [...errors, ...checks.filter((check) => !check.ok).map((check) => check.detail)] };
}

export function summarizeDraft(draft: Draft) {
  const { p, total, slabTop, capTop, capBase, a1, a2, supports } = assessDraft(draft);
  const footingWidth = p.capWidth + p.toe + p.heel + p.dirt;
  const stemArea = draft.family === "GRAVITY"
    ? footingWidth * 0.72
    : draft.family === "FULL_HEIGHT_WALL"
      ? p.capWidth
      : p.stemWidth;
  const dirtHeight = Math.max(slabTop - capTop, 0);
  const fixedArea = p.capWidth * p.capDepth + footingWidth * p.footing + p.dirt * dirtHeight;
  return {
    overallLength: total,
    deckConcrete: total * p.deckWidth * p.slab / 1000,
    abutmentConcrete: 2 * fixedArea + stemArea * (2 * capBase - a1.top - a2.top),
    footingWidth,
    footingBaseRl: Math.min(...supports.map(({ base }) => base)),
  };
}

type Point = readonly [number, number];
const asMm = (m: number) => m * 1000;
const mmText = (m: number) => `${Math.round(asMm(m))} mm`;
const APPROACH_LENGTH_M = 3.5;
const APPROACH_DEPTH_M = .3;

function diagram(id: ViewId, title: string, textM: number) {
  const prims: Prim[] = [];
  const points: Point[] = [];
  function line(layer: string, [x1, y1]: Point, [x2, y2]: Point) {
    points.push([x1, y1], [x2, y2]);
    prims.push({ k: "line", layer, x1: asMm(x1), y1: asMm(y1), x2: asMm(x2), y2: asMm(y2) });
  }
  function shape(layer: string, vertices: Point[]) {
    points.push(...vertices);
    prims.push({ k: "poly", layer, pts: vertices.flatMap(([x, y]) => [asMm(x), asMm(y)]), closed: true });
  }
  function rect(layer: string, x: number, y: number, w: number, h: number) {
    shape(layer, [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]);
  }
  function circle(layer: string, x: number, y: number, r: number) {
    if (r <= 0) return;
    points.push([x-r, y-r], [x+r, y+r]);
    prims.push({ k: "circle", layer, cx: asMm(x), cy: asMm(y), r: asMm(r) });
  }
  function text(s: string, x: number, y: number, anchor: "start" | "middle" | "end" = "start", layer = "TEXT") {
    const width = s.length * textM * .64;
    const left = x - (anchor === "middle" ? width / 2 : anchor === "end" ? width : 0);
    points.push([left, y-textM*.3], [left+width, y+textM]);
    prims.push({ k: "text", layer, x: asMm(x), y: asMm(y), s, size: asMm(textM), anchor });
  }
  function dimH(a: number, b: number, edge: number, y: number, label = mmText(b-a)) {
    if (b <= a) return;
    line("DIM", [a, edge], [a, y]); line("DIM", [b, edge], [b, y]);
    line("DIM", [a, y], [b, y]);
    for (const x of [a, b]) line("DIM", [x-textM*.27, y-textM*.27], [x+textM*.27, y+textM*.27]);
    text(label, (a+b)/2, y+textM*.45, "middle", "DIM");
  }
  function dimV(a: number, b: number, edge: number, x: number, label = mmText(b-a)) {
    if (b <= a) return;
    line("DIM", [edge, a], [x, a]); line("DIM", [edge, b], [x, b]);
    line("DIM", [x, a], [x, b]);
    for (const y of [a, b]) line("DIM", [x-textM*.27, y-textM*.27], [x+textM*.27, y+textM*.27]);
    text(label, x+textM*.55, (a+b)/2+textM*.65, "start", "DIM");
  }
  function finish(): DraftView {
    const center = (Math.min(...points.map(([x]) => x)) + Math.max(...points.map(([x]) => x))) / 2;
    const bottom = Math.min(...points.map(([, y]) => y));
    text("REVIEW DRAFT", center, bottom - textM * 1.5, "middle");
    const xs = points.map(([x]) => x), ys = points.map(([, y]) => y);
    const left = Math.min(...xs)-textM*2, right = Math.max(...xs)+textM*2;
    const low = Math.min(...ys)-textM*2, high = Math.max(...ys)+textM*2;
    return { id, title, prims, box: [asMm(left), SHEET.H-asMm(high), asMm(right-left), asMm(high-low)] };
  }
  return { line, shape, rect, circle, text, dimH, dimV, finish };
}

function shiftVertically(prim: Prim, offset: number): Prim {
  switch (prim.k) {
    case "line": return { ...prim, y1: prim.y1 + offset, y2: prim.y2 + offset };
    case "circle": return { ...prim, cy: prim.cy + offset };
    case "poly": return { ...prim, pts: prim.pts.map((coordinate, i) => i % 2 ? coordinate + offset : coordinate) };
    default: return { ...prim, y: prim.y + offset };
  }
}

function combineGaAndPlan(elevation: DraftView, plan: DraftView, labelSize: number): DraftView {
  const [ex, ey, ew, eh] = elevation.box;
  const [px, py, pw, ph] = plan.box;
  const left = Math.min(ex, px);
  const right = Math.max(ex+ew, px+pw);
  const planTop = ey+eh+labelSize*2.8;
  const sheetTop = ey-labelSize*2.2;
  const heading = (s: string, top: number): Prim => ({
    k: "text", layer: "TEXT-HEADER", x: left+labelSize,
    y: SHEET.H-top+labelSize*.65, size: labelSize, anchor: "start", s,
  });
  return {
    id: "ga-plan",
    title: "GAD elevation and bridge plan",
    box: [left, sheetTop, right-left, planTop+ph-sheetTop],
    prims: [heading("LONGITUDINAL ELEVATION", ey), ...elevation.prims,
      heading("BRIDGE PLAN · FOUNDATIONS", planTop), ...plan.prims.map((prim) => shiftVertically(prim, py-planTop))],
  };
}

export function buildDraftViews(draft: Draft): DraftView[] {
  const { p, spans, stations, total, slabTop: structureTop, soffit, capTop, capBase, a1, a2, piers, supports, errors } = assessDraft(draft);
  if (errors.length) return [];
  const slabBottom = structureTop-p.slab/1000;
  const { base, top: shaftBase } = a1;
  const stemHeight = capBase - shaftBase;
  const pccDepth = p.pccDepth / 1000;
  const pccProjection = pccDepth ? p.pccProjection / 1000 : 0;
  const padNote = `PCC PAD ${mmText(pccDepth)} THICK · ${mmText(pccProjection)} PROJECTION ALL ROUND`;
  const wing = wingWallGeometry({ abtl: p.abtl, carriageway: p.carriageway, splay: p.splay, deckRl: p.road, foundingRl: base });
  const model = (paper: number) => paper * SHEET.SCALE / 1000;
  const gravity = draft.family === "GRAVITY";
  function abutmentFootprint(footing: typeof a1) {
    const profile = abutmentProfile("left", 0, 0, capBase-footing.top, {
      capW: p.capWidth, capD: p.capDepth, dirtW: p.dirt, above: structureTop-capTop,
      frontBatter: p.frontBatter, backBatter: p.backBatter, toeOff: p.toe, heelOff: p.heel, footD: p.footing,
    });
    return {
      ...footing, profile,
      frontToe: gravity ? model(profile.x7) : p.capWidth+p.toe,
      backHeel: gravity ? model(profile.x10) : -p.dirt-p.heel,
    };
  }
  const leftAbutment = abutmentFootprint(a1);
  const rightAbutment = abutmentFootprint(a2);
  const { frontToe, backHeel, profile } = leftAbutment;
  const xFace = -p.dirt;
  const approachEnd = xFace - APPROACH_LENGTH_M;
  const approachSoffit = structureTop - APPROACH_DEPTH_M;
  const deckEdge = p.deckWidth/2;

  function drawPadSection(view: ReturnType<typeof diagram>, left: number, footingBase: number, width: number) {
    if (pccDepth) view.rect("FOUND-PCC", left-pccProjection, footingBase-pccDepth, width+2*pccProjection, pccDepth);
  }

  function drawPadPlan(view: ReturnType<typeof diagram>, left: number, width: number, depth: number) {
    if (pccDepth) view.rect("FOUND-PCC", left-pccProjection, -depth/2-pccProjection, width+2*pccProjection, depth+2*pccProjection);
  }

  function drawSupport(view: ReturnType<typeof diagram>, abutment: typeof leftAbutment, sign: number) {
    const { station, base, top: shaftBase, frontToe, backHeel, profile } = abutment;
    const project = (vertices: Point[]) => vertices.map(([x, y]): Point => [station+x*sign, y]);
    drawPadSection(view, station+(sign > 0 ? backHeel : -frontToe), base, frontToe-backHeel);
    if (gravity) {
      const gravityPoints = profile.pts.reduce<Point[]>((out, x, i, list) => {
        if (i % 2 === 0) out.push([model(x), capBase+model(list[i+1])]);
        return out;
      }, []);
      view.shape("ABUT-PROF", project(gravityPoints));
      return;
    }
    view.shape("FOUND-CAP", project([[backHeel, base], [frontToe, base], [frontToe, shaftBase], [backHeel, shaftBase]]));
    if (draft.family === "FULL_HEIGHT_WALL") {
      view.shape("SUB-ABUT", project([[xFace, shaftBase], [p.capWidth, shaftBase], [p.capWidth, capTop],
        [0, capTop], [0, structureTop], [xFace, structureTop]]));
      return;
    }
    view.shape("SUB-ABUT", project([[xFace, capBase], [xFace+p.stemWidth, capBase],
      [xFace+p.stemWidth, shaftBase], [xFace, shaftBase]]));
    view.shape("SUB-ABUT", project([[xFace, capBase], [p.capWidth, capBase], [p.capWidth, capTop], [xFace, capTop]]));
    view.shape("ABUT-PROF", project([[xFace, capTop], [0, capTop], [0, structureTop], [xFace, structureTop]]));
  }

  function drawApproach(view: ReturnType<typeof diagram>, station: number, inward: 1 | -1, dimY: number) {
    const wall = station + inward * xFace;
    const end = station + inward * approachEnd;
    const left = Math.min(wall, end);
    const right = Math.max(wall, end);
    view.rect("CIVIL-ROAD", left, approachSoffit, right-left, APPROACH_DEPTH_M);
    if (p.wear) view.rect("SUPER-WEARING", left, structureTop, right-left, p.wear/1000);
    view.dimH(left, right, p.road, dimY);
  }

  const gaText = Math.max(.27, total*.017);
  const ga = diagram("elevation", "Longitudinal elevation", gaText);
  const tightSpans = Math.min(...spans) < gaText*8;
  const scheduleBase = Math.min(...supports.map(({ base }) => base))-pccDepth;
  const halfGap = p.gap / 2000;
  const foundation = diagram("foundation", "Bridge foundation plan", gaText);
  const planHalfWidth = Math.max(deckEdge, p.abtl/2+pccProjection,
    piers.length ? p.pierFootingAcross/2+pccProjection : 0);
  for (let i=0; i<spans.length; i++) {
    const x = stations[i]+(i ? halfGap : 0), end = stations[i+1]-(i < spans.length-1 ? halfGap : 0);
    ga.rect("SUPER-DECK", x, slabBottom, end-x, p.slab/1000);
    if (p.girder) ga.rect("SUPER-GIRDER", x, soffit, end-x, p.girder/1000);
    if (p.wear) ga.rect("SUPER-WEARING", x, structureTop, end-x, p.wear/1000);
    if (!tightSpans) ga.dimH(stations[i], stations[i+1], p.road+gaText*.8, p.road+gaText*2.2);
    foundation.rect("HIDD", x, -deckEdge, end-x, p.deckWidth);
  }
  ga.dimH(0, total, p.road+gaText*2.3, p.road+gaText*4.3, `${mmText(total)} C/C`);
  for (const [index, { id, station }] of supports.entries()) {
    ga.text(id, station,
      p.road+gaText*(tightSpans && index%2 ? 1.65 : .55), "middle");
  }
  for (const { station: x, top, base } of piers) {
    const capW = Math.max(p.pierWidth+.4, p.gap/1000+.4);
    ga.rect("SUB-PIER", x-capW/2, capBase, capW, p.capDepth);
    if (p.bearing) ga.rect("SUB-BEARING", x-.3, capTop, .6, p.bearing/1000);
    for (const face of [x-p.pierWidth/2, x+p.pierWidth/2]) ga.line("SUB-PIER", [face, capBase], [face, top]);
    drawPadSection(ga, x-p.pierFootingAlong/2, base, p.pierFootingAlong);
    ga.rect("FOUND-PIER", x-p.pierFootingAlong/2, base, p.pierFootingAlong, p.pierFootingDepth);
    ga.line("CL", [x, p.road], [x, capBase]);
  }
  drawSupport(ga, leftAbutment, 1); drawSupport(ga, rightAbutment, -1);
  if (pccDepth) {
    const tipX = backHeel-pccProjection;
    const tipY = base-pccDepth/2;
    const labelX = tipX-gaText*.75;
    const labelY = tipY-gaText*1.1;
    ga.line("FOUND-PCC", [tipX, tipY], [labelX, labelY]);
    ga.text(`PCC PAD ${mmText(pccDepth)}`, labelX-gaText*.2, labelY, "end", "FOUND-PCC");
  }
  drawApproach(ga, 0, 1, p.road+gaText*2.2);
  drawApproach(ga, total, -1, p.road+gaText*2.2);
  if (p.bearing) {
    ga.rect("SUB-BEARING", -.3, capTop, .6, p.bearing/1000);
    ga.rect("SUB-BEARING", total-.3, capTop, .6, p.bearing/1000);
  }
  const outsideApproaches = Math.max(-backHeel+pccProjection, -rightAbutment.backHeel+pccProjection, -approachEnd);
  for (const [label, rl, layer] of [
    ["HFL", p.hfl, "CIVIL-HFL"], ["NGL", p.ngl, "CIVIL-NGL"],
  ] as const) {
    ga.line(layer, [-outsideApproaches-gaText, rl], [total+outsideApproaches+gaText, rl]);
    ga.text(`${label} ${rl.toFixed(3)} m`, total+outsideApproaches+gaText*1.35, rl, "start", "TEXT-LEVEL");
  }
  ga.text(`ROAD RL ${p.road.toFixed(3)} m`, total+outsideApproaches+gaText*1.35, p.road, "start", "TEXT-LEVEL");
  if (piers.length) {
    const labelPier = piers.reduce((lowest, pier) => {
      const difference = pier.base - lowest.base;
      if (Math.abs(difference) < 1e-9) {
        return Math.abs(pier.station-total/2) < Math.abs(lowest.station-total/2) ? pier : lowest;
      }
      return difference < 0 ? pier : lowest;
    });
    const footingEdge = labelPier.station+p.pierFootingAlong/2;
    const leaderX = footingEdge+pccProjection+gaText*.65;
    const leaderY = labelPier.base-pccDepth-gaText*.65;
    ga.line("TEXT-LEVEL", [footingEdge, labelPier.base], [leaderX, leaderY]);
    ga.text(`PIER FOOTING BASE RL ${labelPier.base.toFixed(3)} m`, leaderX+gaText*.2, leaderY, "start", "TEXT-LEVEL");
  }
  if (spans.length > 1) ga.text(`PIER JOINT ${p.gap ? `${p.gap} mm` : "GAP UNSPECIFIED"}`, total/2, scheduleBase-gaText*2, "middle");
  if (tightSpans) for (let start=0; start<spans.length; start+=4) {
    const lengths = spans.slice(start, start+4).map((span, i) => `S${start+i+1} ${mmText(span)}`);
    ga.text(lengths.join("   /   "), total/2, scheduleBase-gaText*(3.8+start/4*1.4), "middle", "DIM");
  }

  const section = diagram("section", "Abutment section · A1", .21);
  drawSupport(section, leftAbutment, 1);
  drawApproach(section, 0, 1, p.road+.76);
  section.dimV(approachSoffit, structureTop, approachEnd, approachEnd-.95);
  section.text("APPROACH SLAB", (xFace+approachEnd)/2, p.road+.22, "middle");
  section.rect("SUPER-DECK", 0, slabBottom, p.capWidth+1.4, p.slab/1000);
  if (p.bearing) section.rect("SUB-BEARING", Math.max(0, (p.capWidth-.6)/2), capTop, .6, p.bearing/1000);
  if (p.girder) section.rect("SUPER-GIRDER", 0, soffit, p.capWidth+1.4, p.girder/1000);
  if (p.wear) section.rect("SUPER-WEARING", 0, structureTop, p.capWidth+1.4, p.wear/1000);
  section.dimH(backHeel, frontToe, base, base-.75, `${mmText(frontToe-backHeel)} FOOTING`);
  section.dimH(backHeel, gravity ? model(profile.x12) : xFace, shaftBase, base-.38, `HEEL ${mmText(p.heel)}`);
  section.dimH(frontToe-p.toe, frontToe, shaftBase, base-.38, `TOE ${mmText(p.toe)}`);
  section.dimV(shaftBase, capBase, backHeel, backHeel-.8, `${mmText(stemHeight)} STEM`);
  section.dimV(base, shaftBase, frontToe, frontToe+.55);
  section.dimV(capBase, capTop, p.capWidth, frontToe+.55, `${mmText(p.capDepth)} CAP`);
  section.dimH(xFace, 0, structureTop, p.road+.42, `DIRT WALL ${mmText(p.dirt)}`);
  if (draft.family === "CANTILEVER") section.text(`STEM ${mmText(p.stemWidth)}`, xFace+.1, shaftBase+.25);
  section.text(`ROAD RL ${p.road.toFixed(3)} m`, p.capWidth+.35, p.road+.23, "start", "TEXT-LEVEL");
  section.text(`FOOTING BASE RL ${base.toFixed(3)} m`, backHeel, base-1.32, "start", "TEXT-LEVEL");
  if (pccDepth) section.text(padNote, backHeel, base-Math.max(1.72, pccDepth+.55), "start", "FOUND-PCC");
  if (gravity) section.text(`FACE 1:${p.frontBatter}  /  BACK 1:${p.backBatter}`, xFace+.12, shaftBase+.25);

  const front = diagram("front", "Abutment front elevation · A1", .30);
  const width = p.abtl/2;
  drawPadSection(front, -width, base, p.abtl);
  front.rect("FOUND-CAP", -width, base, p.abtl, p.footing);
  front.rect("SUB-ABUT", -width, shaftBase, p.abtl, stemHeight);
  front.rect("SUB-ABUT", -width, capBase, p.abtl, p.capDepth);
  front.rect("ABUT-PROF", -width, capTop, p.abtl, structureTop-capTop);
  front.line("CL", [0, base-.4], [0, p.road+.6]);
  const holes = Math.floor((p.abtl-.6)/p.weepSpacing)+1;
  if (p.weepDiameter) for (let i=0; i<holes; i++) front.circle("SUB-ABUT", (i-(holes-1)/2)*p.weepSpacing, shaftBase+Math.min(.65,stemHeight/2), p.weepDiameter/2000);
  front.dimH(-width, width, structureTop, p.road+.92, `${mmText(p.abtl)} ABUTMENT FACE`);
  front.dimV(base, structureTop, width, width+.57);
  if (p.weepDiameter) front.text(`${holes} WEEP HOLES Ø${p.weepDiameter} mm @ ${mmText(p.weepSpacing)} C/C`, 0, base-.82, "middle");

  drawPadPlan(foundation, backHeel, frontToe-backHeel, p.abtl);
  drawPadPlan(foundation, total-rightAbutment.frontToe, rightAbutment.frontToe-rightAbutment.backHeel, p.abtl);
  foundation.rect("FOUND-CAP", backHeel, -width, frontToe-backHeel, p.abtl);
  foundation.rect("FOUND-CAP", total-rightAbutment.frontToe, -width, rightAbutment.frontToe-rightAbutment.backHeel, p.abtl);
  foundation.rect("CIVIL-ROAD", approachEnd, -deckEdge, APPROACH_LENGTH_M, p.deckWidth);
  foundation.rect("CIVIL-ROAD", total-xFace, -deckEdge, APPROACH_LENGTH_M, p.deckWidth);
  foundation.line("CL", [approachEnd-gaText, 0], [total-approachEnd+gaText, 0]);
  for (const [index, { id, station }] of supports.entries()) {
    foundation.line("CL", [station, -planHalfWidth-gaText], [station, planHalfWidth+gaText*.65]);
    foundation.text(id, station,
      planHalfWidth+gaText*(tightSpans && index%2 ? 2.4 : 1.15), "middle");
  }
  for (const { station: x } of piers) {
    drawPadPlan(foundation, x-p.pierFootingAlong/2, p.pierFootingAlong, p.pierFootingAcross);
    foundation.rect("FOUND-PIER", x-p.pierFootingAlong/2, -p.pierFootingAcross/2, p.pierFootingAlong, p.pierFootingAcross);
    foundation.rect("SUB-PIER", x-p.pierWidth/2, -p.pierShaftAcross/2, p.pierWidth, p.pierShaftAcross);
  }
  foundation.dimH(0, total, -planHalfWidth-gaText, -planHalfWidth-gaText*2.2, `${mmText(total)} C/C`);
  if (piers.length) {
    foundation.text(`TYPICAL PIER FOOTING ${mmText(p.pierFootingAlong)} ALONG × ${mmText(p.pierFootingAcross)} ACROSS`,
      total/2, -planHalfWidth-gaText*3.7, "middle");
  } else {
    foundation.text("SINGLE SPAN · END ABUTMENT FOOTINGS", total/2, -planHalfWidth-gaText*3.7, "middle");
  }
  if (pccDepth) foundation.text(padNote, total/2, -planHalfWidth-gaText*5, "middle", "FOUND-PCC");

  const plan = diagram("plan", "Abutment plan · A1", .28);
  drawPadPlan(plan, backHeel, frontToe-backHeel, p.abtl);
  plan.rect("FOUND-CAP", backHeel, -width, frontToe-backHeel, p.abtl);
  plan.rect("SUB-ABUT", xFace, -width, p.capWidth+p.dirt, p.abtl);
  plan.rect("ABUT-PROF", xFace, -width, p.dirt, p.abtl);
  plan.rect("CIVIL-ROAD", approachEnd, -deckEdge, APPROACH_LENGTH_M, p.deckWidth);
  const visibleDeckRun = Math.min(spans[0]/2, 5);
  plan.rect("SUPER-DECK", 0, -deckEdge, visibleDeckRun, p.deckWidth);
  const wingRun = draft.wingType === "SPLAYED" ? wing.returnM : draft.wingType === "STRAIGHT" ? Math.max(1.5, wing.returnM) : .6;
  for (const sign of [-1, 1]) {
    plan.line("STRUC-OUTLINE", [p.capWidth, sign*p.carriageway/2], [visibleDeckRun, sign*p.carriageway/2]);
    const splayed = draft.wingType === "SPLAYED";
    const dx = splayed ? -wing.faceRunM / wing.lengthM * p.wingThickness : 0;
    const dy = splayed ? -sign * wing.returnM / wing.lengthM * p.wingThickness : -sign * p.wingThickness;
    const start = sign*p.carriageway/2, end = splayed ? sign*width : start;
    plan.shape("SUB-ABUT", [[xFace, start], [xFace-wingRun, end],
      [xFace-wingRun+dx, end+dy], [xFace+dx, start+dy]]);
  }
  plan.line("CL", [Math.min(approachEnd, xFace-wingRun)-.35, 0], [visibleDeckRun+.38, 0]);
  plan.dimV(-width, width, xFace-wingRun, xFace-wingRun-.63, `${mmText(p.abtl)} FACE`);
  plan.dimH(xFace-wingRun, xFace, width, width+.76, `${mmText(wingRun)} RETURN`);
  plan.dimH(approachEnd, xFace, -deckEdge, -width-1.4, `${mmText(APPROACH_LENGTH_M)} APPROACH SLAB`);
  plan.dimV(-deckEdge, deckEdge, visibleDeckRun, visibleDeckRun+.64, `${mmText(p.deckWidth)} DECK`);
  const wingLabel = WING_TYPES.find((type) => type.id === draft.wingType)?.label ?? "Splayed / flared";
  plan.text(`${wingLabel.toUpperCase()} · ${mmText(wingRun)} RETURN`, xFace-wingRun, -width-.76);

  const elevation = ga.finish();
  const foundationPlan = foundation.finish();
  return [elevation, section.finish(), front.finish(), plan.finish(), foundationPlan,
    combineGaAndPlan(elevation, foundationPlan, asMm(gaText * 1.15))];
}

export function canExportDraft(draft: unknown): draft is Draft {
  return isDraft(draft) && assessDraft(draft).errors.length === 0;
}
