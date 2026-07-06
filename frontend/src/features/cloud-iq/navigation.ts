import { SideNavGroup } from "@swo/design-system/navigation";

import { PATHS } from "~features/cloud-iq/paths";

export const sideNavGroups: SideNavGroup[] = [
  {
    label: "Dashboard",
    icon: { name: "home" },
    items: [
      { label: "Home", path: PATHS.home },
      { label: "Products", path: PATHS.products },
    ],
  },
  {
    label: "Accounts and Subscriptions",
    icon: { name: "category" },
    items: [
      { label: "Microsoft CSP", path: PATHS.microsoftCsp },
      { label: "Adobe", path: PATHS.adobe },
      { label: "Amazon Web Services", path: PATHS.amazonWebServices },
    ],
  },
  {
    label: "Operations",
    icon: { name: "query_stats" },
    items: [
      { label: "Transactions", path: PATHS.transactions },
      { label: "Insights", path: PATHS.insights },
      { label: "Reseller Administration", path: PATHS.resellerAdministration },
    ],
  },
  {
    label: "Administration",
    icon: { name: "settings" },
    items: [
      { label: "Support", path: PATHS.support },
      { label: "API Integrations", path: PATHS.apiIntegrations },
      { label: "Settings", path: PATHS.settings },
      { label: "Previous Cloud-iQ", path: PATHS.previousCloudIq },
    ],
  },
];
