export const ABUTMENT_OPTIONS = {
  CANTILEVER: "Cantilever",
  GRAVITY: "Gravity",
  FULL_HEIGHT_WALL: "Full-height wall",
};

export type OverviewAbutment = keyof typeof ABUTMENT_OPTIONS;

export type ProjectState = {
  name: string;
  number: string;
  revision: string;
  spans: number;
  spanLength: number;
  width: number;
  rtl: number;
  datum: number;
};

// River-to-approach section envelopes, mirrored at A1. Coordinates match the
// A1 PDF's longitudinal profiles. The preview uses schematic support sizes.
const ABUTMENT_PROFILES = {
  CANTILEVER: [[.25, 1], [.60, 1], [.60, .18], [1, .18], [1, 0], [0, 0], [0, .18], [.25, .18]],
  GRAVITY: [[0, 1], [.60, 1], [1, 0], [0, 0]],
  FULL_HEIGHT_WALL: [[0, 1], [1, 1], [1, 0], [0, 0]],
};

export default function Sheet01Overview({ project, abutment }: { project: ProjectState; abutment: OverviewAbutment }) {
  const count = Math.max(1, Math.min(12, Math.trunc(project.spans) || 1));
  const deckLeft = 138;
  const deckRight = 1018;
  const deckWidth = deckRight - deckLeft;
  const spanWidth = deckWidth / count;
  const total = count * project.spanLength;
  const supports = Array.from({ length: count + 1 }, (_, i) => ({
    name: i === 0 ? "A1" : i === count ? "A2" : `P${i}`,
    x: deckLeft + i * spanWidth,
    end: i === 0 || i === count,
    outboard: i === 0 ? -1 : 1,
  }));
  const piers = supports.slice(1, -1);
  const halfDeck = Math.max(18, Math.min(52, project.width * 3.2));
  const planY = 485;
  const roadY = 179;
  const soffitY = 203;
  const capDepth = 12;
  const capBottomY = soffitY + capDepth;
  const dirtWallWidth = 6;
  const capWidth = 44;
  const baseY = 302;
  const spanLabel = `${project.spanLength.toFixed(2)} m`;

  return (
    <svg className="drawing-sheet gad-overview" viewBox="0 0 1200 802" role="img" aria-label="Bridge general arrangement, longitudinal elevation, plan and typical details">
      <rect className="sheet-bg" width="1200" height="802" />
      <rect className="sheet-border" x="18" y="18" width="1164" height="766" />
      <text className="sheet-kicker" x="48" y="52">BRIDGE GENERAL ARRANGEMENT</text>
      <text className="sheet-note" x="1150" y="52" textAnchor="end">SCHEMATIC REVIEW · NTS</text>

      <g className="view-label">
        <text x="48" y="86">LONGITUDINAL ELEVATION</text>
        <line x1="48" y1="96" x2="1150" y2="96" />
        <text x="48" y="361">PLAN</text>
        <line x1="48" y1="371" x2="1150" y2="371" />
        <text x="48" y="637">TYPICAL DETAILS</text>
        <line x1="48" y1="647" x2="1150" y2="647" />
      </g>

      <g className="elevation">
        <line className="dimension-line" x1={deckLeft} y1="120" x2={deckRight} y2="120" />
        {supports.map(({ name, x }, i) => (
          <g key={name}>
            <line className="dimension-tick" x1={x} y1="114" x2={x} y2="126" />
            <text className="component-label" x={x} y="148" textAnchor="middle">{name}</text>
            {i < count && <text className="dimension-label" x={x + spanWidth / 2} y="113" textAnchor="middle">{spanLabel}</text>}
          </g>
        ))}
        <rect className="deck-fill" x={deckLeft} y={roadY} width={deckWidth} height={soffitY - roadY} />
        <rect className="barrier" x={deckLeft} y={roadY - 5} width={deckWidth} height="5" />
        <line className="structure-line" x1={deckLeft} y1={roadY} x2={deckRight} y2={roadY} />
        {supports.filter((support) => support.end).map(({ name, x, outboard }) => {
          const dirtWallX = outboard < 0 ? x - dirtWallWidth : x;
          return (
            <g key={name} data-abutment={name}>
              <rect className="footing-fill" x={x - capWidth / 2 - 4} y={baseY} width={capWidth + 8} height="8" />
              <polygon className="abutment-fill" points={ABUTMENT_PROFILES[abutment]
                .map(([u, v]) => `${x + outboard * (u - .5) * capWidth},${baseY - v * (baseY - capBottomY)}`).join(" ")} />
              <rect className="abutment-cap" x={x - capWidth / 2} y={soffitY} width={capWidth} height={capDepth} />
              <rect className="dirt-wall" x={dirtWallX} y={roadY} width={dirtWallWidth} height={capBottomY - roadY} />
              <circle className="dirt-wall-weep" cx={dirtWallX + dirtWallWidth / 2} cy={roadY + 13} r="1.4" />
              <rect className="approach-slab" x={outboard < 0 ? dirtWallX - 58 : dirtWallX + dirtWallWidth} y={roadY} width="58" height="6" />
            </g>
          );
        })}
        {piers.map(({ name, x }) => (
          <g key={name}>
            <rect className="support-fill" x={x - 16} y={soffitY} width="32" height="14" />
            <rect className="support-fill" x={x - 9} y={soffitY + 14} width="18" height={baseY - soffitY - 14} />
            <rect className="footing-fill" x={x - 25} y={baseY} width="50" height="8" />
          </g>
        ))}
        {piers.map(({ name, x }) => <line key={name} data-joint={name} className="gad-joint" x1={x} y1={roadY + 2} x2={x} y2={soffitY} />)}
        <line className="datum-line" x1="48" y1="321" x2="1150" y2="321" />
        <text className="dimension-label" x="48" y="336">DATUM RL {project.datum.toFixed(3)} m</text>
        <text className="component-label" x="600" y="336" textAnchor="middle">DIRT WALL DRAINAGE / WEEP HOLES · SHEET 05</text>
        <text className="component-label" x="1150" y="336" textAnchor="end">A1 / A2 · {ABUTMENT_OPTIONS[abutment]}</text>
      </g>

      <g className="plan">
        <rect className="approach-slab" x={deckLeft - 58} y={planY - halfDeck} width="58" height={halfDeck * 2} />
        <rect className="approach-slab" x={deckRight} y={planY - halfDeck} width="58" height={halfDeck * 2} />
        <rect className="deck-fill" x={deckLeft} y={planY - halfDeck} width={deckWidth} height={halfDeck * 2} />
        {[-1, 1].map((sign) => <line key={sign} className="section-line" x1={deckLeft} y1={planY + sign * halfDeck * .72} x2={deckRight} y2={planY + sign * halfDeck * .72} />)}
        <line className="datum-line" x1={deckLeft - 36} y1={planY} x2={deckRight + 36} y2={planY} />
        {supports.map(({ name, x, end }) => (
          <g key={name}>
            <rect className="gad-hidden-support" x={x - (end ? 22 : 16)} y={planY - halfDeck - 5} width={end ? 44 : 32} height={halfDeck * 2 + 10} />
            <text className="component-label" x={x} y={planY - halfDeck - 17} textAnchor="middle">{name}</text>
          </g>
        ))}
        {piers.map(({ name, x }) => <line key={name} data-joint={name} className="gad-joint" x1={x} y1={planY - halfDeck} x2={x} y2={planY + halfDeck} />)}
        {[deckLeft, deckRight].map((x) => <line key={x} className="dimension-tick" x1={x} y1={planY + halfDeck + 10} x2={x} y2="583" />)}
        <line className="dimension-line" x1={deckLeft} y1="579" x2={deckRight} y2="579" />
        <text className="dimension-label" x={(deckLeft + deckRight) / 2} y="570" textAnchor="middle">{total.toFixed(2)} m C/C END SUPPORTS</text>
        <text className="dimension-label" x="1035" y={planY + 3}>{project.width.toFixed(2)} m OVERALL</text>
        <text className="component-label" x="48" y="603">DASHED OUTLINES · SUPPORTS BELOW DECK</text>
        {piers.length > 0 && <text className="component-label" x="1150" y="603" textAnchor="end">PIER CENTRES · SLAB BREAKS (GAP UNSPECIFIED)</text>}
      </g>

      <g className="section-column">
        <text className="component-label" x="48" y="671">DECK CROSS-SECTION</text>
        <rect className="deck-fill" x="48" y="689" width="235" height="18" />
        <rect className="barrier" x="48" y="680" width="12" height="9" />
        <rect className="barrier" x="271" y="680" width="12" height="9" />
        <text className="dimension-label" x="165" y="728" textAnchor="middle">{project.width.toFixed(2)} m OVERALL</text>
        {piers.length > 0 && <g>
          <text className="component-label" x="433" y="671">TYPICAL PIER</text>
          <rect className="support-fill" x="433" y="681" width="100" height="10" />
          <rect className="support-fill" x="468" y="691" width="30" height="31" />
          <rect className="footing-fill" x="445" y="722" width="76" height="8" />
        </g>}
      </g>
      <g className="title-block">
        <line x1="48" y1="746" x2="1150" y2="746" />
        <text className="title-main" x="48" y="770">{project.name}</text>
        <text className="title-value" x="1150" y="770" textAnchor="end">{project.number} · REV {project.revision}</text>
      </g>
    </svg>
  );
}
