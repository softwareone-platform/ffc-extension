import { Page } from '@playwright/test';

import { PlatformPage } from './platform-page';

export class PlatformUsersPage extends PlatformPage {
  constructor(page: Page) {
    super(page, '/administration/settings/users');
  }
}
