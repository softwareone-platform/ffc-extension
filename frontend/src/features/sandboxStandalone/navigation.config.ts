import { SideNavGroup, SideNavItem } from "@swo/design-system/navigation";

import {
  NavGroupId,
  navGroupDefinitions,
  topLevelSections,
} from "~features/sandboxStandalone/manifest";

export type NavItemConfig = SideNavItem & { enabled?: boolean };
export type NavGroupConfig = Omit<SideNavGroup, "items"> & {
  enabled?: boolean;
  items: NavItemConfig[];
};

const navItemsByGroup = (groupId: NavGroupId): NavItemConfig[] =>
  topLevelSections
    .filter((section) => section.nav?.groupId === groupId)
    .map((section) => ({
      label: section.nav?.label ?? section.path,
      path: section.path,
      enabled: section.enabled !== false && section.nav?.enabled !== false,
    }));

/**
 * Side-menu definition derived from `manifest.ts`. Flip `enabled` to `false`
 * on group/section entries in the manifest to hide them.
 * `navigation.ts` filters this into the `SideNavGroup[]` the layout renders.
 */
export const navGroups: NavGroupConfig[] = [
  {
    label: navGroupDefinitions.stayCurrent.label,
    icon: { name: "flag" },
    enabled: navGroupDefinitions.stayCurrent.enabled,
    items: navItemsByGroup("stayCurrent"),
  },
  {
    label: navGroupDefinitions.catalog.label,
    icon: { name: "category" },
    enabled: navGroupDefinitions.catalog.enabled,
    items: navItemsByGroup("catalog"),
  },
  {
    label: navGroupDefinitions.marketplace.label,
    icon: { name: "storefront" },
    enabled: navGroupDefinitions.marketplace.enabled,
    items: navItemsByGroup("marketplace"),
  },
  {
    label: navGroupDefinitions.billing.label,
    icon: { name: "payments" },
    enabled: navGroupDefinitions.billing.enabled,
    items: navItemsByGroup("billing"),
  },
];
