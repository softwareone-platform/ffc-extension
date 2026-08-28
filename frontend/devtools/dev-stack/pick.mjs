#!/usr/bin/env node
// Interactive launcher for the dev stack. Prints the equivalent npm command before running it,
// so the task names stay learnable and this stops being needed. The decisions live here; how
// each one is carried out lives in dev.mjs and stack.mjs.
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import {
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

const SERVE_TASKS = new Set(["serve", "serve:start"]);

// These hand the terminal to something long-lived (a server in the foreground, `tail -f`, a
// shell). Ctrl-C out of them reaches this process too, so redrawing the menu afterwards would
// be unreliable — exit instead of looping.
const TAKES_OVER_TERMINAL = new Set(["serve", "serve:logs", "shell", "watch:logs"]);

/**
 * Only offer what the current state allows, so no choice leads to a "not running" error. The
 * serve tasks are listed regardless of the stack: `compose run` brings up `db` via depends_on,
 * so serving does not require `up` first.
 */
function tasksFor({ stackUp, serverUp, watchUp }) {
  return [
    ...(serverUp
      ? [
          { task: "serve:logs", summary: "follow the serve container's log" },
          { task: "serve:stop", summary: "stop and remove the serve container" },
          { task: "serve:status", summary: "show the serve container" },
        ]
      : [
          { task: "serve", summary: "ffcops in a one-off container, Ctrl-C stops" },
          { task: "serve:start", summary: "the same, detached" },
        ]),
    ...(watchUp
      ? [
          { task: "watch:logs", summary: "follow the frontend watcher's log" },
          { task: "watch:stop", summary: "stop the frontend watcher" },
        ]
      : [{ task: "watch:start", summary: "run `npm start` in the background" }]),
    ...(stackUp
      ? [
          { task: "shell", summary: "bash in the app container" },
          { task: "stop", summary: "stop the stack (containers kept)" },
        ]
      : [{ task: "up", summary: "start app, db and test_db" }]),
    { task: "rebuild", summary: "rebuild the app image and recreate" },
    { task: "rebuild:clean", summary: "rebuild with --no-cache and recreate" },
    { task: "prune", summary: "reclaim disk: dangling images + build cache" },
  ];
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
    ...tasksFor({ stackUp, serverUp, watchUp }).map(({ task, summary }) => ({
      label: `${pad(task, 14)} ${summary}`,
      value: task,
    })),
    { label: "quit", value: "quit" },
  ];

  const choice = await choose("What should this do?", options);
  if (choice === "quit") return "done";

  // rebuild:clean isn't an npm script — it's `rebuild` plus a docker flag, kept out of
  // package.json so there's one rebuild task rather than two that can drift.
  const [task, extraArgs] = choice === "rebuild:clean" ? ["rebuild", ["--no-cache"]] : [choice, []];

  // Serving without the watcher means ../static is a snapshot. Offering to start it here
  // matches the flow the user actually wants: pick serve, watchers come along for the ride.
  if (SERVE_TASKS.has(task) && !watchUp) {
    console.log(
      "\n!  `npm start` is not running — the app container will serve the last built bundle\n" +
        "   in ../static, so frontend changes will not appear.",
    );
    if (!/^n/i.test(await ask("Start it in the background first? [Y/n]: "))) {
      const status = runTask("watch:start", [], {});
      if (status !== 0) process.exit(status);
    }
  }

  const workers = SERVE_TASKS.has(task) ? await askWorkers() : WORKERS;
  const env = workers === WORKERS ? {} : { FFC_SERVE_WORKERS: workers };
  const prefix = Object.entries(env).map(([key, value]) => `${key}=${value}`);
  console.log(`\n$ ${[...prefix, "npm", "run", task, ...extraArgs].join(" ")}\n`);

  if (/^n/i.test(await ask("Run it? [Y/n]: "))) return "done";

  const status = runTask(task, extraArgs, env);
  if (status !== 0) process.exit(status);
  // Anything that held the terminal has already had its say; only state-changing tasks are
  // worth redrawing the menu for.
  return TAKES_OVER_TERMINAL.has(task) ? "done" : "again";
}

while ((await runOnce()) === "again") {
  console.log("\n──────────────────────────────────────────");
}
