export type SheetTheme = {
  id: "ink" | "paper";
  bg: string;
  frame: string;
  found: string;
  sub: string;
  bearing: string;
  super: string;
  wearing: string;
  struc: string;
  hatch: string;
  cl: string;
  dim: string;
  text: string;
  header: string;
  level: string;
  civil: string;
  font: string;
};

const FONT = 'ui-monospace, SFMono-Regular, Menlo, Consolas, "Courier New", monospace';

export const INK: SheetTheme = {
  id: "ink",
  bg: "#0e1418",
  frame: "#8a969e",
  found: "#d9c26a",
  sub: "#9fc3d8",
  bearing: "#e08a5a",
  super: "#7fb2cc",
  wearing: "#8ec7a8",
  struc: "#b8c4cc",
  hatch: "#7a8894",
  cl: "#c76a9c",
  dim: "#c9a227",
  text: "#dfe6ea",
  header: "#ffffff",
  level: "#e08a5a",
  civil: "#5fb0c8",
  font: FONT,
};

export const PAPER: SheetTheme = {
  id: "paper",
  bg: "#fbf9f2",
  frame: "#3c3c3c",
  found: "#8a6a12",
  sub: "#245a72",
  bearing: "#a4471c",
  super: "#2f6b8a",
  wearing: "#2f7a55",
  struc: "#4a4a4a",
  hatch: "#8a8a8a",
  cl: "#8a2f5e",
  dim: "#7a5c00",
  text: "#1c1c1c",
  header: "#000000",
  level: "#a4471c",
  civil: "#1d6f88",
  font: FONT,
};

const TOKEN: Record<string, keyof SheetTheme> = {
  FRAME: "frame",
  "FOUND-CAP": "found",
  "FOUND-PILE": "found",
  "FOUND-WELL": "found",
  "SUB-PIER": "sub",
  "SUB-ABUT": "sub",
  "ABUT-PROF": "sub",
  "SUB-BEARING": "bearing",
  "SUPER-GIRDER": "super",
  "SUPER-DECK": "super",
  "SUPER-WEARING": "wearing",
  "SUPER-CAMBER": "wearing",
  "STRUC-DETAIL": "struc",
  "STRUC-SECTION": "struc",
  "STRUC-OUTLINE": "struc",
  HTCH: "hatch",
  HIDD: "hatch",
  CL: "cl",
  DIM: "dim",
  TEXT: "text",
  "TEXT-HEADER": "header",
  "TEXT-LEVEL": "level",
  "CIVIL-SCOUR": "civil",
  "CIVIL-HFL": "civil",
};

export const inkFor = (theme: SheetTheme, layer: string): string =>
  theme[TOKEN[layer] ?? "text"] as string;
