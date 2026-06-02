import fs from 'fs';
import { isSessionValid, storeSecretToFile } from './session-utils';
import { Browser, chromium, Response } from 'playwright-core';
import { expect } from 'playwright/test';

export default class User {
  public email: string; // The user's email address.
  public name?: string; // The user's name.
  public role?: string; // The user's role (optional).
  private readonly password: string; // The user's password.
  private readonly _safeName: string; // A sanitized version of the user's email for file naming.
  private _userToken?: string; // The user's token (optional).
  private readonly _tokenStoragePath: string; // Path to store the user's token.

  /**
   * Creates a new User instance.
   * @param email - The user's email address.
   * @param name - The user's name (optional, defaults to email).
   * @param role - The user's role (optional).
   * @param password - The user's password (optional).
   */
  constructor(email: string, password: string, name?: string, role?: string) {
    this.email = email;
    this.name = name != null ? name : email;
    this.password = password;
    this._safeName = email
      .replace(/@.*/g, '')
      .replace(/[^A-Za-z]/g, '_')
      .toUpperCase();
    this._tokenStoragePath = `.cache/${this._safeName}_${process.env.ENVIRONMENT}_TOKEN.txt`;
    this.role = role;
  }

  public get sessionStoragePath(): string {
    const path = `.cache/${this._safeName}_${process.env.ENVIRONMENT}_SESSION.json`;
    if (!fs.existsSync('.cache')) fs.mkdirSync('.cache');
    if (!fs.existsSync(path)) fs.writeFileSync(path, JSON.stringify({}));
    return path;
  }

  /**
   * Logs the user in and saves the session storage state.
   * @returns The path to the session storage file or undefined if login fails.
   */
  public async login(): Promise<string | undefined> {
    if (await isSessionValid(this.sessionStoragePath)) {
      console.log('session found valid, returning storage path');
      return this.sessionStoragePath;
    }
    // if (this._userPass == null || this._userPass == '') await this.getPassword();

    let browser: Browser | undefined;
    try {
      browser = await chromium.launch({ headless: true, timeout: 60000 });
      const page = await browser.newPage({ storageState: undefined });
      const userNameInput = page.locator('input[name="username"]');
      const passInput = page.locator('input[name="password"]');
      const actionBtn = page.locator('button[data-action-button-primary="true"]');

      // Listen for token response and save it
      page.on('response', async (response: Response) => {
        try {
          const status = response.status();
          const url = response.url();

          if (status == 200 && url.includes('oauth/token')) {
            const body = await response.json();

            console.log('Access token saved ...');
            this._userToken = body['access_token'];
            if (this._userToken != null && this.password != null)
              await storeSecretToFile(this._tokenStoragePath, this._userToken, this.password);

            console.log('Current session saved ...');
          }
        } catch {
          // Continue if login not successful
        }
      });

      await page.goto(process.env.BASE_URL);
      await expect(userNameInput).toBeVisible({ timeout: 60000 });
      await userNameInput.fill(this.email);
      await actionBtn.click();
      await expect(passInput).toBeVisible();
      await passInput.fill(this.password);
      await actionBtn.click();
      if (await page.isVisible('#error-element-password')) {
        throw new Error(`Incorrect password specified on login screen. User:${this.email}`);
      }
      expect(await page.title()).not.toContain('Login');
      await page.waitForLoadState('load', { timeout: 60000 });
      await page.context().storageState({ path: this.sessionStoragePath });
      console.log(`User ${this.email} logged in`);
      return this.sessionStoragePath;
    } catch (error) {
      console.error(`Failed to login user ${this.email}:`, error);
    } finally {
      if (browser) {
        await browser.close();
      }
    }
  }
}