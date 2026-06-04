import { FullConfig } from '@playwright/test';
import dotenv from 'dotenv';
import { setEnvironment } from '../utils/environment-util';
import path from 'path';
import fs from 'fs';
import TestUsers from '../test-data/test-users';
import { debugLog } from '../utils/debug-logging';

/**
 * Cleans up previous test artifacts before starting a new test run.
 * This ensures no stale traces, logs, or videos from previous runs interfere with the current run.
 */
function cleanupTestArtifacts(): void {
  const testResultsDir = path.resolve(process.cwd(), 'test-results');
  try {
    if (fs.existsSync(testResultsDir)) {
      debugLog('Cleaning up previous test artifacts...');
      // Remove directory and all contents
      fs.rmSync(testResultsDir, { recursive: true, force: true });
      debugLog('Test artifacts cleaned');
    }
  } catch (error) {
    console.error('Failed to clean up test artifacts:', error);
    // Don't throw - let setup continue even if cleanup fails
  }
}

/**
 * Global setup function for Playwright tests.
 *
 * This function is executed before the test suite begins and is used to configure
 * environment variables and log important test configuration details.
 *
 * @param {FullConfig} config - The full configuration object provided by Playwright.
 */
async function globalSetup(config: FullConfig) {
  if (!config) console.error('No config found');

  dotenv.config({
    path: '.env.local',
    override: true,
  });

  process.env.ENVIRONMENT = setEnvironment();

  // Log key environment variables for debugging purposes
  debugLog(`Tests running on ${process.env.BASE_URL}`);
  debugLog(`Ignoring HTTPS errors: ${process.env.IGNORE_HTTPS_ERRORS}`);
  debugLog(`BROWSER_ERROR_LOGGING: ${process.env.BROWSER_ERROR_LOGGING}`);
  debugLog(`DEBUG_LOG: ${process.env.DEBUG_LOG}`);
  if (process.env.BASE_URL === undefined) console.error('***BASE_URL is not set. This is required for the tests to run.');
  if (process.env.DEV === undefined || process.env.TEST === undefined || process.env.STAGING === undefined)
    console.error('***DEV, TEST, or STAGING is not set. One of these is required for the tests to run.');
  if (process.env.DEFAULT_USER_EMAIL === undefined || process.env.DEFAULT_USER_PASSWORD === undefined)
    console.warn('***DEFAULT_USER_EMAIL or DEFAULT_USER_PASSWORD is not set. This will block login for tests not using live demo.');

  // Clean up artifacts from previous run first
  cleanupTestArtifacts();

  // Log in all test users concurrently and handle any login failures
  await Promise.allSettled([
    TestUsers.Admin.login().catch(error => {
      console.error('Global Setup Login failed: ' + error);
    }),
  ]);

  debugLog('Global setup: finished');
}

// Export the global setup function as a module
module.exports = globalSetup;
