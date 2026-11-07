/**
 * presets.js — superstructure typology and standard parameter bundles.
 *
 * Two things live here:
 *   1. the superstructure *types* (RCC solid slab / RCC T-beam), which set only
 *      the deck-thickness, girder-depth and girder-count family; and
 *   2. the *standard* presets (NHAI 2-lane, MoRTH 4-lane), which set a whole
 *      project + detail parameter bundle at once so the workspace opens in a
 *      code-compliant configuration instead of an arbitrary one.
 *
 * Pure and framework-free: no DOM, no imports.
 */

/**
 * @typedef {object} SuperstructureType
 * @property {string} id
 * @property {string} label
 * @property {string} description
 * @property {number} deckThickMm
 * @property {number} girderDepthMm
 * @property {number} girders
 */

/** @type {SuperstructureType[]} */
export const SUPERSTRUCTURE_TYPES = [
  {
    id: "slab",
    label: "RCC SOLID SLAB",
    description: "Reinforced-concrete solid slab deck — simply supported, span / depth ≈ 20.",
    deckThickMm: 650,
    girderDepthMm: 0,
    girders: 2,
  },
  {
    id: "tbeam",
    label: "RCC T-BEAM",
    description: "Reinforced-concrete T-beam and slab deck — span / depth ≈ 12.",
    deckThickMm: 250,
    girderDepthMm: 1200,
    girders: 4,
  },
];

/**
 * @typedef {object} StandardPreset
 * @property {string} id
 * @property {string} label
 * @property {string} standard  the reference the bundle follows
 * @property {string} typeId    the superstructure type the preset uses
 * @property {Record<string, any>} project  ProjectState overrides
 * @property {Record<string, any>} detail   DetailParams overrides
 */

/** @type {StandardPreset[]} */
export const STANDARD_PRESETS = [
  {
    id: "nhai_2lane_slab_12m",
    label: "Standard NHAI 2-Lane Solid Slab (12 m)",
    standard: "MoRTH 5th Rev · IRC:5 / IRC:21",
    typeId: "slab",
    project: { spans: 1, spanLength: 12, width: 12, rtl: 100.98, datum: 100 },
    detail: {
      carriageway: 7.5, abtl: 12, splay: 45,
      deckThickMm: 650, girderDepthMm: 0, girders: 2,
      deckRl: 100, hflRl: 98, lwlRl: 97.5, foundingRl: 96.775, scourRl: 96.775,
      pileDiaMm: 600, pileLenM: 6, capTMm: 800, spacingM: 2.5, rows: 2, cols: 2,
      pierLenM: 9, pierWidM: 1.2, pierHgtM: 6, capWidM: 1.8, capDepM: 0.65,
      abtHgtM: 2.8, retHgtM: 2.5, bearingsPerPier: 4, mainBarMm: 25, sbckPa: 240,
      wellDiaM: 0,
    },
  },
  {
    id: "nhai_2lane_tbeam_16m",
    label: "Standard NHAI 2-Lane T-Beam (16 m)",
    standard: "MoRTH 5th Rev · IRC:5 / IRC:21",
    typeId: "tbeam",
    project: { spans: 2, spanLength: 16, width: 12, rtl: 100.98, datum: 100 },
    detail: {
      carriageway: 7.5, abtl: 12, splay: 45,
      deckThickMm: 250, girderDepthMm: 1200, girders: 4,
      deckRl: 100, hflRl: 97.5, lwlRl: 96.8, foundingRl: 95, scourRl: 95,
      pileDiaMm: 1000, pileLenM: 12, capTMm: 1200, spacingM: 2.5, rows: 2, cols: 2,
      pierLenM: 9, pierWidM: 1.5, pierHgtM: 7, capWidM: 2, capDepM: 0.75,
      abtHgtM: 3.5, retHgtM: 3, bearingsPerPier: 4, mainBarMm: 25, sbckPa: 300,
      wellDiaM: 0,
    },
  },
  {
    id: "morth_4lane_slab_12m",
    label: "MoRTH 4-Lane Divided Solid Slab (12 m)",
    standard: "MoRTH 5th Rev · IRC:5 / IRC:21",
    typeId: "slab",
    project: { spans: 3, spanLength: 12, width: 20, rtl: 100.98, datum: 100 },
    detail: {
      carriageway: 11, abtl: 20, splay: 30,
      deckThickMm: 650, girderDepthMm: 0, girders: 2,
      deckRl: 100, hflRl: 98, lwlRl: 97.5, foundingRl: 96.5, scourRl: 96.5,
      pileDiaMm: 1000, pileLenM: 10, capTMm: 1000, spacingM: 3, rows: 2, cols: 3,
      pierLenM: 9, pierWidM: 1.6, pierHgtM: 6, capWidM: 2.2, capDepM: 0.7,
      abtHgtM: 3, retHgtM: 2.6, bearingsPerPier: 6, mainBarMm: 25, sbckPa: 280,
      wellDiaM: 0,
    },
  },
];

/**
 * Resolve a preset by id.
 * @param {string} id
 * @returns {StandardPreset | undefined}
 */
export function presetById(id) {
  return STANDARD_PRESETS.find((preset) => preset.id === id);
}

/**
 * Resolve a superstructure type by id, falling back to the slab.
 * @param {string} id
 * @returns {SuperstructureType}
 */
export function typeById(id) {
  return SUPERSTRUCTURE_TYPES.find((type) => type.id === id) ?? SUPERSTRUCTURE_TYPES[0];
}

/**
 * Apply a superstructure type to an existing detail parameter set: only the
 * thickness family moves, so openings, levels and the title block survive the
 * switch.
 * @param {Record<string, any>} detail
 * @param {string} typeId
 * @returns {Record<string, any>}
 */
export function applySuperstructureType(detail, typeId) {
  const type = typeById(typeId);
  return { ...detail, deckThickMm: type.deckThickMm, girderDepthMm: type.girderDepthMm, girders: type.girders };
}

/**
 * Flatten a preset into the two state slices the workspace holds.
 * @param {string} id
 * @returns {{ project: Record<string, any>, detail: Record<string, any>, typeId: string } | undefined}
 */
export function presetBundle(id) {
  const preset = presetById(id);
  if (!preset) return undefined;
  return { project: { ...preset.project }, detail: { ...preset.detail }, typeId: preset.typeId };
}

/** The preset the workspace opens on. */
export const DEFAULT_PRESET_ID = "nhai_2lane_slab_12m";
