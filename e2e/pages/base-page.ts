import { FrameLocator, Locator, Page } from '@playwright/test';
import { debugLog, errorLog } from '../utils/debug-logging';
import { LARGE_DATA_TIMEOUT } from '../playwright.config';

/**
 * Abstract class representing the base structure for all pages.
 * This class provides common functionality for interacting with web pages in Playwright tests.
 */
export abstract class BasePage {
  readonly page: Page; // The Playwright page object representing the current page.
  readonly url: string; // The URL of the page.
  readonly main: Locator;
  readonly extensionFrame: FrameLocator;
  readonly navigationHeaderBarTitle: Locator;
  readonly loadingPageImg: Locator;

  /**
   * Initializes a new instance of the BasePage class.
   * @param {Page} page - The Playwright page object.
   * @param {string} url - The URL of the page.
   */
  protected constructor(page: Page, url: string) {
    this.page = page;
    this.url = url;
    this.main = this.page.locator('main');
    this.extensionFrame = this.main.frameLocator('iframe');
    this.navigationHeaderBarTitle = this.main.getByTestId('navigation__header-bar__title');
    this.loadingPageImg = this.page.locator('#Vector_5');
  }

  /**
   * Navigates to the page URL.
   *
   * This method navigates to either a custom URL or the default page URL and waits
   * for the loading page image to disappear before continuing.
   *
   * @param {string | null} [customUrl=null] - Optional custom URL to navigate to. If not provided, uses the page's default URL.
   * @returns {Promise<void>} A promise that resolves when navigation is complete and the page has loaded.
   *
   * @example
   * // Navigate to the default page URL
   * await resourcesPage.navigateToURL();
   *
   * @example
   * // Navigate to a custom URL
   * await resourcesPage.navigateToURL('/resources?filter=active');
   *
   * @remarks
   * This method waits for the 'load' event and also ensures the loading spinner/image
   * has disappeared, providing a more reliable indication that the page is ready for interaction.
   */
  async navigateToURL(customUrl: string = null): Promise<void> {
    debugLog(`Navigating to URL: ${customUrl ? customUrl : this.url}`);
    await this.page.goto(customUrl ? customUrl : this.url, { waitUntil: 'load' });
    await this.waitForLoadingPageImgToDisappear();
    await this.waitForPageLoad(LARGE_DATA_TIMEOUT);
  }
  /**
   * Waits for the page to load completely.
   * This method uses Playwright's `waitForLoadState` to ensure the page has reached the 'load' state.
   * An optional timeout can be provided to override the default waiting time.
   *
   * @param {number} [timeout] - Optional timeout in milliseconds to wait for the page load state.
   * @returns {Promise<void>} A promise that resolves when the page has fully loaded.
   */
  async waitForPageLoad(timeout?: number): Promise<void> {
    const options = timeout ? { timeout } : undefined; // Set timeout options if provided.
    await this.page.waitForLoadState('load', options); // Wait for the page to reach the 'load' state.
  }

  /**
   * Fits the viewport to the full height of the page content.
   *
   * This method adjusts the browser viewport to match the full scrollable height
   * of the main content wrapper, up to a maximum height limit. This is useful
   * for capturing full-page screenshots or ensuring all content is visible
   * without scrolling.
   *
   * @returns {Promise<void>} A promise that resolves when the viewport has been resized.
   *
   * @example
   * // Fit viewport before taking a full-page screenshot
   * await resourcesPage.fitViewportToFullPage();
   * await resourcesPage.page.screenshot({ path: 'full-page.png' });
   *
   * @example
   * // Ensure all table rows are visible for testing
   * await poolsPage.fitViewportToFullPage();
   * const rowCount = await poolsPage.table.locator('tr').count();
   *
   * @remarks
   * - The viewport width remains unchanged to maintain consistency
   * - Maximum height is capped at 12000px to avoid GPU/OS limitations
   * - Includes an 80px header height adjustment
   * - If the main content wrapper is not found, returns 0 height (no resize)
   */
  async fitViewportToFullPage(): Promise<void> {
    const { maxHeight = 12000 } = {};
    const headerHeight = 80;
    // Get current width (keep it stable) and full content height
    const { width } = this.page.viewportSize() ?? { width: 1280 };
    const scrollHeight = await this.page.evaluate(() => {
      const contentWrapper = document.querySelector('main#mainLayoutWrapper') as HTMLElement | null;
      if (!contentWrapper) return 0;
      return Math.max(contentWrapper.scrollHeight, contentWrapper.offsetHeight, contentWrapper.clientHeight);
    });

    // Clamp to avoid GPU/OS caps (varies by browser/os)
    const targetHeight = Math.min(scrollHeight + headerHeight, maxHeight);

    await this.page.setViewportSize({ width, height: targetHeight });
  }

  /**
   * Waits for an API response whose URL contains the specified text.
   *
   * Listens for incoming network responses and resolves as soon as one is received
   * whose URL includes `urlText` and has an HTTP 200 status code.
   *
   * @param {string} urlText - A substring to match against the URL of incoming responses.
   * @param {number} timeout - Maximum time in milliseconds to wait for a matching response.
   *   Rejects if no matching response is received within this duration.
   * @returns {Promise<void>} Resolves when a matching 200 response is received.
   *
   * @example
   * // Wait for the resources API to respond
   * await basePage.waitForAPIResponseByPartialTextMatch('op=CleanExpenses', 30000);
   *
   * @remarks
   * For waiting on any one of multiple possible URLs, use
   * `waitForFirstAPIResponseByPartialTextMatch` instead.
   */
  async waitForAPIResponseByPartialTextMatch(urlText: string, timeout: number): Promise<void> {
    debugLog(`Waiting for ${urlText} API response`);
    await this.page.waitForResponse(response => response.url().includes(urlText) && response.status() === 200, { timeout });
    debugLog(`API response including ${urlText} received`);
  }

  /**
   * Waits for the first API response whose URL matches any of the provided strings.
   *
   * Resolves as soon as one matching response is received, ignoring the rest.
   * Useful when multiple endpoints may satisfy a condition and only the first is needed.
   *
   * @param {string[]} urlTexts - Array of URL substrings to match against incoming responses.
   * @param {number} timeout - Maximum time in milliseconds to wait for a matching response.
   * @returns {Promise<void>} Resolves when the first matching response is received.
   */
  async waitForFirstAPIResponseByPartialTextMatch(urlTexts: string[], timeout: number): Promise<void> {
    debugLog(`Waiting for first API response matching any of: [${urlTexts.join(', ')}]`);
    await this.page.waitForResponse(response => urlTexts.some(urlText => response.url().includes(urlText)) && response.status() === 200, {
      timeout,
    });
    debugLog(`First matching API response received`);
  }

  /**
   * Waits for the text content of an element to include the expected text.
   *
   * This method filters the locator to match only elements containing the specified
   * text, then waits for that filtered element to appear in the DOM. It is useful for
   * asserting that dynamic content has been rendered before proceeding with further
   * interactions or assertions.
   *
   * @param {Locator} locator - The locator for the element whose text content is being checked.
   * @param {string} expectedText - The text expected to be present within the element's text content.
   * @returns {Promise<void>} Resolves when the element containing the expected text is attached to the DOM.
   *
   * @example
   * // Wait for a success message to appear
   * await basePage.waitForTextContent(basePage.tooltip, 'Saved successfully');
   *
   * @example
   * // Wait for a table cell to display a specific value
   * await basePage.waitForTextContent(basePage.table.locator('td').first(), '$1,234.56');
   *
   * @remarks
   * - Uses Playwright's `filter({ hasText })` which performs a substring match, not an exact match.
   * - The method waits for the element to be attached to the DOM but does not assert visibility.
   *   Use `toBeVisible()` for stricter visibility assertions.
   */
  async waitForTextContent(locator: Locator, expectedText: string): Promise<void> {
    await locator.filter({ hasText: expectedText }).waitFor();
  }

  /**
   * Evaluates whether a button element has the active button class.
   *
   * This method inspects the CSS class list of the given button element and returns
   * `true` if any class name ends with `-button-activeButton`, which is the convention
   * used in this codebase to mark a button as active/selected.
   *
   * @param {Locator} button - The Playwright locator for the button element to evaluate.
   * @returns {Promise<boolean>} Resolves to `true` if the button has the active class, `false` otherwise.
   *
   * @example
   * // Check if a toggle button is active before clicking
   * const isActive = await basePage.evaluateActiveButton(myToggleBtn);
   * console.log(`Button is active: ${isActive}`);
   *
   * @example
   * // Use with clickButtonIfNotActive to ensure a button is activated
   * await basePage.clickButtonIfNotActive(viewToggleBtn);
   *
   * @remarks
   * - The check is based on the CSS class suffix `-button-activeButton`, which is specific
   *   to MUI-based components in this project. If the component library changes, this
   *   detection logic may need to be updated.
   * - This method evaluates the element in the browser context via `element.evaluate`.
   */
  async evaluateActiveButton(button: Locator): Promise<boolean> {
    return await button.evaluate(el => {
      return Array.from(el.classList).some(className => className.endsWith('-button-activeButton'));
    });
  }

  /**
   * Clicks a button if it is not already active.
   *
   * This method checks whether the specified button has the active class.
   * If the button is not active, it performs a click action on the button.
   *
   * @param {Locator} button - The Playwright locator representing the button to be clicked.
   * @returns {Promise<void>} A promise that resolves when the button is clicked or skipped if already active.
   */
  async clickButtonIfNotActive(button: Locator): Promise<void> {
    if (!(await this.evaluateActiveButton(button))) {
      await button.click();
    }
  }

  /**
   * Checks if an element is marked as selected using the aria-selected attribute.
   *
   * This method retrieves the `aria-selected` attribute from the specified element
   * and returns true if its value is 'true', otherwise returns false.
   * This is commonly used for checking the selection state of elements in accessible
   * UI components like tabs, options in listboxes, or tree items.
   *
   * @param {Locator} element - The Playwright locator for the element to check.
   * @returns {Promise<boolean>} A promise that resolves to true if the element has aria-selected="true", false otherwise.
   *
   * @example
   * // Check if a tab is selected
   * const tab = page.getByRole('tab', { name: 'Overview' });
   * const isSelected = await basePage.isAriaSelected(tab);
   * if (isSelected) {
   *   console.log('Tab is currently selected');
   * }
   *
   * @example
   * // Use in an assertion
   * const option = page.getByRole('option', { name: 'Option 1' });
   * await expect(await basePage.isAriaSelected(option)).toBe(true);
   *
   * @remarks
   * This method checks the ARIA attribute rather than visual state, making it
   * more reliable for accessibility-compliant components. If the aria-selected
   * attribute is not present, the method will return false.
   */
  async isAriaSelected(element: Locator): Promise<boolean> {
    return (await element.getAttribute('aria-selected')) === 'true';
  }

  /**
   * Brings the current page to the front of the browser window stack.
   *
   * This method calls Playwright's `bringToFront` on the current page, ensuring it
   * is the active/focused tab. It is useful in multi-page or multi-context test
   * scenarios where focus may have shifted to another page or popup.
   *
   * @returns {Promise<void>} Resolves when the page has been brought to the front.
   *
   * @example
   * // Bring the main page back into focus after a popup was opened
   * await basePage.bringContextToFront();
   *
   * @remarks
   * - This is a thin wrapper around Playwright's `page.bringToFront()`.
   * - Has no effect if the page is already the active tab.
   */
  async bringContextToFront(): Promise<void> {
    await this.page.bringToFront();
  }

  /**
   * Waits for an element to be detached from the DOM.
   *
   * This method waits until the specified element is removed from the DOM entirely.
   * It is useful for asserting that a modal, tooltip, spinner, or other transient
   * element has been fully dismissed before proceeding.
   *
   * @param {Locator} element - The Playwright locator for the element to wait for detachment.
   * @returns {Promise<void>} Resolves when the element has been detached from the DOM,
   *   or rejects if the default Playwright timeout is exceeded.
   *
   * @example
   * // Wait for a loading spinner to be removed before interacting with the page
   * await basePage.waitForElementDetached(basePage.progressBar);
   *
   * @example
   * // Wait for a modal to be closed and removed from the DOM
   * await confirmModal.clickCancel();
   * await basePage.waitForElementDetached(confirmModal.dialog);
   *
   * @remarks
   * - Uses Playwright's `waitFor({ state: 'detached' })`, which waits for the element
   *   to be removed from the DOM, not just hidden.
   * - If the element is already detached when this method is called, it resolves immediately.
   */
  async waitForElementDetached(element: Locator): Promise<void> {
    await element.waitFor({ state: 'detached' });
  }

  /**
   * Waits for the loading page image to disappear.
   * This method checks if the loading image is present and waits for it to become hidden.
   * It logs the waiting process and handles cases where the image does not disappear within the timeout.
   *
   * @param {number} [timeout=10000] - The maximum time to wait for the loading image to disappear, in milliseconds.
   * @returns {Promise<void>} A promise that resolves when the loading image is no longer visible or exits early if the image is not present.
   */
  async waitForLoadingPageImgToDisappear(timeout: number = LARGE_DATA_TIMEOUT): Promise<void> {
    try {
      await this.loadingPageImg.first().waitFor({ timeout: 1000 });
    } catch (_error) {
      return; // Exit the method if the loading image is not present.
    }
    try {
      debugLog('Waiting for loading page image to disappear...');
      await this.loadingPageImg.waitFor({ state: 'hidden', timeout: timeout });
    } catch (_error) {
      errorLog('[ERROR] Loading page image did not disappear within the timeout.'); // Log a warning if the image remains visible after the timeout.
    }
  }

  /**
   * Introduces a delay for a specified duration.
   *
   * This method creates a promise that resolves after the given number of milliseconds,
   * effectively pausing execution for the specified time.
   *
   * @param {number} ms - The duration of the delay in milliseconds.
   * @returns {Promise<void>} A promise that resolves after the specified delay.
   */
  async delay(ms: number): Promise<void> {
    debugLog(`Waiting for ${ms}ms...`);
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Clicks on a specified locator.
   *
   * This method performs a click action on the provided Playwright `Locator`.
   * It is useful for interacting with elements on the page, such as buttons, links, or other clickable elements.
   *
   * @param {Locator} locator - The Playwright locator representing the element to be clicked.
   * @returns {Promise<void>} A promise that resolves when the click action is completed.
   */
  async click(locator: Locator): Promise<void> {
    await locator.click();
  }

  /**
   * Toggles the state of a checkbox.
   * @param {Locator} checkbox - The locator for the checkbox element.
   * @returns {Promise<void>} A promise that resolves when the checkbox state is toggled.
   */
  async toggleCheckbox(checkbox: Locator): Promise<void> {
    const isChecked = await checkbox.isChecked();
    if (isChecked) {
      await checkbox.uncheck();
    } else {
      await checkbox.check();
    }
  }

  /**
   * Unchecks a checkbox if it is currently checked.
   *
   * This method evaluates the current state of the checkbox and performs
   * an uncheck action only if the checkbox is already checked.
   *
   * @param {Locator} checkbox - The Playwright locator representing the checkbox element.
   * @returns {Promise<void>} A promise that resolves when the checkbox is unchecked.
   */
  async uncheckCheckbox(checkbox: Locator): Promise<void> {
    const isChecked = await checkbox.isChecked();
    if (isChecked) {
      await checkbox.uncheck();
    }
  }

  /**
   * Checks a checkbox if it is currently unchecked.
   *
   * This method evaluates the current state of the checkbox and performs
   * a check action only if the checkbox is not already checked.
   *
   * @param {Locator} checkbox - The Playwright locator representing the checkbox element.
   * @returns {Promise<void>} A promise that resolves when the checkbox is checked.
   */
  async checkCheckbox(checkbox: Locator): Promise<void> {
    const isChecked = await checkbox.isChecked();
    if (!isChecked) {
      await checkbox.check();
    }
  }

  /**
   * Retrieves the current value from an input field.
   *
   * This method uses Playwright's `inputValue` function to fetch the value
   * of the specified input element.
   *
   * @param {Locator} input - The Playwright locator representing the input field.
   * @returns {Promise<string>} A promise that resolves to the current value of the input field as a string.
   */
  async getValueFromInput(input: Locator): Promise<string> {
    return await input.inputValue();
  }
}
