import { test as base } from '@playwright/test';

import * as Pages from '../pages';
import { logBrowserConsoleErrors } from '../utils/debug-logging';

/**
 * Extends the base test with custom fixtures for page objects.
 */
export const test = base.extend<{
  _browserConsoleErrorLogging: void;
  homePage: Pages.HomePage;
  header: Pages.Header;
  organizationsPage: Pages.OrganizationsPage;
  organizationDetailsPage: Pages.OrganizationDetailsPage;
  entitlementsPage: Pages.EntitlementsPage;
}>({
  _browserConsoleErrorLogging: [
    async ({ page }, use) => {
      logBrowserConsoleErrors(page);
      await use();
    },
    { auto: true },
  ],
  homePage: async ({ page }, use) => {
    await use(new Pages.HomePage(page));
  },
  header: async ({ page }, use) => {
    await use(new Pages.Header(page));
  },
  organizationsPage: async ({ page }, use) => {
    await use(new Pages.OrganizationsPage(page));
  },
  organizationDetailsPage: async ({ page }, use) => {
    await use(new Pages.OrganizationDetailsPage(page));
  },
  entitlementsPage: async ({ page }, use) => {
    await use(new Pages.EntitlementsPage(page));
  },
});

export default test;
