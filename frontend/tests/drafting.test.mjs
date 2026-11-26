import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";
import { createServer } from "vite";

let server;
let geometry;
let toDxf;

before(async () => {
  server = await createServer({
    root: fileURLToPath(new URL("../", import.meta.url)),
    server: { middlewareMode: true },
    optimizeDeps: { noDiscovery: true, include: [] },
    appType: "custom",
  });
  geometry = await server.ssrLoadModule("/src/sheets/draftingGeometry.ts");
  ({ toDxf } = await server.ssrLoadModule("/src/sheets/detailGeometry.js"));
});

after(async () => server?.close());

for (const [problem, fields] of [
  ["empty schedule", { spans: "" }],
  ["span count overflow", { spans: "999999999x12" }],
  ["unknown abutment family", { family: "other" }],
  ["unknown wing layout", { wingType: "other" }],
  ["non-finite deck width", { deckWidth: "Infinity" }],
  ["missing structural depth", { slab: "" }],
  ["carriageway wider than deck", { carriageway: "18", deckWidth: "10" }],
  ["high flood above soffit", { hfl: "120" }],
  ["scour above high flood", { scour: "120" }],
  ["footing top above cap soffit", { foundingLevels: { A1: "120" } }],
  ["non-numeric founding level", { foundingLevels: { P1: "NaN" } }],
]) {
  test(`draft export blocks ${problem}`, () => {
    assert.equal(geometry.canExportDraft({ ...geometry.DRAFT_PRESETS[0], ...fields }), false);
  });
}

test("draft export recovers when inputs are corrected", () => {
  const preset = geometry.DRAFT_PRESETS[0];
  assert.equal(geometry.canExportDraft({ ...preset, hfl: "120" }), false);
  assert.equal(geometry.canExportDraft(preset), true);
  const views = geometry.buildDraftViews(preset);
  assert.ok(views.find(({ id }) => id === "ga-plan"));
  assert.ok(views.every((view) => toDxf(view).includes("REVIEW DRAFT")));
});

test("unequal spans leave the entered gaps centred on intermediate piers", () => {
  const elevation = geometry.buildDraftViews({ ...geometry.DRAFT_PRESETS[0], spans: "10, 16, 12", gap: "80" })[0];
  const slabRuns = elevation.prims.filter((p) => p.layer === "SUPER-DECK" && p.k === "poly");
  assert.deepEqual(slabRuns.map(({ pts }) => [pts[0], pts[2]]), [[0, 9960], [10040, 25960], [26040, 38000]]);
});

test("span shorthand expands in order and matches the equivalent comma schedule", () => {
  const base = geometry.DRAFT_PRESETS[0];
  const shorthand = { ...base, spans: "10, 2x12.5, 3 × 15, 2 X 18" };
  const expanded = { ...base, spans: "10, 12.5, 12.5, 15, 15, 15, 18, 18" };
  assert.deepEqual(geometry.assessDraft(shorthand).spans, [10, 12.5, 12.5, 15, 15, 15, 18, 18]);
  assert.equal(geometry.summarizeDraft(shorthand).overallLength, 116);
  assert.deepEqual(geometry.buildDraftViews(shorthand), geometry.buildDraftViews(expanded));
});

test("span shorthand rejects invalid groups and limits the expanded count", () => {
  const base = geometry.DRAFT_PRESETS[0];
  assert.equal(geometry.assessDraft({ ...base, spans: "11 x 12, 18" }).spans.length, 12);
  for (const spans of ["0x12", "1.5x12", "12x12, 18", "999999999x12", "2x", "12,", "2x3.9", "2x80.1"]) {
    const draft = { ...base, spans };
    assert.equal(geometry.assessDraft(draft).checks[0].ok, false, spans);
    assert.deepEqual(geometry.buildDraftViews(draft), [], spans);
  }
});

test("each abutment family has distinct longitudinal geometry and fitted views", () => {
  const base = geometry.DRAFT_PRESETS[0];
  const viewsByFamily = geometry.DRAFT_PRESETS.map(({ family }) => geometry.buildDraftViews({ ...base, family }));
  for (const views of viewsByFamily) {
    assert.deepEqual(views.map((view) => view.id), ["elevation", "section", "front", "plan", "foundation", "ga-plan"]);
    assert.ok(views.every(({ box }) => box.every(Number.isFinite) && box[2] > 0 && box[3] > 0));
  }
  assert.equal(new Set(viewsByFamily.map((views) => JSON.stringify(views[1].prims))).size, 3);
});

test("the combined drawing stacks elevation and plan without moving any support along chainage", () => {
  const views = geometry.buildDraftViews({ ...geometry.DRAFT_PRESETS[0], spans: "10, 16, 12" });
  const [elevation] = views;
  const plan = views.find((view) => view.id === "foundation");
  const combined = views.find((view) => view.id === "ga-plan");
  const supports = (view) => view.prims.filter((p) => p.k === "text" && /^(?:A[12]|P\d+)$/.test(p.s));
  const elevSupports = supports(elevation);
  const planSupports = supports(plan);
  const both = supports(combined);
  assert.deepEqual(both.slice(0, elevSupports.length), elevSupports);
  assert.deepEqual(both.slice(elevSupports.length).map(({ s, x }) => [s, x]), planSupports.map(({ s, x }) => [s, x]));
  assert.ok(both[elevSupports.length].y < Math.min(...elevSupports.map(({ y }) => y)));
  assert.ok(combined.box[3] > elevation.box[3] + plan.box[3]);
  assert.match(toDxf(combined), /BRIDGE PLAN · FOUNDATIONS/);
});

test("pier foundations share centrelines, dimensions and founding levels across both views", () => {
  const base = geometry.DRAFT_PRESETS[0];
  const draft = { ...base, spans: "10, 2 x 15", pierFootingAlong: "4", pierFootingAcross: "6", pierFootingDepth: "1", pierScourCover: "0.4" };
  const views = geometry.buildDraftViews(draft);
  const [elevation] = views;
  const plan = views.find((view) => view.id === "foundation");
  const footingVertices = (view) => view.prims.filter((p) => p.k === "poly" && p.layer === "FOUND-PIER").map(({ pts }) => pts.map(Math.round));
  assert.deepEqual(footingVertices(elevation), [
    [8000, 101000, 12000, 101000, 12000, 102000, 8000, 102000],
    [23000, 101000, 27000, 101000, 27000, 102000, 23000, 102000],
  ]);
  assert.deepEqual(footingVertices(plan), [
    [8000, -3000, 12000, -3000, 12000, 3000, 8000, 3000],
    [23000, -3000, 27000, -3000, 27000, 3000, 23000, 3000],
  ]);
  assert.match(toDxf(plan), /\nLINE\n8\nFOUND-PIER\n10\n8000\n/);
  assert.match(toDxf(elevation), /\nLINE\n8\nFOUND-PIER\n10\n8000\n/);
  const single = geometry.buildDraftViews({ ...draft, spans: "12" });
  assert.equal(single.flatMap(footingVertices).length, 0);
  assert.ok(geometry.assessDraft({ ...draft, pierFootingAlong: "16" }).errors.some((error) => /footing length/.test(error)));
});

test("approach slabs are 3500 mm long, 300 mm thick and as wide as the deck", () => {
  const base = geometry.DRAFT_PRESETS[0];
  const approaches = (view) => view.prims.filter((prim) => prim.k === "poly" && prim.layer === "CIVIL-ROAD");
  const bounds = ({ pts }) => {
    const xs = pts.filter((_, index) => index % 2 === 0);
    const ys = pts.filter((_, index) => index % 2 === 1);
    return [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)].map(Math.round);
  };

  for (const { family } of geometry.DRAFT_PRESETS) {
    const [elevation, section, , plan, foundation] = geometry.buildDraftViews({
      ...base, family, dirt: "0.45", spans: "2 x 12, 18", deckWidth: "12.4", carriageway: "8.5",
    });
    const left = [-3950, -450, 110615, 110915];
    assert.deepEqual(approaches(elevation).map(bounds), [left, [42450, 45950, 110615, 110915]]);
    assert.deepEqual(approaches(section).map(bounds), [left]);
    assert.deepEqual(approaches(plan).map(bounds), [[-3950, -450, -6200, 6200]]);
    assert.deepEqual(approaches(foundation).map(bounds), [
      [-3950, -450, -6200, 6200], [42450, 45950, -6200, 6200],
    ]);
    assert.match(toDxf(foundation), /\nLINE\n8\nCIVIL-ROAD\n10\n-3950\n20\n-6200\n/);
    assert.match(toDxf(elevation), /\n2\nCIVIL-ROAD\n/);
    assert.match(toDxf(elevation), /\nLINE\n8\nCIVIL-ROAD\n10\n-3950\n/);
  }
});

test("PCC pads sit below footings and project 150 mm on each plan edge by default", () => {
  const outlines = (view, layer) => view.prims.filter((p) => p.k === "poly" && p.layer === layer).map(({ pts }) => {
    const xs = pts.filter((_, i) => i % 2 === 0);
    const ys = pts.filter((_, i) => i % 2 === 1);
    return [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)].map(Math.round);
  });
  for (const preset of geometry.DRAFT_PRESETS) {
    const [elevation, section, front, plan, foundation, combined] = geometry.buildDraftViews(preset);
    const sectionFooting = outlines(section, preset.family === "GRAVITY" ? "ABUT-PROF" : "FOUND-CAP")[0];
    const [left, right, base] = sectionFooting;
    assert.deepEqual(outlines(section, "FOUND-PCC"), [[left-150, right+150, base-300, base]]);
    assert.deepEqual(outlines(front, "FOUND-PCC"), [[-6650, 6650, base-300, base]]);
    const projected = ([x0, x1, y0, y1]) => [x0-150, x1+150, y0-150, y1+150];
    assert.deepEqual(outlines(plan, "FOUND-PCC"), outlines(plan, "FOUND-CAP").map(projected));
    assert.deepEqual(outlines(foundation, "FOUND-PCC"), [
      ...outlines(foundation, "FOUND-CAP"), ...outlines(foundation, "FOUND-PIER"),
    ].map(projected));
    const pierPads = outlines(elevation, "FOUND-PIER").map(([x0, x1, y0]) => [x0-150, x1+150, y0-300, y0]);
    assert.deepEqual(outlines(elevation, "FOUND-PCC").slice(0, -2), pierPads);
    assert.match(toDxf(combined), /\nLINE\n8\nFOUND-PCC\n/);
  }
  const base = geometry.DRAFT_PRESETS[0];
  const [custom] = geometry.buildDraftViews({ ...base, spans: "12", pccDepth: "400", pccProjection: "200" });
  assert.deepEqual(outlines(custom, "FOUND-PCC"), outlines(custom, "FOUND-CAP")
    .map(([x0, x1, y0]) => [x0-200, x1+200, y0-400, y0]));
  assert.equal(geometry.buildDraftViews({ ...base, pccDepth: "0" }).flatMap((view) => outlines(view, "FOUND-PCC")).length, 0);
});

test("dirt walls meet the concrete slab tops for all abutments and girder depths", () => {
  const top = ({ pts }) => Math.max(...pts.filter((_, i) => i % 2 === 1));
  for (const { family } of geometry.DRAFT_PRESETS) {
    for (const [slab, girder] of [["650", "0"], ["250", "1150"], ["230", "1800"]]) {
      for (const wear of ["0", "65"]) {
        const draft = { ...geometry.DRAFT_PRESETS[0], family, slab, girder, wear };
        const [elevation, section, front] = geometry.buildDraftViews(draft);
        const slabTop = (Number(draft.road) - Number(wear) / 1000) * 1000;
        for (const view of [elevation, section]) {
          const profiles = view.prims.filter((p) => p.k === "poly" && p.layer === (family === "FULL_HEIGHT_WALL" ? "SUB-ABUT" : "ABUT-PROF"));
          assert.equal(profiles.length, view === elevation ? 2 : 1);
          for (const profile of profiles) assert.ok(Math.abs(top(profile) - slabTop) < .001);
          for (const slabOutline of view.prims.filter((p) => p.k === "poly" && ["SUPER-DECK", "CIVIL-ROAD"].includes(p.layer))) {
            assert.ok(Math.abs(top(slabOutline) - slabTop) < .001);
          }
        }
        assert.ok(Math.abs(top(front.prims.find((p) => p.k === "poly" && p.layer === "ABUT-PROF")) - slabTop) < .001);
      }
    }
  }
});

test("wing layouts produce distinct plan geometry", () => {
  const base = geometry.DRAFT_PRESETS[0];
  const plans = ["SPLAYED", "STRAIGHT", "CURTAIN"].map((wingType) =>
    geometry.buildDraftViews({ ...base, wingType }).find((view) => view.id === "plan"));
  assert.equal(new Set(plans.map((view) => JSON.stringify(view.prims))).size, 3);
  assert.ok(plans.every((view) => view.box.every(Number.isFinite) && view.box[2] > 0 && view.box[3] > 0));
});

test("the elevation labels road, HFL and NGL and tags the footing at one pier", () => {
  const base = geometry.DRAFT_PRESETS[0];
  const draft = { ...base, spans: "10, 16, 12" };
  const elevation = geometry.buildDraftViews(draft)[0];
  const levelLabels = (view) => view.prims.filter((p) => p.k === "text" && p.layer === "TEXT-LEVEL").map(({ s }) => s);
  assert.ok(elevation.prims.some((prim) => prim.layer === "SUB-BEARING"));
  assert.deepEqual(levelLabels(elevation), ["HFL 107.300 m", "NGL 105.200 m", "ROAD RL 110.980 m", "PIER FOOTING BASE RL 101.100 m"]);
  const leaders = elevation.prims.filter((p) => p.k === "line" && p.layer === "TEXT-LEVEL");
  assert.deepEqual(leaders.map(({ x1, y1 }) => [Math.round(x1), Math.round(y1)]), [[27600, 101100]]);
  assert.ok(!elevation.prims.some((prim) => ["CIVIL-OFL", "CIVIL-SCOUR"].includes(prim.layer)));
  const [singleSpan] = geometry.buildDraftViews({ ...base, spans: "12" });
  assert.equal(levelLabels(singleSpan).length, 3);
  assert.notDeepEqual(elevation.prims, geometry.buildDraftViews({ ...draft, bearing: "0" })[0].prims);
});

test("support-specific footing RLs update both abutments, the piers and their PCC pads", () => {
  const base = geometry.DRAFT_PRESETS[0];
  const draft = { ...base, spans: "10, 16, 12", foundingLevels: { A1: "104.25", A2: "98.5", P1: "96.75" } };
  for (const { family } of geometry.DRAFT_PRESETS) {
    const [elevation, section, front, , plan] = geometry.buildDraftViews({ ...draft, family });
    const polys = (view, layer) => view.prims.filter((p) => p.k === "poly" && p.layer === layer);
    const lows = (view, layer) => polys(view, layer).map(({ pts }) =>
      Math.round(Math.min(...pts.filter((_, i) => i % 2 === 1))));
    const abutmentLayer = family === "GRAVITY" ? "ABUT-PROF" : "FOUND-CAP";
    assert.deepEqual(lows(elevation, abutmentLayer), [104250, 98500]);
    assert.deepEqual(lows(elevation, "FOUND-PIER"), [96750, 101100]);
    assert.deepEqual(lows(elevation, "FOUND-PCC"), [96450, 100800, 103950, 98200]);
    assert.deepEqual(lows(section, abutmentLayer), [104250]);
    assert.deepEqual(lows(front, "FOUND-CAP"), [104250]);
    const level = elevation.prims.find((p) => p.k === "text" && p.s.startsWith("PIER FOOTING"));
    assert.equal(level.s, "PIER FOOTING BASE RL 96.750 m");
    const leader = elevation.prims.find((p) => p.k === "line" && p.layer === "TEXT-LEVEL");
    assert.equal(leader.x1, 11600);
    assert.match(toDxf(elevation), /PIER FOOTING BASE RL 96\.750 m/);

    if (family === "GRAVITY") {
      const widths = polys(plan, "FOUND-CAP").map(({ pts }) => pts[2]-pts[0]);
      assert.ok(widths[1] > widths[0], "the taller A2 gravity abutment has a wider footing footprint");
    }
  }

  const assessed = geometry.assessDraft({ ...base, foundingLevels: { A1: "", P1: " " } });
  assert.equal(assessed.a1.base, assessed.a2.base);
  assert.equal(assessed.piers[0].base, assessed.piers[1].base);
  assert.equal(geometry.isDraft(base), true);
  assert.equal(geometry.isDraft({ ...base, foundingLevels: { P1: 96 } }), false);
  assert.match(geometry.assessDraft({ ...draft, foundingLevels: { A2: "110" } }).errors[0], /A2.*stem/);
  assert.match(geometry.assessDraft({ ...draft, foundingLevels: { P2: "110" } }).errors[0], /P2.*cap soffit/);
  const single = geometry.assessDraft({ ...draft, spans: "12" });
  assert.deepEqual(single.supports.map(({ id, base }) => [id, base]), [["A1", 104.25], ["A2", 98.5]]);
});

test("live summaries report finite geometry-derived quantities", () => {
  const summary = geometry.summarizeDraft(geometry.DRAFT_PRESETS[0]);
  assert.equal(summary.overallLength, 36);
  assert.ok(summary.deckConcrete > 0);
  assert.ok(summary.abutmentConcrete > 0);
  assert.ok(summary.footingWidth > 0);
  assert.ok(Number.isFinite(summary.footingBaseRl));
});

test("splay changes both plan wing outlines and invalid dimensions suppress generation", () => {
  const initial = geometry.DRAFT_PRESETS[0];
  const plan = (draft) => geometry.buildDraftViews(draft).find((view) => view.id === "plan");
  const wings = (view) => view.prims.filter((p) => p.k === "poly" && p.layer === "SUB-ABUT").slice(-2);
  assert.notDeepEqual(wings(plan(initial)), wings(plan({ ...initial, splay: "54" })));
  const invalid = { ...initial, deckWidth: "23" };
  assert.ok(geometry.assessDraft(invalid).errors.length);
  assert.deepEqual(geometry.buildDraftViews(invalid), []);
});
