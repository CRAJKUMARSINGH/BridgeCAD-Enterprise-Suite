import { buildSheet4, type DetailParams } from "./detailGeometry";
import { Prims, SheetFrame } from "./SheetChrome";
import type { SheetTheme } from "./theme";

export default function Sheet04Foundation({ params, theme }: { params: DetailParams; theme: SheetTheme }) {
  const sheet = buildSheet4(params);
  return (
    <SheetFrame theme={theme}>
      <Prims prims={sheet.prims} theme={theme} />
    </SheetFrame>
  );
}
