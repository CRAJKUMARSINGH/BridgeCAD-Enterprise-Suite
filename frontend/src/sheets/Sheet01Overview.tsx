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

export default function Sheet01Overview({ project }: { project: ProjectState }) {
  const left = 58;
  const mainRight = 815;
  const elevationY = 186;
  const planY = 503;
  const spanWidth = 610 / project.spans;
  const sectionX = 895;
  const viewGap = planY - elevationY;
  const totalLength = project.spans * project.spanLength;

  return (
    <svg className="drawing-sheet" viewBox="0 0 1200 720" role="img" aria-label="Bridge general arrangement drawing with elevation, plan and typical sections">
      <rect className="sheet-bg" x="0" y="0" width="1200" height="720" rx="4" />
      <rect className="sheet-border" x="18" y="18" width="1164" height="684" />
      <rect className="sheet-inner-border" x="27" y="27" width="1146" height="666" />
      <text className="sheet-kicker" x="48" y="54">BRIDGE GENERAL ARRANGEMENT DRAWING</text>
      <text className="sheet-note" x="1145" y="54" textAnchor="end">NOT FOR CONSTRUCTION · REVIEW ISSUE</text>

      <g className="view-label">
        <text x={left} y="84">ELEVATION</text>
        <line x1={left} y1="94" x2={mainRight} y2="94" />
        <text x={left} y="411">PLAN</text>
        <line x1={left} y1="421" x2={mainRight} y2="421" />
      </g>

      <g className="elevation">
        <line className="datum-line" x1={left} y1={elevationY + 94} x2={mainRight} y2={elevationY + 94} />
        <text className="dimension-label" x={left - 2} y={elevationY + 111}>DATUM {project.datum.toFixed(3)}</text>
        {Array.from({ length: project.spans + 1 }).map((_, index) => {
          const x = left + index * spanWidth;
          return <line className="dimension-tick" key={`elev-${index}`} x1={x} y1={elevationY - 42} x2={x} y2={elevationY + 112} />;
        })}
        <rect className="deck-fill" x={left} y={elevationY - 32} width={610} height="19" rx="2" />
        <line className="structure-line" x1={left} y1={elevationY - 32} x2={left + 610} y2={elevationY - 32} />
        {Array.from({ length: Math.max(project.spans - 1, 0) }).map((_, index) => {
          const x = left + (index + 1) * spanWidth;
          return <g key={`pier-${index}`}><rect className="support-fill" x={x - 9} y={elevationY - 13} width="18" height="82" rx="2" /><rect className="footing-fill" x={x - 28} y={elevationY + 69} width="56" height="12" rx="2" /></g>;
        })}
        <rect className="abutment-fill" x={left - 13} y={elevationY - 5} width="13" height="76" />
        <rect className="abutment-fill" x={left + 610} y={elevationY - 5} width="13" height="76" />
        <line className="dimension-line" x1={left} y1={elevationY - 64} x2={left + 610} y2={elevationY - 64} />
        {Array.from({ length: project.spans }).map((_, index) => {
          const x = left + index * spanWidth + spanWidth / 2;
          return <g key={`span-${index}`}><line className="dimension-tick" x1={x - spanWidth / 2} y1={elevationY - 70} x2={x - spanWidth / 2} y2={elevationY - 58} /><line className="dimension-tick" x1={x + spanWidth / 2} y1={elevationY - 70} x2={x + spanWidth / 2} y2={elevationY - 58} /><text className="dimension-label" x={x} y={elevationY - 73} textAnchor="middle">{project.spanLength.toFixed(2)} m</text></g>;
        })}
        <text className="component-label" x={left + 610} y={elevationY - 45} textAnchor="end">RCC deck · {totalLength.toFixed(2)} m total length</text>
      </g>

      <g className="view-gap">
        <line x1={left} y1="366" x2={mainRight} y2="366" />
        <line x1={left} y1="387" x2={mainRight} y2="387" />
        <text x={(left + mainRight) / 2} y="381" textAnchor="middle">CLEAR VIEW BAND · {viewGap === 317 ? "2.0 m" : "2.0 m"} MINIMUM · DIMENSIONS KEPT OUTSIDE VIEWS</text>
      </g>

      <g className="plan">
        <rect className="plan-outline" x={left} y={planY - 21} width="610" height="42" rx="2" />
        {Array.from({ length: Math.max(project.spans - 1, 0) }).map((_, index) => {
          const x = left + (index + 1) * spanWidth;
          return <g key={`plan-pier-${index}`}><rect className="support-outline" x={x - 9} y={planY - 48} width="18" height="96" rx="2" /><rect className="footing-outline" x={x - 25} y={planY - 60} width="50" height="120" rx="2" /></g>;
        })}
        <line className="dimension-line" x1={left} y1={planY + 72} x2={left + 610} y2={planY + 72} />
        <text className="dimension-label" x={left + 305} y={planY + 91} textAnchor="middle">{totalLength.toFixed(2)} m overall</text>
        <text className="component-label" x={left + 305} y={planY - 35} textAnchor="middle">CARRIAGEWAY / DECK PLAN</text>
        <text className="component-label" x={left + 305} y={planY + 112} textAnchor="middle">P1 · P2 · TYPICAL SUPPORT CENTRES</text>
      </g>

      <g className="section-column">
        <text className="view-label" x={sectionX} y="84">TYPICAL DETAILS</text>
        <line x1={sectionX} y1="94" x2="1138" y2="94" />
        <text className="section-title" x={sectionX} y="128">A-A · DECK CROSS-SECTION</text>
        <rect className="section-deck" x={sectionX} y="150" width="210" height="34" rx="2" />
        <line className="section-line" x1={sectionX + 16} y1="150" x2={sectionX + 16} y2="184" />
        <line className="section-line" x1={sectionX + 194} y1="150" x2={sectionX + 194} y2="184" />
        <text className="section-note" x={sectionX + 105} y="204" textAnchor="middle">WIDTH {project.width.toFixed(2)} m · CAMBER / KERB / BARRIER</text>

        <text className="section-title" x={sectionX} y="258">B-B · TYPICAL PIER</text>
        <rect className="section-deck" x={sectionX + 82} y="282" width="46" height="14" rx="1" />
        <path className="pier-profile" d={`M ${sectionX + 90} 296 L ${sectionX + 120} 296 L ${sectionX + 132} 385 L ${sectionX + 78} 385 Z`} />
        <rect className="footing-fill" x={sectionX + 58} y="385" width="94" height="18" rx="2" />
        <text className="section-note" x={sectionX + 105} y="424" textAnchor="middle">PIER · CAP · FOOTING · LEVELS</text>
      </g>

      <g className="title-block">
        <rect x="895" y="518" width="243" height="153" />
        <line x1="895" y1="548" x2="1138" y2="548" />
        <line x1="895" y1="577" x2="1138" y2="577" />
        <line x1="895" y1="610" x2="1138" y2="610" />
        <line x1="895" y1="641" x2="1138" y2="641" />
        <line x1="1030" y1="577" x2="1030" y2="610" />
        <text className="title-main" x="905" y="539">BRIDGE GAD</text>
        <text className="title-value" x="905" y="568">{project.name}</text>
        <text className="title-label" x="905" y="570">PROJECT</text>
        <text className="title-value" x="905" y="601">{project.number}</text>
        <text className="title-value" x="1040" y="601">REV {project.revision}</text>
        <text className="title-label" x="905" y="628">STANDARD</text>
        <text className="title-value" x="905" y="636">IRC / MoRTH</text>
        <text className="title-label" x="1040" y="628">SCALE</text>
        <text className="title-value" x="1040" y="636">1:100</text>
        <text className="title-value" x="905" y="662">DRAWN / CHECKED / APPROVED</text>
      </g>
    </svg>
  );
}
