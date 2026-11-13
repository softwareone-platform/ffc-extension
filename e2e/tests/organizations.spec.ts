import { expect } from '@playwright/test';

import test from '../fixtures/fixture';

test.describe('Organizations Grid', () => {
  test('Check Organizations views', async ({ organizationsPage }) => {
    await test.step('Check view: Active Organizations', async () => {
      await organizationsPage.navigateToURL();
      await organizationsPage.waitForExtensionIframeLoading();
      await expect(organizationsPage.activeNavLink).toHaveText('Organizations');

      await organizationsPage.viewSelectorButton.click();
      await organizationsPage.extensionFrame.getByText('Active Organizations').click();
      await organizationsPage.waitForExtensionIframeLoading();
      await expect(organizationsPage.viewSelectorButton).toHaveText('Active Organizations');

      const orgItemStatusItems = await organizationsPage.gridTable.getByTestId('status-chip');
      await expect(orgItemStatusItems.first()).toBeVisible();
      await expect(orgItemStatusItems.filter({ hasNotText: /^Active$/ })).toHaveCount(0);
    });

    await test.step('Check view: Deleted Organizations', async () => {
      await organizationsPage.viewSelectorButton.click();
      await organizationsPage.extensionFrame.getByText('Deleted Organizations').click();
      await organizationsPage.waitForExtensionIframeLoading();
      await expect(organizationsPage.viewSelectorButton).toHaveText('Deleted Organizations');

      const orgItemStatusItems = await organizationsPage.gridTable.getByTestId('status-chip');
      await expect(orgItemStatusItems.first()).toBeVisible();
      await expect(orgItemStatusItems.filter({ hasNotText: /^Deleted$/ })).toHaveCount(0);
    });

    await test.step('Check view: Default', async () => {
      const headings = [
        'Organization',
        'Currency',
        'Billing Currency',
        'Operations Additional ID',
        'Client',
        'Updated',
        'Status',
        'Actions',
      ];

      await organizationsPage.viewSelectorButton.click();
      await organizationsPage.extensionFrame.getByText('Default').click();
      await organizationsPage.waitForExtensionIframeLoading();
      await expect(organizationsPage.viewSelectorButton).toHaveText('Default');

      await expect(organizationsPage.columnHeaders).toContainText(headings);

      const statusChips = organizationsPage.gridTable.getByTestId('status-chip');
      await expect(statusChips.first()).toBeVisible();
      await expect(statusChips.filter({ hasText: /^Deleted$/ })).toHaveCount(0);
    });

    await test.step('Check paging', async () => {
      await organizationsPage.viewSelectorButton.click();
      await organizationsPage.extensionFrame.getByText('Default').click();
      await organizationsPage.waitForExtensionIframeLoading();
      await expect(organizationsPage.viewSelectorButton).toHaveText('Default');

      const orgItemStatusItems = await organizationsPage.gridTable.getByTestId('status-chip');
      await expect(orgItemStatusItems.first()).toBeVisible();
      await organizationsPage.nextPageButton.click();
      await organizationsPage.waitForExtensionIframeLoading();
      await expect(organizationsPage.gridTable.getByTestId('status-chip').first()).toBeVisible();

      var pageCount = await organizationsPage.pageCount.textContent();
      if (pageCount !== null && pageCount !== '1' && pageCount > '2') {
        await organizationsPage.pageInput.fill('3'); 
        await organizationsPage.pageInput.press('Enter');
        await expect(organizationsPage.pageInput).toHaveValue('3');
      }

      await organizationsPage.waitForExtensionIframeLoading();
      await expect(organizationsPage.gridTable.getByTestId('status-chip').first()).toBeVisible();
      await organizationsPage.selectPageSize(10);

      await expect(organizationsPage.pageSizeButton).toHaveText('10');
      expect(await organizationsPage.rows.count()).toBeLessThanOrEqual(10);
    });
  });
 
});
