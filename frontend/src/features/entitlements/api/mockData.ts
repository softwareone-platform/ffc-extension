import { Account, Entitlement } from "./model";

// Static fixtures backing the sandbox entitlements API. Shapes match the real
// read types (plus the local `owner`/`integration` extensions in ./model).

const stamp = {
  at: "2026-01-15T10:00:00Z",
  by: { id: "user-ada", type: "user" as const, name: "Ada Lovelace" },
};
const events = { created: stamp, updated: stamp };

export const mockEntitlements: Entitlement[] = [
  {
    id: "ent-1",
    name: "AWS Production Spend",
    affiliate_external_id: "AFF-001",
    datasource_id: "ds-1",
    status: "active",
    events,
    owner: {
      id: "acc-affil-1",
      external_id: "AFF-001",
      name: "Contoso Affiliate",
      type: "affiliate",
      integration: "aws",
    },
  },
  {
    id: "ent-2",
    name: "Azure Tenant Spend",
    affiliate_external_id: "AFF-002",
    datasource_id: "ds-2",
    status: "new",
    events,
    owner: {
      id: "acc-affil-2",
      external_id: "AFF-002",
      name: "Fabrikam Affiliate",
      type: "affiliate",
      integration: "microsoft",
    },
  },
];

export const mockAccounts: Account[] = [
  {
    id: "acc-affil-1",
    name: "Contoso Affiliate",
    external_id: "AFF-001",
    status: "active",
    type: "affiliate",
    integration: "aws",
    events,
    account_user: null,
    stats: { entitlements: { new: 1, redeemed: 4, terminated: 0 } },
  },
  {
    id: "acc-affil-2",
    name: "Fabrikam Affiliate",
    external_id: "AFF-002",
    status: "active",
    type: "affiliate",
    integration: "microsoft",
    events,
    account_user: null,
    stats: { entitlements: { new: 2, redeemed: 1, terminated: 1 } },
  },
];
