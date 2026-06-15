import { test as base } from '@playwright/test';
import { HomePage } from '../pages/home-page';
import { Header } from '../pages/header';
import { PlatformUsersPage } from '../pages/platform-users-page';
import { OrganizationsPage } from '../pages/organizations-page';
import { EntitlementsPage } from '../pages/entitlements-page';
import { OrganizationDetailsPage } from '../pages/organization-details-page';

/**
 * Extends the base test with custom fixtures for page objects.
 */
export const test = base.extend<{
  _browserConsoleErrorLogging: void;
  homePage: HomePage;
  header: Header;
  usersPage: PlatformUsersPage;
  organizationsPage: OrganizationsPage;
  organizationDetailsPage: OrganizationDetailsPage;
  entitlementsPage: EntitlementsPage;
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
    await use(new HomePage(page));
  },
  header: async ({ page }, use) => {
    await use(new Header(page));
  },
  usersPage: async ({ page }, use) => {
    await use(new PlatformUsersPage(page));
  },
  organizationsPage: async ({ page }, use) => {
    await use(new OrganizationsPage(page));
  },
  organizationDetailsPage: async ({ page }, use) => {
    await use(new OrganizationDetailsPage(page));
  },
  entitlementsPage: async ({ page }, use) => {
    await use(new EntitlementsPage(page));
  },
});

export default test;
