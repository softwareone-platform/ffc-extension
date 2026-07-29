import { context } from 'esbuild';
import { sassPlugin } from 'esbuild-sass-plugin';
import { exec } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

import { themeResolver } from './theme-resolver/index.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const srcDir = (sub) => path.resolve(__dirname, 'src', sub);

const watch = process.argv.includes("--watch");
const env = process?.env?.NODE_ENV ?? JSON.stringify("production");
// Active theme for the Adobe feature (build-time only). Overrides live under
// `src/features/adobe/themes/<APP_THEME>/`. Unset -> canonical sources are used.
const adobeTheme = process.env.APP_THEME;

// Dev-only: after each successful rebuild, reload any Brave tab pointing at the
// portal so changes show up without a manual refresh. The portal page is served
// remotely, so esbuild's own live-reload can't inject into it — we drive the
// browser via AppleScript instead (macOS only).
const RELOAD_URL_MATCH = 'portal.s1.show';
const reloadBravePlugin = {
  name: 'reload-brave',
  setup(build) {
    build.onEnd((result) => {
      if (!watch || result.errors.length > 0) return;
      const script = [
        'tell application "Brave Browser"',
        'repeat with w in every window',
        'repeat with t in every tab of w',
        `if (URL of t) contains "${RELOAD_URL_MATCH}" then reload t`,
        'end repeat',
        'end repeat',
        'end tell',
      ]
        .map((line) => `-e '${line}'`)
        .join(' ');
      exec(`osascript ${script}`, (err) => {
        if (err) console.error(`Brave reload failed: ${err.message}`);
        else console.log(`Reloaded ${RELOAD_URL_MATCH} tab(s) in Brave`);
      });
    });
  },
};

const ctx = await context({
  // `out` names are kept flat (no subfolder) so the emitted bundles stay at
  // `../static/<Name>.js` — the paths the MPT host and package.json reference —
  // even though the sources are grouped into standalone/ modals/ feature-views/.
  entryPoints: [
    { in: './src/entries/single-entry/OrganizationsEntry.tsx', out: 'OrganizationsEntry' },
    { in: './src/entries/single-entry/EntitlementsEntry.tsx', out: 'EntitlementsEntry' },
    { in: './src/entries/modals/CreateEntitlementModal.tsx', out: 'CreateEntitlementModal' },
    { in: './src/entries/standalone/SandboxStandaloneRoot.tsx', out: 'SandboxStandaloneRoot' },
  ],
  outdir: '../static',
  bundle: true,
  platform: 'browser',
  mainFields: ["browser", "module", "main"],
  format: 'esm',
  // Set explicitly so JSX doesn't depend on per-file tsconfig discovery — plugin
  // resolved files (e.g. theme overrides) otherwise fall back to the classic
  // `React.createElement` transform and crash with "React is not defined".
  jsx: 'automatic',
  sourcemap: true,
  allowOverwrite: true,
  // Keep these in sync with `compilerOptions.paths` in tsconfig.json.
  alias: {
    '~app': srcDir('app'),
    '~features': srcDir('features'),
    '~organizations': srcDir('features/organizations'),
    '~entitlements': srcDir('features/entitlements'),
    '~shared': srcDir('shared'),
    '~assets': srcDir('assets'),
    '~i18n': srcDir('i18n'),
  },
  define: {
    "process.env.NODE_ENV": env,
  },
  loader: {
    '.png': 'dataurl',
    '.jpg': 'dataurl',
    '.jpeg': 'dataurl',
    '.webp': 'dataurl',
  },
  plugins: [
    // Must run before sassPlugin so themed .scss overrides are redirected
    // before Sass compiles them.
    themeResolver({ theme: adobeTheme, featureDir: srcDir('features/adobe') }),
    // `*.module.scss` -> esbuild CSS modules: hashed, unique class names exposed
    // as a default-exported class map (`import styles from './x.module.scss'`).
    // Registered first so it wins for module files; the global instance below
    // (esbuild's Go regex has no lookbehind) then handles the remaining `.scss`.
    sassPlugin({
      filter: /\.module\.scss$/,
      type: 'local-css',
    }),
    // Everything else -> global stylesheet injected as <style> (side-effect import).
    sassPlugin({
      filter: /\.scss$/,
      type: 'style',
    }),
    reloadBravePlugin,
  ],
});

if (watch) {
  await ctx.watch();
  console.log('watching...');
} else {
  await ctx.rebuild();
  await ctx.dispose();
}
