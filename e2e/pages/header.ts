import { Locator, Page } from '@playwright/test';

import { PlatformPage } from './platform-page';

export class Header extends PlatformPage {
  readonly header: Locator;
  readonly navigationMenuBtn: Locator;
  readonly navigationMenu: Locator;
  readonly navigationMenuSettings: Locator;
  readonly navigationMenuFinOpsForCloud: Locator;
  readonly menuContent: Locator;
  readonly usersMenuItem: Locator;

  readonly tenantName: Locator;

  constructor(page: Page) {
    super(page, '/');
    this.header = this.page.locator('header').first();
    this.navigationMenuBtn = this.header.getByTestId('navigation-menu-toggle');
    this.navigationMenu = this.header.getByTestId('navigation-menu');
    this.navigationMenuSettings = this.page.getByTestId('side-menu').getByRole('button', { name: 'Settings' });
    this.navigationMenuFinOpsForCloud = this.navigationMenu.getByText('FinOps for Cloud', { exact: true });
    this.menuContent = this.navigationMenu.getByTestId('menu-content');
    this.usersMenuItem = this.menuContent.getByText('Users', { exact: true });

    this.tenantName = this.header.getByTestId('tenant-name');
  }
  async navigateToUsersPage(): Promise<void> {
    await this.navigationMenuBtn.click();
    await this.navigationMenuSettings.click();
    await this.usersMenuItem.click();
  }

  /** Single `portal.root` plug; Organizations/Entitlements live inside it (see ExtensionPage.openNavTab). */
  async openFinOpsForCloud(): Promise<void> {
    await this.navigationMenuBtn.click();
    await this.navigationMenuFinOpsForCloud.click();
  }
}
