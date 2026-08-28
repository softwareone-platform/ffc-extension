#!/usr/bin/env node
// Flag-driven entry point for the dev stack, so the compose incantations from README.md and
// docs/dev/devcontainer.md don't have to be retyped or remembered. `pick.mjs` is the
// interactive front end to the same tasks; the plumbing lives in stack.mjs.
import { spawn, spawnSync } from "node:child_process";
import { openSync, truncateSync } from "node:fs";
import { dirname, resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import {
  COMPOSE_BASE,
  COMPOSE_DEV,
  SERVE_CONTAINER,
  SERVE_HINT,
  SERVICES,
  WATCH_LOG,
  WATCH_MATCH,
  WORKERS,
  composeDev,
  docker,
  fail,
  requireApp,
  serveIsRunning,
  serveRunArgs,
  watchIsRunning,
} from "./stack.mjs";

// frontend/devtools/dev-stack/ -> frontend/, where package.json's start script lives.
const FRONTEND_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

export const commands = {
  up(extraArgs) {
    const result = composeDev(["up", "-d", ...SERVICES, ...extraArgs]);
    if (result.status !== 0) fail("Could not start the stack.");
    console.log("\n✓  Stack is up. Start the API with `npm run serve`.");
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
    // ~3 GB image; `npm run prune` reclaims those.
    if (docker([...COMPOSE_DEV, "build", "app", ...extraArgs]).status !== 0) {
      fail("Build failed.");
    }
    if (composeDev(["up", "-d", "--force-recreate", ...SERVICES]).status !== 0) {
      fail("Rebuilt the image but could not recreate the containers.");
    }
    console.log("\n✓  Rebuilt and restarted. Start the API with `npm run serve`.");
  },

  serve(extraArgs) {
    if (serveIsRunning()) {
      fail(`${SERVE_CONTAINER} already exists. Stop it with \`npm run serve:stop\`.`);
    }
    warnIfWatcherMissing();
    console.log(`Starting ffcops with ${WORKERS} workers, ${SERVE_HINT} — Ctrl-C to stop.\n`);
    // A one-off container per README, so nothing is left behind: --rm removes it on exit, and
    // compose starts `db` first via depends_on even if the stack was never brought up.
    const result = docker([...COMPOSE_BASE, ...serveRunArgs(extraArgs)]);
    process.exit(result.status ?? 1);
  },

  "serve:start"(extraArgs) {
    if (serveIsRunning()) {
      fail(`${SERVE_CONTAINER} already exists. Stop it with \`npm run serve:stop\`.`);
    }
    warnIfWatcherMissing();
    if (docker([...COMPOSE_BASE, ...serveRunArgs(extraArgs, { detach: true })]).status !== 0) {
      fail("Could not start the server.");
    }
    console.log(`\n✓  Server started in the background, ${SERVE_HINT}.`);
    console.log("   Logs: `npm run serve:logs`   Stop: `npm run serve:stop`");
  },

  "serve:stop"() {
    if (!serveIsRunning()) {
      console.log("No server is running.");
      return;
    }
    // `rm -f` rather than `stop`: the container was created with --rm, so stopping it races the
    // auto-remove and leaves nothing reliable to report on. This is deterministic.
    if (docker(["rm", "-f", SERVE_CONTAINER], { quiet: true }).status !== 0) {
      fail(`Could not remove ${SERVE_CONTAINER}.`);
    }
    console.log("\n✓  Server stopped.");
  },

  "serve:status"() {
    if (!serveIsRunning()) {
      console.log("Server: stopped");
      return;
    }
    console.log(`Server: running, ${SERVE_HINT}`);
    docker([
      "ps",
      "-a",
      "--filter",
      `name=^${SERVE_CONTAINER}$`,
      "--format",
      "table {{.Names}}\t{{.Status}}\t{{.Command}}",
    ]);
  },

  "serve:logs"(extraArgs) {
    if (!serveIsRunning()) {
      fail("No server is running. Start one with `npm run serve:start`.");
    }
    const follow = extraArgs.includes("--no-follow") ? [] : ["-f"];
    docker(["logs", ...follow, "--tail", "200", SERVE_CONTAINER]);
  },

  shell() {
    // Deliberately the devcontainer pair and `exec`: this is for poking at the container you
    // are working in, which is what docs/dev/devcontainer.md describes.
    requireApp();
    composeDev(["exec", "app", "bash"]);
  },

  "watch:start"() {
    // Detached from the picker: writes to ../static that the app container reads, so it needs
    // to keep running while the picker moves on to other tasks. `npm start` (npm-run-all)
    // supervises tsc --watch and esbuild --watch in parallel.
    if (watchIsRunning()) {
      fail("The watcher is already running. Stop it with `npm run watch:stop`.");
    }
    const log = openTruncatedLog(WATCH_LOG);
    // `detached: true` also makes the child its own process-group leader, so watch:stop can
    // signal the whole tree (npm-run-all + tsc + esbuild) instead of just the outermost npm,
    // which used to orphan the two watchers.
    const child = spawn("npm", ["start"], {
      cwd: FRONTEND_DIR,
      stdio: ["ignore", log, log],
      detached: true,
    });
    child.unref();
    console.log(`\n✓  Started \`npm start\` (pid ${child.pid}). Logs: \`npm run watch:logs\``);
  },

  "watch:stop"() {
    if (!watchIsRunning()) {
      console.log("Watcher: not running.");
      return;
    }
    // npm-run-all + tsc + esbuild share a process group (the outer `npm start` created it via
    // detached: true). Signal the group rather than the parent pid, so all three go down.
    // `kill -0` on the pgid asks "does this group still exist" without disturbing it.
    const match = spawnSync("pgrep", ["-f", WATCH_MATCH], { encoding: "utf8" });
    const pid = (match.stdout ?? "").split("\n")[0];
    if (!pid) fail("Could not locate the watcher process.");
    const pgid = spawnSync("ps", ["-o", "pgid=", "-p", pid], { encoding: "utf8" })
      .stdout.trim();
    if (!pgid) fail("Could not read the watcher's process group.");
    if (spawnSync("kill", ["-TERM", `-${pgid}`]).status !== 0) {
      fail("Found the watcher but could not stop its process group.");
    }
    console.log("\n✓  Watcher stopped.");
  },

  "watch:status"() {
    if (!watchIsRunning()) {
      console.log("Watcher: not running.");
      return;
    }
    console.log("Watcher: running");
    spawnSync("pgrep", ["-af", WATCH_MATCH], { stdio: "inherit" });
  },

  "watch:logs"(extraArgs) {
    const follow = extraArgs.includes("--no-follow") ? [] : ["-f"];
    spawnSync("sh", ["-c", `touch ${WATCH_LOG}`]);
    spawnSync("tail", [...follow, "-n", "200", WATCH_LOG], { stdio: "inherit" });
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
 * Printed on serve so an unwatched frontend doesn't silently serve stale bundles. This runs
 * unconditionally: the picker adds an interactive "start it?" prompt, but even a bare
 * `npm run serve` from a script or CI shell benefits from the warning.
 */
function warnIfWatcherMissing() {
  if (watchIsRunning()) return;
  console.error(
    "!  `npm start` is not running — the app container will serve the last built bundle\n" +
      "   in ../static. Start it with `npm run watch:start` (or `npm start` in another\n" +
      "   terminal) to keep the bundle fresh.\n",
  );
}

/** Truncate and reopen: keeps a single log file per session rather than an ever-growing one. */
function openTruncatedLog(path) {
  // openSync(path, "w") would suffice for creation, but truncateSync + append keeps the file
  // descriptor semantics identical whether the log existed or not.
  const fd = openSync(path, "a");
  truncateSync(path, 0);
  return fd;
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
  console.log(`  serve          ffcops in a one-off container (${WORKERS} workers, Ctrl-C stops)`);
  console.log("  serve:start    the same, detached");
  console.log("  serve:stop     remove the serve container");
  console.log("  serve:status   show whether it's running");
  console.log("  serve:logs     tail the serve container's log");
  console.log("  shell          open a bash shell in the app container");
  console.log("  watch:start    run `npm start` (tsc + esbuild watchers) in the background");
  console.log("  watch:stop     stop the background watcher");
  console.log("  watch:status   show whether it's running");
  console.log("  watch:logs     tail the watcher's log");
  console.log("  prune          reclaim dangling images and build cache (keeps volumes)");
  console.log("\n`npm run pick` offers these interactively.");
  console.log("Workers default to 4; override with FFC_SERVE_WORKERS.");
  process.exit(command ? 1 : 0);
}

commands[command](extraArgs);
