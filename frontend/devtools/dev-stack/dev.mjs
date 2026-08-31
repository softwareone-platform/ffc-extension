#!/usr/bin/env node
// Flag-driven entry point for the dev stack, so the compose incantations from README.md and
// docs/dev/devcontainer.md don't have to be retyped or remembered. `pick.mjs` is the
// interactive front end to the same tasks; the plumbing lives in stack.mjs.
import { spawnSync } from "node:child_process";
import process from "node:process";
import {
  COMPOSE_DEV,
  SERVE_HINT,
  SERVICES,
  WORKERS,
  WORKERS_LOG,
  WORKERS_MATCH,
  composeDev,
  docker,
  fail,
  requireApp,
  watchIsRunning,
  workersAreRunning,
  workersExecArgs,
} from "./stack.mjs";

export const commands = {
  up(extraArgs) {
    const result = composeDev(["up", "-d", ...SERVICES, ...extraArgs]);
    if (result.status !== 0) fail("Could not start the stack.");
    console.log("\n✓  Stack is up. Start the workers with `npm run workers:start`.");
  },

  stop(extraArgs) {
    // `stop` rather than `down` on purpose: this keeps the containers and their state so a
    // later `up` is fast, and never touches volumes.
    const result = composeDev(["stop", ...SERVICES, ...extraArgs]);
    if (result.status !== 0) fail("Could not stop the stack.");
    console.log("\n✓  Stack stopped (containers kept — use `docker compose down` to remove).");
  },

  rebuild(extraArgs) {
    // Pass --no-cache through for a clean rebuild. Note every rebuild orphans the previous
    // ~3 GB image; `npm run prune` reclaims those. --force-recreate also drops any workers
    // that were running inside the app container.
    if (docker([...COMPOSE_DEV, "build", "app", ...extraArgs]).status !== 0) {
      fail("Build failed.");
    }
    if (composeDev(["up", "-d", "--force-recreate", ...SERVICES]).status !== 0) {
      fail("Rebuilt the image but could not recreate the containers.");
    }
    console.log("\n✓  Rebuilt and restarted. Start the workers with `npm run workers:start`.");
  },

  "workers:start"(extraArgs) {
    requireApp();
    if (workersAreRunning()) {
      fail("ffcops workers are already running. Stop them with `npm run workers:stop`.");
    }
    warnIfWatcherMissing();
    console.log(`Starting ffcops with ${WORKERS} workers, ${SERVE_HINT} (detached inside app).\n`);
    // `exec -d` returns as soon as the command is dispatched into the container. The process
    // survives this shell exiting, which is what makes the picker's "stop workers" step useful.
    if (composeDev(workersExecArgs(extraArgs)).status !== 0) {
      fail("Could not start ffcops workers.");
    }
    console.log("\n✓  ffcops workers started.");
    console.log("   Logs: `npm run workers:logs`   Stop: `npm run workers:stop`");
  },

  "workers:stop"() {
    if (!workersAreRunning()) {
      console.log("No ffcops workers are running.");
      return;
    }
    // -T disables TTY allocation so this works from a non-interactive shell (e.g. CI, pick's
    // spawnSync). pkill excludes its own pid from the match set by default. Ignore pkill's
    // exit code: a race where the process already exited on its own would leave nothing to
    // signal, and the poll below is the authoritative "are they gone" check.
    composeDev(["exec", "-T", "app", "pkill", "-f", WORKERS_MATCH], { quiet: true });

    // SIGTERM is asynchronous — ffcops's uvicorn workers finish handling in-flight requests
    // before exiting, which is why pkill returned instantly but `workersAreRunning()` still
    // sees them for a few hundred ms. Poll until they're actually gone, otherwise a follow-up
    // `workers:start` refuses ("already running") against a shutting-down process tree.
    const deadline = Date.now() + 10_000;
    while (workersAreRunning()) {
      if (Date.now() >= deadline) {
        composeDev(["exec", "-T", "app", "pkill", "-9", "-f", WORKERS_MATCH], { quiet: true });
        if (workersAreRunning()) fail("ffcops workers did not exit after SIGKILL.");
        break;
      }
      // Shell sleep so we don't spin the event loop. spawnSync blocks the whole thread,
      // which is what we want here — the CLI is synchronous by design.
      spawnSync("sleep", ["0.2"]);
    }
    console.log("\n✓  ffcops workers stopped.");
  },

  shell() {
    // Deliberately the devcontainer pair and `exec`: this is for poking at the container you
    // are working in, which is what docs/dev/devcontainer.md describes.
    requireApp();
    composeDev(["exec", "app", "bash"]);
  },

  "docker:logs"() {
    // Follow every service's stdout. The app container itself runs `sleep infinity` under
    // the devcontainer overlay so its stream is quiet — most of the interesting output
    // comes from db/test_db. For workers, use `workers:logs`.
    composeDev(["logs", "-f", ...SERVICES]);
  },

  "workers:logs"() {
    requireApp();
    // `tail -F` (follow name, retry) so the tail survives ffcops rotating the log or the
    // file not existing yet. `touch` first makes the initial tail deterministic instead of
    // exiting with "No such file or directory" when workers have never been started.
    composeDev([
      "exec",
      "-T",
      "app",
      "bash",
      "-c",
      `touch ${WORKERS_LOG} && tail -n 200 -F ${WORKERS_LOG}`,
    ]);
  },

  prune() {
    // Reclaims the two things that actually grow here: the untagged image each rebuild leaves
    // behind (~3 GB apiece) and the build cache. Volumes are deliberately left alone — Docker
    // reports them as unused even when they hold database or IDE state.
    printDiskUsage("Before");
    if (docker(["image", "prune", "-f"]).status !== 0) fail("Could not prune images.");
    if (docker(["builder", "prune", "-f"]).status !== 0) fail("Could not prune the build cache.");
    printDiskUsage("After");
    console.log("\n✓  Pruned dangling images and build cache (volumes untouched).");
  },
};

/**
 * Printed on workers:start so an unwatched frontend doesn't silently serve stale bundles. Runs
 * unconditionally: the picker adds an interactive "open in new terminal?" prompt, but even a
 * bare `npm run workers:start` from a script or CI shell benefits from the warning.
 */
function warnIfWatcherMissing() {
  if (watchIsRunning()) return;
  console.error(
    "!  `npm start` is not running — the app container will serve the last built bundle\n" +
      "   in ../static. Start `npm start` in frontend/ (in another terminal) to keep the\n" +
      "   bundle fresh.\n",
  );
}

/**
 * Best effort on purpose: when the Docker disk is completely full, `system df` fails with the
 * very out-of-space error the prune is meant to fix, so it must never abort the run.
 */
function printDiskUsage(label) {
  const result = docker(["system", "df"], { quiet: true });
  if (result.status === 0) {
    console.log(`${label}:\n${result.stdout.trim()}\n`);
    return;
  }
  console.log(`${label}: unavailable (docker system df failed — usually means the disk is full)\n`);
}

const [command, ...extraArgs] = process.argv.slice(2);

if (!command || !commands[command]) {
  if (command) console.error(`Unknown command: ${command}\n`);
  console.log("Usage: npm run <command> [-- extra docker/ffcops args]\n");
  console.log("  up             start app, db and test_db");
  console.log("  stop           stop them (containers and volumes kept)");
  console.log("  rebuild        rebuild the app image and recreate the containers");
  console.log(`  workers:start  run ffcops inside the app container (${WORKERS} workers, detached)`);
  console.log("  workers:stop   kill the ffcops workers running inside the app container");
  console.log("  workers:logs   tail ffcops's redirected stdout inside the container");
  console.log("  docker:logs    tail `docker compose logs -f` for every service");
  console.log("  shell          open a bash shell in the app container");
  console.log("  prune          reclaim dangling images and build cache (keeps volumes)");
  console.log("\n`npm run pick` offers these interactively.");
  console.log("Workers default to 4; override with FFC_SERVE_WORKERS.");
  process.exit(command ? 1 : 0);
}

commands[command](extraArgs);
