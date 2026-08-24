import { Browser, expect } from '@playwright/test';

import { TIMEOUTS, paths } from './config';
import { debugLog } from './debug-logging';
import { env } from './env';
import { ensureDir, safeReadJsonFile } from './file';

/** Cookies must outlive the run, so require headroom rather than just "not expired yet". */
const EXPIRY_MARGIN_MS = 5 * 60 * 1000;

type StoredCookie = { name: string; domain: string; expires: number };

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

  /** Path only; the setup project creates the file. */
  public get sessionStoragePath(): string {
    return paths.sessionFile(this.safeName);
  }

  /**
   * True when every persistent cookie is still comfortably in date. The file is
   * already origin-scoped, so a cached session can't belong to another cluster.
   */
  public hasValidSession(): boolean {
    const cookies = safeReadJsonFile<{ cookies?: StoredCookie[] }>(this.sessionStoragePath)?.cookies ?? [];
    if (cookies.length === 0) return false;

    // expires === -1 marks a session cookie, which carries no expiry to check;
    // with nothing verifiable we re-login rather than assume the session holds.
    const persistent = cookies.filter(cookie => cookie.expires > 0);
    if (persistent.length === 0) return false;

    const deadline = Date.now() + EXPIRY_MARGIN_MS;
    return persistent.every(cookie => cookie.expires * 1000 > deadline);
  }

  /** Throws on failure. */
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
