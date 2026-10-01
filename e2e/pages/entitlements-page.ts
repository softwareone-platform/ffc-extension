import { Locator, Page } from '@playwright/test';

import { extensionRoute } from '../utils/extension-root';
import { ExtensionPage } from './extension-page';

export class EntitlementsPage extends ExtensionPage {
  /** App-owned root for this screen; everything below is scoped to it. */
  readonly grid: Locator;
  readonly rows: Locator;
  readonly viewSelectorButton: Locator;

  readonly pageInput: Locator;
  readonly pageCount: Locator;
  readonly nextPageButton: Locator;
  readonly previousPageButton: Locator;
  readonly pageSizeButton: Locator;

  constructor(page: Page) {
    super(page, extensionRoute('entitlements'));

    this.grid = this.extensionFrame.getByTestId('ffc-extension__entitlements-grid');
    this.rows = this.grid.locator('tbody tr');
    this.viewSelectorButton = this.grid.getByTestId('grid__toolbar__view-selector__selector-button');

    const pagination = this.grid.getByTestId('pagination');
    this.pageInput = pagination.getByTestId('pagination__page-input');
    this.pageCount = pagination.getByTestId('pagination__page-count');
    this.nextPageButton = pagination.getByTestId('pagination__navigation__next__button');
    this.previousPageButton = pagination.getByTestId('pagination__navigation__previous__button');
    this.pageSizeButton = pagination.getByTestId('pagination__page-size-selector__button');
  }

  /** Entitlement names render as links to `/entitlements/<id>/general`. */
  entitlementLink(name: string): Locator {
    return this.grid.getByRole('link', { name, exact: true });
  }

  rowByEntitlement(name: string): Locator {
    return this.rows.filter({ has: this.entitlementLink(name) });
  }

  statusChip(name: string): Locator {
    return this.rowByEntitlement(name).getByTestId('status-chip');
  }

  rowActionsButton(name: string): Locator {
    return this.rowByEntitlement(name).getByTestId('dropdown__popover__target');
  }

  firstRowWithStatus(status: string): Locator {
    return this.rows.filter({ has: this.grid.getByTestId('status-chip').filter({ hasText: status }) }).first();
  }

  /**
   * `<thead>` holds a duplicate sticky copy of every header (`grid-fixed-row`),
   * so column locators must exclude it or they match twice and fail strict mode.
   * Only `name`, `affiliate` and `status` render a dropdown.
   */
  columnHeaderMenu(field: 'name' | 'affiliate' | 'status'): Locator {
    return this.grid.locator('thead tr:not([data-is-pinned="true"])').getByTestId(`${field}__Action-Dropdown__popover`);
  }
}
