# Experimental Theme Resolver (esbuild)

> **Experimental.** Not part of the supported build path — the plugin is inert
> unless `APP_THEME` is set. Exported as `experimentalThemeResolver`.

esbuild port of the optscale Vite theme resolver (`optscale/ngui/ui/src/utils/themeResolver`),
scoped to a single feature. It lets you keep canonical sources in place and ship
per-theme overrides in a parallel directory, without touching import sites.

> TL;DR: keep sources under `<feature>/…`, drop overrides under
> `<feature>/themes/<theme>/…`. When the active theme has a matching file, the
> import resolves to it; otherwise it falls back to the canonical file.

This project builds with **esbuild**, not Vite, so the resolver is implemented as an
esbuild plugin (`onResolve` + `build.resolve`) instead of a Vite `resolveId` plugin.

## Usage

The active theme is chosen at build time via the `APP_THEME` env var and wired up in
`esbuild.config.js`:

```js
experimentalThemeResolver({ theme: process.env.APP_THEME, featureDir: srcDir('features/<feature>') })
```

Run a themed build:

```bash
APP_THEME=acme npm run build:code
# or while developing
APP_THEME=acme npm run watch:code
```

With `APP_THEME` unset the plugin is inactive and canonical sources are used.

## Directory layout

```
src/features/<feature>/
├── AdobeLayout.tsx            # canonical
└── themes/
    └── acme/
        └── AdobeLayout.tsx    # override, used when APP_THEME=acme
```

The override path mirrors the file's path relative to the feature root.

Note: current experimental ACME assets were moved under
`src/features/sandboxExperimentalAcme/acme/` and are intentionally kept outside
this resolver layout.

## Behaviour

- Only files inside the themed feature are redirected.
- Files already inside the active theme dir are left alone.
- Imports made **from** a theme file are not redirected, so an override can import
  the canonical/shared modules (use the `~features` / `~shared` aliases for those).

## Limitations (same as upstream)

- Build-time selection only — no runtime theme switching.
- No deep merging: an override replaces the whole file.
- Theme files can drift from their canonical counterparts if not monitored.
