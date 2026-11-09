import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
import "./sheets/sheets.css";
import { DETAIL_DEFAULTS, audit, buildSheet4, buildSheet5, toDxf, type DetailParams } from "./sheets/detailGeometry";
import { SHEETS, findSheet } from "./sheets/registry";
import type { ProjectState } from "./sheets/Sheet01Overview";
import { INK, PAPER, type SheetTheme } from "./sheets/theme";
import { buildComplianceReport } from "./sheets/compliance";
import { LAYER_GROUPS, hiddenLayersFor, DEFAULT_HIDDEN_GROUPS } from "./sheets/layerGroups";
import { SUPERSTRUCTURE_TYPES, STANDARD_PRESETS, presetBundle, typeById, applySuperstructureType, DEFAULT_PRESET_ID } from "./sheets/presets";
import { buildBoq, formatINR } from "./sheets/boq";

type BackendState = "checking" | "online" | "demo" | "offline";
type DockTab = "geometry" | "checks" | "boq" | "export";

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

const DETAIL_FIELDS: Array<{ key: string; label: string; step?: string }> = [
  { key: "abtl", label: "ABTL (m)", step: "0.05" },
  { key: "carriageway", label: "Carriageway (m)", step: "0.1" },
  { key: "splay", label: "Wing wall splay (°)", step: "1" },
  { key: "pierLenM", label: "Pier length (m)", step: "0.1" },
  { key: "pierWidM", label: "Pier width (m)", step: "0.05" },
  { key: "abtHgtM", label: "Abutment height (m)", step: "0.1" },
  { key: "retHgtM", label: "Return wall height (m)", step: "0.1" },
  { key: "pileDiaMm", label: "Pile Ø (mm)", step: "50" },
  { key: "pileLenM", label: "Pile length (m)", step: "0.5" },
  { key: "capTMm", label: "Cap thickness (mm)", step: "50" },
  { key: "deckRl", label: "Deck level RL", step: "0.1" },
  { key: "foundingRl", label: "Founding level RL", step: "0.1" },
];

// The sidebar nav and the right-rail dock are the same four destinations, so a
// click in either place lands on the same panel — no dead nav entries.
const NAV: Array<{ id: DockTab; label: string; icon: string }> = [
  { id: "geometry", label: "Drawing workspace", icon: "▧" },
  { id: "checks", label: "IRC / MoRTH checks", icon: "✓" },
  { id: "boq", label: "Bill of quantities", icon: "₹" },
  { id: "export", label: "Export package", icon: "⇩" },
];

function App() {
  const [project, setProject] = useState(initialProject);
  const [sheetIndex, setSheetIndex] = useState(5);
  const [detail, setDetail] = useState<DetailParams>({ ...DETAIL_DEFAULTS });
  const [dock, setDock] = useState<DockTab>("geometry");
  const [typeId, setTypeId] = useState(typeById(presetBundle(DEFAULT_PRESET_ID)?.typeId ?? "").id);
  const [presetId, setPresetId] = useState(DEFAULT_PRESET_ID);
  const [hiddenGroups, setHiddenGroups] = useState<string[]>([...DEFAULT_HIDDEN_GROUPS]);
  const [backend, setBackend] = useState<BackendState>("checking");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [generatedUrl, setGeneratedUrl] = useState<string | null>(null);
  const [generatedPdfUrl, setGeneratedPdfUrl] = useState<string | null>(null);
  const [notice, setNotice] = useState("Detail sheets 04 and 05 render locally — no Python engine required.");
  const [theme, setTheme] = useState<SheetTheme>(INK);
  const [zoom, setZoom] = useState<number | "fit">("fit");

  // The detail-sheet title block must track the project form: the identity
  // fields are read straight off `project` on every render rather than seeded
  // once, so editing the drawing number in the sidebar updates sheets 04/05 too.
  const liveDetail = useMemo<DetailParams>(
    () => ({ ...detail, projectName: project.name, number: project.number, revision: project.revision }),
    [detail, project.name, project.number, project.revision],
  );

  // Layer visibility: the coarse group switches are resolved to a flat set of
  // IRC layer names, which the sheet renderers suppress at draw time.
  const hiddenLayers = useMemo(() => hiddenLayersFor(hiddenGroups), [hiddenGroups]);

  const sheet = findSheet(sheetIndex);
  const ctx = { project, detail: liveDetail, theme, hiddenLayers };
  const sheetWidth = sheetIndex === 1 ? 1200 : 841;
  const sheetOrdinal = SHEETS.findIndex((s) => s.index === sheetIndex) + 1;
  const activeNav = NAV.find((entry) => entry.id === dock) ?? NAV[0];

  // Printing always uses the paper palette, whatever is on screen, and restores
  // the on-screen theme afterwards — no timeout, no stale ink strokes.
  useEffect(() => {
    const before = () => setTheme(PAPER);
    const after = () => setTheme(INK);
    window.addEventListener("beforeprint", before);
    window.addEventListener("afterprint", after);
    return () => {
      window.removeEventListener("beforeprint", before);
      window.removeEventListener("afterprint", after);
    };
  }, []);

  // Report the deployment's engine state once at mount.
  useEffect(() => {
    fetch("/api/health")
      .then((response) => {
        if (!response.ok) throw new Error("Backend unavailable");
        return response.json() as Promise<{ mode?: string }>;
      })
      .then((payload) => setBackend(payload.mode === "demo" ? "demo" : "online"))
      .catch(() => setBackend("offline"));
  }, []);

  const verdict = useMemo(() => {
    try {
      const issues = [
        ...audit(buildSheet4(detail)).issues,
        ...audit(buildSheet5(detail)).issues,
      ];
      return { count: issues.length, codes: issues.map((i) => i.code) };
    } catch (err) {
      return { count: -1, codes: [String(err)] };
    }
  }, [detail]);

  const compliance = useMemo(() => buildComplianceReport(project, detail), [project, detail]);
  const boq = useMemo(() => buildBoq(project, detail), [project, detail]);

  function updateProject<K extends keyof ProjectState>(key: K, value: ProjectState[K]) {
    setProject((current) => ({ ...current, [key]: value }));
  }

  function applyPreset(id: string) {
    const bundle = presetBundle(id);
    if (!bundle) return;
    setPresetId(id);
    setProject((current) => ({ ...current, ...bundle.project }));
    setDetail((current) => ({ ...DETAIL_DEFAULTS, ...current, ...bundle.detail }));
    setTypeId(bundle.typeId);
    const preset = STANDARD_PRESETS.find((entry) => entry.id === id);
    setNotice(`Applied standard preset: ${preset?.label ?? id}.`);
  }

  function changeType(id: string) {
    setTypeId(id);
    setDetail((current) => applySuperstructureType(current, id));
  }

  function toggleGroup(id: string) {
    setHiddenGroups((current) =>
      current.includes(id) ? current.filter((group) => group !== id) : [...current, id],
    );
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
      const dxfResponse = await fetch("/api/predict?output_format=dxf", { method: "POST", body: formData });
      if (!dxfResponse.ok) throw new Error("DXF generation failed");
      const dxfBlob = await dxfResponse.blob();
      if (generatedUrl) URL.revokeObjectURL(generatedUrl);
      setGeneratedUrl(URL.createObjectURL(dxfBlob));

      setNotice("Generating PDF output…");
      const pdfResponse = await fetch("/api/predict?output_format=pdf", { method: "POST", body: formData });
      if (!pdfResponse.ok) throw new Error("PDF generation failed");
      const pdfBlob = await pdfResponse.blob();
      if (generatedPdfUrl) URL.revokeObjectURL(generatedPdfUrl);
      setGeneratedPdfUrl(URL.createObjectURL(pdfBlob));

      setBackend("online");
      setNotice("DXF and PDF generated successfully. Download them from the export panel.");
    } catch {
      setBackend("demo");
      setNotice("Python engine offline — sheets 04/05 still render locally; use the local DXF button.");
    } finally {
      setBusy(false);
    }
  }

  function downloadLocalDxf() {
    const built = sheetIndex === 4 ? buildSheet4(detail) : buildSheet5(detail);
    const blob = new Blob([toDxf(built)], { type: "application/dxf" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${project.number}_Sheet${String(sheetIndex).padStart(2, "0")}.dxf`;
    a.click();
    // Revoking the object URL synchronously can cancel the download in some
    // browsers because the downloader has not read the blob yet; release it on
    // the next macrotask instead.
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setNotice(`Sheet ${String(sheetIndex).padStart(2, "0")} exported locally on layer set ${built.meta.layersUsed.length} layers.`);
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
          {NAV.map((item) => (
            <button
              className={dock === item.id ? "nav-item active" : "nav-item"}
              key={item.id}
              onClick={() => setDock(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
              {item.id === "geometry" && <span className="nav-count">{String(SHEETS.length).padStart(2, "0")}</span>}
              {item.id === "checks" && (
                <span className={compliance.nFailed === 0 ? "nav-count ok" : "nav-count bad"}>
                  {compliance.nPassed}/{compliance.nChecks}
                </span>
              )}
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
            <span className="breadcrumb">PROJECTS / {project.number} / SHEET {String(sheetIndex).padStart(2, "0")}</span>
            <h1>{activeNav.label}</h1>
          </div>
          <div className="topbar-actions">
            <span className="sheet-chip">SHEET {String(sheetOrdinal).padStart(2, "0")} / {String(SHEETS.length).padStart(2, "0")}</span>
            <span className={`audit-chip ${compliance.nFailed === 0 ? "ok" : "bad"}`}>
              {compliance.nFailed === 0 ? `IRC checks ${compliance.nPassed}/${compliance.nChecks}` : `${compliance.nFailed} IRC check(s) fail`}
            </span>
            <span className={`audit-chip ${verdict.count === 0 ? "ok" : "bad"}`}>
              {verdict.count === 0 ? "audit clean" : `${verdict.count} audit issue(s)`}
            </span>
            <button className="button button-outline" onClick={downloadLocalDxf} type="button">Export this sheet (DXF)</button>
            <a className="button button-dark" href="/api/template?template_key=simple_12m">Download template</a>
          </div>
        </header>

        <section className="workspace-grid">
          <div className="canvas-panel panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">SHEET REGISTER</span>
                <h2>{sheet.title}</h2>
              </div>
              <span className="ready-pill"><span className="status-dot online" /> Review-ready</span>
            </div>

            <div className="sheet-nav" role="tablist" aria-label="Sheet register">
              {SHEETS.map((entry) => (
                <button
                  key={entry.id}
                  role="tab"
                  aria-selected={entry.index === sheetIndex}
                  className={entry.index === sheetIndex ? "on" : ""}
                  onClick={() => setSheetIndex(entry.index)}
                >
                  {String(entry.index).padStart(2, "0")} · {entry.title}
                </button>
              ))}
              <div className="sheet-tools">
                {(["fit", 0.75, 1, 1.5, 2] as const).map((z) => (
                  <button key={String(z)} className={zoom === z ? "on" : ""} onClick={() => setZoom(z)}>
                    {z === "fit" ? "fit" : `${Math.round((z as number) * 100)}%`}
                  </button>
                ))}
                <button onClick={() => setTheme(theme.id === "ink" ? PAPER : INK)}>{theme.id === "ink" ? "paper" : "ink"}</button>
                <button onClick={() => window.print()}>print</button>
              </div>
            </div>

            <div className="layer-strip" role="group" aria-label="Layer visibility">
              <span className="layer-strip-label">LAYERS</span>
              {LAYER_GROUPS.map((group) => {
                const hidden = hiddenGroups.includes(group.id);
                return (
                  <button
                    key={group.id}
                    type="button"
                    title={hidden ? `Show ${group.hint}` : `Hide ${group.hint}`}
                    aria-pressed={!hidden}
                    className={hidden ? "layer-toggle off" : "layer-toggle"}
                    onClick={() => toggleGroup(group.id)}
                  >
                    {group.label}
                  </button>
                );
              })}
              <button
                type="button"
                className="layer-toggle reset"
                disabled={hiddenGroups.length === 0}
                onClick={() => setHiddenGroups([])}
              >
                ALL ON
              </button>
            </div>

            <div className="bcsheet-wrap">
              <div className="bcsheet-stage" style={{ width: zoom === "fit" ? "100%" : sheetWidth * zoom }}>
                {sheet.render(ctx)}
              </div>
            </div>
            <div className="canvas-footer">
              <span>Sheet 01 is the overview; 04 and 05 are the restored abutment-foundation and wing-wall detail sheets.</span>
              <span className="legend"><i className="legend-line cyan" /> Structure <i className="legend-line amber" /> Foundation <i className="legend-line violet" /> Dimension</span>
            </div>
          </div>

          <aside className="right-rail">
            <div className="panel dock-panel">
              <div className="dock-tabs" role="tablist" aria-label="Review dock">
                {NAV.map((item) => (
                  <button
                    key={item.id}
                    role="tab"
                    aria-selected={dock === item.id}
                    className={dock === item.id ? "on" : ""}
                    onClick={() => setDock(item.id)}
                  >
                    {item.icon} {item.label}
                  </button>
                ))}
              </div>

              {dock === "geometry" && (
                <section className="dock-body">
                  <div className="panel-heading compact">
                    <div><span className="eyebrow">TYPOLOGY</span><h2>Superstructure type</h2></div>
                  </div>
                  <div className="chip-row">
                    {SUPERSTRUCTURE_TYPES.map((type) => (
                      <button
                        key={type.id}
                        type="button"
                        title={type.description}
                        className={typeId === type.id ? "chip-button on" : "chip-button"}
                        onClick={() => changeType(type.id)}
                      >
                        {type.label}
                      </button>
                    ))}
                  </div>
                  <label className="dock-field">
                    Standard preset
                    <select value={presetId} onChange={(e) => applyPreset(e.target.value)}>
                      {STANDARD_PRESETS.map((preset) => (
                        <option key={preset.id} value={preset.id}>{preset.label}</option>
                      ))}
                    </select>
                  </label>
                  <p className="notice">{typeById(typeId).description} · {STANDARD_PRESETS.find((p) => p.id === presetId)?.standard}</p>

                  <div className="panel-heading compact">
                    <div><span className="eyebrow">PROJECT</span><h2>Identity & span</h2></div>
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

                  <div className="panel-heading compact">
                    <div><span className="eyebrow">DETAIL PARAMETERS</span><h2>Foundation & wing wall</h2></div>
                  </div>
                  <div className="detail-grid">
                    {DETAIL_FIELDS.map((field) => (
                      <label key={field.key}>
                        {field.label}
                        <input
                          type="number"
                          step={field.step ?? "0.01"}
                          value={String(detail[field.key] ?? "")}
                          onChange={(e) => setDetail((current) => ({ ...current, [field.key]: Number(e.target.value) }))}
                        />
                      </label>
                    ))}
                  </div>
                  <div className="callout">
                    <span className="callout-mark">i</span>
                    Wing walls are measured from the abutment face: face run = (ABTL − carriageway) / 2, length = face run / cos(splay). The ABTL rung that fired is printed on the sheet.
                  </div>
                </section>
              )}

              {dock === "checks" && (
                <section className="dock-body">
                  <div className="panel-heading compact">
                    <div><span className="eyebrow">IRC / MORTH</span><h2>Compliance checks</h2></div>
                    <span className={compliance.nFailed === 0 ? "verdict-pill ok" : "verdict-pill bad"}>
                      {compliance.nPassed}/{compliance.nChecks} pass
                    </span>
                  </div>
                  <div className="callout">
                    <span className="callout-mark">i</span>
                    Governing check: <strong>{compliance.governing?.id}</strong> {compliance.governing?.title} — utilisation {compliance.maxUtilisation.toFixed(3)}.
                  </div>
                  <ul className="check-list">
                    {compliance.checks.map((check) => (
                      <li key={check.id} className={check.pass ? "check-row" : "check-row fail"}>
                        <div className="check-head">
                          <span className="check-id">{check.id}</span>
                          <span className="check-title">{check.title}</span>
                          <span className={check.pass ? "verdict-badge ok" : "verdict-badge bad"}>{check.verdict}</span>
                        </div>
                        <div className="check-cite">{check.citation}</div>
                        <div className="check-values">
                          <span>Provided <strong>{check.provided}</strong> {check.unit === "–" ? "" : check.unit}</span>
                          <span>Required <strong>{check.comparator}</strong></span>
                          <span>Util. <strong>{check.utilisation.toFixed(3)}</strong></span>
                        </div>
                        <div className="check-bar"><i style={{ width: `${Math.min(check.utilisation * 100, 100)}%` }} /></div>
                        <div className="check-why">{check.rationale}</div>
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {dock === "boq" && (
                <section className="dock-body">
                  <div className="panel-heading compact">
                    <div><span className="eyebrow">MORTH SCHEDULE</span><h2>Bill of quantities</h2></div>
                    <span className="verdict-pill ok">{boq.nItems} items</span>
                  </div>
                  {boq.sections.map((section) => (
                    <div className="boq-section" key={section.code}>
                      <div className="boq-section-head">
                        <span>{section.code} · {section.title}</span>
                        <strong>₹ {formatINR(section.total)}</strong>
                      </div>
                      <table className="boq-table">
                        <thead>
                          <tr><th>Code</th><th>Description</th><th>Qty</th><th>Rate</th><th>Amount</th></tr>
                        </thead>
                        <tbody>
                          {section.items.map((item, index) => (
                            <tr key={`${item.code}-${index}`}>
                              <td className="mono">{item.code}</td>
                              <td>{item.desc}<span className="boq-basis">{item.ref} · {item.basis}</span></td>
                              <td className="num">{item.qty} {item.unit}</td>
                              <td className="num">{formatINR(item.rate)}</td>
                              <td className="num">{formatINR(item.amount)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ))}
                  <div className="boq-totals">
                    <div><span>Subtotal</span><strong>₹ {formatINR(boq.subtotal)}</strong></div>
                    <div><span>Contingency {boq.contingencyPct}%</span><strong>₹ {formatINR(boq.contingencyAmount)}</strong></div>
                    <div className="grand"><span>Grand total</span><strong>₹ {formatINR(boq.grandTotal)}</strong></div>
                  </div>
                </section>
              )}

              {dock === "export" && (
                <section className="dock-body">
                  <div className="panel-heading compact">
                    <div><span className="eyebrow">INPUT CONTROL</span><h2>Generate from workbook</h2></div>
                    <span className="step-number">01</span>
                  </div>
                  <form onSubmit={generateDrawing}>
                    <label className="upload-zone">
                      <span className="upload-icon">↑</span>
                      <strong>{selectedFile ? selectedFile.name : "Upload parameter workbook"}</strong>
                      <span>Excel .xlsx or .xls · optional for the local detail sheets</span>
                      <input type="file" accept=".xlsx,.xls" onChange={onFileChange} />
                    </label>
                    <button className="button button-primary" disabled={busy} type="submit">
                      {busy ? "Generating…" : "Generate via Python engine"} <span>→</span>
                    </button>
                    <p className="notice" role="status">{notice}</p>
                  </form>

                  <div className="panel-heading compact">
                    <div><span className="eyebrow">DELIVERABLES</span><h2>Export package</h2></div>
                  </div>
                  <div className="export-actions">
                    {generatedUrl && <a className="button button-outline" href={generatedUrl} download={`${project.number}.dxf`}>Download generated DXF</a>}
                    {generatedPdfUrl && <a className="button button-outline" href={generatedPdfUrl} download={`${project.number}.pdf`}>Download generated PDF</a>}
                    <button className="button button-outline" onClick={downloadLocalDxf} type="button">Download local DXF</button>
                    <a className="button button-outline" href="/bridge-catalogue-11.pdf" target="_blank" rel="noreferrer">Open 11-bridge PDF catalogue ↗</a>
                    <a className="button button-outline" href="/samples/sample_input.xlsx" download>Download sample workbook</a>
                  </div>
                </section>
              )}
            </div>
          </aside>
        </section>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
