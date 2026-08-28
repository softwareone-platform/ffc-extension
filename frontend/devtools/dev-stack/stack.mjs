// Docker/compose plumbing for the dev stack. Split out so the flag-driven CLI (./dev.mjs) and
// the interactive picker (./pick.mjs) inspect and drive the stack through the same code.
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

// Compose is always run from the repo root, so the relative -f paths resolve regardless of
// where the npm script or the picker was invoked from.
// frontend/devtools/dev-stack/ -> repo root; the docker-compose files live there.
export const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");

// Stack lifecycle uses the devcontainer pair, matching docs/dev/devcontainer.md: the overlay
// replaces the app command with `sleep infinity` so the container is a place to work in rather
// than a running server, and publishes 8001->8000.
export const COMPOSE_DEV = [
  "compose",
  "-f",
  "docker-compose.yaml",
  "-f",
  ".devcontainer/docker-compose.yml",
];

// Serving uses the base file alone, which is the form README documents:
//   docker compose run --rm --service-ports app uv run ffcops serve --server-workers 4
// Keeping the overlay out matters: it publishes 8001, and --service-ports would then collide
// with the already-running app container over that host port.
export const COMPOSE_BASE = ["compose", "-f", "docker-compose.yaml"];

// Mirrors `runServices` in .devcontainer/devcontainer.json.
export const SERVICES = ["app", "db", "test_db"];

export const WORKERS = process.env.FFC_SERVE_WORKERS ?? "4";

// docker-compose.yaml's own app command passes this, so serve keeps parity with
// `docker compose up app`. Override by passing the flag again — the last one wins.
export const DEFAULT_SERVE_ARGS = ["--ziti-load-timeout-ms", "20000"];

// A fixed name is what makes a one-off `compose run` container addressable afterwards, so
// stop/status/logs are plain docker operations instead of hunting processes inside a container.
export const SERVE_CONTAINER = "ffc-extension-serve";

// `ffcops serve` registers on a ziti service (mrok.proxy / ziticorn) instead of binding a TCP
// port, so there is no localhost URL to hit — reach it through the platform.
export const SERVE_HINT = "listening on the ziti service (no local port)";

// Bracketed first letter so pgrep can't match the shell that is running it — same trick used
// to be needed inside the container for ffcops, and it applies just as well on the host.
export const WATCH_MATCH = "[n]pm-run-all --parallel watch:types watch:code";
export const WATCH_LOG = "/tmp/ffc-frontend-watch.log";

export function docker(args, { quiet = false } = {}) {
  return spawnSync("docker", args, {
    cwd: repoRoot,
    stdio: quiet ? ["ignore", "pipe", "pipe"] : "inherit",
    encoding: "utf8",
  });
}

export function composeDev(args, options) {
  return docker([...COMPOSE_DEV, ...args], options);
}

export function fail(message) {
  console.error(`\n!  ${message}`);
  process.exit(1);
}

export function appIsRunning() {
  const result = composeDev(["ps", "--status", "running", "--services"], { quiet: true });
  return (result.stdout ?? "").split("\n").includes("app");
}

/** True when the one-off serve container exists, running or still shutting down. */
export function serveIsRunning() {
  const result = docker(
    ["ps", "-a", "--filter", `name=^${SERVE_CONTAINER}$`, "--format", "{{.Names}}"],
    { quiet: true },
  );
  return (result.stdout ?? "").trim() === SERVE_CONTAINER;
}

/**
 * True when `npm start` (the parallel type + code watcher) is running on the host. Serving
 * without it means the container is reading a stale bundle from ../static.
 */
export function watchIsRunning() {
  const result = spawnSync("pgrep", ["-f", WATCH_MATCH], {
    stdio: ["ignore", "pipe", "pipe"],
    encoding: "utf8",
  });
  return result.status === 0;
}

export function requireApp() {
  if (!appIsRunning()) {
    fail("The app container isn't running. Start it with `npm run up` first.");
  }
}

/**
 * `ffcops` isn't on PATH in the container's login shell — it only resolves through `uv run`,
 * which is also the form README documents.
 */
export function serveArgs(extraArgs) {
  return [
    "uv",
    "run",
    "ffcops",
    "serve",
    "--server-workers",
    WORKERS,
    ...DEFAULT_SERVE_ARGS,
    ...extraArgs,
  ];
}

/** The documented `run` invocation, shared by the foreground and detached variants. */
export function serveRunArgs(extraArgs, { detach = false } = {}) {
  return [
    "run",
    ...(detach ? ["-d"] : []),
    "--rm",
    "--service-ports",
    "--name",
    SERVE_CONTAINER,
    "app",
    ...serveArgs(extraArgs),
  ];
}
