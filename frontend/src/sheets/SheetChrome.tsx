import type { ReactNode } from "react";
import { SHEET } from "./detailGeometry";

/** Flip y-up model space into SVG space. */
export function Y(y: number) {
  return SHEET.H - y;
}

export function SheetFrame({ children }: { children: ReactNode }) {
  return (
    <svg className="drawing-sheet" viewBox={`0 0 ${SHEET.W} ${SHEET.H}`} role="img" aria-label="Detail sheet">
      <rect className="sheet-bg" x="0" y="0" width={SHEET.W} height={SHEET.H} />
      {children}
    </svg>
  );
}

export function Prim({ p }: { p: any }) {
  const cls = `lyr-${p.layer}`;
  switch (p.k) {
    case "line":
      return <line className={cls} x1={p.x1} y1={Y(p.y1)} x2={p.x2} y2={Y(p.y2)} />;
    case "rect":
      return <rect className={cls} x={p.x} y={Y(p.y + p.h)} width={p.w} height={p.h} />;
    case "circle":
      return <circle className={cls} cx={p.cx} cy={Y(p.cy)} r={p.r} />;
    case "poly": {
      const pts: string[] = [];
      for (let i = 0; i < p.pts.length; i += 2) pts.push(`${p.pts[i]},${Y(p.pts[i + 1])}`);
      return <polygon className={cls} points={pts.join(" ")} />;
    }
    case "text":
      return (
        <text className={cls} x={p.x} y={Y(p.y)} fontSize={p.size} textAnchor={p.anchor === "middle" ? "middle" : "start"}>
          {p.s}
        </text>
      );
    default:
      return null;
  }
}

export function Prims({ prims }: { prims: any[] }) {
  return <>{prims.map((p: any, i: number) => <Prim p={p} key={i} />)}</>;
}
