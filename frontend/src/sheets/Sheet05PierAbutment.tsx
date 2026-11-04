import { buildSheet5 } from "./detailGeometry";
import { Prims, SheetFrame } from "./SheetChrome";

export default function Sheet05PierAbutment({ params }: { params: any }) {
  const sheet = buildSheet5(params);
  return (
    <SheetFrame>
      <Prims prims={sheet.prims} />
    </SheetFrame>
  );
}
