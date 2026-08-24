import { Locator, Page } from '@playwright/test';

import { debugLog } from '../utils/debug-logging';
import { ExtensionPage } from './extension-page';

export class OrganizationDetailsPage extends ExtensionPage {
  readonly orgDetailsTitle: Locator;

  readonly dataSourcesTab: Locator;
  readonly usersTab: Locator;

  readonly addUserEmailInput: Locator;
  readonly addUserNameInput: Locator;

  constructor(page: Page) {
    super(page, '/');

    this.orgDetailsTitle = this.extensionFrame.locator('//span[@class="organization-details-title"]');
    this.dataSourcesTab = this.tabsNavItems.getByTestId('tab-data-sources');

    //UsersTab
    this.usersTab = this.tabsNavItems.getByTestId('tab-users');
    this.addUserEmailInput = this.wizardFrame.locator('input#email');
    this.addUserNameInput = this.wizardFrame.locator('input#display_name');
  }
  /**
   * Clicks a tab if it is not already the active tab.
   *
   * Evaluates the tab's active state and performs a click only when it is not
   * currently selected, preventing unnecessary navigation or re-renders.
   *
   * @param {Locator} tab - The locator for the tab element to activate.
   * @returns {Promise<void>} Resolves when the tab is active.
   */
  async selectTabIfNotActive(tab: Locator): Promise<void> {
    const isActive = await this.evaluateActiveTab(tab);
    if (!isActive) {
      await tab.click();
    }
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
    await this.addAnotherCondition.click();
    await this.fieldSelectInput.click();
    await this.filterPopover.getByRole('option', { name: 'Email' }).click();
    await this.conditionalOperatorSelectInput.click();
    await this.filterPopover.getByRole('option', { name: 'Contains', exact: true }).click();
    await this.valueInput.fill(email);
    await this.waitForFilterCommitted('Email');
    await this.closeFilterPopover();
  }

  /**
   * Returns a locator for the table row that contains the given email address.
   *
   * Traverses up from a `<span>` with the exact email text to find its ancestor
   * `<tr>` element, allowing further interactions or assertions on the whole row.
   *
   * @param {string} email - The exact email address to locate in the table.
   * @returns {Promise<Locator>} Resolves to a locator for the matching row.
   */
  async getTableRowByEmail(email: string): Promise<Locator> {
    return this.extensionFrame.locator(`//span[.="${email}"]/ancestor::tr`);
  }
}
