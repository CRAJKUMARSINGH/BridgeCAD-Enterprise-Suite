/**
 * boq.js — MoRTH-grounded quantity take-off for the drawing workspace.
 *
 * The workspace already knows the geometry parameters that drive sheets 04/05;
 * this module turns those same parameters into a priced Bill of Quantities.
 * Every line carries its MoRTH item code, unit and rate so a reviewer can trace
 * a rupee back to a clause — the rates mirror the seed table in
 * `bridgecad_bill.rates_db` (MoRTH 2024-25 indicative values, INR).
 *
 * Formwork and reinforcement are multiplier lines on concrete volume, exactly as
 * `bridgecad_bill.processor` derives them, so the tab and the Python BOQ agree
 * on how a number was reached. A line that cannot be reached from the drawn
 * parameters is simply not emitted — never a silent default.
 *
 * Pure and framework-free: no DOM, no imports, so the Node test harness can load
 * it directly.
 */

/**
 * @typedef {object} BoqItem
 * @property {string} code      MoRTH item code
 * @property {string} desc      schedule description
 * @property {string} unit      CUM / SQM / RM / MT / EACH
 * @property {number} qty
 * @property {number} rate      INR per unit
 * @property {number} amount    qty × rate, 2 dp
 * @property {string} ref       MoRTH reference
 * @property {string} basis     how the quantity was derived
 */

/**
 * @typedef {object} BoqSection
 * @property {string} code
 * @property {string} title
 * @property {BoqItem[]} items
 * @property {number} total
 */

/* MoRTH 2024-25 indicative rates — mirrors `bridgecad_bill.rates_db._SEED_RATES`.
   Only the codes this take-off emits are carried here. */
const RATES = Object.freeze({
  "301.1": { desc: "Earthwork in excavation for foundations", unit: "CUM", rate: 350, ref: "MORTH 301" },
  "301.2": { desc: "Earthwork in embankment with imported moorum", unit: "CUM", rate: 620, ref: "MORTH 301" },
  "1601.1": { desc: "Reinforcement steel Fe500D (supply & fix)", unit: "MT", rate: 75000, ref: "MORTH 1601" },
  "1701.2": { desc: "Concrete M25 — foundation (pile cap / footing)", unit: "CUM", rate: 7200, ref: "MORTH 1700" },
  "1701.3": { desc: "Concrete M30 — substructure (pier & abutment)", unit: "CUM", rate: 8400, ref: "MORTH 1700" },
  "1701.4": { desc: "Concrete M35 — superstructure girder / deck", unit: "CUM", rate: 9600, ref: "MORTH 1700" },
  "1702.1": { desc: "Formwork — ordinary (plain slab / wall)", unit: "SQM", rate: 950, ref: "MORTH 1700" },
  "1702.2": { desc: "Formwork — curved soffit (T-beam / box girder)", unit: "SQM", rate: 1850, ref: "MORTH 1700" },
  "1801.1": { desc: "Bored cast-in-situ pile dia 600 mm", unit: "RM", rate: 2800, ref: "MORTH 1800" },
  "1801.2": { desc: "Bored cast-in-situ pile dia 1000 mm", unit: "RM", rate: 5500, ref: "MORTH 1800" },
  "1801.3": { desc: "Bored cast-in-situ pile dia 1200 mm", unit: "RM", rate: 7800, ref: "MORTH 1800" },
  "1801.4": { desc: "Bored cast-in-situ pile dia 1500 mm", unit: "RM", rate: 11500, ref: "MORTH 1800" },
  "1801.6": { desc: "Cut off pile head (M25 concrete)", unit: "EACH", rate: 5500, ref: "MORTH 1800" },
  "2601.1": { desc: "Bituminous waterproofing membrane — deck", unit: "SQM", rate: 850, ref: "MORTH 2600" },
  "2601.3": { desc: "Drainage scupper (precast RCC) 150 mm dia", unit: "EACH", rate: 2800, ref: "MORTH 2600" },
  "2701.1": { desc: "Elastomeric bearing pad (400×400×65 mm IRHD60)", unit: "EACH", rate: 12000, ref: "MORTH 2701" },
  "2801.2": { desc: "Strip seal joint (±40 mm movement)", unit: "RM", rate: 12500, ref: "MORTH 2801" },
  "2901.1": { desc: "Approach slab M30 — 3.5 m × full width", unit: "CUM", rate: 8500, ref: "MORTH 2900" },
  "2901.2": { desc: "Weep holes (PVC pipe 100 mm dia)", unit: "EACH", rate: 350, ref: "MORTH 2900" },
  "2901.4": { desc: "Backfill of abutment (select granular)", unit: "CUM", rate: 850, ref: "MORTH 2900" },
  "501.3": { desc: "Bituminous concrete (BC) wearing coat — 40 mm", unit: "SQM", rate: 380, ref: "MORTH 510" },
  "801.1": { desc: "Metal beam crash barrier (W-beam) HDG", unit: "RM", rate: 4200, ref: "MORTH 810" },
  "801.4": { desc: "Thermoplastic road marking — 100 mm wide", unit: "RM", rate: 120, ref: "MORTH 803" },
});

/** The MoRTH rate code for a bored pile of the given diameter.
 * @param {number} diaMm @returns {string} */
function pileCodeFor(diaMm) {
  if (diaMm <= 600) return "1801.1";
  if (diaMm <= 1000) return "1801.2";
  if (diaMm <= 1200) return "1801.3";
  return "1801.4";
}

/** @param {*} v @param {number} d @returns {number} */
const num = (v, d) => {
  const n = typeof v === "number" ? v : Number.parseFloat(String(v ?? ""));
  return Number.isFinite(n) ? n : d;
};

/** @param {number} n @param {number} lo @param {number} hi @returns {number} */
const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n));

/** @param {number} n @returns {number} */
const r3 = (n) => Math.round(n * 1000) / 1000;

/**
 * Round a rupee amount to paise.
 * @param {number} n @returns {number}
 */
const money = (n) => Math.round(n * 100) / 100;

/** Format an INR amount with Indian digit grouping, e.g. 12,34,567.89
 * @param {number} n @returns {string} */
export function formatINR(n) {
  if (!Number.isFinite(n)) return "–";
  const sign = n < 0 ? "-" : "";
  const [whole, frac] = Math.abs(n).toFixed(2).split(".");
  const last3 = whole.slice(-3);
  const rest = whole.slice(0, -3);
  const grouped = rest ? `${rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",")},${last3}` : last3;
  return `${sign}${grouped}.${frac}`;
}

/**
 * Build the priced quantity take-off for one project + detail parameter set.
 *
 * @param {Record<string, any>} [project]
 * @param {Record<string, any>} [detail]
 * @param {{ contingencyPct?: number }} [options]
 * @returns {{ sections: BoqSection[], nItems: number, subtotal: number, contingencyPct: number, contingencyAmount: number, grandTotal: number }}
 */
export function buildBoq(project = {}, detail = {}, options = {}) {
  const spans = Math.round(clamp(num(project.spans, 1), 1, 12));
  const spanLengthM = clamp(num(project.spanLength, 12), 1, 60);
  const widthM = clamp(num(project.width, 12), 1, 60);
  const cwM = clamp(num(detail.carriageway, 7.5), 5, 12);
  const abtl = clamp(num(detail.abtl, 12), 6, 26);
  const splay = clamp(num(detail.splay, 45), 15, 60);

  const pileDiaMm = clamp(num(detail.pileDiaMm, 600), 600, 1500);
  const pileLenM = clamp(num(detail.pileLenM, 6), 4, 25);
  const capTMm = clamp(num(detail.capTMm, 800), 800, 1800);
  const rows = Math.round(clamp(num(detail.rows, 2), 1, 3));
  const cols = Math.round(clamp(num(detail.cols, 2), 1, 3));

  const pierLenM = clamp(num(detail.pierLenM, 9), 3, 10);
  const pierWidM = clamp(num(detail.pierWidM, 1.2), 0.8, 2.5);
  const pierHgtM = clamp(num(detail.pierHgtM, 6), 3, 12);
  const abtHgtM = clamp(num(detail.abtHgtM, 2.8), 1.5, 6);
  const retHgtM = clamp(num(detail.retHgtM, 2.5), 1.2, 5);

  const girders = Math.round(clamp(num(detail.girders, 4), 2, 8));
  const girderDepthMm = clamp(num(detail.girderDepthMm, 0), 0, 1800);
  const deckThickMm = clamp(num(detail.deckThickMm, 650), 150, 400);
  const bearingsPerPier = Math.round(clamp(num(detail.bearingsPerPier, 4), 2, 8));

  // ── Geometry counts ───────────────────────────────────────────────────────
  const totalLengthM = spans * spanLengthM;
  const nPiers = Math.max(0, spans - 1);
  const nAbutments = 2;
  const nSupports = nPiers + nAbutments;
  const perSupportPiles = rows * cols;
  const totalPiles = perSupportPiles * nSupports;
  const pileDiaM = pileDiaMm / 1000;
  const pileRunM = totalPiles * pileLenM;

  // ── Component volumes (m³) ────────────────────────────────────────────────
  const capVol = nSupports * (pierLenM * (pierWidM + 1.2) * (capTMm / 1000));
  const pileVol = totalPiles * (Math.PI / 4) * pileDiaM * pileDiaM * pileLenM;
  const foundationVol = capVol + pileVol;

  const pierShaftVol = nPiers * (pierLenM * pierWidM * pierHgtM);
  const abutBodyVol = nAbutments * (abtl * abtHgtM * 1.2);
  const faceRunM = Math.max((abtl - cwM) / 2, 0);
  const wingLenM = faceRunM / Math.max(Math.cos((splay * Math.PI) / 180), 0.5);
  const wingVol = 4 * (wingLenM * retHgtM * 0.3);

  const appSlabVol = 2 * 3.5 * widthM * 0.3;

  const deckVol = totalLengthM * widthM * (deckThickMm / 1000);
  const girderVol = girders * totalLengthM * ((girderDepthMm / 1000) * 0.35);

  // ── Drainage counts (dirt wall weep holes @ 3 m, both walls) ──────────────
  const nWeep = nAbutments * Math.max(2, Math.round(abtl / 3));
  const barrierM = (totalLengthM + 2 * 3.5) * 2;
  const nScuppers = Math.max(4, Math.round(totalLengthM / 6) * 2);
  const nBearings = bearingsPerPier * nSupports;

  /** @type {Array<{ code: string, qty: number, desc?: string, basis: string }>} */
  const items = [
    { code: "301.1", qty: foundationVol * 4.5, basis: "foundation concrete volume × 4.5 (excavation allowance)" },
    { code: "301.2", qty: Math.max(0, foundationVol * 4.5 - foundationVol * 1.2), basis: "excavation − displaced foundation volume" },

    { code: pileCodeFor(pileDiaMm), qty: pileRunM, desc: `Bored cast-in-situ pile dia ${pileDiaMm.toFixed(0)} mm`, basis: `${totalPiles} piles × ${pileLenM.toFixed(2)} m` },
    { code: "1801.6", qty: totalPiles, basis: `${rows}×${cols} pile group × ${nSupports} supports` },
    { code: "1701.2", qty: capVol, desc: "Concrete M25 — pile cap / footing", basis: `${nSupports} caps × ${pierLenM.toFixed(2)} × ${(pierWidM + 1.2).toFixed(2)} × ${(capTMm / 1000).toFixed(2)} m` },
    { code: "1702.1", qty: capVol * 3.2, desc: "Formwork — pile cap soffit and sides", basis: "cap concrete volume × 3.2" },
    { code: "1601.1", qty: capVol * 0.12, desc: "Reinforcement Fe500D — pile caps", basis: "cap concrete volume × 0.12 t/cum" },

    { code: "1701.3", qty: pierShaftVol + abutBodyVol + wingVol, desc: "Concrete M30 — pier, abutment and wing walls", basis: "pier shaft + abutment body + wing walls" },
    { code: "1702.1", qty: pierShaftVol * 4.5 + abutBodyVol * 4.2 + wingVol * 4.0, desc: "Formwork — pier, abutment and wing walls", basis: "each concrete volume × its formwork ratio" },
    { code: "1601.1", qty: pierShaftVol * 0.09 + abutBodyVol * 0.08 + wingVol * 0.07, desc: "Reinforcement Fe500D — pier, abutment and wing walls", basis: "each concrete volume × its rebar ratio" },
    { code: "2901.1", qty: appSlabVol, desc: "Concrete M30 — approach slab both ends", basis: "2 ends × 3.5 m × width × 0.30 m" },
    { code: "2901.2", qty: nWeep, basis: `dirt walls @ 3 m spacing — ${nWeep} No. weep holes` },
    { code: "2901.4", qty: widthM * abtHgtM * 2, desc: "Select granular backfill behind abutments", basis: "width × abutment height × 2 ends" },

    { code: "1701.4", qty: deckVol + girderVol, desc: "Concrete M35 — deck slab and girders", basis: "deck slab + longitudinal girders" },
    { code: "1702.2", qty: deckVol * 4.8 + girderVol * 6.0, desc: "Formwork — deck slab and girders", basis: "deck volume × 4.8, girder volume × 6.0" },
    { code: "1601.1", qty: deckVol * 0.11 + girderVol * 0.135, desc: "Reinforcement Fe500D — deck and girders", basis: "deck × 0.11, girders × 0.135 t/cum" },
    { code: "501.3", qty: totalLengthM * cwM, desc: "Bituminous concrete wearing coat over deck", basis: "deck length × carriageway width" },
    { code: "2601.1", qty: totalLengthM * widthM, basis: "deck length × out-to-out width" },

    { code: "2701.1", qty: nBearings, basis: `${bearingsPerPier} bearings × ${nSupports} supports` },
    { code: "2801.2", qty: 2 * widthM, desc: "Strip seal expansion joint at abutments", basis: "2 abutment lines × deck width" },

    { code: "801.1", qty: barrierM, basis: "(deck length + 2 × approach) × 2 sides" },
    { code: "801.4", qty: totalLengthM * 2, basis: "deck length × 2 carriageways" },
    { code: "2601.3", qty: nScuppers, basis: `@ 6 m spacing both sides — ${nScuppers} No.` },
  ];

  // ── Group into sections and price ─────────────────────────────────────────
  /** @type {Record<string, [string, string]>} */
  const SECTION_OF = {
    "301.1": ["300", "EARTHWORK AND EMBANKMENT"],
    "301.2": ["300", "EARTHWORK AND EMBANKMENT"],
    "1801.1": ["1800", "PILING AND FOUNDATION"],
    "1801.2": ["1800", "PILING AND FOUNDATION"],
    "1801.3": ["1800", "PILING AND FOUNDATION"],
    "1801.4": ["1800", "PILING AND FOUNDATION"],
    "1801.6": ["1800", "PILING AND FOUNDATION"],
    "1701.2": ["1800", "PILING AND FOUNDATION"],
    "1702.1": ["1700", "CONCRETE, FORMWORK AND REINFORCEMENT"],
    "1701.3": ["1700", "CONCRETE, FORMWORK AND REINFORCEMENT"],
    "1702.2": ["1700", "CONCRETE, FORMWORK AND REINFORCEMENT"],
    "1601.1": ["1700", "CONCRETE, FORMWORK AND REINFORCEMENT"],
    "2901.1": ["1700", "CONCRETE, FORMWORK AND REINFORCEMENT"],
    "1701.4": ["1700", "CONCRETE, FORMWORK AND REINFORCEMENT"],
    "2901.2": ["2900", "DECK ACCESSORIES AND APPROACH"],
    "2901.4": ["2900", "DECK ACCESSORIES AND APPROACH"],
    "501.3": ["2900", "DECK ACCESSORIES AND APPROACH"],
    "2601.1": ["2900", "DECK ACCESSORIES AND APPROACH"],
    "2601.3": ["2900", "DECK ACCESSORIES AND APPROACH"],
    "2701.1": ["2700", "BEARINGS AND EXPANSION JOINTS"],
    "2801.2": ["2700", "BEARINGS AND EXPANSION JOINTS"],
    "801.1": ["800", "SAFETY AND TRAFFIC WORKS"],
    "801.4": ["800", "SAFETY AND TRAFFIC WORKS"],
  };

  /** @type {Map<string, BoqSection>} */
  const bySection = new Map();
  for (const raw of items) {
    if (!(raw.qty > 0)) continue;
    const meta = RATES[/** @type {keyof typeof RATES} */ (raw.code)];
    if (!meta) continue;
    const [code, title] = SECTION_OF[raw.code] ?? ["0000", "MISCELLANEOUS"];
    if (!bySection.has(code)) bySection.set(code, { code, title, items: [], total: 0 });
    const section = /** @type {BoqSection} */ (bySection.get(code));
    const amount = money(r3(raw.qty) * meta.rate);
    section.items.push({
      code: raw.code,
      desc: raw.desc ?? meta.desc,
      unit: meta.unit,
      qty: r3(raw.qty),
      rate: meta.rate,
      amount,
      ref: meta.ref,
      basis: raw.basis,
    });
    section.total = money(section.total + amount);
  }

  const sections = [...bySection.values()].sort((a, b) => a.code.localeCompare(b.code));
  for (const section of sections) section.total = money(section.items.reduce((s, i) => s + i.amount, 0));

  const nItems = sections.reduce((s, section) => s + section.items.length, 0);
  const subtotal = money(sections.reduce((s, section) => s + section.total, 0));
  const contingencyPct = clamp(num(options.contingencyPct, 15), 0, 100);
  const contingencyAmount = money(subtotal * (contingencyPct / 100));
  const grandTotal = money(subtotal + contingencyAmount);

  return { sections, nItems, subtotal, contingencyPct, contingencyAmount, grandTotal };
}

/** The MoRTH codes this take-off can emit. */
export const BOQ_CODES = Object.freeze(Object.keys(RATES));
