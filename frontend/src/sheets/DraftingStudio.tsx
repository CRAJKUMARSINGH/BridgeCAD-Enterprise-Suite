import { useId, useMemo, useRef, useState, type PointerEvent, type WheelEvent } from "react";
import { Prims } from "./SheetChrome";
import { INK, PAPER, type SheetTheme } from "./theme";
import { ABUTMENT_OPTIONS } from "./Sheet01Overview";
import { toDxf } from "./detailGeometry";
import { assessDraft, buildDraftViews, canExportDraft, DRAFT_PRESETS, FIELD_GROUPS, summarizeDraft, WING_TYPES, type Draft, type DraftView, type ViewId, type WingType } from "./draftingGeometry";
import "./draftingStudio.css";

const STORAGE_KEY = "bridgecad.drafting.designs.v1";
const VIEW_LABELS: Record<ViewId, string> = {
  "ga-plan": "GAD + plan", elevation: "Elevation", section: "Section", front: "Front", plan: "Abutment plan", foundation: "Foundation plan",
};
type SavedDesign = { id: string; draft: Draft };

function readDesigns(): SavedDesign[] {
  try {
    const values: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
    if (!Array.isArray(values)) return [];
    return values.flatMap((value) => {
      if (!value || typeof value.id !== "string" || !value.draft || typeof value.draft !== "object") return [];
      const stored = value.draft as Partial<Draft>;
      const draft: Draft = { ...DRAFT_PRESETS[0], ...stored, wingType: stored.wingType ?? "SPLAYED" };
      return canExportDraft(draft) ? [{ id: value.id, draft }] : [];
    });
  } catch {
    return [];
  }
}

function download(name: string, text: string, mime: string) {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function Viewport({ view, draft, valid, focus, grid, theme }: { view: DraftView; draft: Draft; valid: boolean; focus?: () => void; grid: boolean; theme: SheetTheme }) {
  const ref = useRef<SVGSVGElement>(null);
  const gridId = useId().replace(/:/g, "");
  const [camera, setCamera] = useState({ zoom: 1, x: 0, y: 0 });
  const drag = useRef<{ x: number; y: number; ratio: number; pointer: number }>();
  const [x, y, width, height] = view.box;
  const scale = camera.zoom;

  function startPan(event: PointerEvent<SVGSVGElement>) {
    if (event.button !== 0 || scale === 1 || !ref.current) return;
    const matrix = ref.current.getScreenCTM();
    if (!matrix) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    drag.current = { x: event.clientX, y: event.clientY, ratio: 1 / matrix.a, pointer: event.pointerId };
  }

  function pan(event: PointerEvent<SVGSVGElement>) {
    const current = drag.current;
    if (!current || current.pointer !== event.pointerId) return;
    const dx = (current.x-event.clientX)*current.ratio, dy = (current.y-event.clientY)*current.ratio;
    drag.current = { ...current, x: event.clientX, y: event.clientY };
    setCamera((old) => ({ ...old, x: old.x+dx, y: old.y+dy }));
  }

  function zoomBy(factor: number) {
    setCamera((old) => {
      const zoom = Math.min(5, Math.max(1, old.zoom * factor));
      return zoom <= 1 ? { zoom: 1, x: 0, y: 0 } : { ...old, zoom };
    });
  }

  function wheelZoom(event: WheelEvent<SVGSVGElement>) {
    event.preventDefault();
    zoomBy(event.deltaY < 0 ? 1.2 : 1 / 1.2);
  }

  const filename = `${draft.name.trim().replace(/[^a-z0-9_-]+/gi, "-").replace(/^-+|-+$/g, "") || "BridgeCAD"}-${view.id}-review-draft`;
  function saveSvg() {
    if (!canExportDraft(draft) || !ref.current) return;
    const svg = ref.current.cloneNode(true) as SVGSVGElement;
    svg.setAttributeNS("http://www.w3.org/2000/xmlns/", "xmlns", "http://www.w3.org/2000/svg");
    svg.setAttribute("viewBox", view.box.join(" "));
    svg.setAttribute("width", "1400");
    svg.setAttribute("height", String(Math.round(1400*height/width)));
    svg.removeAttribute("class");
    download(`${filename}.svg`, new XMLSerializer().serializeToString(svg), "image/svg+xml");
  }

  function saveDxf() {
    if (!canExportDraft(draft)) return;
    download(`${filename}.dxf`, toDxf(view), "application/dxf");
  }

  return <article className="draft-view" data-view={view.id}>
    <header>
      <h2>{view.title}</h2>
      <div className="draft-view-actions">
        <button type="button" disabled={scale <= 1} aria-label={`Zoom out ${view.title}`} onClick={() => zoomBy(1 / 1.35)}>−</button>
        <span className="draft-zoom-label" aria-live="polite">{Math.round(scale * 100)}%</span>
        <button type="button" disabled={scale >= 5} aria-label={`Zoom in ${view.title}`} onClick={() => zoomBy(1.35)}>+</button>
        <button type="button" onClick={() => setCamera({ zoom: 1, x: 0, y: 0 })}>Fit</button>
        {focus && <button type="button" onClick={focus}>Focus</button>}
      </div>
    </header>
    <svg ref={ref} viewBox={`${x+width*(1-1/scale)/2+camera.x} ${y+height*(1-1/scale)/2+camera.y} ${width/scale} ${height/scale}`}
      className={scale > 1 ? "draft-drawing pannable" : "draft-drawing"} role="img" aria-label={view.title}
      onPointerDown={startPan} onPointerMove={pan} onLostPointerCapture={() => { drag.current = undefined; }} onWheel={wheelZoom}>
      <title>{view.title}</title>
      <defs>
        <pattern id={gridId} width="500" height="500" patternUnits="userSpaceOnUse">
          <path d="M 500 0 L 0 0 0 500" fill="none" stroke={theme.frame} strokeWidth="1" opacity=".18" vectorEffect="non-scaling-stroke" />
        </pattern>
      </defs>
      <rect x={x} y={y} width={width} height={height} fill={theme.bg} />
      {grid && <rect x={x} y={y} width={width} height={height} fill={`url(#${gridId})`} />}
      <Prims prims={view.prims} theme={theme} />
    </svg>
    <footer><span>Dimensions in mm · levels in m</span><div className="draft-view-actions">
      <button type="button" disabled={!valid} onClick={saveSvg}>SVG</button>
      <button type="button" disabled={!valid} onClick={saveDxf}>DXF</button>
    </div></footer>
  </article>;
}

export default function DraftingStudio() {
  const [draft, setDraft] = useState<Draft>(DRAFT_PRESETS[0]);
  const [lastValid, setLastValid] = useState<Draft>(DRAFT_PRESETS[0]);
  const [saved, setSaved] = useState(readDesigns);
  const [active, setActive] = useState<ViewId | "all">("ga-plan");
  const [dimensions, setDimensions] = useState(true);
  const [levels, setLevels] = useState(true);
  const [grid, setGrid] = useState(false);
  const [theme, setTheme] = useState<SheetTheme>(PAPER);
  const [notice, setNotice] = useState("");
  const assessment = useMemo(() => assessDraft(draft), [draft]);
  const valid = assessment.errors.length === 0;
  const summary = useMemo(() => summarizeDraft(lastValid), [lastValid]);
  const views = useMemo(() => buildDraftViews(lastValid), [lastValid]);
  const visibleViews = useMemo(() => views.map((view) => ({
    ...view,
    prims: view.prims.filter(({ layer }) => (dimensions || layer !== "DIM")
      && (levels || !["TEXT-LEVEL", "CIVIL-HFL", "CIVIL-OFL", "CIVIL-NGL", "CIVIL-SCOUR"].includes(layer))),
  })), [views, dimensions, levels]);

  function update(next: Draft) {
    setDraft(next);
    if (!assessDraft(next).errors.length) setLastValid(next);
  }

  function setField<K extends keyof Draft>(key: K, value: Draft[K]) {
    update({ ...draft, [key]: value });
  }

  function saveDesign() {
    const name = draft.name.trim();
    if (!canExportDraft(draft) || !name) return;
    const existing = saved.find((entry) => entry.draft.name === name);
    const entry = { id: existing?.id ?? globalThis.crypto?.randomUUID?.() ?? Date.now().toString(36), draft: { ...draft, name } };
    const next = [entry, ...saved.filter((design) => design.id !== entry.id)];
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      setSaved(next);
      setNotice(`${name} saved on this browser.`);
    } catch {
      setNotice("Browser storage is unavailable. Drawing exports are still available.");
    }
  }

  function loadDesign(item: SavedDesign) {
    update(item.draft);
    setNotice(`${item.draft.name} loaded.`);
  }

  function deleteDesign(id: string) {
    const next = saved.filter((entry) => entry.id !== id);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      setSaved(next);
      setNotice("Saved design removed from this browser.");
    } catch {
      setNotice("Browser storage is unavailable. The saved design was not removed.");
    }
  }

  function resetDraft() {
    update({ ...DRAFT_PRESETS[0] });
    setNotice("IRC default parameters restored.");
  }

  return <div className="draft-studio">
    <header className="draft-masthead">
      <div><a href="#home" className="draft-brand">BridgeCAD home</a><h1>Live drafting</h1></div>
      <nav aria-label="BridgeCAD workspaces">
        <a href="#workspace">Workbook workspace →</a>
        <div className="draft-theme-switch" role="group" aria-label="Drawing theme">
          <button type="button" aria-pressed={theme.id === "paper"} onClick={() => setTheme(PAPER)}>Paper</button>
          <button type="button" aria-pressed={theme.id === "ink"} onClick={() => setTheme(INK)}>Ink</button>
        </div>
      </nav>
    </header>
    <main className="draft-layout">
      <aside className="draft-controls" aria-label="Drawing controls">
        <div className="draft-controls-title"><h2>Drawing inputs</h2><span className={valid ? "draft-valid" : "draft-invalid"}>{valid ? "Live" : "Check inputs"}</span></div>
        <p className="draft-field-help">Presets use sample data. Preview and export run in this browser.</p>
        <div className="draft-preset-row">
          <label>Preset<select value="" onChange={(event) => { const preset = DRAFT_PRESETS[Number(event.target.value)]; if (event.target.value && preset) { update(preset); setNotice(""); } }}>
            <option value="" disabled>Choose a starting design</option>
            {DRAFT_PRESETS.map((preset, i) => <option key={preset.family} value={String(i)}>{ABUTMENT_OPTIONS[preset.family]}</option>)}
          </select></label>
          <button type="button" onClick={resetDraft}>Reset</button>
        </div>
        <label>Abutment family<select value={draft.family} onChange={(event) => setField("family", event.target.value as Draft["family"])}>
          {Object.entries(ABUTMENT_OPTIONS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select></label>
        <label>Wing-wall layout<select value={draft.wingType} onChange={(event) => setField("wingType", event.target.value as WingType)}>
          {WING_TYPES.map((type) => <option key={type.id} value={type.id}>{type.label}</option>)}
        </select></label>
        <label>Span lengths in order <span>m · comma or count × length</span><input value={draft.spans} placeholder="3 x 12, 18" maxLength={156} onChange={(event) => setField("spans", event.target.value)} /></label>
        <details open>
          <summary>Founding levels</summary>
          <p className="draft-field-help">Leave blank to use the shared level for abutments or piers. Levels are measured at the underside of the RCC footing.</p>
          <div className="draft-field-grid">{assessment.supports.map(({ id, defaultRl }) => (
            <label key={id}>
              {id} footing base RL<span>m</span>
              <input type="number" step="0.001" value={draft.foundingLevels?.[id] ?? ""}
                placeholder={Number.isFinite(defaultRl) ? defaultRl.toFixed(3) : undefined}
                onChange={(event) => setField("foundingLevels", { ...draft.foundingLevels, [id]: event.target.value })} />
            </label>
          ))}</div>
        </details>
        {FIELD_GROUPS.map(({ title, fields }, i) => <details key={title} open={i === 0 || i === 1 ? true : undefined}>
          <summary>{title}</summary>
          <div className="draft-field-grid">{fields.map(([key, label, unit, min, max, step]) => <label key={key}>
            {label}<span>{unit}</span><input type="number" min={min} max={max} step={step} value={draft[key]}
              disabled={(draft.family !== "GRAVITY" && (key === "frontBatter" || key === "backBatter")) || (draft.family !== "CANTILEVER" && key === "stemWidth")}
              onChange={(event) => setField(key, event.target.value)} />
          </label>)}</div>
        </details>)}
        <section className="draft-saves" aria-label="Saved drawings">
          <p className="draft-field-help">Saved designs are stored on this browser profile. Use a project code on shared devices.</p>
          <label>Design name<input value={draft.name} maxLength={64} onChange={(event) => setField("name", event.target.value)} /></label>
          <button type="button" onClick={saveDesign} disabled={!valid || !draft.name.trim()}>{saved.some((entry) => entry.draft.name === draft.name.trim()) ? "Update saved design" : "Save on this browser"}</button>
          {saved.length > 0 && <>
            <label>Saved designs<select value="" onChange={(event) => {
              const selected = saved.find((entry) => entry.id === event.target.value);
              if (selected) loadDesign(selected);
            }}><option value="" disabled>Load a design</option>{saved.map(({ id, draft: item }) => <option key={id} value={id}>{item.name}</option>)}</select></label>
            <div className="draft-saved-list">{saved.slice(0, 4).map((entry) => <div key={entry.id}>
              <button type="button" onClick={() => loadDesign(entry)}>{entry.draft.name}</button>
              <button type="button" aria-label={`Delete ${entry.draft.name}`} onClick={() => deleteDesign(entry.id)}>×</button>
            </div>)}</div>
          </>}
          {saved.length === 0 && <p className="draft-field-help">No saved designs yet.</p>}
          {notice && <p role="status">{notice}</p>}
        </section>
      </aside>
      <section className="draft-output" aria-label="Live drawings">
        <div className="draft-output-head"><div><h2>{lastValid.name || "Untitled design"}</h2><p>{ABUTMENT_OPTIONS[lastValid.family]} · {WING_TYPES.find((type) => type.id === lastValid.wingType)?.label} · Review draft</p></div>
          <div className="draft-tabs" role="group" aria-label="Drawing views">
            <button type="button" aria-pressed={active === "ga-plan"} onClick={() => setActive("ga-plan")}>{VIEW_LABELS["ga-plan"]}</button>
            <button type="button" aria-pressed={active === "all"} onClick={() => setActive("all")}>All views</button>
            {views.filter(({ id }) => id !== "ga-plan").map(({ id }) => <button type="button" key={id} aria-pressed={active === id} onClick={() => setActive(id)}>{VIEW_LABELS[id]}</button>)}
          </div>
        </div>
        <div className="draft-review-tools">
          <div className="draft-checks" aria-label="Geometry checks" aria-live="polite">
            {assessment.checks.map(({ label, ok, detail }) => <span key={label} className={ok ? "draft-valid" : "draft-invalid"} title={detail}>{ok ? "✓" : "!"} {label}</span>)}
          </div>
          <div className="draft-tabs" role="group" aria-label="Drawing overlays">
            <button type="button" aria-pressed={dimensions} onClick={() => setDimensions(!dimensions)}>Dimensions</button>
            <button type="button" aria-pressed={levels} onClick={() => setLevels(!levels)}>Levels</button>
            <button type="button" aria-pressed={grid} onClick={() => setGrid(!grid)}>Grid</button>
          </div>
        </div>
        <div className="draft-metrics" aria-label="Live design summary">
          <article><span>Overall length</span><strong>{summary.overallLength.toFixed(1)} m</strong></article>
          <article><span>Deck concrete · est.</span><strong>{summary.deckConcrete.toFixed(1)} m³</strong></article>
          <article><span>Abutments · est.</span><strong>{summary.abutmentConcrete.toFixed(1)} m³</strong></article>
          <article><span>Lowest footing base RL</span><strong>{summary.footingBaseRl.toFixed(3)} m</strong></article>
        </div>
        {!valid && <div className="draft-errors" role="status"><strong>Showing the last valid drawing. Correct the inputs to export.</strong>
          <ul>{assessment.errors.map((message) => <li key={message}>{message}</li>)}</ul></div>}
        <div className={`draft-views ${active === "all" ? "" : "draft-single"}`}>
          {visibleViews.filter((view) => active === "all" ? view.id !== "ga-plan" : active === view.id).map((view) => <Viewport key={`${active}-${view.id}`}
            view={view} draft={draft} valid={valid} focus={active === "all" ? () => setActive(view.id) : undefined} grid={grid} theme={theme} />)}
        </div>
      </section>
    </main>
  </div>;
}
