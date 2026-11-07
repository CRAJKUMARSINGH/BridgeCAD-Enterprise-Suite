/**
 * compliance.js — clause-mapped IRC / MoRTH compliance checks for the drawing
 * workspace.
 *
 * The checks are computed from the very same parameters that drive sheets 04
 * and 05, so the panel and the drawing can never disagree about what was
 * provided. Each check carries the clause it cites, the value provided, the
 * value required and a one-line reason — a check that cannot cite its clause
 * and edition is not a check (mirrors `bridgecad_qa.compliance_engine`, whose
 * `ClauseRef` and `utilisation = demand / capacity` model this module follows).
 *
 * Pure and framework-free: no DOM, no imports, so the Node test harness can
 * load it directly.
 */

/** @typedef {"min" | "max" | "range"} Relation */

/**
 * @typedef {object} ComplianceCheck
 * @property {string} id            stable check id (CC-1xx)
 * @property {string} standard      e.g. "IRC:21"
 * @property {string} edition       e.g. "2000"
 * @property {string} clause        e.g. "Table 12"
 * @property {string} citation      "IRC:21-2000 Table 12"
 * @property {string} title         short human title
 * @property {number} provided      numeric value the design provides
 * @property {number} required      numeric limit (`lo` or `hi`; nominal for a range)
 * @property {string} unit          unit suffix ("m", "mm", "°", "–", ...)
 * @property {Relation} relation    how `provided` is compared with `required`
 * @property {number} demand        demand side of utilisation (clamped to the band)
 * @property {number} capacity      capacity side of utilisation
 * @property {string} comparator    rendered requirement, e.g. "≥ 600 mm"
 * @property {number} utilisation   demand / capacity; ≤ 1 passes
 * @property {boolean} pass
 * @property {"PASS" | "FAIL"} verdict
 * @property {string} rationale     one-line engineering reason
 */

/* ── small numeric helpers (kept local: this module must stay import-free) ── */

/** @param {*} v @param {number} d @returns {number} */
const num = (v, d) => {
  const n = typeof v === "number" ? v : Number.parseFloat(String(v ?? ""));
  return Number.isFinite(n) ? n : d;
};

/** @param {number} n @param {number} lo @param {number} hi @returns {number} */
const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n));

/** @param {number} n @returns {number} */
const r2 = (n) => Math.round(n * 100) / 100;

/** @param {number} n @returns {number} */
const r3 = (n) => Math.round(n * 1000) / 1000;

/** @param {number} n @returns {number} */
const dp = (n) => (Math.abs(n) >= 100 ? 0 : Math.abs(n) >= 10 ? 1 : 2);

/** @param {number} n @param {number} d @returns {string} */
const fmt = (n, d) => n.toFixed(d);

/** The wing-wall splay is a design band, not a single floor. */
const SPLAY_LO = 15;
const SPLAY_HI = 60;

/**
 * Build the clause-mapped compliance report for one project + detail parameter
 * set. `project` supplies the span geometry; `detail` supplies the
 * substructure/foundation parameters (the same shape `normalizeParams` emits).
 *
 * @param {Record<string, any>} [project]
 * @param {Record<string, any>} [detail]
 * @returns {{ checks: ComplianceCheck[], nChecks: number, nPassed: number, nFailed: number, ok: boolean, governing: ComplianceCheck | null, maxUtilisation: number }}
 */
export function buildComplianceReport(project = {}, detail = {}) {
  const spanM = clamp(num(project.spanLength, 12), 1, 100);
  const widthM = clamp(num(project.width, 12), 1, 60);
  const carriageway = clamp(num(detail.carriageway, 7.5), 5, 12);
  const abtl = num(detail.abtl, 12);
  const splay = clamp(num(detail.splay, 45), 15, 60);
  const deckThickMm = clamp(num(detail.deckThickMm, 650), 150, 400);
  const girderDepthMm = clamp(num(detail.girderDepthMm, 0), 0, 1800);
  const deckRl = num(detail.deckRl, 100);
  const hflRl = num(detail.hflRl, deckRl - 2);
  const pileDiaMm = clamp(num(detail.pileDiaMm, 600), 600, 1500);
  const capTMm = clamp(num(detail.capTMm, 800), 800, 1800);
  const spacingM = clamp(num(detail.spacingM, 2.5), 1.5, 4);
  const rows = Math.round(clamp(num(detail.rows, 2), 1, 3));
  const cols = Math.round(clamp(num(detail.cols, 2), 1, 3));

  // Effective structural depth: the girder depth when the superstructure is a
  // T-beam / girder, otherwise the slab itself.
  const effDepthM = (girderDepthMm + deckThickMm) / 1000;
  const spanDepth = spanM / Math.max(effDepthM, 1e-6);
  const spanDepthLimit = girderDepthMm > 0 ? 12 : 20; // IRC:21-2000 Table 12

  const impactFactor = 4.5 / (6 + spanM); // IRC:6-2017 Clause 3.5
  const soffitRl = deckRl - effDepthM;
  const freeboardM = soffitRl - hflRl; // IRC:5-2015 Clause 22.1
  const pileSpacingMinM = 2.5 * (pileDiaMm / 1000); // IRC:78-2011 Clause 708.3
  const nPiles = rows * cols;
  const kerbBarrierM = 2.4; // kerb + crash barrier, both edges — MoRTH 5th Rev Sec. 2.2

  /**
   * @type {Array<{ id: string, standard: string, edition: string, clause: string, title: string,
   *   provided: number, required: number, unit: string, relation: Relation, rationale: string }>}
   */
  const specs = [
    {
      id: "CC-101", standard: "IRC:21", edition: "2000", clause: "Table 12",
      title: "Span / effective depth ratio",
      provided: r2(spanDepth), required: spanDepthLimit, unit: "–", relation: "max",
      rationale: `Span ${fmt(spanM, 2)} m over an effective depth of ${fmt(effDepthM, 3)} m; ${girderDepthMm > 0 ? "RCC T-beam" : "RCC solid slab"} band.`,
    },
    {
      id: "CC-102", standard: "IRC:21", edition: "2000", clause: "Clause 304.7",
      title: "Minimum deck slab thickness",
      provided: deckThickMm, required: 200, unit: "mm", relation: "min",
      rationale: "Minimum structural slab thickness for an RC deck — governs cover and punching.",
    },
    {
      id: "CC-103", standard: "IRC:6", edition: "2017", clause: "Clause 3.5",
      title: "Impact factor ceiling",
      provided: r3(impactFactor), required: 0.5, unit: "–", relation: "max",
      rationale: "IRC:6 caps the Class A dynamic allowance at IF = 4.5 / (6 + span), never above 0.50.",
    },
    {
      id: "CC-104", standard: "IRC:5", edition: "2015", clause: "Clause 22.1",
      title: "Freeboard above HFL",
      provided: r3(freeboardM), required: 0.6, unit: "m", relation: "min",
      rationale: "Deck soffit minus HFL must clear the design flood with margin for afflux and debris.",
    },
    {
      id: "CC-105", standard: "IRC:78", edition: "2011", clause: "Clause 708.1",
      title: "Pile diameter",
      provided: pileDiaMm, required: 600, unit: "mm", relation: "min",
      rationale: "Minimum bored cast-in-situ pile diameter adopted for bridge foundations.",
    },
    {
      id: "CC-106", standard: "IRC:78", edition: "2011", clause: "Clause 708.3",
      title: "Pile spacing / diameter",
      provided: r2(spacingM), required: r2(pileSpacingMinM), unit: "m", relation: "min",
      rationale: "Centre-to-centre pile spacing must not fall below 2.5 × diameter for group efficiency.",
    },
    {
      id: "CC-107", standard: "MoRTH", edition: "5th Rev", clause: "Sec. 2.7.1",
      title: "Abutment cap thickness",
      provided: capTMm, required: 600, unit: "mm", relation: "min",
      rationale: "The cap carries the pedestals, dirt wall and corbel loads into the piles.",
    },
    {
      id: "CC-108", standard: "BridgeCAD", edition: "ABT-006", clause: "Abutment length envelope",
      title: "ABTL versus carriageway",
      provided: r2(abtl), required: r2(carriageway + 2), unit: "m", relation: "min",
      rationale: "Abutment face length must cover the carriageway plus both edge margins — the ladder floor.",
    },
    {
      id: "CC-109", standard: "BridgeCAD", edition: "FND-002", clause: "Pile group size",
      title: "Pile group count",
      provided: nPiles, required: 9, unit: "No.", relation: "max",
      rationale: "The drawn pile group is capped at 3 rows × 3 columns by the foundation layout engine.",
    },
    {
      id: "CC-110", standard: "BridgeCAD", edition: "WNG-001", clause: "Wing-wall splay envelope",
      title: "Wing-wall splay from abutment face",
      provided: r2(splay), required: 45, unit: "°", relation: "range",
      rationale: "A splay outside 15°–60° either buries the wing wall in the deck end or overshoots the embankment.",
    },
    {
      id: "CC-111", standard: "MoRTH", edition: "5th Rev", clause: "Sec. 2.2",
      title: "Deck width over carriageway",
      provided: r2(widthM), required: r2(carriageway + kerbBarrierM), unit: "m", relation: "min",
      rationale: "Out-to-out deck width must accommodate the carriageway plus both kerbs and crash barriers.",
    },
  ];

  const checks = specs.map(finalise);
  const nPassed = checks.filter((c) => c.pass).length;
  const nFailed = checks.length - nPassed;
  const maxUtilisation = checks.reduce((m, c) => Math.max(m, c.utilisation), 0);
  const governing = checks.find((c) => c.utilisation === maxUtilisation) ?? null;

  return {
    checks,
    nChecks: checks.length,
    nPassed,
    nFailed,
    ok: nFailed === 0,
    governing,
    maxUtilisation: r3(maxUtilisation),
  };
}

/**
 * Turn a spec into a whole check: render the comparator, derive
 * `utilisation = demand / capacity` (≤ 1 passes) and the PASS/FAIL verdict.
 *
 * @param {{ id: string, standard: string, edition: string, clause: string, title: string,
 *   provided: number, required: number, unit: string, relation: Relation, rationale: string }} spec
 * @returns {ComplianceCheck}
 */
function finalise(spec) {
  const { provided, required, unit, relation } = spec;
  // A dimensionless check ("–") is rendered without a unit suffix.
  const shown = unit === "–" ? "" : ` ${unit}`;

  let demand;
  let capacity;
  let comparator;

  if (relation === "min") {
    demand = required;
    capacity = provided;
    comparator = `≥ ${fmt(required, dp(required))}${shown}`;
  } else if (relation === "max") {
    demand = provided;
    capacity = required;
    comparator = `≤ ${fmt(required, dp(required))}${shown}`;
  } else {
    // Range: clamp the provided value to the band so demand / capacity keeps
    // its meaning — inside the band it is exactly 1, outside it exceeds 1.
    const bounded = clamp(provided, SPLAY_LO, SPLAY_HI);
    demand = provided < SPLAY_LO ? SPLAY_LO : provided > SPLAY_HI ? provided : bounded;
    capacity = provided < SPLAY_LO ? provided : provided > SPLAY_HI ? SPLAY_HI : bounded;
    comparator = `${fmt(SPLAY_LO, 0)}–${fmt(SPLAY_HI, 0)}${shown}`;
    capacity = Math.max(capacity, 1e-9);
  }

  const raw = capacity > 0 ? demand / capacity : demand > 0 ? Infinity : 0;
  const utilisation = r3(Math.min(raw, 1e6));
  const pass = raw <= 1 + 1e-9;

  return {
    ...spec,
    citation: `${spec.standard}-${spec.edition} ${spec.clause}`,
    demand,
    capacity,
    comparator,
    utilisation,
    pass,
    verdict: pass ? "PASS" : "FAIL",
  };
}

/** Stable list of the check ids this module emits. */
export const CHECK_IDS = Object.freeze([
  "CC-101", "CC-102", "CC-103", "CC-104", "CC-105", "CC-106",
  "CC-107", "CC-108", "CC-109", "CC-110", "CC-111",
]);
