export type Prim =
  | { k: "line"; layer: string; x1: number; y1: number; x2: number; y2: number }
  | { k: "rect"; layer: string; x: number; y: number; w: number; h: number }
  | { k: "circle"; layer: string; cx: number; cy: number; r: number }
  | { k: "poly"; layer: string; pts: number[]; closed: boolean }
  | { k: "text"; layer: string; x: number; y: number; s: string; size: number; anchor: "start" | "middle" | "end" }
  | { k: "panel"; layer: string; id: string; x: number; y: number; w: number; h: number };

export type DetailParams = Record<string, string | number | undefined>;

export type Wall = {
  side: "left" | "right";
  splayDeg: number;
  faceRunM: number;
  lengthM: number;
  returnM: number;
  topLevelM: number;
  baseLevelM: number;
};

export type Sheet = { sheet: 4 | 5; prims: Prim[]; meta: Record<string, any> };
export type Issue = { code: string; detail: string };
export type AuditResult = { ok: boolean; issues: Issue[] };

export const SHEET: Readonly<{ W: number; H: number; MARGIN: number; SCALE: number }>;
export const LAYERS: Readonly<Record<string, readonly [string, string]>>;
export const DETAIL_DEFAULTS: Readonly<Record<string, string | number>>;
export function normalizeParams(input?: DetailParams): Record<string, any>;
export function resolveAbtl(p: Record<string, any>): { valueM: number; source: string };
export function wingWallGeometry(p: Record<string, any>): { abtl: number; source: string; splayDeg: number; faceRunM: number; lengthM: number; returnM: number; walls: Wall[] };
export function abutmentProfile(side: "left" | "right", xFace: number, yCapB: number, stemHM: number): { pts: number[]; rtl: number; altbl: number; y8: number; x3: number; x7: number; x10: number; x12: number; x14: number; dirtWallX: number };
export function abutmentFamily(abutmentType?: string | null): "gravity" | "cantilever" | "battered";
export function abutmentOutlineNorm(family: "gravity" | "cantilever" | "battered"): number[];
export function foundationLayout(p: Record<string, any>): { rows: number; cols: number; nPiles: number; capWm: number; capTm: number; pileDm: number; pileLm: number; wellDiaM: number; foundingRl: number };
export function buildSheet4(raw?: DetailParams): Sheet;
export function buildSheet5(raw?: DetailParams): Sheet;
export function audit(sheet: Sheet): AuditResult;
export function toDxf(sheet: Sheet): string;
