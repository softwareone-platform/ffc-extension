import { test as base } from '@playwright/test';
import { HomePage } from '../pages/home-page';
import { Header } from '../pages/header';
import { UsersPage } from '../pages/users-page';
import { OrganizationsPage } from '../pages/organizations-page';
import { EntitlementsPage } from '../pages/entitlements-page';

/**
 * Extends the base test with custom fixtures for page objects.
 */
export const test = base.extend<{
  homePage: HomePage;
  header: Header;
  usersPage: UsersPage;
  organizationsPage: OrganizationsPage;
  entitlementsPage: EntitlementsPage;
}>({
  homePage: async ({ page }, use) => {
    await use(new HomePage(page));
  },
  header: async ({ page }, use) => {
    await use(new Header(page));
  },
  usersPage: async ({ page }, use) => {
    await use(new UsersPage(page));
  },
  organizationsPage: async ({ page }, use) => {
    await use(new OrganizationsPage(page));
  },
  entitlementsPage: async ({ page }, use) => {
    await use(new EntitlementsPage(page));
  },
});

export default test;
