import { defineConfig, devices } from '@playwright/test';

import TestUsers from './test-data/test-users';
// Importing env first loads the .env files before anything reads process.env.
import { TIMEOUTS } from './utils/config';
import { env } from './utils/env';

const VIEWPORT = { width: 1920, height: 1080 };

export default defineConfig({
  globalTeardown: './setup/global-teardown.ts',
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: env.isCI,
  retries: env.isCI ? 2 : 0,
  workers: env.isCI ? 1 : env.workers,
  timeout: TIMEOUTS.test,
  expect: { timeout: TIMEOUTS.expect },
  reporter: [['list'], ['json', { outputFile: 'results.json' }], ['html', { open: 'never' }]],
  use: {
    actionTimeout: TIMEOUTS.action,
    baseURL: env.baseUrl,
    headless: true,
    viewport: VIEWPORT,
    ignoreHTTPSErrors: env.ignoreHttpsErrors,
    // The app's own attribute, so getByTestId() matches what the UI renders.
    testIdAttribute: 'data-testid',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    screenshot: { mode: 'only-on-failure', fullPage: true },
  },

  projects: [
    {
      name: 'setup',
      testDir: './setup',
      testMatch: /.*\.setup\.ts/,
      use: { ...devices['Desktop Chrome'], viewport: VIEWPORT },
    },
    {
      name: 'FFC Admin Panel',
      use: { ...devices['Desktop Chrome'], viewport: VIEWPORT, storageState: TestUsers.Admin.sessionStoragePath },
      dependencies: ['setup'],
    },
  ],
});
