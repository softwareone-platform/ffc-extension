import { Browser, expect } from '@playwright/test';

import { TIMEOUTS, paths } from './config';
import { debugLog } from './debug-logging';
import { env } from './env';
import { ensureDir, safeReadJsonFile, safeWriteJsonFile } from './file';

/** Cookies must outlive the run, so require headroom rather than just "not expired yet". */
const EXPIRY_MARGIN_MS = 5 * 60 * 1000;

type StoredCookie = { name: string; domain: string; expires: number };

/** `extensionRootUrl` rides along in the storageState file; Playwright copies only the
 * keys it knows when loading one, so the extra field is inert. */
type StoredSession = { cookies?: StoredCookie[]; extensionRootUrl?: string };

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
    const cookies = safeReadJsonFile<StoredSession>(this.sessionStoragePath)?.cookies ?? [];
    if (cookies.length === 0) return false;

    // expires === -1 marks a session cookie, which carries no expiry to check;
    // with nothing verifiable we re-login rather than assume the session holds.
    const persistent = cookies.filter(cookie => cookie.expires > 0);
    if (persistent.length === 0) return false;

    const deadline = Date.now() + EXPIRY_MARGIN_MS;
    return persistent.every(cookie => cookie.expires * 1000 > deadline);
  }

  /** The URL the portal redirects to when this user opens the extension from the menu. */
  public get extensionRootUrl(): string | undefined {
    return safeReadJsonFile<StoredSession>(this.sessionStoragePath)?.extensionRootUrl;
  }

  /** Merges rather than writes: `login()` owns the cookies in the same file. */
  public saveExtensionRootUrl(url: string): void {
    const session = safeReadJsonFile<StoredSession>(this.sessionStoragePath);
    if (!session) {
      throw new Error(`No session file at ${this.sessionStoragePath} to store the extension root URL in.`);
    }

    safeWriteJsonFile(this.sessionStoragePath, { ...session, extensionRootUrl: url });
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
