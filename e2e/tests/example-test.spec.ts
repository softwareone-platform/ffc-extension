import { expect } from '@playwright/test';
import TestUsers from '../test-data/test-users';
import test from '../fixtures/fixture';

test.describe('Example test suite', () => {
  test.use({ storageState: TestUsers.Admin.sessionStoragePath });

  test.beforeEach(async ({ homePage, header }) => {
    await test.step('Navigate to home page', async () => {
      await homePage.navigateToURL();
      await homePage.waitForIframeLoading();
      await header.tenantName.waitFor();
    });
  });

  test('Example test - should log in successfully', async ({ header, usersPage }) => {
    await test.step('Open Users page from navigation menu', async () => {
      await header.navigateToUsersPage();
    });

    await test.step('Verify Users page is displayed', async () => {
      await expect(usersPage.navigationHeaderBarTitle).toHaveText('Users');
    });
  });

  test('Example test - should navigate to FinOps for Cloud > Organizations', async ({ header, organizationsPage }) => {
    await test.step('Open Organizations page from navigation menu', async () => {
      await header.navigateToOrganizationsPage();
    });

    await test.step('Verify Organizations tab is active', async () => {
      await expect(organizationsPage.activeNavLink).toHaveText('Organizations');
    });
  });

  test('Example test - should navigate to FinOps for Cloud > Entitlements', async ({ header, entitlementsPage }) => {
    await test.step('Open Entitlements page from navigation menu', async () => {
      await header.navigateToEntitlementsPage();
    });

    await test.step('Verify Entitlements tab is active', async () => {
      await expect(entitlementsPage.activeNavLink).toHaveText('Entitlements');
    });
  });
});
