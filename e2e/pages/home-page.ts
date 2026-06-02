import { BasePage } from './base-page';
import { Page } from '@playwright/test';
import { debugLog } from '../utils/debug-logging';

export class HomePage extends BasePage {
  constructor(page: Page) {
    super(page, '/');
  }

  /**
   * Waits for the first iframe on the page to be attached and ready.
   *
   * This is useful after navigation when the app shell or embedded content
   * is expected to load inside an iframe.
   *
   * @param timeout - Maximum time to wait (in milliseconds) before failing.
   * Defaults to `10000`.
   * @returns A promise that resolves when the first iframe is found within the timeout.
   */
  async waitForIframeLoading(timeout = 10000): Promise<void> {
    debugLog('Waiting for iframes to load...');
    await this.page.locator('iframe').first().waitFor({ timeout });
  }
}
