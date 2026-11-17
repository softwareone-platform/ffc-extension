import { expect } from '@playwright/test';

import test from '../fixtures/fixture';
import type { OrganizationsResponse } from '../types/organizations-response';

test.describe('[233299] As a vendor view the organizations list', () => {
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

    /**
     * Refreshes the Default view and captures the live API response for page 1:
     * 10 rows, excluding deleted organizations, newest updated first.
     * Compares the first five UI rows with the API IDs and names in order.
     * Checks that their first-column IDs follow the FORG-####-####-#### format.
     * Checks that their displayed Client IDs follow the ACC-####-#### format.
     * Checks that their Client icons are visible and their images load successfully.
     * Requires at least five non-deleted organizations in the selected environment.
     */
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

      await organizationsPage.selectPageSize(10);
      await organizationsPage.pageInput.fill('1');
      await organizationsPage.pageInput.press('Enter');
      await expect(organizationsPage.pageInput).toHaveValue('1');
      await expect(organizationsPage.pageSizeButton).toHaveText('10');

      await organizationsPage.viewSelectorButton.click();
      await organizationsPage.toolbarDropdown.getByText('Default', { exact: true }).click();
      await expect(organizationsPage.viewSelectorButton).toHaveText('Default');

      const extensionOrigin = await organizationsPage.extensionFrame.locator('body').evaluate(() => window.location.origin);
      // Returning to a view can reuse cached data; Refresh ensures a live response for the comparison.
      const [organizationsResponse] = await Promise.all([
        organizationsPage.page.waitForResponse(response => {
          const url = new URL(response.url());
          return response.request().method() === 'GET' && url.origin === extensionOrigin && url.pathname === '/ops/v1/organizations';
        }),
        organizationsPage.grid.getByRole('button', { name: 'Refresh', exact: true }).click(),
      ]);
      expect(organizationsResponse.status()).toBe(200);
      const query = new URL(organizationsResponse.url()).searchParams;
      expect(query.has('ne(status,"deleted")'), 'Exclude deleted organizations').toBe(true);
      expect(query.has('order_by(-events.updated.at)'), 'Order by updated time descending').toBe(true);
      expect(query.get('offset')).toBe('0');
      expect(query.get('limit')).toBe('10');

      const organizations: OrganizationsResponse = await organizationsResponse.json();
      expect(organizations).toMatchObject({
        items: expect.any(Array),
        total: expect.any(Number),
        offset: 0,
        limit: 10,
      });
      expect(organizations.items.length, 'At least five organizations are required for the ordered UI comparison').toBeGreaterThanOrEqual(
        5
      );
      expect(organizations.items.length).toBeLessThanOrEqual(10);
      expect(organizations.total).toBeGreaterThanOrEqual(organizations.items.length);

      const updatedTimes = organizations.items.map(item => Date.parse(item.events.updated.at));
      for (const item of organizations.items) {
        expect(item).toMatchObject({ id: expect.any(String), name: expect.any(String) });
        expect(item.status).not.toBe('deleted');
        expect(Number.isFinite(Date.parse(item.events.updated.at)), `Valid updated timestamp for organization ${item.id}`).toBe(true);
      }
      expect(updatedTimes, 'API organizations are ordered by updated time descending').toEqual([...updatedTimes].sort((a, b) => b - a));

      await organizationsPage.waitForExtensionIframeLoading();

      await expect(organizationsPage.columnHeaders).toContainText(headings);
      await expect(organizationsPage.rows).toHaveCount(organizations.items.length);
      for (let index = 0; index < 5; index++) {
        const organization = organizations.items[index];
        const row = organizationsPage.rows.nth(index);
        const organizationCell = row.getByRole('cell').first();
        await expect(organizationCell.getByText(/^FORG-\d{4}-\d{4}-\d{4} \| /)).toBeVisible();
        const organizationLink = organizationCell.getByRole('link', { name: organization.name, exact: true });
        await expect(organizationLink).toHaveText(organization.name);
        await expect(organizationLink, `Organization ID in row ${index + 1}`).toHaveAttribute(
          'href',
          new RegExp(`/organizations/${organization.id}/general$`)
        );
        const clientCell = row.getByRole('cell').nth(headings.indexOf('Client'));
        await expect(clientCell.getByText(/^ACC-\d{4}-\d{4}$/)).toBeVisible();
        const clientIcon = clientCell.getByRole('img', { name: 'avatar', exact: true });
        await expect(clientIcon).toBeVisible();
        await expect
          .poll(
            () =>
              clientIcon.evaluate(
                icon => icon instanceof HTMLImageElement && icon.complete && icon.naturalWidth > 0 && icon.naturalHeight > 0
              ),
            { message: `Client icon in row ${index + 1} loads successfully` }
          )
          .toBe(true);
      }

      const statusChips = organizationsPage.gridTable.getByTestId('status-chip');
      await expect(statusChips.first()).toBeVisible();
      await expect(statusChips.filter({ hasText: /^Deleted$/ })).toHaveCount(0);
    });

    await test.step('Check paging', async () => {
      await organizationsPage.viewSelectorButton.click();
      await organizationsPage.toolbarDropdown.getByText('Default', { exact: true }).click();
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
