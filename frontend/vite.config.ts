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

export default defineConfig({
  plugins: [react(), skipTypeDeclarations()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:3000",
    },
  },
  build: {
    sourcemap: true,
  },
});
