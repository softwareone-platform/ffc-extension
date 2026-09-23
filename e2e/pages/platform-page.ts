import { Locator, Page } from '@playwright/test';

import { LARGE_DATA_TIMEOUT } from '../utils/config';
import { debugLog, errorLog } from '../utils/debug-logging';

/** Shared portal shell: everything outside the extension iframe. */
export abstract class PlatformPage {
  readonly page: Page;
  readonly url: string;
  readonly main: Locator;
  readonly navigationHeaderBarTitle: Locator;
  readonly loadingPageImg: Locator;

  protected constructor(page: Page, url: string) {
    this.page = page;
    this.url = url;
    this.main = this.page.locator('main');

    this.navigationHeaderBarTitle = this.main.getByTestId('navigation__header-bar__title');
    this.loadingPageImg = this.page.locator('#Vector_5');
  }

  async navigateToURL(customUrl?: string): Promise<void> {
    const target = customUrl ?? this.url;
    debugLog(`Navigating to URL: ${target}`);
    await this.page.goto(target, { waitUntil: 'load' });
    await this.waitForLoadingPageImgToDisappear();
    await this.waitForPageLoad(LARGE_DATA_TIMEOUT);
  }

  async waitForPageLoad(timeout?: number): Promise<void> {
    await this.page.waitForLoadState('load', timeout ? { timeout } : undefined);
  }

  /** Non-throwing poll: a caught `waitFor` still paints a failed step in the trace. */
  protected async probeVisible(locator: Locator, timeout: number = 1_500): Promise<boolean> {
    const deadline = Date.now() + timeout;
    const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

    do {
      if (await locator.first().isVisible()) return true;
      await sleep(100);
    } while (Date.now() < deadline);

    return false;
  }

  async waitForLoadingPageImgToDisappear(timeout: number = LARGE_DATA_TIMEOUT): Promise<void> {
    if (!(await this.probeVisible(this.loadingPageImg))) return;

    try {
      debugLog('Waiting for loading page image to disappear...');
      await this.loadingPageImg.waitFor({ state: 'hidden', timeout });
    } catch (_error) {
      errorLog('Loading page image did not disappear within the timeout.');
    }
  }
}
