# E2E Tests (Playwright)

Playwright end-to-end tests for the FFC Admin Panel. These run against a **real
deployed environment** — see [`CLAUDE.md`](./CLAUDE.md) for the conventions.

## Local Execution

### 1) Install dependencies

From the `e2e` folder:

```powershell
npm install
npx playwright install chromium
```

### 2) Choose an environment

`ENVIRONMENT` selects the deployment and is **required** — there is no default, so a
missing or misspelled value fails immediately rather than silently running against
TEST. Valid values come from `env.config.ts`: `TEST`, `DEV`.

The npm scripts set it for you:

| Command            | Environment |
| ------------------ | ----------- |
| `npm test`         | TEST        |
| `npm run test:dev` | DEV         |

Or inline:

```powershell
$env:ENVIRONMENT='TEST'; npx playwright test
```

### 3) Configure secrets

Put per-machine values in `e2e/.env.local` (git-ignored):

```dotenv
DEFAULT_USER_PASSWORD=<password>
IGNORE_HTTPS_ERRORS=true
BROWSER_ERROR_LOGGING=false
DEBUG_LOG=true
CLEAN_UP=true
```

Optionally, `LOCAL_TEST_ENV=<name>` additionally loads `e2e/.env.<name>` (for example
`.env.TEST`) after `.env.local`, and doubles as the `ENVIRONMENT` value when
`ENVIRONMENT` is not set. Pointing it at a missing file fails at startup.

## Run tests

```powershell
npm test                 # TEST
npm run test:dev         # DEV
npm run test:ui          # Playwright UI mode
npm run test:headed      # headed, single worker
npm run test:debug       # inspector
npm run report           # open the last HTML report
```

Run a single spec:

```powershell
npm test -- tests/navigation.spec.ts
```

List tests without running them (validates config and specs compile — no live
environment needed):

```powershell
npx playwright test --list
```

## Layout

| Path                       | Contents                                                   |
| -------------------------- | ---------------------------------------------------------- |
| `env.config.ts`            | Environment registry, validated at import                  |
| `utils/env.ts`             | `.env` loading, typed config, `requireEnv()`               |
| `setup/auth.setup.ts`      | `setup` project: logs in once, saves `storageState`        |
| `setup/global-teardown.ts` | Deletes test data when `CLEAN_UP=true`                     |
| `pages/`                   | Page objects (`PlatformPage` → `ExtensionPage` → concrete) |
| `fixtures/fixture.ts`      | Page-object fixtures                                       |
| `tests/`                   | Specs, one area per file                                   |

## Authentication

The `setup` project logs in once and writes a session to
`.cache/<USER>_<ENVIRONMENT>_SESSION.json`; specs opt in with
`test.use({ storageState: ... })`. A cached session is reused only after it's proven to
still authenticate, and it's scoped per environment so it is never reused across
deployments. Delete the file to force a fresh login.

## Notes

- `DEFAULT_USER_PASSWORD` is required for login and for teardown API token generation.
- `CLEAN_UP=true` enables global teardown cleanup. Set `false` to keep created test
  data for debugging.
