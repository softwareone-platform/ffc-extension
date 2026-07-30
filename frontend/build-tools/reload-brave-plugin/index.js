import { exec } from "node:child_process";

/**
 * Dev-only esbuild plugin: after each successful rebuild, reload any Brave tab
 * pointing at the portal so changes show up without a manual refresh. The portal
 * page is served remotely, so esbuild's own live-reload can't inject into it —
 * we drive the browser via AppleScript instead (macOS only).
 *
 * @param {{ watch: boolean, urlMatch: string }} options
 * @returns {import('esbuild').Plugin}
 */
export function reloadBravePlugin({ watch, urlMatch }) {
  return {
    name: "reload-brave",
    setup(build) {
      build.onEnd((result) => {
        if (!watch || result.errors.length > 0) return;
        const script = [
          'tell application "Brave Browser"',
          "repeat with w in every window",
          "repeat with t in every tab of w",
          `if (URL of t) contains "${urlMatch}" then reload t`,
          "end repeat",
          "end repeat",
          "end tell",
        ]
          .map((line) => `-e '${line}'`)
          .join(" ");
        exec(`osascript ${script}`, (err) => {
          if (err) console.error(`Brave reload failed: ${err.message}`);
          else console.log(`Reloaded ${urlMatch} tab(s) in Brave`);
        });
      });
    },
  };
}
