# reload-brave-plugin

Dev-only esbuild plugin (macOS). After each successful **watch** rebuild it
reloads any Brave tab whose URL contains `urlMatch`, so changes show up without
a manual refresh. The portal page is served remotely, so esbuild's own
live-reload can't inject into it — this drives the browser via AppleScript
(`osascript`) instead.

## Usage

Wired up in `esbuild.config.js`:

```js
import { reloadBravePlugin } from "./build-tools/reload-brave-plugin/index.js";

plugins: [
  reloadBravePlugin({ watch, urlMatch: "portal.s1.show" }),
];
```

- `watch` — the plugin only fires when this is `true` (i.e. `node esbuild.config.js --watch`).
- `urlMatch` — substring matched against each open tab's URL.

## Limitations

- macOS + Brave only (uses `osascript` / AppleScript).
- No-op on build errors and on non-watch builds.
