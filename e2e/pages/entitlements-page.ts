import { Page } from '@playwright/test';

import { ExtensionPage } from './extension-page';

/** Locators are inherited from ExtensionPage. */
export class EntitlementsPage extends ExtensionPage {
  constructor(page: Page) {
    super(page, '/');
  }
}
