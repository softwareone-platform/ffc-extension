import { expect } from '@playwright/test';

import test from '../fixtures/fixture';
import { getCurrentEnv } from '../utils/env';
import { generateRandomEmail } from '../utils/random-email-utils';

test.describe('Organization users', () => {
  test('Adds a user to an organization', async ({ organizationDetailsPage }) => {
    const { softwareOneOrgId, softwareOneOrgName } = getCurrentEnv();
    const email = generateRandomEmail();
    const userName = 'Test User';

    await test.step('Open the organization users tab', async () => {
      await organizationDetailsPage.openUsersTab(softwareOneOrgId);
      await expect(organizationDetailsPage.navigationHeaderBarSubtitle).toHaveText(`Organization ${softwareOneOrgName}`);
    });

    await test.step('Add user', async () => {
      await organizationDetailsPage.addUser(email, userName);
    });

    await test.step('Verify user is added to organization', async () => {
      await organizationDetailsPage.showAllRows();
      await expect(organizationDetailsPage.tableRowByEmail(email)).toBeVisible();
    });
  });
});
