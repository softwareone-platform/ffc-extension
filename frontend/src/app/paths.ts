import { PATHS as entitlements } from "~features/entitlements/paths";
import { PATHS as organizations } from "~features/organizations/paths";

// App-level aggregator: cross-feature URLs and a single import for callers
// (e.g. MainLayout) that touch more than one feature. Per-feature files own
// their own SEGMENTS / PARAMS / PATHS — import those directly when scoped.
export const PATHS = {
  root: "/",
  entitlements,
  organizations,
} as const;
