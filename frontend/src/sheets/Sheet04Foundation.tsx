import { buildSheet4 } from "./detailGeometry";
import { Prims, SheetFrame } from "./SheetChrome";

export default function Sheet04Foundation({ params }: { params: any }) {
  const sheet = buildSheet4(params);
  return (
    <SheetFrame>
      <Prims prims={sheet.prims} />
    </SheetFrame>
  );
}
