import { expect } from '@playwright/test';
import TestUsers from '../test-data/test-users';
import test from '../fixtures/fixture';
import { generateRandomEmail } from '../utils/random-email-utils';

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
      await organizationsPage.waitForExtensionIframeLoading();
      await expect(organizationsPage.activeNavLink).toHaveText('Organizations');
    });
  });

  test('Example test - should navigate to FinOps for Cloud > Entitlements', async ({ header, entitlementsPage }) => {
    await test.step('Open Entitlements page from navigation menu', async () => {
      await header.navigateToEntitlementsPage();
    });

    await test.step('Verify Entitlements tab is active', async () => {
      await entitlementsPage.waitForExtensionIframeLoading();
      await expect(entitlementsPage.activeNavLink).toHaveText('Entitlements');
    });
  });

  test('Add user to organization', async ({ header, organizationsPage, organizationDetailsPage }) => {
    const orgName = 'SoftwareOne (Test Environment)';
    const email = generateRandomEmail();
    const userName = 'Test User';

    await test.step('Open Organizations page from navigation menu', async () => {
      await header.navigateToOrganizationsPage();
      await organizationsPage.waitForExtensionIframeLoading();
      await organizationsPage.waitForDataRefreshingMessageToDetach();
    });

    await test.step('Find organization via filters and open details page', async () => {
      await organizationsPage.filterOrgByName(orgName);
      await (await organizationsPage.getFirstActiveOrgLinkFromGrid()).click();
      await expect(organizationDetailsPage.navigationHeaderBarSubtitle).toHaveText(`Organization ${orgName}`);
    });

    await test.step('Click User Tab and add user', async () => {
      await organizationDetailsPage.selectTabIfNotActive(organizationDetailsPage.usersTab);
      await organizationDetailsPage.addUser(email, userName);
    });

    await test.step('Verify user is added to organization', async () => {
      await organizationDetailsPage.filterUsersByEmail(email);
      await expect(await organizationDetailsPage.getTableRowByEmail(email)).toBeVisible();
    });
  });
});
