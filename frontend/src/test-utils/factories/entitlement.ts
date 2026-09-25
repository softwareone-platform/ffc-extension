import type { AccountRead } from "~api/ffc-api-model";
import type { Entitlement } from "~features/entitlements/api/model";

export function makeEntitlement(overrides: Partial<Entitlement> = {}): Entitlement {
  return {
    id: "ent-1",
    name: "Entitlement 1",
    affiliate_external_id: "aff-ext-1",
    datasource_id: "ds-1",
    linked_datasource_id: "linked-ds-1",
    linked_datasource_name: "Linked DS",
    linked_datasource_type: "aws_cnr",
    status: "active",
    owner: {
      id: "own-1",
      external_id: "own-ext-1",
      name: "Owner",
      type: "affiliate",
      integration: "aws",
    },
    events: {} as Entitlement["events"],
    ...overrides,
  } as Entitlement;
}

export function makeAccount(overrides: Partial<AccountRead> = {}): AccountRead {
  return {
    id: "acc-1",
    name: "Account 1",
    external_id: "ext-1",
    type: "affiliate",
    integration: "aws",
    events: {} as AccountRead["events"],
    ...overrides,
  } as AccountRead;
}
