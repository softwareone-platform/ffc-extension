import type { ClientAccountReference } from "~api/ffc-api-model";

export function makeClientAccount(
  overrides: Partial<ClientAccountReference> = {},
): ClientAccountReference {
  return {
    id: "cli-1",
    name: "Client Co",
    external_id: "cli-ext-1",
    icon: "clients/cli-1.png",
    ...overrides,
  };
}
