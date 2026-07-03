import { context } from 'esbuild';
import { sassPlugin } from 'esbuild-sass-plugin';
import { exec } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const srcDir = (sub) => path.resolve(__dirname, 'src', sub);

const watch = process.argv.includes("--watch");
const env = process?.env?.NODE_ENV ?? JSON.stringify("production");

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
  entryPoints: [
    './src/entries/OrganizationsEntry.tsx',
    './src/entries/EntitlementsEntry.tsx',
    './src/entries/CreateEntitlementModal.tsx',
    './src/entries/CreateUserModal.tsx',
    './src/entries/StandaloneRoot.tsx',
    './src/entries/AdobeRoot.tsx',
  ],
  outdir: '../static',
  outbase: './src/entries',
  bundle: true,
  platform: 'browser',
  mainFields: ["browser", "module", "main"],
  format: 'esm',
  sourcemap: true,
  allowOverwrite: true,
  // Keep these in sync with `compilerOptions.paths` in tsconfig.json.
  alias: {
    '~app': srcDir('app'),
    '~features': srcDir('features'),
    '~organizations': srcDir('features/organizations'),
    '~entitlements': srcDir('features/entitlements'),
    '~shared': srcDir('shared'),
    '~i18n': srcDir('i18n'),
  },
  define: {
    "process.env.NODE_ENV": env,
  },
  plugins: [
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
