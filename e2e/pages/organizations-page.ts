import { BasePage } from './base-page';
import { Locator, Page } from '@playwright/test';

/**
 * Represents the Organizations page under FinOps for Cloud.
 */
export class OrganizationsPage extends BasePage {
  readonly navHeaderBarList: Locator;
  readonly activeNavLink: Locator;

  constructor(page: Page) {
    super(page, '/finops-for-cloud/organizations');
    this.navHeaderBarList = this.page.getByTestId('navigation__header-bar__list');
    this.activeNavLink = this.navHeaderBarList.locator('a[aria-current="page"]');
  }
}
