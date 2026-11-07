import type { ReactElement } from "react";
import Sheet01Overview from "./Sheet01Overview";
import Sheet04Foundation from "./Sheet04Foundation";
import Sheet05PierAbutment from "./Sheet05PierAbutment";
import type { SheetTheme } from "./theme";

export type SheetContext = { project: any; detail: any; theme: SheetTheme; hiddenLayers?: Set<string> };

export type SheetEntry = {
  index: number;
  id: string;
  title: string;
  render: (ctx: SheetContext) => ReactElement;
};

export const SHEETS: SheetEntry[] = [
  { index: 1, id: "sheet1_overview", title: "General arrangement", render: ({ project }) => <Sheet01Overview project={project} /> },
  { index: 4, id: "sheet4_foundation", title: "Abutment & pier foundation", render: ({ detail, theme, hiddenLayers }) => <Sheet04Foundation params={detail} theme={theme} hiddenLayers={hiddenLayers} /> },
  { index: 5, id: "sheet5_pier_abutment", title: "Pier, abutment & wing wall details", render: ({ detail, theme, hiddenLayers }) => <Sheet05PierAbutment params={detail} theme={theme} hiddenLayers={hiddenLayers} /> },
];

export const findSheet = (index: number): SheetEntry => SHEETS.find((s) => s.index === index) ?? SHEETS[0];
