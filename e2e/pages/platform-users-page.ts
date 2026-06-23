import { PlatformPage } from './platform-page';
import { Page } from '@playwright/test';

export class PlatformUsersPage extends PlatformPage {
  constructor(page: Page) {
    super(page, '/administration/settings/users');
  }
}
