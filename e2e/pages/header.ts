import { PlatformPage } from './platform-page';
import { Locator, Page } from '@playwright/test';

/**
 * Represents the Header component of the page.
 * Extends the BasePage class.
 */
export class Header extends PlatformPage {
  readonly header: Locator;
  readonly navigationMenuBtn: Locator;
  readonly navigationMenu: Locator;
  readonly navigationMenuSettings: Locator;
  readonly navigationMenuFinOpsForCloud: Locator;
  readonly menuContent: Locator;
  readonly usersMenuItem: Locator;
  readonly organizationsMenuItem: Locator;
  readonly entitlementsMenuItem: Locator;

  readonly tenantName: Locator;
  readonly profileUserName: Locator;
  readonly profileSignOutBtn: Locator;

  /**
   * Initializes a new instance of the Header class.
   * @param {Page} page - The Playwright page object.
   */
  constructor(page: Page) {
    super(page, '/');
    this.header = this.page.locator('header').first();
    this.navigationMenuBtn = this.header.getByTestId('navigation-menu-toggle');
    this.navigationMenu = this.header.getByTestId('navigation-menu');
    this.navigationMenuSettings = this.page.getByTestId('side-menu').getByRole('button', { name: 'Settings' });
    this.navigationMenuFinOpsForCloud = this.navigationMenu.getByText('FinOps for Cloud', { exact: true });
    this.menuContent = this.navigationMenu.getByTestId('menu-content');
    this.usersMenuItem = this.menuContent.getByText('Users', { exact: true });
    this.organizationsMenuItem = this.menuContent.getByText('Organizations', { exact: true });
    this.entitlementsMenuItem = this.menuContent.getByText('Entitlements', { exact: true });

    this.tenantName = this.header.getByTestId('tenant-name');
    this.profileUserName = this.header.getByTestId('user-full-name');
    this.profileSignOutBtn = this.header.getByTestId('logout-btn');
  }
  /**
   * Opens the profile menu.
   * @returns {Promise<void>}
   */
  async openProfileMenu(): Promise<void> {
    await this.tenantName.click();
  }

  /**
   * Signs out the current user.
   * @returns {Promise<void>}
   */
  async signOut(): Promise<void> {
    await this.openProfileMenu();
    await this.profileSignOutBtn.click();
  }

  async navigateToUsersPage(): Promise<void> {
    await this.navigationMenuBtn.click();
    await this.navigationMenuSettings.click();
    await this.usersMenuItem.click();
  }

  /**
   * Navigates to the FinOps for Cloud > Organizations page via the navigation menu.
   * @returns {Promise<void>}
   */
  async navigateToOrganizationsPage(): Promise<void> {
    await this.navigationMenuBtn.click();
    await this.navigationMenuFinOpsForCloud.click();
    await this.organizationsMenuItem.click();
  }

  /**
   * Navigates to the FinOps for Cloud > Entitlements page via the navigation menu.
   * @returns {Promise<void>}
   */
  async navigateToEntitlementsPage(): Promise<void> {
    await this.navigationMenuBtn.click();
    await this.navigationMenuFinOpsForCloud.click();
    await this.entitlementsMenuItem.click();
  }
}
