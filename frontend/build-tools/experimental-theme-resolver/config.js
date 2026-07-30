export const THEME_RESOLVER_CONFIG = {
  // File extensions / index files tried when matching a themed override.
  extensions: [
    "",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".json",
    "/index.tsx",
    "/index.ts",
    "/index.js",
    "/index.jsx",
    "/index.mjs",
    "/index.cjs",
    "/index.css",
    "/index.scss"
  ],
  // Sub-directory (inside the themed feature) that holds per-theme overrides.
  themesDir: "themeExperimental"
};
