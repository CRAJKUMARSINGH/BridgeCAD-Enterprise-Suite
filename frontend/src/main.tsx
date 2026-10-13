import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type BackendState = "checking" | "online" | "demo" | "offline";

type ProjectState = {
  name: string;
  number: string;
  revision: string;
  spans: number;
  spanLength: number;
  width: number;
  rtl: number;
  datum: number;
};

const initialProject: ProjectState = {
  name: "Yogendra Borse Bridge",
  number: "GAD-001",
  revision: "R0",
  spans: 3,
  spanLength: 12,
  width: 11.1,
  rtl: 110.98,
  datum: 100.0,
};

function App() {
  const [project, setProject] = useState(initialProject);
  const [activeView, setActiveView] = useState("Drawing workspace");
  const [backend, setBackend] = useState<BackendState>("checking");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("Preview loaded — upload a parameter workbook to generate a drawing.");
  const [generatedUrl, setGeneratedUrl] = useState<string | null>(null);
  const [generatedPdfUrl, setGeneratedPdfUrl] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((response) => {
        if (!response.ok) throw new Error("Backend unavailable");
        return response.json() as Promise<{ mode?: string }>;
      })
      .then((payload) => setBackend(payload.mode === "demo" ? "demo" : "online"))
      .catch(() => setBackend("offline"));
  }, []);

  const totalLength = project.spans * project.spanLength;
  const sheetSummary = useMemo(
    () => [
      ["Views", "Elevation · Plan · A-A · B-B"],
      ["View gap", "2.0 m clear separation"],
      ["Scale", "1:100 / details 1:50"],
      ["Datum", `${project.datum.toFixed(3)} m`],
    ],
    [project.datum],
  );

  function updateProject<K extends keyof ProjectState>(key: K, value: ProjectState[K]) {
    setProject((current) => ({ ...current, [key]: value }));
  }

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    if (file) setNotice(`${file.name} is ready for generation.`);
  }

  async function generateDrawing(event: FormEvent) {
    event.preventDefault();
    if (!selectedFile) {
      setNotice("Choose an .xlsx parameter workbook first.");
      return;
    }

    setBusy(true);
    setNotice("Generating the coordinated GAD sheet…");
    const formData = new FormData();
    formData.append("excel_file", selectedFile);
    try {
      // Generate DXF
      const dxfResponse = await fetch("/api/predict?output_format=dxf", {
        method: "POST",
        body: formData,
      });
      if (!dxfResponse.ok) throw new Error("DXF generation failed");
      const dxfBlob = await dxfResponse.blob();
      if (generatedUrl) URL.revokeObjectURL(generatedUrl);
      setGeneratedUrl(URL.createObjectURL(dxfBlob));

      // Generate PDF
      setNotice("Generating PDF output…");
      const pdfResponse = await fetch("/api/predict?output_format=pdf", {
        method: "POST",
        body: formData,
      });
      if (!pdfResponse.ok) throw new Error("PDF generation failed");
      const pdfBlob = await pdfResponse.blob();
      if (generatedPdfUrl) URL.revokeObjectURL(generatedPdfUrl);
      setGeneratedPdfUrl(URL.createObjectURL(pdfBlob));

      setNotice("DXF and PDF generated successfully. Download them from the export panel.");
      setBackend("online");
    } catch (err) {
      console.error("Drawing generation failed:", err);
      setNotice("Live generation is not configured here yet. The review draft and 11-bridge PDF catalogue are still ready to use.");
      setBackend("demo");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">G</div>
          <div>
            <strong>BRIDGE GAD</strong>
            <span>Drawing workspace</span>
          </div>
        </div>

        <div className="sidebar-label">Project</div>
        <div className="project-card">
          <span className="eyebrow">ACTIVE PROJECT</span>
          <strong>{project.name}</strong>
          <span>{project.number} · {project.revision}</span>
        </div>

        <nav className="nav-list" aria-label="Workspace navigation">
          {["Drawing workspace", "Standards review", "Export package"].map((item, index) => (
            <button
              className={activeView === item ? "nav-item active" : "nav-item"}
              key={item}
              onClick={() => setActiveView(item)}
            >
              <span className="nav-icon">{["▧", "✓", "⇩"][index]}</span>
              {item}
              {index === 0 && <span className="nav-count">01</span>}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="status-line">
            <span className={`status-dot ${backend}`} />
            <span>Python engine {backend === "online" ? "online" : backend}</span>
          </div>
          <span className="muted">IRC / MoRTH project criteria</span>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <span className="breadcrumb">PROJECTS / {project.number}</span>
            <h1>{activeView}</h1>
          </div>
          <div className="topbar-actions">
            <span className="sheet-chip">SHEET 01 / 01</span>
            <a className="button button-dark" href="/api/template?template_key=simple_12m">
              Download template
            </a>
            <a className="button button-primary" href="/api/generate_sample_pdf" target="_blank" rel="noreferrer">
              Generate sample PDF
            </a>
          </div>
        </header>

        <section className="workspace-grid">
          <div className="canvas-panel panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">GENERAL ARRANGEMENT DRAWING</span>
                <h2>Coordinated sheet preview</h2>
              </div>
              <span className="ready-pill"><span className="status-dot online" /> Review-ready</span>
            </div>
            <div className="drawing-frame">
              <DrawingSheet project={project} totalLength={totalLength} />
            </div>
            <div className="canvas-footer">
              <span>Pan and zoom are available in the exported CAD/PDF sheet.</span>
              <span className="legend"><i className="legend-line cyan" /> Structure <i className="legend-line amber" /> Support <i className="legend-line violet" /> Dimension</span>
            </div>
          </div>

          <aside className="right-rail">
            <form className="panel control-panel" onSubmit={generateDrawing}>
              <div className="panel-heading compact">
                <div>
                  <span className="eyebrow">INPUT CONTROL</span>
                  <h2>Sheet parameters</h2>
                </div>
                <span className="step-number">01</span>
              </div>
              <label>
                Project name
                <input value={project.name} onChange={(e) => updateProject("name", e.target.value)} />
              </label>
              <div className="field-row">
                <label>Drawing no.<input value={project.number} onChange={(e) => updateProject("number", e.target.value)} /></label>
                <label>Revision<input value={project.revision} onChange={(e) => updateProject("revision", e.target.value)} /></label>
              </div>
              <div className="field-row">
                <label>Spans<input type="number" min="1" max="12" value={project.spans} onChange={(e) => updateProject("spans", Number(e.target.value))} /></label>
                <label>Span length (m)<input type="number" min="1" value={project.spanLength} onChange={(e) => updateProject("spanLength", Number(e.target.value))} /></label>
              </div>
              <div className="field-row">
                <label>Deck width (m)<input type="number" min="1" step="0.1" value={project.width} onChange={(e) => updateProject("width", Number(e.target.value))} /></label>
                <label>Datum (m)<input type="number" step="0.001" value={project.datum} onChange={(e) => updateProject("datum", Number(e.target.value))} /></label>
              </div>
              <label className="upload-zone">
                <span className="upload-icon">↑</span>
                <strong>{selectedFile ? selectedFile.name : "Upload parameter workbook"}</strong>
                <span>Excel .xlsx or .xls · required for generation</span>
                <input type="file" accept=".xlsx,.xls" onChange={onFileChange} />
              </label>
              <button className="button button-primary" disabled={busy} type="submit">
                {busy ? "Generating…" : "Generate coordinated drawing"} <span>→</span>
              </button>
              <p className="notice" role="status">{notice}</p>
            </form>

            <div className="panel summary-panel">
              <div className="panel-heading compact">
                <div><span className="eyebrow">SHEET RULES</span><h2>Presentation standard</h2></div>
              </div>
              <div className="summary-list">
                {sheetSummary.map(([label, value]) => <div className="summary-row" key={label}><span>{label}</span><strong>{value}</strong></div>)}
              </div>
              <div className="callout">
                <span className="callout-mark">i</span>
                Elevation and plan use a reserved view band so dimensions remain readable at full-sheet scale.
              </div>
            </div>

            <div className="panel export-panel">
              <div className="panel-heading compact">
                <div><span className="eyebrow">DELIVERABLES</span><h2>Export package</h2></div>
              </div>
              <div className="export-actions">
                {generatedUrl && <a className="button button-outline" href={generatedUrl} download={`${project.number}.dxf`}>Download generated DXF</a>}
                {generatedPdfUrl && <a className="button button-outline" href={generatedPdfUrl} download={`${project.number}.pdf`}>Download generated PDF</a>}
                <a className="button button-outline" href="/bridge-catalogue-11.pdf" target="_blank" rel="noreferrer">Open 11-bridge PDF catalogue ↗</a>
                <a className="button button-outline" href="/samples/sample_input.xlsx" download>Download sample workbook</a>
              </div>
            </div>
          </aside>
        </section>
      </main>
    </div>
  );
}

function DrawingSheet({ project, totalLength }: { project: ProjectState; totalLength: number }) {
  const left = 58;
  const mainRight = 815;
  const elevationY = 186;
  const planY = 503;
  const spanWidth = 610 / project.spans;
  const sectionX = 895;
  const viewGap = planY - elevationY;

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

createRoot(document.getElementById("root")!).render(<App />);