import { SideNavGroup, SideNavItem } from "@swo/design-system/navigation";

import { PATHS } from "~features/adobe/paths";

export type NavItemConfig = SideNavItem & { enabled?: boolean };
export type NavGroupConfig = Omit<SideNavGroup, "items"> & {
  enabled?: boolean;
  items: NavItemConfig[];
};

/**
 * Full side-menu definition. Flip `enabled` to `false` on any group or item to
 * hide it. This file is theme-overridable: drop a copy under
 * `themes/<APP_THEME>/navigation.config.ts` to give a theme its own toggles.
 * `navigation.ts` filters this into the `SideNavGroup[]` the layout renders.
 */
export const navGroups: NavGroupConfig[] = [
  {
    label: "Stay current",
    icon: { name: "flag" },
    enabled: true,
    items: [
      { label: "News and updates", path: PATHS.newsAndUpdates, enabled: true },
      { label: "Spotlight", path: PATHS.spotlight, enabled: true },
    ],
  },
  {
    label: "Catalog",
    icon: { name: "category" },
    enabled: true,
    items: [
      { label: "Products", path: PATHS.products, enabled: true },
      { label: "Price lists", path: PATHS.priceLists, enabled: true },
    ],
  },
  {
    label: "Marketplace",
    icon: { name: "storefront" },
    enabled: true,
    items: [
      { label: "Agreements", path: PATHS.agreements, enabled: true },
      { label: "Subscriptions", path: PATHS.subscriptions, enabled: true },
      { label: "Assets", path: PATHS.assets, enabled: true },
      { label: "Entitlements", path: PATHS.entitlements, enabled: true },
      { label: "Orders", path: PATHS.orders, enabled: true },
    ],
  },
  {
    label: "Billing",
    icon: { name: "payments" },
    enabled: true,
    items: [
      { label: "Invoices", path: PATHS.invoices, enabled: true },
      { label: "Credit Memos", path: PATHS.creditMemos, enabled: true },
    ],
  },
];
