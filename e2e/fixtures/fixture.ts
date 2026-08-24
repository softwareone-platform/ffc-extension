import { test as base } from '@playwright/test';

import * as Pages from '../pages';

/**
 * Extends the base test with custom fixtures for page objects.
 */
export const test = base.extend<{
  _browserConsoleErrorLogging: void;
  homePage: Pages.HomePage;
  header: Pages.Header;
  usersPage: Pages.PlatformUsersPage;
  organizationsPage: Pages.OrganizationsPage;
  organizationDetailsPage: Pages.OrganizationDetailsPage;
  entitlementsPage: Pages.EntitlementsPage;
}>({
  _browserConsoleErrorLogging: [
    async ({ page }, use) => {
      if (process.env.BROWSER_ERROR_LOGGING === 'true') {
        page.on('console', msg => {
          if (msg.type() === 'error') {
            console.error(`[Browser Console Error] ${msg.text()}`);
          }
        });
      }
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
  usersPage: async ({ page }, use) => {
    await use(new Pages.PlatformUsersPage(page));
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
