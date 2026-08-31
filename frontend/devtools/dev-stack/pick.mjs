#!/usr/bin/env node
// Interactive launcher for the dev stack. Prints the equivalent npm command before running it,
// so the task names stay learnable and this stops being needed. The decisions live here; how
// each one is carried out lives in dev.mjs and stack.mjs.
//
// Layout: a main menu routes into two sub-panels — Docker (container lifecycle, image builds,
// disk reclaim) and App (ffcops workers inside the running app container). Each sub-panel has
// a `back` option and redraws its status banner on every iteration, so the current state is
// always visible without leaving the picker.
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import {
  SERVE_HINT,
  WORKERS,
  appIsRunning,
  repoRoot,
  watchIsRunning,
  workersAreRunning,
} from "./stack.mjs";
import { ask, choose, pad } from "./prompt.mjs";

// Resolved from this file's URL rather than repoRoot + a hard-coded path, so this keeps
// working if the dev-stack folder moves as a unit.
const DEV_SCRIPT = resolve(dirname(fileURLToPath(import.meta.url)), "dev.mjs");
// frontend/devtools/dev-stack/ -> frontend/, where package.json's start script lives.
const FRONTEND_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

/** Runs dev.mjs directly, matching what `npm run <task>` would do without npm's wrapping. */
function runTask(task, extraArgs, env) {
  const result = spawnSync(process.execPath, [DEV_SCRIPT, task, ...extraArgs], {
    cwd: repoRoot,
    stdio: "inherit",
    env: { ...process.env, ...env },
  });
  return result.status ?? 1;
}

function showStatus() {
  const stackUp = appIsRunning();
  const workersUp = stackUp && workersAreRunning();
  const watchUp = watchIsRunning();
  console.log(`\nStack:    ${stackUp ? "up" : "down"}`);
  console.log(`Workers:  ${workersUp ? `running — ${SERVE_HINT}` : "stopped"}`);
  console.log(`Frontend: ${watchUp ? "running (npm start)" : "stopped"}`);
  return { stackUp, workersUp, watchUp };
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
 * macOS: open Terminal.app in a fresh window running `shellCommand` from `cwd`. AppleScript's
 * `do script` always opens a new window; new *tabs* would need System Events keystrokes and
 * Accessibility permissions — too much setup fragility for a one-line convenience.
 */
function openInNewTerminal(shellCommand, cwd = FRONTEND_DIR) {
  const cd = cwd.replace(/"/g, '\\"');
  const cmd = shellCommand.replace(/"/g, '\\"');
  const script =
    `tell application "Terminal"\n` +
    `  activate\n` +
    `  do script "cd ${cd} && ${cmd}"\n` +
    `end tell`;
  const result = spawnSync("osascript", ["-e", script], { stdio: "inherit" });
  if (result.status !== 0) {
    console.error(
      `\n!  Could not open a new Terminal window. Run \`${shellCommand}\` in ${cwd} manually.`,
    );
  }
}

async function ensureWatcherOrAsk() {
  if (watchIsRunning()) return;
  console.log(
    "\n!  `npm start` is not running — the app container will serve the last built bundle\n" +
      "   in ../static, so frontend changes will not appear.",
  );
  if (!/^n/i.test(await ask("Open `npm start` in a new Terminal window? [Y/n]: "))) {
    openInNewTerminal("npm start");
  }
}

/** Interactive workers:start: watcher nudge, worker count, echo the equivalent npm command. */
async function launchWorkers() {
  await ensureWatcherOrAsk();
  const workers = await askWorkers();
  const env = workers === WORKERS ? {} : { FFC_SERVE_WORKERS: workers };
  const prefix = Object.entries(env).map(([key, value]) => `${key}=${value}`);
  console.log(`\n$ ${[...prefix, "npm", "run", "workers:start"].join(" ")}\n`);
  if (/^n/i.test(await ask("Run it? [Y/n]: "))) return;
  const status = runTask("workers:start", [], env);
  if (status !== 0) process.exit(status);
}

/** Straight-through: echo the equivalent npm command, prompt, run. Used by tasks that don't
 * need any additional interactive prompt. `rebuild:clean` is expanded to `rebuild --no-cache`
 * here so it stays out of package.json (one npm rebuild task rather than two that can drift). */
async function runPassthrough(choice) {
  const [task, extraArgs] =
    choice === "rebuild:clean" ? ["rebuild", ["--no-cache"]] : [choice, []];
  console.log(`\n$ ${["npm", "run", task, ...extraArgs].join(" ")}\n`);
  if (/^n/i.test(await ask("Run it? [Y/n]: "))) return;
  const status = runTask(task, extraArgs, {});
  if (status !== 0) process.exit(status);
}

async function runDockerPanel() {
  while (true) {
    const { stackUp } = showStatus();

    const items = [
      stackUp
        ? { task: "stop", summary: "stop the stack (containers kept)" }
        : { task: "up", summary: "start app, db and test_db" },
      { task: "rebuild", summary: "rebuild the app image and recreate" },
      { task: "rebuild:clean", summary: "rebuild with --no-cache and recreate" },
      { task: "prune", summary: "reclaim disk: dangling images + build cache" },
      { task: "shell", summary: "bash in the app container", disabled: !stackUp },
      { task: "logs", summary: "tail all services in a new Terminal window", disabled: !stackUp },
    ].filter((item) => !item.disabled);

    const choice = await choose("Docker panel", [
      ...items.map(({ task, summary }) => ({
        label: `${pad(task, 14)} ${summary}`,
        value: task,
      })),
      { label: "back", value: "back" },
    ]);

    if (choice === "back") return;
    if (choice === "logs") openInNewTerminal("npm run docker:logs");
    else await runPassthrough(choice);
    console.log("\n──────────────────────────────────────────");
  }
}

async function runAppPanel() {
  while (true) {
    const { stackUp, workersUp, watchUp } = showStatus();

    if (!stackUp) {
      console.log(
        "\n!  The app container isn't running. Start it from Docker → up before touching workers.",
      );
      // Even without the stack we can still start the host-side frontend watcher — the two
      // are independent, and there's no reason to force the user to leave the panel for it.
      const stackDownItems = [];
      if (!watchUp) {
        stackDownItems.push({
          task: "frontend",
          summary: "start `npm start` in a new Terminal window",
        });
      }
      stackDownItems.push({ task: "back", summary: "return to main menu" });
      const choice = await choose(
        "App panel",
        stackDownItems.map(({ task, summary }) => ({
          label: `${pad(task, 14)} ${summary}`,
          value: task,
        })),
      );
      if (choice === "back") return;
      if (choice === "frontend") openInNewTerminal("npm start");
      continue;
    }

    const workersItems = workersUp
      ? [
          { task: "workers:stop", summary: "stop ffcops workers (containers stay up)" },
          { task: "restart", summary: "kill + relaunch ffcops workers" },
          { task: "logs", summary: "tail ffcops output in a new Terminal window" },
        ]
      : [
          { task: "workers:start", summary: "start ffcops workers inside the app container" },
          {
            task: "start+logs",
            summary: "start workers, then tail their output in a new Terminal window",
          },
          { task: "logs", summary: "tail ffcops output in a new Terminal window" },
        ];

    // `frontend` runs on the host, not in the container, so its availability is orthogonal
    // to workers state — offer it regardless when it isn't already running.
    const items = watchUp
      ? workersItems
      : [
          ...workersItems,
          {
            task: "frontend",
            summary: "start `npm start` in a new Terminal window",
          },
        ];

    const choice = await choose("App panel", [
      ...items.map(({ task, summary }) => ({
        label: `${pad(task, 14)} ${summary}`,
        value: task,
      })),
      { label: "back", value: "back" },
    ]);

    if (choice === "back") return;
    if (choice === "workers:start") {
      await launchWorkers();
    } else if (choice === "start+logs") {
      // launchWorkers() returns after the detached exec dispatches; opening the log tail
      // right after is safe because ffcops's early boot output (uvicorn banner) is already
      // being appended to the log by the time the new Terminal window is up.
      await launchWorkers();
      openInNewTerminal("npm run workers:logs");
    } else if (choice === "workers:stop") {
      await runPassthrough("workers:stop");
    } else if (choice === "restart") {
      // Two steps rather than a new dev.mjs command: the picker already knows how to prompt
      // for worker count and watcher status via launchWorkers().
      if (runTask("workers:stop", [], {}) !== 0) process.exit(1);
      await launchWorkers();
    } else if (choice === "logs") {
      openInNewTerminal("npm run workers:logs");
    } else if (choice === "frontend") {
      openInNewTerminal("npm start");
    }
    console.log("\n──────────────────────────────────────────");
  }
}

async function runMainMenu() {
  while (true) {
    showStatus();
    const choice = await choose("Main menu", [
      { label: `${pad("docker", 10)} manage containers, images, disk`, value: "docker" },
      { label: `${pad("app", 10)} manage ffcops workers`, value: "app" },
      { label: "quit", value: "quit" },
    ]);
    if (choice === "quit") return;
    if (choice === "docker") await runDockerPanel();
    else if (choice === "app") await runAppPanel();
    console.log("\n──────────────────────────────────────────");
  }
}

await runMainMenu();
