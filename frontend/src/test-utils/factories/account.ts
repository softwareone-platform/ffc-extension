import type { AccountRead } from "~api/ffc-api-model";

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
