import { Locator, Page } from '@playwright/test';
import { ExtensionPage } from './extension-page';

/**
 * Represents the Entitlements page under FinOps for Cloud.
 */
export class EntitlementsPage extends ExtensionPage {
  readonly navHeaderBarList: Locator;
  readonly activeNavLink: Locator;

  constructor(page: Page) {
    super(page, '/');
    this.navHeaderBarList = this.page.getByTestId('navigation__header-bar__list');
    this.activeNavLink = this.navHeaderBarList.locator('a[aria-current="page"]');
  }
}
