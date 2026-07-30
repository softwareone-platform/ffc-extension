# build-tools

Build-time helpers for the esbuild build (`frontend/esbuild.config.js`). Nothing
here is bundled into the app — these are Node ESM modules that run only while
building, so they live outside `src/` (and outside `tsc`).

## Plugins

- [`experimental-theme-resolver/`](./experimental-theme-resolver/README.md) —
  **experimental** esbuild plugin that redirects imports to per-theme overrides
  based on `APP_THEME` (currently under `<feature>/themeExperimental/<theme>/`).
  Inert unless `APP_THEME` is set.
- [`reload-brave-plugin/`](./reload-brave-plugin/README.md) — dev-only plugin
  that reloads the portal tab in Brave after each rebuild (macOS).

## Adding a build helper

Add a folder here exporting a factory (e.g. `myPlugin(options)` returning an
esbuild `Plugin`), then import it in `esbuild.config.js`. Keep it framework-free
Node code — it never ships to the browser.
