import { FrameLocator, Locator, Page } from '@playwright/test';
import { PlatformPage } from './platform-page';
import { debugLog, errorLog } from '../utils/debug-logging';
import { LARGE_DATA_TIMEOUT } from '../playwright.config';

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
  readonly resetFilters: Locator;
  readonly addAnotherCondition: Locator;
  readonly fieldSelectInput: Locator;
  readonly conditionalOperatorSelectInput: Locator;
  readonly valueInput: Locator;

  readonly gridTable: Locator;
  readonly toolbarDropdown: Locator;

  readonly wizardModalHeaderTitle: Locator;
  readonly wizardModalSaveBtn: Locator;

  protected constructor(page: Page, url: string) {
    super(page, '');
    this.url = url;
    this.extensionFrame = this.main.frameLocator('(//iframe)[1]');
    this.dataRefreshSpinner = this.extensionFrame.getByTestId('grid__info-dialog__refresh');

    this.navigationHeaderBar = this.extensionFrame.getByTestId('navigation__header-bar');
    this.navigationHeaderBarSubtitle = this.navigationHeaderBar.getByTestId('navigation__header-bar__subtitle');
    this.navHeaderBarList = this.page.getByTestId('navigation__header-bar__list');
    this.activeNavLink = this.navHeaderBarList.locator('a[aria-current="page"]');

    this.tabsNavItems = this.extensionFrame.getByTestId('tabs-nav__items');
    this.generalTab = this.tabsNavItems.getByTestId('tab-general');
    this.addBtn = this.extensionFrame.getByRole('button', { name: 'Add' });

    //Filters
    this.filteredByButton = this.extensionFrame.getByTestId('filter-selector__selector-button');
    this.filterPopover = this.extensionFrame.getByTestId('filter-selector__popover__content');
    this.resetFilters = this.extensionFrame.getByTestId('filter-selector__popover__reset-filters');
    this.addAnotherCondition = this.extensionFrame.getByTestId('filter-selector__popover__add-another-condition');
    this.fieldSelectInput = this.extensionFrame.getByTestId('expression-row__field-select__input__input-text');
    this.conditionalOperatorSelectInput = this.extensionFrame.getByTestId('expression-row__conditional-operator-select__input__input-text');
    this.valueInput = this.extensionFrame.getByTestId('expression-row__value-input__input-text');

    this.gridTable = this.extensionFrame.getByTestId('grid__table');
    this.toolbarDropdown = this.extensionFrame.getByTestId('grid__toolbar__view-selector__dropdown');

    this.wizardModalHeaderTitle = this.wizardFrame.locator('//div[@class="modal-header-title"]');
    this.wizardModalSaveBtn = this.wizardFrame.getByRole('button', { name: 'Save' });
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
    try {
      await this.dataRefreshSpinner.first().waitFor({ timeout: 1000 });
    } catch (_error) {
      return; // Exit the method if the loading image is not present.
    }
    try {
      debugLog('Waiting for data refreshing dialog to disappear...');
      await this.dataRefreshSpinner.waitFor({ state: 'hidden', timeout: timeout });
    } catch (_error) {
      errorLog('[ERROR] Loading data refreshing did not disappear within the timeout.'); // Log a warning if the image remains visible after the timeout.
    }
  }

  /**
   * Resets grid filters when a filtered state is currently applied.
   *
   * The method checks for the "Filtered by:" indicator, opens the filter popover,
   * clicks reset, waits for the popover to close, and waits for any data refresh
   * message to disappear.
   *
   * @returns {Promise<void>} Resolves when filters are reset or no reset is needed.
   */
  async resetFiltersIfFiltered(): Promise<void> {
    await this.filteredByButton.waitFor();
    if (await this.filteredByButton.filter({ hasText: 'Filtered by:' }).isVisible()) {
      await this.filteredByButton.click();
      await this.filterPopover.waitFor();
      await this.resetFilters.click();
      await this.filterPopover.waitFor({ state: 'hidden' });
      await this.waitForDataRefreshingMessageToDetach();
    }
  }

  /**
   * Evaluates whether a tab element is currently active.
   *
   * Inspects the tab's CSS class list in the browser context and returns `true`
   * if any class name starts with `_tab__active`, which is the convention used
   * in this codebase to mark the selected tab.
   *
   * @param {Locator} tab - The locator for the tab element to evaluate.
   * @returns {Promise<boolean>} Resolves to `true` if the tab has the active class, `false` otherwise.
   *
   * @remarks
   * - The check relies on the CSS class prefix `_tab__active`. If the component
   *   library or CSS modules naming changes, this detection logic may need updating.
   * - This method evaluates in the browser context via `element.evaluate`.
   */
  async evaluateActiveTab(tab: Locator): Promise<boolean> {
    return await tab.evaluate(el => {
      return Array.from(el.classList).some(className => className.startsWith('_tab__active'));
    });
  }
}
