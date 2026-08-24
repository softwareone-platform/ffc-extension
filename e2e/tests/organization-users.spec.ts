import { expect } from '@playwright/test';

import test from '../fixtures/fixture';
import { generateRandomEmail } from '../utils/random-email-utils';

test.beforeEach(async ({ homePage, header }) => {
  await test.step('Navigate to home page', async () => {
    await homePage.navigateToURL();
    await homePage.waitForIframeLoading();
    await header.tenantName.waitFor();
  });
});

test.describe('Organization users', () => {
  test('Adds a user to an organization', async ({ header, organizationsPage, organizationDetailsPage }) => {
    const orgName = 'SoftwareOne (Test Environment)';
    const email = generateRandomEmail();
    const userName = 'Test User';

    await test.step('Open Organizations page from navigation menu', async () => {
      await header.openFinOpsForCloud();
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
