import { Browser, expect } from '@playwright/test';

import { TIMEOUTS, paths } from './config';
import { debugLog } from './debug-logging';
import { env } from './env';
import { ensureDir, fileAgeMs, safeReadJsonFile } from './file';

/** Beyond this the cached session is re-created rather than probed. */
const MAX_SESSION_AGE_MS = 7 * 24 * 60 * 60 * 1000;

export default class User {
  public readonly email: string;
  public readonly name: string;
  public readonly role?: string;
  private readonly password: string;
  private readonly safeName: string;

  constructor(email: string, password: string, name?: string, role?: string) {
    this.email = email;
    this.name = name ?? email;
    this.password = password;
    this.role = role;
    this.safeName = email
      .replace(/@.*/g, '')
      .replace(/[^A-Za-z]/g, '_')
      .toUpperCase();
  }

  /** Pure path lookup — creating the file is the setup project's job. */
  public get sessionStoragePath(): string {
    return paths.sessionFile(this.safeName);
  }

  /** Cheap pre-check so we only pay for a browser probe on a plausible session. */
  public hasUsableSessionFile(): boolean {
    const state = safeReadJsonFile<{ cookies?: unknown[] }>(this.sessionStoragePath);
    if (!state?.cookies?.length) return false;

    const age = fileAgeMs(this.sessionStoragePath);
    return age !== undefined && age < MAX_SESSION_AGE_MS;
  }

  /**
   * Proves the cached session still authenticates instead of trusting the file's
   * existence — a stale cookie otherwise fails much later, inside a test.
   */
  public async hasValidSession(browser: Browser): Promise<boolean> {
    if (!this.hasUsableSessionFile()) return false;

    const context = await browser.newContext({
      storageState: this.sessionStoragePath,
      ignoreHTTPSErrors: env.ignoreHttpsErrors,
    });

    try {
      const page = await context.newPage();
      await page.goto(env.baseUrl, { waitUntil: 'domcontentloaded', timeout: TIMEOUTS.login });

      const landedOnLogin = await page
        .locator('input[name="username"]')
        .waitFor({ state: 'visible', timeout: 5_000 })
        .then(() => true)
        .catch(() => false);

      return !landedOnLogin;
    } catch {
      return false;
    } finally {
      await context.close();
    }
  }

  /** Logs in through the identity provider and persists the session. Throws on failure. */
  public async login(browser: Browser): Promise<string> {
    const context = await browser.newContext({
      storageState: undefined,
      ignoreHTTPSErrors: env.ignoreHttpsErrors,
    });

    try {
      const page = await context.newPage();
      const userNameInput = page.locator('input[name="username"]');
      const passwordInput = page.locator('input[name="password"]');
      const submitButton = page.locator('button[data-action-button-primary="true"]');

      await page.goto(env.baseUrl, { timeout: TIMEOUTS.login });

      await expect(userNameInput).toBeVisible({ timeout: TIMEOUTS.login });
      await userNameInput.fill(this.email);
      await submitButton.click();

      await expect(passwordInput).toBeVisible();
      await passwordInput.fill(this.password);
      await submitButton.click();

      await expect(page.locator('#error-element-password'), `Identity provider rejected the password for ${this.email}`).toBeHidden();

      await page.waitForLoadState('load', { timeout: TIMEOUTS.login });
      await expect(page).not.toHaveTitle(/login/i);

      ensureDir(paths.cacheDir);
      await context.storageState({ path: this.sessionStoragePath });
      debugLog(`User ${this.email} logged in against ${env.baseUrl}`);

      return this.sessionStoragePath;
    } finally {
      await context.close();
    }
  }
}
