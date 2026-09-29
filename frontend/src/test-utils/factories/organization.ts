import type { OrganizationRead } from "~api/ffc-api-model";

export function makeOrganization(overrides: Partial<OrganizationRead> = {}): OrganizationRead {
  return {
    id: "org-1",
    name: "Acme",
    status: "active",
    currency: "USD",
    billing_currency: "USD",
    operations_external_id: "ext-1",
    linked_organization_id: "linked-1",
    ...overrides,
  } as OrganizationRead;
}
