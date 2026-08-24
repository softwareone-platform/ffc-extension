import { expect } from '@playwright/test';

import test from '../fixtures/fixture';
import { openPortalAndWaitForShell } from '../utils/test-steps';

test.beforeEach(async ({ homePage, header }) => {
  await openPortalAndWaitForShell(homePage, header);
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
    await test.step('Open the FinOps for Cloud extension', async () => {
      await header.openFinOpsForCloud();
      await organizationsPage.waitForExtensionIframeLoading();
      await organizationsPage.openNavTab('Organizations');
    });

    await test.step('Verify Organizations tab is active', async () => {
      await expect(organizationsPage.activeNavLink).toHaveText('Organizations');
    });
  });

  test('Opens the Entitlements tab', async ({ header, entitlementsPage }) => {
    await test.step('Open the FinOps for Cloud extension', async () => {
      await header.openFinOpsForCloud();
      await entitlementsPage.waitForExtensionIframeLoading();
      await entitlementsPage.openNavTab('Entitlements');
    });

    await test.step('Verify Entitlements tab is active', async () => {
      await expect(entitlementsPage.activeNavLink).toHaveText('Entitlements');
    });
  });
});
