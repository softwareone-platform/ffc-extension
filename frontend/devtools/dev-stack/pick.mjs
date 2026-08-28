#!/usr/bin/env node
// Interactive launcher for the dev stack. Prints the equivalent npm command before running it,
// so the task names stay learnable and this stops being needed. The decisions live here; how
// each one is carried out lives in dev.mjs and stack.mjs.
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import {
  SERVE_CONTAINER,
  SERVE_HINT,
  WORKERS,
  appIsRunning,
  repoRoot,
  serveIsRunning,
  watchIsRunning,
} from "./stack.mjs";
import { ask, choose, pad } from "./prompt.mjs";

// Resolved from this file's URL rather than repoRoot + a hard-coded path, so this keeps
// working if the dev-stack folder moves as a unit.
const DEV_SCRIPT = resolve(dirname(fileURLToPath(import.meta.url)), "dev.mjs");
// frontend/devtools/dev-stack/ -> frontend/, where package.json's start script lives.
const FRONTEND_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

// Foreground tasks that hand the terminal to something long-lived. Ctrl-C out of them reaches
// this process too, so redrawing the menu afterwards would be unreliable — exit instead.
const TAKES_OVER_TERMINAL = new Set(["serve", "shell"]);

/** Only offer what the current state allows, so no choice leads to a "not running" error. */
function menuFor({ stackUp, serverUp }) {
  const items = [];
  if (stackUp) {
    if (!serverUp) items.push({ task: "serve", summary: "start ffcops (Ctrl-C stops)" });
    items.push(
      { task: "shell", summary: "bash in the app container" },
      { task: "stop", summary: "stop the stack (containers kept)" },
    );
  } else {
    items.push({ task: "up", summary: "start app, db and test_db" });
  }
  items.push(
    { task: "rebuild", summary: "rebuild the app image and recreate" },
    { task: "rebuild:clean", summary: "rebuild with --no-cache and recreate" },
    { task: "prune", summary: "reclaim disk: dangling images + build cache" },
  );
  return items;
}

/** Runs dev.mjs directly: package.json maps each task to exactly this, and going through npm
 * would wrap a foreground `serve` or a `tail -f` in its own output. */
function runTask(task, extraArgs, env) {
  const result = spawnSync(process.execPath, [DEV_SCRIPT, task, ...extraArgs], {
    cwd: repoRoot,
    stdio: "inherit",
    env: { ...process.env, ...env },
  });
  return result.status ?? 1;
}

async function askWorkers() {
  const answer = await ask(`How many workers? (default ${WORKERS}): `);
  if (answer === "") return WORKERS;
  if (!/^\d+$/.test(answer)) {
    console.error(`\nNot a worker count: "${answer}"`);
    process.exit(1);
  }
  return answer;
}

/**
 * macOS: open Terminal.app in a fresh window running `npm start` in frontend/. Logs stay
 * visible in that window rather than tucked away in a file, which is why we prefer this over
 * a detached background process.
 */
function openWatcherInNewTerminal() {
  const script =
    `tell application "Terminal"\n` +
    `  activate\n` +
    `  do script "cd ${FRONTEND_DIR.replace(/"/g, '\\"')} && npm start"\n` +
    `end tell`;
  const result = spawnSync("osascript", ["-e", script], { stdio: "inherit" });
  if (result.status !== 0) {
    console.error(
      "\n!  Could not open a new Terminal window. Run `npm start` in frontend/ manually.",
    );
  }
}

/**
 * Serving without the host watcher means ../static is a snapshot. Offer to launch it in a new
 * Terminal window so its logs stay visible while this shell runs the foreground serve.
 */
async function ensureWatcherOrAsk() {
  if (watchIsRunning()) return;
  console.log(
    "\n!  `npm start` is not running — the app container will serve the last built bundle\n" +
      "   in ../static, so frontend changes will not appear.",
  );
  if (!/^n/i.test(await ask("Open `npm start` in a new Terminal window? [Y/n]: "))) {
    openWatcherInNewTerminal();
  }
}

async function runServe() {
  if (serveIsRunning()) {
    console.error(
      `\n!  A serve container already exists. Remove it with \`docker rm -f ${SERVE_CONTAINER}\`.`,
    );
    return "done";
  }
  await ensureWatcherOrAsk();
  const workers = await askWorkers();
  const env = workers === WORKERS ? {} : { FFC_SERVE_WORKERS: workers };
  const prefix = Object.entries(env).map(([key, value]) => `${key}=${value}`);
  console.log(`\n$ ${[...prefix, "npm", "run", "serve"].join(" ")}\n`);
  if (/^n/i.test(await ask("Run it? [Y/n]: "))) return "done";

  const status = runTask("serve", [], env);
  if (status !== 0) process.exit(status);
  return "done";
}

async function runOnce() {
  const stackUp = appIsRunning();
  // Asked of the container rather than assumed, because the server is a process inside it that
  // outlives any one of these invocations.
  const serverUp = stackUp && serveIsRunning();
  const watchUp = watchIsRunning();

  console.log(`\nStack:   ${stackUp ? "up" : "down"}`);
  console.log(`Server:  ${serverUp ? `running — ${SERVE_HINT}` : "stopped"}`);
  console.log(`Watcher: ${watchUp ? "running" : "not running"}`);

  const options = [
    ...menuFor({ stackUp, serverUp }).map(({ task, summary }) => ({
      label: `${pad(task, 14)} ${summary}`,
      value: task,
    })),
    { label: "quit", value: "quit" },
  ];

  const choice = await choose("What should this do?", options);
  if (choice === "quit") return "done";
  if (choice === "serve") return runServe();

  // rebuild:clean isn't an npm script — it's `rebuild` plus a docker flag, kept out of
  // package.json so there's one rebuild task rather than two that can drift.
  const [task, extraArgs] = choice === "rebuild:clean" ? ["rebuild", ["--no-cache"]] : [choice, []];

  console.log(`\n$ ${["npm", "run", task, ...extraArgs].join(" ")}\n`);
  if (/^n/i.test(await ask("Run it? [Y/n]: "))) return "done";

  const status = runTask(task, extraArgs, {});
  if (status !== 0) process.exit(status);

  // After `up`, offer serve inline — the caller almost always wants ffcops next, and this
  // spares them a menu redraw to pick it.
  if (task === "up" && appIsRunning() && !serveIsRunning()) {
    if (!/^n/i.test(await ask("\nStart ffcops now? [Y/n]: "))) {
      return runServe();
    }
  }

  // Anything that held the terminal has already had its say; only state-changing tasks are
  // worth redrawing the menu for.
  return TAKES_OVER_TERMINAL.has(task) ? "done" : "again";
}

while ((await runOnce()) === "again") {
  console.log("\n──────────────────────────────────────────");
}
