import { buildSheet4, type DetailParams } from "./detailGeometry";
import { Prims, SheetFrame } from "./SheetChrome";
import type { SheetTheme } from "./theme";

export default function Sheet04Foundation({ params, theme, hiddenLayers }: { params: DetailParams; theme: SheetTheme; hiddenLayers?: Set<string> }) {
  const sheet = buildSheet4(params);
  return (
    <SheetFrame theme={theme}>
      <Prims prims={sheet.prims} theme={theme} hiddenLayers={hiddenLayers} />
    </SheetFrame>
  );
}
