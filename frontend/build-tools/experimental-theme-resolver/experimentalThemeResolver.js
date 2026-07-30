import fs from "node:fs";
import path from "node:path";

import { THEME_RESOLVER_CONFIG } from "./config.js";

/**
 * EXPERIMENTAL: esbuild port of the optscale Vite theme resolver, scoped to a
 * single feature. Not part of the supported build path — enabled only when
 * APP_THEME is set.
 *
 * Keep canonical sources under `<featureDir>/…` and drop per-theme overrides under
 * `<featureDir>/<themesDir>/<theme>/…` mirroring the same relative structure. When the
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
      const themeSegment = `${path.sep}${THEME_RESOLVER_CONFIG.themesDir}${path.sep}${theme}${path.sep}`;
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

      const resolveImportTarget = (targetPath) =>
        (isFile(targetPath) && targetPath) ||
        resolveWithExtensions(targetPath.replace(/\.[^./\\]+$/, ""));

      build.onResolve({ filter: /.*/ }, async (args) => {
        const importer = args.importer || "";
        const isRelative = args.path.startsWith(".") || args.path.startsWith("/");
        const referencesFeature = args.path.includes(featureImportMarker);
        const fromFeature = importer.startsWith(featureMarker);

        // Relative imports inside an override should first use themed siblings,
        // then transparently fall back to canonical files when missing.
        if (isRelative && importer.includes(themeSegment)) {
          const themedRequest = path.resolve(path.dirname(importer), args.path);
          if (resolveImportTarget(themedRequest)) return null;

          const canonicalImporter = importer.replace(themeSegment, path.sep);
          const canonicalRequest = path.resolve(path.dirname(canonicalImporter), args.path);
          const canonicalFallback = resolveImportTarget(canonicalRequest);

          return canonicalFallback ? { path: canonicalFallback } : null;
        }

        // Skip the lookup we trigger ourselves to find the canonical path.
        if (args.pluginData?.skipThemeResolver) return null;

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
        if (canonical.startsWith(themeMarker) || canonical.includes(themeSegment)) return null;
        // An override importing a sibling should fall back to canonical sources
        // rather than being redirected onto itself.
        if (importer.startsWith(themeMarker) || importer.includes(themeSegment)) return null;

        const relFromFeature = path.relative(featureRoot, canonical);
        const overrideExact = path.join(themeBase, relFromFeature);
        const override = resolveImportTarget(overrideExact);

        return override ? { path: override } : null;
      });
    }
  };
}
