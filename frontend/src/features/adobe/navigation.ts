import { SideNavGroup } from "@swo/design-system/navigation";

import { PATHS } from "~features/adobe/paths";

export const sideNavGroups: SideNavGroup[] = [
  {
    label: "Stay current",
    icon: { name: "flag" },
    items: [
      { label: "News and updates", path: PATHS.newsAndUpdates },
      { label: "Spotlight", path: PATHS.spotlight },
    ],
  },
  {
    label: "Catalog",
    icon: { name: "category" },
    items: [
      { label: "Products", path: PATHS.products },
      { label: "Price lists", path: PATHS.priceLists },
    ],
  },
  {
    label: "Marketplace",
    icon: { name: "storefront" },
    items: [
      { label: "Agreements", path: PATHS.agreements },
      { label: "Subscriptions", path: PATHS.subscriptions },
      { label: "Assets", path: PATHS.assets },
      { label: "Entitlements", path: PATHS.entitlements },
      { label: "Orders", path: PATHS.orders },
    ],
  },
  {
    label: "Billing",
    icon: { name: "payments" },
    items: [
      { label: "Invoices", path: PATHS.invoices },
      { label: "Credit Memos", path: PATHS.creditMemos },
    ],
  },
];
