import { AccountRead, EntitlementRead } from "~api/ffc-api-model";

export type Account = AccountRead;
export type Entitlement = EntitlementRead;

export type EntitlementAction = "redeem" | "terminate" | "delete";
