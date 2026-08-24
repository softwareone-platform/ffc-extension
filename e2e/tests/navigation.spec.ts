import { expect } from '@playwright/test';

import test from '../fixtures/fixture';
import TestUsers from '../test-data/test-users';

test.use({ storageState: TestUsers.Admin.sessionStoragePath });

test.beforeEach(async ({ homePage, header }) => {
  await test.step('Navigate to home page', async () => {
    await homePage.navigateToURL();
    await homePage.waitForIframeLoading();
    await header.tenantName.waitFor();
  });
});

test.describe('Navigation', () => {
  test('Opens the Users page from the navigation menu', async ({ header, usersPage }) => {
    await test.step('Open Users page from navigation menu', async () => {
      await header.navigateToUsersPage();
    });

    await test.step('Verify Users page is displayed', async () => {
      await expect(usersPage.navigationHeaderBarTitle).toHaveText('Users');
    });
  });

  test('Opens the Organizations tab', async ({ header, organizationsPage }) => {
    await test.step('Open Organizations page from navigation menu', async () => {
      await header.navigateToOrganizationsPage();
    });

    await test.step('Verify Organizations tab is active', async () => {
      await organizationsPage.waitForExtensionIframeLoading();
      await expect(organizationsPage.activeNavLink).toHaveText('Organizations');
    });
  });

  test('Opens the Entitlements tab', async ({ header, entitlementsPage }) => {
    await test.step('Open Entitlements page from navigation menu', async () => {
      await header.navigateToEntitlementsPage();
    });

    await test.step('Verify Entitlements tab is active', async () => {
      await entitlementsPage.waitForExtensionIframeLoading();
      await expect(entitlementsPage.activeNavLink).toHaveText('Entitlements');
    });
  });
});
