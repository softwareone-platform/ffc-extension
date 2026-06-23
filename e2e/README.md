# E2E Tests (Playwright)

This folder contains Playwright end-to-end tests for the extension UI.

## Local Execution

### 1) Install dependencies

From the `e2e` folder:

```powershell
npm install
npx playwright install chromium
```

### 2) Configure environment files

`e2e/.env.local` is optional. Use it when running from an IDE Playwright test runner and you want a default `LOCAL_TEST_ENV` without passing it every time.

If you do not use `e2e/.env.local`, pass `LOCAL_TEST_ENV` on the command line or use the npm scripts.

When `LOCAL_TEST_ENV` is set, the test runner loads env files in this order:

1. `e2e/.env.local`
2. `e2e/.env.<LOCAL_TEST_ENV>` (for example `e2e/.env.TEST` or `e2e/.env.DEV`)

`LOCAL_TEST_ENV` can come from `.env.local`, the command line, or npm scripts.

#### Optional: `e2e/.env.local` (recommended for IDE runs)

```dotenv
LOCAL_TEST_ENV=TEST
```

Use `TEST` or `DEV` based on which env file you want to load.

If you prefer command line execution, set the variable inline instead:

```powershell
$env:LOCAL_TEST_ENV='TEST'; npx playwright test
$env:LOCAL_TEST_ENV='DEV'; npx playwright test
```

#### Required: `e2e/.env.TEST` (if `LOCAL_TEST_ENV=TEST`)

```dotenv
ENVIRONMENT=TEST
DEFAULT_USER_PASSWORD=<password>
IGNORE_HTTPS_ERRORS=true
BROWSER_ERROR_LOGGING=false
DEBUG_LOG=true
CLEAN_UP=true
```

#### Required: `e2e/.env.DEV` (if `LOCAL_TEST_ENV=DEV`)

```dotenv
ENVIRONMENT=DEV
DEFAULT_USER_PASSWORD=<password>
IGNORE_HTTPS_ERRORS=true
BROWSER_ERROR_LOGGING=false
DEBUG_LOG=true
CLEAN_UP=true
```

## Run tests

From `e2e`:

```powershell
npm run playwright:test
```

Run against DEV:

```powershell
npm run playwright:test:dev
```

Run a single spec:

```powershell
npx playwright test tests/example-test.spec.ts
```

Run in debug mode:

```powershell
npm run playwright:debug
```

Show latest report:

```powershell
npm run playwright:show-report
```

## Notes

- `DEFAULT_USER_PASSWORD` is required for login and teardown API token generation.
- `CLEAN_UP=true` enables global teardown cleanup. Set `false` to keep created test data for debugging.
- If `LOCAL_TEST_ENV` points to a missing file (for example `.env.STAGING`), test startup fails.

