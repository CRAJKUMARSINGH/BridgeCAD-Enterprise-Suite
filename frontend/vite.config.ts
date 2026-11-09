import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

/**
 * `detailGeometry.d.ts` is the type-only declaration for the sibling
 * `detailGeometry.js`: TypeScript consumes it, the browser never imports it
 * (runtime imports resolve to the `.js`). But Vite's dev server transforms
 * *any* requested file, so an out-of-band request for the `.d.ts` (IDE file
 * preview, a pasted URL) hits esbuild, fails on `export const X: T;`, and
 * raises the HMR error overlay. Serving declaration files as empty modules
 * keeps the dev server quiet without changing what the app loads.
 */
const skipTypeDeclarations = (): Plugin => ({
  name: "bridgecad:skip-type-declarations",
  load(id) {
    return id.split("?")[0].endsWith(".d.ts") ? "export {};" : null;
  },
});

/**
 * On a static Netlify deploy `/api/health` is answered by
 * `netlify/functions/health.js`, which reports `mode: "demo"` when no FastAPI
 * engine is wired. In dev the `server.proxy` rule forwards `/api/*` to
 * `localhost:3000`, and with no engine there the browser logs
 * `net::ERR_ABORTED` on every page load. Registering the middleware directly
 * (not via the returned post-hook) puts it ahead of Vite's internal proxy, so
 * dev serves the same demo payload as the deploy and the console stays clean.
 */
const devHealthStub = (): Plugin => ({
  name: "bridgecad:dev-health-stub",
  apply: "serve",
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      if (req.url?.split("?")[0] !== "/api/health") return next();
      res.setHeader("content-type", "application/json");
      res.end(JSON.stringify({ frontend: "online", python: "demo", mode: "demo" }));
    });
  },
});

export default defineConfig({
  plugins: [react(), skipTypeDeclarations(), devHealthStub()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:3000",
    },
    // Vite serves source modules as `Cache-Control: no-cache`, so the browser
    // revalidates each one and then reads its own copy out of the disk cache.
    // If that entry is corrupt the read fails with `net::ERR_CACHE_READ_FAILURE`
    // (common in embedded preview browsers after a dev-server restart). Dev
    // responses are cheap to re-send, so forbid storing them at all.
    headers: { "Cache-Control": "no-store" },
  },
  build: {
    sourcemap: true,
  },
});
