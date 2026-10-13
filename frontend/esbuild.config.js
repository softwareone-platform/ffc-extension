import { context } from 'esbuild';
import { sassPlugin, postcssModules } from 'esbuild-sass-plugin';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { reloadBrowsersPlugin } from './devtools/reloadBrowsersPlugin.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const srcDir = (sub) => path.resolve(__dirname, 'src', sub);

const watch = process.argv.includes("--watch");
const env = process?.env?.NODE_ENV ?? JSON.stringify("production");
const extensionVersion = process?.env?.FFC_EXT_EXTENSION_VERSION ?? "0.0.0-dev";

const RELOAD_URL_MATCH = 'portal.s1.show';

const ctx = await context({
  entryPoints: [
    './src/entries/StandaloneRoot.tsx',
  ],
  outdir: '../static',
  outbase: './src/entries',
  entryNames: `[dir]/[name]-${extensionVersion}`,
  bundle: true,
  platform: 'browser',
  mainFields: ["browser", "module", "main"],
  format: 'esm',
  sourcemap: true,
  allowOverwrite: true,
  metafile: true,
  // Keep these in sync with `compilerOptions.paths` in tsconfig.json.
  alias: {
    '~api': srcDir('api'),
    '~app': srcDir('app'),
    '~features': srcDir('features'),
    '~fixes': srcDir('fixes'),
    '~organizations': srcDir('features/organizations'),
    '~entitlements': srcDir('features/entitlements'),
    '~shared': srcDir('shared'),
    '~i18n': srcDir('i18n'),
  },
  define: {
    "process.env.NODE_ENV": env,
    "process.env.FFC_EXT_EXTENSION_VERSION": JSON.stringify(extensionVersion),
  },
  plugins: [
    // `*.module.scss` must be registered before the catch-all below: esbuild uses
    // the first plugin whose onLoad filter matches, and /\.scss$/ matches these too.
    sassPlugin({
      filter: /\.module\.scss$/,
      type: 'style',
      transform: postcssModules({
        generateScopedName: '[name]__[local]___[hash:base64:5]',
      }),
    }),
    sassPlugin({
      filter: /\.scss$/,
      type: 'style',
    }),
    reloadBrowsersPlugin({ watch, urlMatch: RELOAD_URL_MATCH }),
  ],
});

if (watch) {
  await ctx.watch();
  console.log('watching...');
} else {
  await ctx.rebuild();
  await ctx.dispose();
}
