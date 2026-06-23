import { FullConfig } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import TestUsers from '../test-data/test-users';
import { debugLog, errorLog } from '../utils/debug-logging';

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


  // Log key environment variables for debugging purposes
  debugLog(`Ignoring HTTPS errors: ${process.env.IGNORE_HTTPS_ERRORS}`);
  debugLog(`BROWSER_ERROR_LOGGING: ${process.env.BROWSER_ERROR_LOGGING}`);
  debugLog(`DEBUG_LOG: ${process.env.DEBUG_LOG}`);

  // Clean up artifacts from previous run first
  cleanupTestArtifacts();

  // Log in all test users concurrently and handle any login failures
  await Promise.allSettled([
    TestUsers.Admin.login().catch(error => {
      errorLog('Global Setup Login failed: ' + error);
    }),
  ]);
  debugLog('Global setup: finished');
}

// Export the global setup function as a module
module.exports = globalSetup;
