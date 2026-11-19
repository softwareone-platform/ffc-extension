---
name: writing-playwright-tests
description: Conventions for writing and modifying Playwright E2E tests in e2e/ — specs, page objects, fixtures, API requests, and test users. Use whenever creating or editing a *.spec.ts under e2e/tests/, a page object under e2e/pages/, the fixture under e2e/fixtures/, or an API client under e2e/api-request/.
---

# Writing Playwright tests in ffc-extension

> **Draft:** This skill is a starting point adapted from the QA repo (`swo-e2e-uitest`). Its rules are not yet verified against this repo. Where a rule conflicts with [e2e/CLAUDE.md](../../../e2e/CLAUDE.md) or the existing specs, the repo wins. Verify each rule before relying on it.

The `e2e/` suite runs true end-to-end tests against a deployed environment. Match the existing patterns rather than inventing new ones. Read [e2e/CLAUDE.md](../../../e2e/CLAUDE.md) first; it holds the rules these conventions depend on.

**The most reliable rule: open the nearest existing spec / page object in the same area and mirror it.** Good exemplars:

- Spec: [e2e/tests/organizations.spec.ts](../../../e2e/tests/organizations.spec.ts)
- Page object: [e2e/pages/organizations-page.ts](../../../e2e/pages/organizations-page.ts)
- Base page objects: [e2e/pages/extension-page.ts](../../../e2e/pages/extension-page.ts), [e2e/pages/platform-page.ts](../../../e2e/pages/platform-page.ts)
- Fixture: [e2e/fixtures/fixture.ts](../../../e2e/fixtures/fixture.ts)

## Project layout — where things go

- `e2e/tests/<name>.spec.ts` — specs (flat folder; name files after the feature)
- `e2e/pages/` — page objects (`ExtensionPage` for pages inside the extension iframe, `PlatformPage` for the shared shell); export new ones from `pages/index.ts`
- `e2e/fixtures/fixture.ts` — the single shared fixture file that exposes page objects, API clients, and users
- `e2e/api-request/` — API clients (`FfcClientRequest`), used for setup and teardown, not as the thing under test
- `e2e/test-data/test-users.ts` — test users
- `e2e/types/` — response and enum types for API payloads
- `e2e/utils/` — `env.ts` (`env`, `getCurrentEnv()`, `requireEnv()`), `extension-root.ts` (`extensionRoute()`), `file.ts`, `format.ts`, `teardown-utils.ts`, `user.ts`
- `e2e/setup/auth.setup.ts` — login and session storage; `e2e/env.config.ts` — environment declarations

## Specs

- Import `test` from the fixture, not from `@playwright/test`. Import `expect` from `@playwright/test`:
  ```ts
  import { expect } from '@playwright/test';

  import test from '../fixtures/fixture';
  ```
- Title the top-level `test.describe` with the test case ID and a description: `test.describe('[233299] As a vendor view the organizations list', ...)`.
- Structure the body with `await test.step('...', async () => { ... })`, one step per logical phase.
- Long flows: `test.slow()` or `test.setTimeout(...)`. **Never commit `test.only`.**
- Keep assertions (`expect`) in the spec, never in page objects.
- Use the `LARGE_DATA_TIMEOUT` / `TIMEOUTS` constants from [e2e/utils/config.ts](../../../e2e/utils/config.ts) rather than new magic numbers.

## Page objects

- Hierarchy: `PlatformPage` (shared shell) → `ExtensionPage` (iframe-aware) → concrete page. Pass the route to `super(page, url)` so it lives with the page object, and build it with `extensionRoute('<route>')`:
  ```ts
  export class OrganizationsPage extends ExtensionPage {
    constructor(page: Page) {
      super(page, extensionRoute('organizations'));
    }
  }
  ```
- Never reconstruct `/extensions/<id>/<plug>/-/...` by hand. It drops the `?account=` param the shell adds and hardcodes a plug id that `meta.yaml` templates.
- Declare locators as `readonly` and initialize them in the constructor.
- **Locators are public; click them from the spec.** Only add a method when it wraps a wait or a condition. Never add a one-line `click()` passthrough.
- Locator priority: prefer `getByTestId` scoped to `main`, then roles, then text/labels. Use CSS/XPath only with a comment saying why.
- Wait for the extension iframe with `waitForExtensionIframeLoading()` rather than ad hoc sleeps.
- For optional elements use `probeVisible()` (inherited from `PlatformPage`), not `try { waitFor() } catch {}`. A caught timeout still paints a failed step in the trace.
- **No `expect` / assertions in page objects.**

## Fixtures

- Add new page objects, API clients, and users to [e2e/fixtures/fixture.ts](../../../e2e/fixtures/fixture.ts) by extending the `base.extend<...>` type and providers. Keep the fixture as the only import path for specs.
- Authenticate through the setup project: specs opt in with `test.use({ storageState: ... })`. Sessions are written by `e2e/setup/auth.setup.ts`. Never launch a browser outside the Playwright runner.
- Seed and clean up data through `e2e/api-request/` clients in setup and teardown. Restore any shared data you change.

## Environment and test data

- **Real environments only.** Do not add request interception, response stubbing, or mock data. If a test needs data, create it through the API and clean it up in teardown.
- `ENVIRONMENT` (or `LOCAL_TEST_ENV`) picks the deployment. There is no default, and an unknown value throws.
- Read config through `env` / `getCurrentEnv()` in `e2e/utils/env.ts`, never `process.env` directly. Use `requireEnv('<key>')` at the point of use so a missing variable names itself.
- **Never hardcode IDs or values in specs.** Add them to `env.config.ts` or the test-data modules, and derive values from the system under test where possible.
- A cached session is reused only when every persistent cookie is still in date (`User.hasValidSession`). Session files are keyed by user and origin.
- Login failures must throw. Swallowing them makes later tests fail for an unrelated-looking reason.

## Waiting & robustness

- Prefer **web-first assertions**, which auto-wait and retry: `await expect(locator).toHaveText(...)`, `.toBeVisible()`, `.toHaveCount(n)`. Never unwrap them into a synchronous check like `expect(await locator.isVisible()).toBe(true)`, which does not wait and is flaky.
- **No `page.waitForTimeout`.** Synchronize on state, not on sleeps.
- Use regexes for case-insensitive text, e.g. `toHaveText(/active/i)`.
- After an action that reloads a grid or page, wait for the settle signal (a loading indicator hides, a status flips) **before** reading rows.
- `click()` already auto-waits. Do not precede it with a redundant `waitFor({ state: 'visible' })`.
- Do not add low-level timeouts (`use.actionTimeout`, or `{ timeout }` on actions as a crutch). Rely on auto-waiting and the per-test timeout.

## Files and state

- Use `e2e/utils/file.ts` for disk access. Its writes are synchronous and verified, because a callback-based write resolved before the file existed and parallel workers read an empty session.

## Comments

- Prefer an expressive name over a comment. Comment only a non-obvious *why*: a constraint, a race, a workaround. Do not restate signatures. Longer explanations belong in `e2e/README.md`.

## Running and verifying

Run these from `e2e/` before saying the work is done:

```bash
npm run typecheck && npm run lint && npm run format:check
npm test            # or: npm run test:dev
npx playwright test --list   # validates config and that specs compile, without a live environment
```

## Anti-patterns — don't

- `expect`/assertions inside page objects
- `page.waitForTimeout` sleeps
- global or crutch timeouts to paper over flakiness
- request interception, stubbing, or mock data
- reading `process.env` directly instead of `env` / `requireEnv`
- hardcoding IDs in specs instead of config or test data
- `try { waitFor() } catch {}` for optional elements (use `probeVisible()`)
- one-line `click()` passthrough methods on page objects
- mutating shared data without restoring it
- committing `test.only`
