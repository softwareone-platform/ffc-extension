import { AccountRead, EntitlementRead } from "~api/ffc-api-model";

export type Account = AccountRead & { integration: string };
export type Entitlement = EntitlementRead & {
  owner: {
    id: string;
    external_id: string;
    name: string;
    type: "operations" | "affiliate";
    integration: "aws" | "google" | "microsoft";
  };
};
