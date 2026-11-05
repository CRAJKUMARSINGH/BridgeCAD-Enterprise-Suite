import { buildSheet5, type DetailParams } from "./detailGeometry";
import { Prims, SheetFrame } from "./SheetChrome";
import type { SheetTheme } from "./theme";

export default function Sheet05PierAbutment({ params, theme }: { params: DetailParams; theme: SheetTheme }) {
  const sheet = buildSheet5(params);
  return (
    <SheetFrame theme={theme}>
      <Prims prims={sheet.prims} theme={theme} />
    </SheetFrame>
  );
}
