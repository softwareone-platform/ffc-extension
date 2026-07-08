import { PropsWithChildren } from "react";

import { useMeApi } from "~shared/api/useMeApi";

import { UserContext } from "./UserContext";

export function UserProvider({ children }: PropsWithChildren) {
  const { data: me } = useMeApi();

  if (!me) {
    return <></>;
  }

  return <UserContext.Provider value={me}>{children}</UserContext.Provider>;
}
