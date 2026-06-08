import { BasePage } from './base-page';
import { Page } from '@playwright/test';

export class UsersPage extends BasePage {
  constructor(page: Page) {
    super(page, '/administration/settings/users');
  }
}
