import { Locator, Page, expect } from '@playwright/test';

import { debugLog } from '../utils/debug-logging';
import { extensionRoute } from '../utils/extension-root';
import { ExtensionPage } from './extension-page';

export class OrganizationDetailsPage extends ExtensionPage {
  readonly orgDetailsTitle: Locator;
  readonly rows: Locator;

  readonly dataSourcesTab: Locator;
  readonly usersTab: Locator;

  readonly pageSizeButton: Locator;

  readonly addUserEmailInput: Locator;
  readonly addUserNameInput: Locator;

  constructor(page: Page) {
    super(page, '/');

    this.orgDetailsTitle = this.extensionFrame.locator('//span[@class="organization-details-title"]');
    this.rows = this.gridTable.locator('tbody tr');
    this.dataSourcesTab = this.tabsNavItems.getByRole('link', { name: 'Data Sources', exact: true });
    this.usersTab = this.tabsNavItems.getByRole('link', { name: 'Users', exact: true });

    this.pageSizeButton = this.extensionFrame.getByTestId('pagination__page-size-selector__button');

    this.addUserEmailInput = this.extensionFrame.locator('input#email');
    this.addUserNameInput = this.extensionFrame.locator('input#display_name');
  }

  /** Tabs are routes, so opening one by URL beats clicking through the grid. */
  async openUsersTab(organizationId: string): Promise<void> {
    await this.navigateToURL(extensionRoute(`organizations/${organizationId}/users`));
    await this.waitForExtensionIframeLoading();
    await this.waitForDataRefreshingMessageToDetach();
  }

  /** Clicks a tab only when it is not the current route, so no needless refetch. */
  async selectTabIfNotActive(tab: Locator): Promise<void> {
    if ((await tab.getAttribute('aria-current')) === 'page') return;

    await tab.click();
    await this.waitForDataRefreshingMessageToDetach();
  }

  /**
   * Grid filters are discarded whenever the grid config recomputes, so a row is found by
   * showing every record instead of filtering down to it.
   */
  async showAllRows(): Promise<void> {
    await this.pageSizeButton.click();
    await this.extensionFrame.getByRole('option', { name: '100', exact: true }).click();
    await this.waitForDataRefreshingMessageToDetach();
  }

  /**
   * Adds a new user to the organization via the wizard modal.
   *
   * Clicks the Add button, waits for the "Add user" wizard to open, fills in the
   * email and display name, submits the form, and waits for the modal to close.
   *
   * @param {string} email - The email address of the user to add.
   * @param {string} name - The display name of the user to add.
   * @returns {Promise<void>} Resolves when the modal has closed after submission.
   */
  async addUser(email: string, name: string): Promise<void> {
    await this.addBtn.click();
    await this.wizardModalHeaderTitle.filter({ hasText: 'Add user' }).waitFor();
    await this.addUserEmailInput.fill(email);
    await this.addUserNameInput.fill(name);
    await this.wizardModalSaveBtn.click();
    debugLog(`User ${name} with email ${email} added.`);
    await this.wizardModalHeaderTitle.filter({ hasText: 'Add user' }).waitFor({ state: 'detached' });
  }

  /** Leaves the users grid filtered on exactly one condition: Email contains the address. */
  async filterUsersByEmail(email: string): Promise<void> {
    await this.filteredByButton.click();
    await this.filterPopover.waitFor();
    await this.removeAllConditions();

    await this.addCondition('Email', 'Contains');
    await this.valueInput.fill(email);

    // See OrganizationsPage.filterActiveOrgByName: the value commits on a debounce that
    // closing the popover cancels, and only the rows show whether it landed.
    await expect(this.rows.first()).toContainText(email);
    await this.closeFilterPopover();
  }

  /** XPath because the row is only identifiable by climbing from the email cell. */
  tableRowByEmail(email: string): Locator {
    return this.extensionFrame.locator(`//span[.="${email}"]/ancestor::tr`);
  }
}
