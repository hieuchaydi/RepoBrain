import { build } from "esbuild";
import { cpSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outdir = resolve(here, "../src/repobrain/web_frontend");

mkdirSync(outdir, { recursive: true });

await build({
  entryPoints: [resolve(here, "src/main.tsx")],
  bundle: true,
  format: "esm",
  target: "es2020",
  outdir,
  entryNames: "app",
  jsx: "automatic",
  minify: true,
  define: {
    "process.env.NODE_ENV": '"production"',
  },
  loader: {
    ".ts": "ts",
    ".tsx": "tsx",
    ".css": "css",
  },
});

cpSync(resolve(here, "src/index.html"), resolve(outdir, "index.html"));
