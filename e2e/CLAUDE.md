# e2e conventions

Rules for the Playwright suite. Each one exists because weakening it broke something.

## Real environments only

These are true end-to-end tests against a deployed environment. **Do not add request
interception, response stubbing or mock data.** If a test needs data, create it through
the API (`api-request/`) and clean it up in teardown.

## Environment selection

- `ENVIRONMENT` (or `LOCAL_TEST_ENV`) picks the deployment. There is **no default** —
  an unset or unknown value throws. A silent default previously meant a run aimed at
  DEV quietly executed against TEST.
- `env.config.ts` is the only place environments are declared, and it validates itself
  at import time so a malformed definition fails before the first test.
- Read config through `utils/env.ts` (`env`, `getCurrentEnv()`), never `process.env`
  directly. Use `requireEnv('defaultUserPassword')` at the point of use so a missing
  variable names itself.

## Authentication

- Login happens once, in the `setup` project (`setup/auth.setup.ts`), which writes a
  `storageState` file. Specs opt in with `test.use({ storageState: ... })`.
- Never launch a browser outside the runner — you lose traces, retries and reporting.
- A cached session is reused only when every persistent cookie is still in date
  (`User.hasValidSession`), never on the file's mere existence. Session files are keyed
  by user _and_ origin, so `portal.s1.show` and `portal.s1.today` never share one.
- Login failures must throw. Swallowing them makes every later test fail for an
  unrelated-looking reason.

## Page objects

- Hierarchy is `PlatformPage` (shared shell) → `ExtensionPage` (iframe-aware) →
  concrete page. Pass the route to `super(page, url)` so it lives with the page object.
- **Locators are public; click them from the spec.** Only add a method when it wraps a
  wait or a condition — never a one-line `click()` passthrough.
- Prefer `getByTestId` scoped to `main`, then roles, then CSS/XPath _with a comment
  saying why_.
- For optional elements use `probeVisible()`, not `try { waitFor() } catch {}` — a
  caught timeout still paints a failed step in the trace.

## Files and state

Use `utils/file.ts` for disk access. Writes are synchronous and verified because a
callback-based write resolved before the file existed, so parallel workers read an
empty session and got redirected to the login page.

## Comments

Prefer an expressive name over a comment. Comment only a non-obvious _why_ — a
constraint, a race, a workaround. Do not restate the signature; long explanations
belong in `README.md`.

## Before saying it works

```bash
npm run typecheck && npm run lint && npm run format:check
npm test            # or: npm run test:dev
```

Listing tests (`npx playwright test --list`) validates config and specs compile
without needing a live environment.
