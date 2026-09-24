import { expect } from '@playwright/test';

import test from '../fixtures/fixture';

test.describe('Navigation', () => {
  test('Opens the Organizations tab', async ({ organizationsPage }) => {
    await test.step('Open the Organizations route', async () => {
      await organizationsPage.navigateToURL();
      await organizationsPage.waitForExtensionIframeLoading();
    });

    await test.step('Verify Organizations tab is active', async () => {
      await expect(organizationsPage.activeNavLink).toHaveText('Organizations');
    });
  });

  test('Opens the Entitlements tab', async ({ organizationsPage, entitlementsPage }) => {
    await test.step('Open the Organizations route', async () => {
      await organizationsPage.navigateToURL();
      await organizationsPage.waitForExtensionIframeLoading();
    });

    await test.step('Move to Entitlements through the extension nav', async () => {
      await entitlementsPage.openNavTab('Entitlements');
    });

    await test.step('Verify Entitlements tab is active', async () => {
      await expect(entitlementsPage.activeNavLink).toHaveText('Entitlements');
    });
  });
});
