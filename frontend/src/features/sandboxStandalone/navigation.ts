import { SideNavGroup } from "@swo/design-system/navigation";

import { navGroups } from "~features/sandboxStandalone/navigation.config";

const isEnabled = <T extends { enabled?: boolean }>({ enabled }: T) => enabled !== false;

const stripEnabled = <T extends { enabled?: boolean }>(entry: T): Omit<T, "enabled"> => {
  const copy = { ...entry };
  delete copy.enabled;
  return copy;
};

export const sideNavGroups: SideNavGroup[] = navGroups
  .filter(isEnabled)
  .map((group) => ({
    ...stripEnabled(group),
    items: group.items.filter(isEnabled).map(stripEnabled),
  }))
  .filter((group) => group.items.length > 0);
