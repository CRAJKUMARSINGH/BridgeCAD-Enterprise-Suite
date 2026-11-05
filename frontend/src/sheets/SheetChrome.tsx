import type { ReactNode } from "react";
import { SHEET } from "./detailGeometry";
import { inkFor, type SheetTheme } from "./theme";

export function Y(y: number) {
  return SHEET.H - y;
}

const DASH: Record<string, string | undefined> = { DASHED: "5 3", DASHDOT: "9 2 2 2" };
const LINETYPE: Record<string, string> = { "SUPER-CAMBER": "DASHED", HIDD: "DASHED", CL: "DASHDOT", "CIVIL-SCOUR": "DASHED", "CIVIL-HFL": "DASHED" };

export function SheetFrame({ theme, children }: { theme: SheetTheme; children: ReactNode }) {
  return (
    <svg
      className="bcsheet"
      viewBox={`0 0 ${SHEET.W} ${SHEET.H}`}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label="Detail sheet"
      style={{ background: theme.bg, display: "block", width: "100%", height: "auto" }}
    >
      <rect x="0" y="0" width={SHEET.W} height={SHEET.H} fill={theme.bg} stroke="none" />
      {children}
    </svg>
  );
}

export function Prim({ p, theme }: { p: any; theme: SheetTheme }) {
  const ink = inkFor(theme, p.layer);
  const stroke = {
    stroke: ink,
    strokeWidth: p.layer === "HTCH" ? 0.5 : 1,
    strokeDasharray: DASH[LINETYPE[p.layer] ?? ""],
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    fill: "none",
    vectorEffect: "non-scaling-stroke" as const,
  };
  const text = {
    fill: ink,
    stroke: "none",
    fontFamily: theme.font,
    fontSize: p.size,
    textAnchor: (p.anchor === "middle" ? "middle" : "start") as "middle" | "start",
    letterSpacing: 0.04,
  };

  switch (p.k) {
    case "line":
      return <line {...stroke} x1={p.x1} y1={Y(p.y1)} x2={p.x2} y2={Y(p.y2)} />;
    case "rect":
      return <rect {...stroke} x={p.x} y={Y(p.y + p.h)} width={p.w} height={p.h} />;
    case "circle":
      return <circle {...stroke} cx={p.cx} cy={Y(p.cy)} r={p.r} />;
    case "poly": {
      const pts: string[] = [];
      for (let i = 0; i < p.pts.length; i += 2) pts.push(`${p.pts[i]},${Y(p.pts[i + 1])}`);
      return <polygon {...stroke} points={pts.join(" ")} />;
    }
    case "text":
      return <text {...text} x={p.x} y={Y(p.y)}>{p.s}</text>;
    case "panel":
      return null;
    default:
      return null;
  }
}

export function Prims({ prims, theme }: { prims: any[]; theme: SheetTheme }) {
  return <>{prims.map((p: any, i: number) => <Prim p={p} theme={theme} key={i} />)}</>;
}
