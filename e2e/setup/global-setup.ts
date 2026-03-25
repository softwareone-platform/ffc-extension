import { FullConfig } from '@playwright/test';
import dotenv from 'dotenv';

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
}

module.exports = globalSetup;
