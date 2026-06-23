import { AccountRead } from "@swo/ffc-api-model";

export type Account = AccountRead & { integration: string };
