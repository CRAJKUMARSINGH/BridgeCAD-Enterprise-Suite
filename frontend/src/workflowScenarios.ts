/** Browser-local scenarios only. This module does not authorize CAD generation. */
export type SavedScenario = {
  schemaVersion: 2; id: string; name: string; type: string;
  overrides: Record<string, string>; paper: string; orientation: string;
  scale: string; savedAt: string;
};
export const SCENARIO_KEY = 'bridgecad.workflow.scenarios.v2';
export function readScenarios(raw: string | null, allowedTypes: string[]): SavedScenario[] {
  if (!raw) return [];
  try {
    const list: unknown = JSON.parse(raw);
    if (!Array.isArray(list)) return [];
    return list.filter((item): item is SavedScenario => {
      if (!item || typeof item !== 'object') return false;
      const x = item as Partial<SavedScenario>;
      return x.schemaVersion === 2 && typeof x.id === 'string' && typeof x.name === 'string'
        && typeof x.type === 'string' && allowedTypes.includes(x.type)
        && !!x.overrides && typeof x.overrides === 'object' && !Array.isArray(x.overrides)
        && Object.values(x.overrides).every(v => typeof v === 'string' && v.trim() !== '' && Number.isFinite(Number(v)))
        && ['A0','A1','A2','A3','A4'].includes(x.paper || '')
        && ['Landscape','Portrait'].includes(x.orientation || '')
        && typeof x.scale === 'string' && Number.isFinite(Number(x.scale)) && Number(x.scale) > 0
        && typeof x.savedAt === 'string';
    }).slice(0, 20);
  } catch { return []; }
}
