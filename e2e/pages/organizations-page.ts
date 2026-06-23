import { Locator, Page } from '@playwright/test';
import { debugLog } from '../utils/debug-logging';
import { ExtensionPage } from './extension-page';

/**
 * Represents the Organizations page under FinOps for Cloud.
 */
export class OrganizationsPage extends ExtensionPage {
  readonly activeOrgButton: Locator;
  readonly deletedOrgButton: Locator;

  constructor(page: Page) {
    super(page, '/');

    this.activeOrgButton = this.extensionFrame
      .getByTestId('grid__toolbar__view-selector__selector-button')
      .filter({ hasText: 'Active Organizations' });
    this.deletedOrgButton = this.extensionFrame
      .getByTestId('grid__toolbar__view-selector__selector-button')
      .filter({ hasText: 'Deleted Organizations' });
  }

  /**
   * Switches the organizations grid to the "Active Organizations" view.
   *
   * If the current view is "Deleted Organizations", it opens the view selector
   * dropdown and selects "Active Organizations".
   *
   * @returns {Promise<void>} Resolves when the active view is selected or already active.
   */
  async setActiveOrganizations(): Promise<void> {
    if (await this.deletedOrgButton.isVisible()) {
      await this.deletedOrgButton.click();
      await this.toolbarDropdown.getByText('Active Organizations').click();
    }
  }

  /**
   * Applies a grid filter so only organizations with the provided name are shown.
   *
   * The method resets existing filters, opens the filter popover, configures the
   * condition as `Name` `Equal` `<orgName>`, and waits for the popover to close.
   *
   * @param {string} orgName - The exact organization name to filter by.
   * @returns {Promise<void>} Resolves when the filter configuration is applied.
   */
  async filterOrgByName(orgName: string): Promise<void> {
    await this.resetFiltersIfFiltered();
    await this.filteredByButton.click();
    await this.addAnotherCondition.click();
    await this.fieldSelectInput.click();
    await this.filterPopover.getByRole('option', { name: 'Name' }).click();
    await this.conditionalOperatorSelectInput.click();
    await this.filterPopover.getByRole('option', { name: 'Equal', exact: true }).click();
    await this.valueInput.fill(orgName);
    await this.filterPopover.waitFor({ state: 'hidden' });
  }

  /**
   * Retrieves the locator for the first active organization's link in the grid.
   *
   * This method finds the first row containing a status cell with text "Active",
   * then targets the link in the first cell of that row.
   *
   * @returns {Promise<Locator>} Resolves to a locator for the first active organization link.
   */
  async getFirstActiveOrgLinkFromGrid(): Promise<Locator> {
    const firstActiveLink = this.extensionFrame.locator('xpath=(//td[normalize-space()="Active"])[1]/ancestor::tr/td[1]//a');
    debugLog(`First active organization link name: ${await firstActiveLink.textContent()}`);
    return firstActiveLink;
  }
}
