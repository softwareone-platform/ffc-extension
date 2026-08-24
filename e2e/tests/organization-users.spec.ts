import { expect } from '@playwright/test';

import test from '../fixtures/fixture';
import { getCurrentEnv } from '../utils/env';
import { generateRandomEmail } from '../utils/random-email-utils';

test.describe('Organization users', () => {
  test('Adds a user to an organization', async ({ organizationsPage, organizationDetailsPage }) => {
    const orgName = getCurrentEnv().softwareOneOrgName;
    const email = generateRandomEmail();
    const userName = 'Test User';

    await test.step('Open Organizations page directly', async () => {
      await organizationsPage.navigateToURL();
      await organizationsPage.waitForExtensionIframeLoading();
      await organizationsPage.waitForDataRefreshingMessageToDetach();
    });

    await test.step('Find organization via filters and open details page', async () => {
      await organizationsPage.filterOrgByName(orgName);
      await organizationsPage.organizationLink(orgName).click();
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
