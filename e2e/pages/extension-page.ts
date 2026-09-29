import { FrameLocator, Locator, Page } from '@playwright/test';

import { LARGE_DATA_TIMEOUT } from '../utils/config';
import { debugLog, errorLog } from '../utils/debug-logging';
import { getCurrentEnv } from '../utils/env';
import { PlatformPage } from './platform-page';

export abstract class ExtensionPage extends PlatformPage {
  readonly url: string;
  readonly extensionFrame: FrameLocator;
  readonly dataRefreshSpinner: Locator;

  readonly navigationHeaderBar: Locator;
  readonly navigationHeaderBarSubtitle: Locator;
  readonly navHeaderBarList: Locator;
  readonly activeNavLink: Locator;

  readonly tabsNavItems: Locator;
  readonly generalTab: Locator;
  readonly addBtn: Locator;

  readonly filteredByButton: Locator;
  readonly filterPopover: Locator;
  readonly filterPopoverCloseButton: Locator;
  readonly resetFilters: Locator;
  readonly addAnotherCondition: Locator;
  readonly conditionRemoveButtons: Locator;
  readonly fieldSelectInput: Locator;
  readonly conditionalOperatorSelectInput: Locator;
  readonly valueInput: Locator;
  readonly valueSelectInput: Locator;

  readonly gridTable: Locator;
  readonly toolbarDropdown: Locator;

  readonly wizardModalHeaderTitle: Locator;
  readonly wizardModalSaveBtn: Locator;

  protected constructor(page: Page, url: string) {
    super(page, '');
    this.url = url;
    // The host serves every plug from https://<extension-id>.<extensions-domain>/bootstrap/,
    // so matching the src pins us to this extension rather than whichever iframe renders first.
    // Case-insensitive because the id becomes a hostname, which the browser may lower-case.
    this.extensionFrame = this.main.locator(`iframe[src*="${getCurrentEnv().extensionId}" i]`).contentFrame();
    this.dataRefreshSpinner = this.extensionFrame.getByTestId('grid__info-dialog__refresh');

    this.navigationHeaderBar = this.extensionFrame.getByTestId('navigation__header-bar');
    this.navigationHeaderBarSubtitle = this.navigationHeaderBar.getByTestId('navigation__header-bar__subtitle');
    // The extension renders its own nav inside the iframe, so these must be
    // frame-scoped: page.getByTestId() does not pierce iframes.
    this.navHeaderBarList = this.extensionFrame.getByTestId('navigation__header-bar__list');
    this.activeNavLink = this.navHeaderBarList.locator('a[aria-current="page"]');

    // Per-entity tabs are router links in the top bar, marked with aria-current.
    this.tabsNavItems = this.extensionFrame.getByTestId('navigation__top-bar__list');
    this.generalTab = this.tabsNavItems.getByRole('link', { name: 'General', exact: true });
    this.addBtn = this.extensionFrame.getByRole('button', { name: 'Add' });

    //Filters
    this.filteredByButton = this.extensionFrame.getByTestId('filter-selector__selector-button');
    this.filterPopover = this.extensionFrame.getByTestId('filter-selector__popover__content');
    // Lives in the popover header, outside __content.
    this.filterPopoverCloseButton = this.extensionFrame.getByTestId('filter-selector__popover__close-button');
    this.resetFilters = this.extensionFrame.getByTestId('filter-selector__popover__reset-filters');
    this.addAnotherCondition = this.extensionFrame.getByTestId('filter-selector__popover__add-another-condition');
    this.conditionRemoveButtons = this.filterPopover.getByTestId(/^expression-row--\d+__remove-condition$/);
    // A view can arrive with conditions already applied, and every row repeats the same
    // test ids, so the fields must be scoped to the row `addAnotherCondition` appended.
    // Anchored: `expression-row--0001__remove-condition` and the logical-operator select
    // share the row's prefix, and a loose match makes `last()` the trash button.
    const newestCondition = this.filterPopover.getByTestId(/^expression-row--\d+$/).last();
    this.fieldSelectInput = newestCondition.getByTestId('expression-row__field-select__input__input-text');
    this.conditionalOperatorSelectInput = newestCondition.getByTestId('expression-row__conditional-operator-select__input__input-text');
    this.valueInput = newestCondition.getByTestId('expression-row__value-input__input-text');
    // `list` fields render a select here, which nests one testid level deeper than a text box.
    this.valueSelectInput = newestCondition.getByTestId('expression-row__value-input__input__input-text');

    this.gridTable = this.extensionFrame.getByTestId('grid__table');
    this.toolbarDropdown = this.extensionFrame.getByTestId('grid__toolbar__view-selector__dropdown');

    // Modals render inside the extension iframe (not a separate wizard iframe). The
    // design-system Modal.Header tags its title with data-testid="modal-header-title",
    // which is stable across the hashed CSS-module class name.
    this.wizardModalHeaderTitle = this.extensionFrame.getByTestId('modal-header-title');
    this.wizardModalSaveBtn = this.extensionFrame.getByRole('button', { name: 'Save' });
  }

  /**
   * Waits for the extension iframe to finish loading.
   *
   * This method waits until the `body` element inside the extension's iframe is
   * attached to the DOM, indicating that the iframe content has been loaded and is
   * ready for interaction. It is useful as a precondition before interacting with
   * any elements inside `extensionFrame`.
   *
   * @param {number} [timeout=10000] - Maximum time in milliseconds to wait for the
   *   iframe body to appear. Defaults to 10 000 ms.
   * @returns {Promise<void>} Resolves when the iframe body is present in the DOM.
   *
   * @example
   * // Ensure the extension iframe is ready before interacting with its contents
   * await resourcesPage.waitForExtensionIframeLoading();
   * await resourcesPage.extensionFrame.getByRole('button', { name: 'Add' }).click();
   *
   * @remarks
   * - Targets `extensionFrame`, which is the first `<iframe>` inside `<main>`.
   * - Resolves on DOM attachment, not full render; call additional waits (e.g.
   *   `waitForDataRefreshMessageToDetach`) if the iframe content itself has a
   *   loading state.
   */
  async waitForExtensionIframeLoading(timeout: number = 10000): Promise<void> {
    debugLog('Waiting for extension frame to load...');
    await this.extensionFrame.locator('body').waitFor({ timeout: timeout });
  }

  /** Extension-internal routes — not portal menu entries. */
  async openNavTab(name: string): Promise<void> {
    debugLog(`Opening extension nav tab: ${name}`);
    await this.navHeaderBarList.getByRole('link', { name, exact: true }).click();
    await this.waitForExtensionIframeLoading();
  }

  /**
   * Waits for the data-refreshing spinner/dialog to disappear from the grid.
   *
   * This method first ensures the grid table is present in the DOM, then checks
   * whether the data-refresh spinner is visible. If the spinner is not present it
   * returns immediately; otherwise it waits for the spinner to become hidden before
   * continuing. It is useful for ensuring that a grid has finished refreshing its
   * data before assertions or further interactions are made.
   *
   * @param {number} [timeout=LARGE_DATA_TIMEOUT] - Maximum time in milliseconds to
   *   wait for the spinner to disappear. Defaults to `LARGE_DATA_TIMEOUT`.
   * @returns {Promise<void>} Resolves when the spinner is hidden or was never present.
   *
   * @example
   * // Wait for the grid to finish refreshing before asserting row count
   * await resourcesPage.waitForDataRefreshingMessageToDetach();
   * const rows = await resourcesPage.gridTable.locator('tr').count();
   *
   * @remarks
   * - The grid table (`grid__table`) is awaited first to guarantee the grid has
   *   mounted before checking for the spinner.
   * - If the spinner does not disappear within the timeout, an error is logged but
   *   no exception is thrown, allowing the test to continue.
   */
  async waitForDataRefreshingMessageToDetach(timeout: number = LARGE_DATA_TIMEOUT): Promise<void> {
    await this.gridTable.waitFor();

    if (!(await this.probeVisible(this.dataRefreshSpinner))) return;

    try {
      debugLog('Waiting for data refreshing dialog to disappear...');
      await this.dataRefreshSpinner.waitFor({ state: 'hidden', timeout: timeout });
    } catch (_error) {
      errorLog('Data refresh spinner did not disappear within the timeout.');
    }
  }

  /**
   * The popover has no apply button: conditions take effect as you edit it, and it
   * stays open until explicitly dismissed. Every filter interaction must end here.
   */
  async closeFilterPopover(): Promise<void> {
    await this.filterPopoverCloseButton.click();
    await this.filterPopover.waitFor({ state: 'hidden' });
    await this.waitForDataRefreshingMessageToDetach();
  }

  /**
   * Empties the open popover of conditions. `resetFilters` is not a substitute: it
   * restores the view's own defaults, which is where the stray Status condition comes
   * from. Rows re-index on every delete, so the first button is clicked repeatedly.
   */
  async removeAllConditions(): Promise<void> {
    const conditions = await this.conditionRemoveButtons.count();

    for (let removed = 0; removed < conditions; removed++) {
      await this.conditionRemoveButtons.first().click();
    }
  }

  /** Appends a condition and points it at a field and operator; the caller sets the value. */
  async addCondition(field: string, operator: string): Promise<void> {
    await this.addAnotherCondition.click();
    await this.fieldSelectInput.click();
    await this.filterPopover.getByRole('option', { name: field, exact: true }).click();
    await this.conditionalOperatorSelectInput.click();
    await this.filterPopover.getByRole('option', { name: operator, exact: true }).click();
  }

  /** For `list` fields, whose value is picked from a dropdown rather than typed. */
  async selectConditionValue(value: string): Promise<void> {
    await this.valueSelectInput.click();
    await this.filterPopover.getByRole('option', { name: value, exact: true }).click();
  }

  /** No-op when the grid is unfiltered, so specs can call it as a precondition. */
  async resetFiltersIfFiltered(): Promise<void> {
    await this.filteredByButton.waitFor();
    if (!(await this.filteredByButton.filter({ hasText: 'Filtered by:' }).isVisible())) return;

    await this.filteredByButton.click();
    await this.filterPopover.waitFor();
    await this.resetFilters.click();
    await this.closeFilterPopover();
  }
}
