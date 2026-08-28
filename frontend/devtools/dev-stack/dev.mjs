#!/usr/bin/env node
// Flag-driven entry point for the dev stack, so the compose incantations from README.md and
// docs/dev/devcontainer.md don't have to be retyped or remembered. `pick.mjs` is the
// interactive front end to the same tasks; the plumbing lives in stack.mjs.
import process from "node:process";
import {
  COMPOSE_BASE,
  COMPOSE_DEV,
  SERVE_CONTAINER,
  SERVE_HINT,
  SERVICES,
  WORKERS,
  composeDev,
  docker,
  fail,
  requireApp,
  serveIsRunning,
  serveRunArgs,
  watchIsRunning,
} from "./stack.mjs";

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
      fail(
        `${SERVE_CONTAINER} already exists. Remove it with \`docker rm -f ${SERVE_CONTAINER}\`.`,
      );
    }
    warnIfWatcherMissing();
    console.log(`Starting ffcops with ${WORKERS} workers, ${SERVE_HINT} — Ctrl-C to stop.\n`);
    // A one-off container per README, so nothing is left behind: --rm removes it on exit, and
    // compose starts `db` first via depends_on even if the stack was never brought up.
    const result = docker([...COMPOSE_BASE, ...serveRunArgs(extraArgs)]);
    process.exit(result.status ?? 1);
  },

  shell() {
    // Deliberately the devcontainer pair and `exec`: this is for poking at the container you
    // are working in, which is what docs/dev/devcontainer.md describes.
    requireApp();
    composeDev(["exec", "app", "bash"]);
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
 * unconditionally: the picker adds an interactive "open in new terminal?" prompt, but even a
 * bare `npm run serve` from a script or CI shell benefits from the warning.
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
  console.log(`  serve          ffcops in a one-off container (${WORKERS} workers, Ctrl-C stops)`);
  console.log("  shell          open a bash shell in the app container");
  console.log("  prune          reclaim dangling images and build cache (keeps volumes)");
  console.log("\n`npm run pick` offers these interactively.");
  console.log("Workers default to 4; override with FFC_SERVE_WORKERS.");
  process.exit(command ? 1 : 0);
}

commands[command](extraArgs);
