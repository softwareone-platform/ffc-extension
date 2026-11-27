import { expect } from '@playwright/test';

import test from '~fixtures/fixture';
import type { OrganizationsPage } from '~pages/organizations-page';
import type { OrganizationsResponse } from '~types/organizations-response';

const PAGE_SIZE = 5;

/** The API error dialog can only be judged once loading has settled; before that it is hidden. */
async function expectGridLoadedWithoutError(organizationsPage: OrganizationsPage): Promise<void> {
  await organizationsPage.waitForGridData();
  await expect(organizationsPage.apiErrorDialog).toBeHidden();
}

/** Reads the total from the pager range, e.g. "6-10 of 76 rows" → 76. */
function totalRowsFromRange(range: string): number {
  return Number(/of (\d+) rows$/.exec(range)?.[1] ?? 0);
}

/** The pager range expected on a page, e.g. for page 2 from 76 rows → "6-10 of 76 rows". */
function rangeText(page: number, totalRows: number): string {
  const first = (page - 1) * PAGE_SIZE + 1;
  const last = Math.min(page * PAGE_SIZE, totalRows);
  return `${first}-${last} of ${totalRows} rows`;
}

test.describe('[233299] As a vendor view the organizations list', () => {
  test.beforeEach(async ({ organizationsPage }) => {
    await organizationsPage.navigateToURL();
    await organizationsPage.waitForExtensionIframeLoading();
  });

  test('Check Organizations list is not empty', async ({ organizationsPage }) => {
    await expectGridLoadedWithoutError(organizationsPage);
    expect(await organizationsPage.hasGridData(), 'Organizations grid has rows').toBe(true);
    await expect(organizationsPage.gridDataRows.first().getByRole('link').first()).toHaveAttribute(
      'href',
      /\/organizations\/FORG-\d{4}-\d{4}-\d{4}\/general$/
    );
    await expect(organizationsPage.grid.getByText(/^\d+-\d+ of [1-9]\d* rows$/)).toBeVisible();
  });

  test('Check Organizations views and paging', async ({ organizationsPage }) => {
    await test.step('Check view: Active Organizations', async () => {
      await expect(organizationsPage.activeNavLink).toHaveText('Organizations');

      await organizationsPage.viewSelectorButton.click();
      await organizationsPage.extensionFrame.getByText('Active Organizations').click();
      await organizationsPage.waitForExtensionIframeLoading();
      await expect(organizationsPage.viewSelectorButton).toHaveText('Active Organizations');

      await expectGridLoadedWithoutError(organizationsPage);
      const orgItemStatusItems = organizationsPage.gridTable.getByTestId('status-chip');
      await expect(orgItemStatusItems.filter({ hasNotText: /^Active$/ })).toHaveCount(0);
    });

    await test.step('Check view: Deleted Organizations', async () => {
      await organizationsPage.viewSelectorButton.click();
      await organizationsPage.extensionFrame.getByText('Deleted Organizations').click();
      await organizationsPage.waitForExtensionIframeLoading();
      await expect(organizationsPage.viewSelectorButton).toHaveText('Deleted Organizations');

      await expectGridLoadedWithoutError(organizationsPage);
      const orgItemStatusItems = organizationsPage.gridTable.getByTestId('status-chip');
      await expect(orgItemStatusItems.filter({ hasNotText: /^Deleted$/ })).toHaveCount(0);
    });

    /**
     * Refreshes the Default view and captures the live API response for page 1:
     * 10 rows, excluding deleted organizations, newest updated first.
     * Compares the first five UI rows with the API IDs and names in order.
     * Checks that first-column IDs follow the FORG-####-####-#### format.
     * Checks that displayed Client IDs follow the ACC-####-#### format.
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
      expect(organizations.items.length, 'Page size of 10 is applied').toBe(Math.min(10, organizations.total));
      expect(organizations.total).toBeGreaterThanOrEqual(organizations.items.length);

      const updatedTimes = organizations.items.map(item => Date.parse(item.events.updated.at));
      for (const item of organizations.items) {
        expect(item).toMatchObject({ id: expect.any(String), name: expect.any(String) });
        expect(item.status).not.toBe('deleted');
        expect(Number.isFinite(Date.parse(item.events.updated.at)), `Valid updated timestamp for organization ${item.id}`).toBe(true);
      }
      expect(updatedTimes, 'API organizations are ordered by updated time descending').toEqual([...updatedTimes].sort((a, b) => b - a));

      await expectGridLoadedWithoutError(organizationsPage);
      await expect(organizationsPage.columnHeaders).toContainText(headings);
      await expect(organizationsPage.gridDataRows).toHaveCount(organizations.items.length);
      for (let index = 0; index < Math.min(5, organizations.items.length); index++) {
        const organization = organizations.items[index];
        const row = organizationsPage.gridDataRows.nth(index);
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
      }

      const statusChips = organizationsPage.gridTable.getByTestId('status-chip');
      await expect(statusChips.filter({ hasText: /^Deleted$/ })).toHaveCount(0);
    });

    await test.step('Check paging: next, previous page buttons, enter specific page number, ', async () => {
      await organizationsPage.viewSelectorButton.click();
      await organizationsPage.toolbarDropdown.getByText('Default', { exact: true }).click();
      await expect(organizationsPage.viewSelectorButton).toHaveText('Default');

      await organizationsPage.selectPageSize(PAGE_SIZE);
      await expectGridLoadedWithoutError(organizationsPage);
      await expect(organizationsPage.pageSizeButton).toHaveText(String(PAGE_SIZE));
      await expect(organizationsPage.gridDataRows).toHaveCount(PAGE_SIZE);
      await organizationsPage.pageInput.fill('1');
      await organizationsPage.pageInput.press('Enter');
      await expectGridLoadedWithoutError(organizationsPage);
      await expect(organizationsPage.pageInput).toHaveValue('1');

      const totalRows = totalRowsFromRange(await organizationsPage.pageRange.innerText());
      expect(totalRows, `Paging needs more than ${2 * PAGE_SIZE} organizations to reach page 3`).toBeGreaterThan(2 * PAGE_SIZE);
      await expect(organizationsPage.pageRange).toHaveText(rangeText(1, totalRows));
      await expect(organizationsPage.pageCount).toHaveText(String(Math.ceil(totalRows / PAGE_SIZE)));

      const firstRowLink = organizationsPage.gridDataRows.first().getByRole('link').first();
      const firstPageHref = String(await firstRowLink.getAttribute('href'));

      await organizationsPage.nextPageButton.click();
      await expectGridLoadedWithoutError(organizationsPage);
      await expect(organizationsPage.pageInput).toHaveValue('2');
      await expect(organizationsPage.pageRange).toHaveText(rangeText(2, totalRows));
      await expect(firstRowLink).not.toHaveAttribute('href', firstPageHref);

      await organizationsPage.previousPageButton.click();
      await expectGridLoadedWithoutError(organizationsPage);
      await expect(organizationsPage.pageInput).toHaveValue('1');
      await expect(organizationsPage.pageRange).toHaveText(rangeText(1, totalRows));
      await expect(firstRowLink).toHaveAttribute('href', firstPageHref);

      await organizationsPage.pageInput.fill('3');
      await organizationsPage.pageInput.press('Enter');
      await expectGridLoadedWithoutError(organizationsPage);
      await expect(organizationsPage.pageInput).toHaveValue('3');
      await expect(organizationsPage.pageRange).toHaveText(rangeText(3, totalRows));
      await expect(organizationsPage.gridDataRows).toHaveCount(PAGE_SIZE);
    });
  });
});
