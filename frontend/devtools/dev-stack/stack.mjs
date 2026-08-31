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
// than a running server, and publishes 8001->8000. Workers run *inside* this container via
// `docker compose exec`, so the base file's one-off `docker compose run` model is not used.
export const COMPOSE_DEV = [
  "compose",
  "-f",
  "docker-compose.yaml",
  "-f",
  ".devcontainer/docker-compose.yml",
];

// Mirrors `runServices` in .devcontainer/devcontainer.json.
export const SERVICES = ["app", "db", "test_db"];

export const WORKERS = process.env.FFC_SERVE_WORKERS ?? "4";

// docker-compose.yaml's own app command passes this, so workers keep parity with
// `docker compose up app`. Override by passing the flag again — the last one wins.
export const DEFAULT_SERVE_ARGS = ["--ziti-load-timeout-ms", "20000"];

// `ffcops serve` registers on a ziti service (mrok.proxy / ziticorn) instead of binding a TCP
// port, so there is no localhost URL to hit — reach it through the platform.
export const SERVE_HINT = "listening on the ziti service (no local port)";

// Bracketed first letter so pgrep can't match the shell that is running it — same trick used
// to be needed inside the container for ffcops, and it applies just as well on the host.
export const WATCH_MATCH = "[n]pm-run-all --parallel watch:types watch:code";

// Pattern for finding the ffcops workers inside the app container.
export const WORKERS_MATCH = "ffcops serve";

// Where ffcops's stdout/stderr goes when workers:start detaches. `docker exec -d` discards
// its child's output by default, so we redirect inside the container to give `workers:logs`
// something to tail.
export const WORKERS_LOG = "/tmp/ffcops-workers.log";

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

/**
 * True when `ffcops serve` is executing inside the running app container. Short-circuits when
 * the container itself is down, since `docker compose exec` would fail loudly there instead of
 * reporting "no workers".
 */
export function workersAreRunning() {
  if (!appIsRunning()) return false;
  const result = composeDev(["exec", "-T", "app", "pgrep", "-f", WORKERS_MATCH], { quiet: true });
  return result.status === 0;
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
 * The `ffcops serve …` invocation that runs inside the app container. `ffcops` isn't on PATH
 * in the container's login shell — it only resolves through `uv run`, which is also the form
 * README documents. Wrapped in `bash -c` so we can redirect stdout/stderr to WORKERS_LOG;
 * `docker exec -d` discards its child's fds otherwise, and `workers:logs` would have nothing
 * to tail.
 */
export function workersExecArgs(extraArgs, { detach = true } = {}) {
  const cmd = [
    "uv",
    "run",
    "ffcops",
    "serve",
    "--server-workers",
    WORKERS,
    ...DEFAULT_SERVE_ARGS,
    ...extraArgs,
  ].join(" ");
  return [
    "exec",
    ...(detach ? ["-d"] : []),
    "app",
    "bash",
    "-c",
    `${cmd} > ${WORKERS_LOG} 2>&1`,
  ];
}
