import { NavGroupConfig } from "~features/adobe/navigation.config";
import { PATHS } from "~features/adobe/paths";

// ACME theme side-menu toggles. Active when APP_THEME=acme.
// Disabled groups/items are filtered out by navigation.ts.
export const navGroups: NavGroupConfig[] = [
  {
    label: "Stay current",
    icon: { name: "flag" },
    enabled: true,
    items: [
      { label: "News and updates", path: PATHS.newsAndUpdates, enabled: true },
      { label: "Spotlight", path: PATHS.spotlight, enabled: false },
    ],
  },
  {
    label: "Catalog123",
    icon: { name: "category" },
    enabled: true,
    items: [
      { label: "Products", path: PATHS.products, enabled: true },
      { label: "Price lists", path: PATHS.priceLists, enabled: false },
    ],
  },
  {
    label: "Marketplace",
    icon: { name: "storefront" },
    enabled: true,
    items: [
      { label: "Agreements", path: PATHS.agreements, enabled: true },
      { label: "Subscriptions", path: PATHS.subscriptions, enabled: false },
      { label: "Assets", path: PATHS.assets, enabled: false },
      { label: "Entitlements", path: PATHS.entitlements, enabled: true },
      { label: "Orders", path: PATHS.orders, enabled: true },
    ],
  },
  {
    label: "Billing",
    icon: { name: "payments" },
    enabled: false,
    items: [
      { label: "Invoices", path: PATHS.invoices, enabled: true },
      { label: "Credit Memos", path: PATHS.creditMemos, enabled: true },
    ],
  },
];
