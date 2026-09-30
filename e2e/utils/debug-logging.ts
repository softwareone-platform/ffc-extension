import { Page } from '@playwright/test';

import { env } from './env';
import { formatDateToYmdHms, limitString } from './format';

export function debugLog(message: string, messageType: string = 'debug'): void {
  if (!env.debugLog) return;

  console.log(`${formatDateToYmdHms(new Date())} [${limitString(messageType.toUpperCase(), 10)}]: ${message}`);
}

export function errorLog(message: string): void {
  console.error(`[ERROR] ${message}`);
}

/** Forwards the page's console errors to the test output when BROWSER_ERROR_LOGGING=true. */
export function logBrowserConsoleErrors(page: Page): void {
  if (!env.browserErrorLogging) return;

  page.on('console', message => {
    if (message.type() === 'error') {
      errorLog(`Browser console: ${message.text()}`);
    }
  });
}
