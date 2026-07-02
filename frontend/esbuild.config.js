import { context } from 'esbuild';
import { sassPlugin } from 'esbuild-sass-plugin';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const srcDir = (sub) => path.resolve(__dirname, 'src', sub);

const watch = process.argv.includes("--watch");
const env = process?.env?.NODE_ENV ?? JSON.stringify("production");

const ctx = await context({
  entryPoints: [
    './src/entries/OrganizationsEntry.tsx',
    './src/entries/EntitlementsEntry.tsx',
    './src/entries/CreateEntitlementModal.tsx',
    './src/entries/CreateUserModal.tsx',
    './src/entries/StandaloneRoot.tsx',
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
  plugins: [sassPlugin({
    filter: /\.scss$/,
    type: 'style',
  })],
});

if (watch) {
  await ctx.watch();
  console.log('watching...');
} else {
  await ctx.rebuild();
  await ctx.dispose();
}
