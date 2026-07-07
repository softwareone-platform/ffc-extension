import { useContext } from "react";

import { AccountType } from "~api/ffc-api-model/types.gen";
import { UserContext } from "~shared/providers/UserContext";

export function useUserRole(): {
  user: React.ContextType<typeof UserContext> | null;
  role: AccountType | undefined;
} {
  const user = useContext(UserContext);
  const role = user?.account.type;

  return { user, role };
}
