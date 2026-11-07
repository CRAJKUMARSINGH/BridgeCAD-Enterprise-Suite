/**
 * layerGroups.js — CAD layer visibility groups for the drawing workspace.
 *
 * The geometry engine already tags every primitive with an IRC layer
 * (`detailGeometry.js` → `LAYERS`). This module bundles those layers into the
 * coarse on/off switches a draughtsman expects (dimensions, text, levels,
 * hatch, centreline, frame, structure), so the reviewer can strip a sheet back
 * to bare outlines without touching the geometry stream itself.
 *
 * Pure and framework-free: no DOM, no imports.
 */

/**
 * @typedef {object} LayerGroup
 * @property {string} id      stable group id
 * @property {string} label   short button label
 * @property {string[]} layers the IRC layer names the group switches
 * @property {string} hint    tooltip / long description
 */

/** @type {LayerGroup[]} */
export const LAYER_GROUPS = [
  {
    id: "STRUCTURE", label: "STRUCT", hint: "Superstructure, substructure, abutment profiles and bearings",
    layers: [
      "FOUND-CAP", "FOUND-PILE", "FOUND-WELL",
      "SUB-PIER", "SUB-ABUT", "ABUT-PROF", "SUB-BEARING",
      "SUPER-GIRDER", "SUPER-DECK", "SUPER-WEARING", "SUPER-CAMBER",
      "STRUC-DETAIL", "STRUC-SECTION", "STRUC-OUTLINE",
    ],
  },
  { id: "HATCH", label: "HATCH", hint: "Material hatching and hidden lines", layers: ["HTCH", "HIDD"] },
  { id: "DIM", label: "DIM", hint: "Dimension lines, ticks and values", layers: ["DIM"] },
  { id: "TEXT", label: "TEXT", hint: "Labels, panel titles and general annotation", layers: ["TEXT", "TEXT-HEADER"] },
  { id: "LEVELS", label: "LEVELS", hint: "Reduced-level callouts (RL text)", layers: ["TEXT-LEVEL"] },
  { id: "CIVIL", label: "SOIL", hint: "Civil / hydraulic lines — scour and HFL", layers: ["CIVIL-SCOUR", "CIVIL-HFL"] },
  { id: "CENTER", label: "CENTER", hint: "Centre lines and pier/pile centrelines", layers: ["CL"] },
  { id: "FRAME", label: "FRAME", hint: "Sheet border, title block and scale bar", layers: ["FRAME"] },
];

/**
 * group id for every layer named in a group, so a layer can only belong to one
 * group (last write wins — the table above is disjoint by construction).
 * @type {Record<string, string>}
 */
export const LAYER_TO_GROUP = Object.freeze(
  LAYER_GROUPS.reduce((acc, group) => {
    for (const layer of group.layers) acc[layer] = group.id;
    return acc;
  }, /** @type {Record<string, string>} */ ({})),
);

/**
 * Resolve a primitive's layer to its visibility group.
 * @param {string} layer
 * @returns {string}
 */
export function groupForLayer(layer) {
  return LAYER_TO_GROUP[layer] ?? "STRUCTURE";
}

/**
 * The set of layers to suppress for a given set of hidden group ids.
 * @param {Iterable<string>} hiddenGroups
 * @returns {Set<string>}
 */
export function hiddenLayersFor(hiddenGroups) {
  const groups = new Set(hiddenGroups);
  /** @type {Set<string>} */
  const hidden = new Set();
  for (const group of LAYER_GROUPS) {
    if (groups.has(group.id)) for (const layer of group.layers) hidden.add(layer);
  }
  return hidden;
}

/** Group ids switched off when the workspace first loads (nothing hidden).
 * @type {readonly string[]} */
export const DEFAULT_HIDDEN_GROUPS = Object.freeze([]);
