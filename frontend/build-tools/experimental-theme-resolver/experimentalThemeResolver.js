import fs from "node:fs";
import path from "node:path";

import { THEME_RESOLVER_CONFIG } from "./config.js";

/**
 * EXPERIMENTAL: esbuild port of the optscale Vite theme resolver, scoped to a
 * single feature. Not part of the supported build path — enabled only when
 * APP_THEME is set.
 *
 * Keep canonical sources under `<featureDir>/…` and drop per-theme overrides under
 * `<featureDir>/themes/<theme>/…` mirroring the same relative structure. When the
 * active theme has an override for a resolved module, the import is redirected to it;
 * otherwise it falls back to the canonical file.
 *
 * The theme is chosen at build time (inactive when `theme` is falsy), matching the
 * upstream plugin's limitations (no runtime switching, no deep merging).
 *
 * @param {{ theme?: string, featureDir: string }} options
 * @returns {import('esbuild').Plugin}
 */
export function experimentalThemeResolver({ theme, featureDir }) {
  return {
    name: "esbuild-experimental-theme-resolver",
    setup(build) {
      if (!theme) return;

      const featureRoot = path.resolve(featureDir);
      const themeBase = path.join(featureRoot, THEME_RESOLVER_CONFIG.themesDir, theme);
      const featureMarker = featureRoot + path.sep;
      const themeMarker = themeBase + path.sep;
      // Path fragment used to cheaply detect imports pointing at the feature,
      // e.g. the "~features/adobe" alias -> "features/adobe".
      const featureImportMarker = `features/${path.basename(featureRoot)}`;

      const isFile = (filePath) => {
        try {
          return fs.statSync(filePath).isFile();
        } catch {
          return false;
        }
      };

      const resolveWithExtensions = (base) =>
        THEME_RESOLVER_CONFIG.extensions
          .map((ext) => (ext.startsWith("/") ? path.join(base, ext) : `${base}${ext}`))
          .find(isFile) || null;

      build.onResolve({ filter: /.*/ }, async (args) => {
        // Skip the lookup we trigger ourselves to find the canonical path.
        if (args.pluginData?.skipThemeResolver) return null;

        const importer = args.importer || "";
        const isRelative = args.path.startsWith(".") || args.path.startsWith("/");
        const referencesFeature = args.path.includes(featureImportMarker);
        const fromFeature = importer.startsWith(featureMarker);

        // Cheap pre-filter: only imports that could touch the themed feature.
        if (!referencesFeature && !(isRelative && fromFeature)) return null;

        const resolved = await build.resolve(args.path, {
          importer: args.importer,
          resolveDir: args.resolveDir,
          kind: args.kind,
          pluginData: { skipThemeResolver: true }
        });
        if (resolved.errors.length || !path.isAbsolute(resolved.path)) return null;

        const canonical = resolved.path;

        // Only redirect files that live inside the themed feature.
        if (!canonical.startsWith(featureMarker)) return null;
        // Already resolved into the active theme directory.
        if (canonical.startsWith(themeMarker)) return null;
        // An override importing a sibling should fall back to canonical sources
        // rather than being redirected onto itself.
        if (importer.startsWith(themeMarker)) return null;

        const relFromFeature = path.relative(featureRoot, canonical);
        const overrideExact = path.join(themeBase, relFromFeature);
        const override =
          (isFile(overrideExact) && overrideExact) ||
          resolveWithExtensions(overrideExact.replace(/\.[^./\\]+$/, ""));

        return override ? { path: override } : null;
      });
    }
  };
}
