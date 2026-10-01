import { useContext } from "react";

import type { AccountType } from "~api/ffc-api-model";
import { UserContext } from "~shared/providers/UserContext";

export function useUserRole(): {
  user: React.ContextType<typeof UserContext> | null;
  role: AccountType | undefined;
} {
  const user = useContext(UserContext);
  const role = user?.account.type;

  return { user, role };
}
