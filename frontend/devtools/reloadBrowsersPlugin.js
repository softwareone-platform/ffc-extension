import { exec } from 'node:child_process';

const DEFAULT_BROWSERS = ['Brave Browser', 'Google Chrome'];

const reloadTabs = (appName, urlMatch) => {
  const script = [
    `tell application "${appName}"`,
    'repeat with w in every window',
    'repeat with t in every tab of w',
    `if (URL of t) contains "${urlMatch}" then reload t`,
    'end repeat',
    'end repeat',
    'end tell',
  ]
    .map((line) => `-e '${line}'`)
    .join(' ');
  exec(`osascript ${script}`, (err) => {
    if (err) console.error(`${appName} reload failed: ${err.message}`);
    else console.log(`Reloaded ${urlMatch} tab(s) in ${appName}`);
  });
};

/**
 * esbuild plugin that reloads matching browser tabs after each successful
 * rebuild. Relies on AppleScript/osascript, so it only runs on macOS.
 *
 * @param {object} [options]
 * @param {boolean} [options.enabled=true] Toggle the plugin on/off.
 * @param {boolean} [options.watch=false] Only reload when watching.
 * @param {string} [options.urlMatch] Substring a tab URL must contain to reload.
 * @param {string[]} [options.browsers] macOS app names to target.
 */
export const reloadBrowsersPlugin = ({
  enabled = true,
  watch = false,
  urlMatch,
  browsers = DEFAULT_BROWSERS,
} = {}) => ({
  name: 'reload-browsers',
  setup(build) {
    if (!enabled || process.platform !== 'darwin') return;
    build.onEnd((result) => {
      if (!watch || result.errors.length > 0) return;
      browsers.forEach((appName) => reloadTabs(appName, urlMatch));
    });
  },
});
