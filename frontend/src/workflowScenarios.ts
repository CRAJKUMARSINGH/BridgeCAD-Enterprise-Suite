/** Browser-local scenarios only. This module does not authorize CAD generation. */
export type SavedScenario = {
  schemaVersion: 2; id: string; name: string; type: string;
  overrides: Record<string, string>; paper: string; orientation: string;
  scale: string; savedAt: string;
};
export const SCENARIO_KEY = 'bridgecad.workflow.scenarios.v2';
export function readScenarios(raw: string | null, allowedTypes: string[], validOverrides?: (type: string, values: Record<string, string>) => boolean): SavedScenario[] {
  if (!raw) return [];
  try {
    const list: unknown = JSON.parse(raw);
    if (!Array.isArray(list)) return [];
    const valid = list.filter((item): item is SavedScenario => {
      if (!item || typeof item !== 'object') return false;
      const x = item as Partial<SavedScenario>;
      return x.schemaVersion === 2 && typeof x.id === 'string' && x.id.length > 0 && x.id.length <= 100 && typeof x.name === 'string' && x.name.trim().length > 0 && x.name.length <= 80
        && typeof x.type === 'string' && allowedTypes.includes(x.type)
        && !!x.overrides && typeof x.overrides === 'object' && !Array.isArray(x.overrides)
        && Object.values(x.overrides).every(v => typeof v === 'string' && v.trim() !== '' && Number.isFinite(Number(v)))
        && ['A0','A1','A2','A3','A4'].includes(x.paper || '')
        && ['Landscape','Portrait'].includes(x.orientation || '')
        && typeof x.scale === 'string' && Number.isFinite(Number(x.scale)) && Number(x.scale) > 0
        // B06 — reject a stored timestamp that no date parser accepts.
        && typeof x.savedAt === 'string' && !Number.isNaN(Date.parse(x.savedAt))
        // B09 — reject an override set that is invalid for its own type.
        && (!validOverrides || validOverrides(x.type, x.overrides));
    }).slice(0, 20);
    // B06 — collapse duplicate ids rather than trusting stored order.
    const seen = new Set<string>();
    return valid.filter((item) => (seen.has(item.id) ? false : (seen.add(item.id), true)));
  } catch { return []; }
}
